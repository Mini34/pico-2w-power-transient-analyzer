from machine import Pin, ADC, SoftI2C, PWM
import ssd1306
import time
import math

try:
    import instrument_state as state_store
except Exception as exc:
    state_store = None
    print("STATE | unavailable |", exc)

try:
    import wifi_manager
except Exception as exc:
    wifi_manager = None
    print("WIFI | module unavailable |", exc)

try:
    import web_server
except Exception as exc:
    web_server = None
    print("WEB  | module unavailable |", exc)

try:
    import experiment_logger
except Exception as exc:
    experiment_logger = None
    print("LOG  | module unavailable |", exc)

try:
    import fault_monitor
except Exception as exc:
    fault_monitor = None
    print("FAULT | module unavailable |", exc)

try:
    import source_characterizer
except Exception as exc:
    source_characterizer = None
    print("SOURCE | module unavailable |", exc)


# ============================================================
# HARDWARE SETUP
# ============================================================

i2c = SoftI2C(
    sda=Pin(6),
    scl=Pin(7),
    freq=50000,
    timeout=50000
)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)

INA219 = 0x40

charge_pin = Pin(0, Pin.OUT, value=0)
discharge_pin = Pin(1, Pin.OUT, value=0)
adc = ADC(26)
temp_adc = ADC(4)

button = Pin(2, Pin.IN, Pin.PULL_UP)

diode_source_pin = Pin(3, Pin.OUT, value=0)
diode_vs_adc = ADC(27)
diode_vf_adc = ADC(28)

network_manager = None
web_service = None
next_web_start_ms = None
next_temp_sample_ms = None
latest_temperature_c = None
current_device_mode = "STARTUP"

experiment_log = None
fault_service = None
source_test_session = None

if experiment_logger is not None:
    try:
        experiment_log = experiment_logger.ExperimentLogger()
    except Exception as exc:
        print("LOG  | startup error |", exc)

if fault_monitor is not None:
    try:
        fault_service = fault_monitor.FaultMonitor(experiment_log)
    except Exception as exc:
        print("FAULT | startup error |", exc)

if source_characterizer is not None:
    try:
        source_test_session = source_characterizer.GuidedSourceTest()
    except Exception as exc:
        print("SOURCE | startup error |", exc)


# ============================================================
# POWER MONITOR SETTINGS
# ============================================================

V_SLOPE = 0.98896
V_OFFSET = -0.03531
SHUNT_OHMS = 0.1
POWER_SAMPLES = 8
POWER_AUTO_SCROLL_MS = 7000

TEMP_SAMPLE_INTERVAL_MS = 5000
TEMP_SAMPLES = 16
TEMP_SAMPLE_DELAY_MS = 2
TEMP_VREF = 3.24
TEMP_DIAGNOSTICS = True


# ============================================================
# RC ANALYZER SETTINGS
# ============================================================

VREF = 3.30
R_CHARGE = 1000.0
R_DISCHARGE = 1000.0
RC_SAMPLE_MS = 100
CHARGE_TIME_MS = 6000
DISCHARGE_TIME_MS = 6000


# ============================================================
# DIODE ANALYZER SETTINGS
# ============================================================

R_TEST = 330.0
DIODE_SETTLE_MS = 180
DIODE_SAMPLES = 12
DIODE_OPEN_MA_THRESHOLD = 0.1
DIODE_LOW_VF_SHORT_MAX = 0.15

DIODE_IV_POINTS = 16
DIODE_IV_STEP_PWM = max(1, 65535 // (DIODE_IV_POINTS - 1))
DIODE_IV_PWM_STEPS = [
    i * DIODE_IV_STEP_PWM
    for i in range(1, DIODE_IV_POINTS)
]
DIODE_IV_SETTLE_MS = 110
DIODE_IV_PROGRESS_REFRESH_MS = 60
DIODE_IV_GRAPH_PAGES = 2
DIODE_IV_SLIDESHOW_MS = 4500
DIODE_IV_PWM_FREQ = 1200


# ============================================================
# BUTTON AND UI SETTINGS
# ============================================================

LONG_PRESS_MS = 700
DEBOUNCE_MS = 30

DIODE_MODE_LONG_MS = 600
DIODE_MODE_DEBOUNCE_MS = 18

MENU_ITEM_CHARS = 14
MENU_ITEM_X = 10


# ============================================================
# GENERAL OLED FUNCTIONS
# ============================================================

def clear():
    oled.fill(0)


def trim_text(text, max_chars):
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[:max_chars - 3] + "..."


def center_text(text, y):
    x = max(0, (128 - len(text) * 8) // 2)
    oled.text(text, x, y)


def set_device_mode(mode):
    global current_device_mode
    current_device_mode = mode
    if state_store is not None:
        state_store.set_mode(mode)


def sync_wifi_state():
    if state_store is None or network_manager is None:
        return
    state_store.set_wifi(
        network_manager.connected,
        network_manager.ssid,
        network_manager.ip,
        network_manager.status,
    )


def sync_logging_state():
    if state_store is None or experiment_log is None:
        return
    try:
        state_store.update_logging(experiment_log.status())
    except Exception as exc:
        print("STATE | logging sync error |", exc)


def sync_fault_state():
    if state_store is None or fault_service is None:
        return
    try:
        state_store.update_faults(fault_service.snapshot())
    except Exception as exc:
        print("STATE | fault sync error |", exc)


def log_experiment(record_type, data, status="completed"):
    if experiment_log is None:
        return None
    try:
        record = experiment_log.append_experiment(record_type, data, status)
        sync_logging_state()
        return record
    except Exception as exc:
        print("LOG  | experiment error |", exc)
        return None


def monitor_faults(
    voltage=None,
    current=None,
    power=None,
    temperature_c=None,
    ina_ok=None,
):
    if fault_service is None:
        return
    try:
        fault_service.update(
            voltage=voltage,
            current=current,
            power=power,
            temperature_c=temperature_c,
            ina_ok=ina_ok,
            mode=current_device_mode,
        )
        sync_fault_state()
        sync_logging_state()
    except Exception as exc:
        print("FAULT | monitor error |", exc)


def log_power_session(
    session_start,
    measurement_count,
    elapsed_s,
    voltage,
    current,
    power,
    min_voltage,
    peak_current,
    peak_power,
    avg_voltage,
    avg_current,
    avg_power,
    charge_mAh,
    energy_Wh,
    status="completed",
):
    if measurement_count <= 0:
        return
    log_experiment(
        "POWER",
        {
            "start_uptime_s": session_start / 1000.0,
            "elapsed_s": elapsed_s,
            "ending_voltage_v": voltage,
            "ending_current_a": current,
            "ending_power_w": power,
            "min_voltage_v": min_voltage,
            "peak_current_a": peak_current,
            "peak_power_w": peak_power,
            "avg_voltage_v": avg_voltage,
            "avg_current_a": avg_current,
            "avg_power_w": avg_power,
            "charge_mAh": charge_mAh,
            "energy_Wh": energy_Wh,
        },
        status,
    )

def read_pico_temperature(samples=TEMP_SAMPLES):
    total = 0
    for _ in range(samples):
        total += temp_adc.read_u16()
        time.sleep_ms(TEMP_SAMPLE_DELAY_MS)

    raw = total / samples
    voltage = raw * TEMP_VREF / 65535
    temp_c = 27 - ((voltage - 0.706) / 0.001721)
    return temp_c, voltage, raw


def service_temperature(allow_sample=True):
    global next_temp_sample_ms, latest_temperature_c

    if not allow_sample:
        return

    now = time.ticks_ms()
    if next_temp_sample_ms is None:
        next_temp_sample_ms = now
    if time.ticks_diff(now, next_temp_sample_ms) < 0:
        return

    next_temp_sample_ms = time.ticks_add(now, TEMP_SAMPLE_INTERVAL_MS)
    try:
        temp_c, voltage, raw = read_pico_temperature()
        latest_temperature_c = temp_c
        if state_store is not None:
            state_store.update_temperature(temp_c, voltage, raw)
        monitor_faults(temperature_c=temp_c)
        if TEMP_DIAGNOSTICS:
            print("TEMP | {:.2f} C | ADC {:.4f} V | RAW {:.0f}".format(
                temp_c, voltage, raw
            ))
    except Exception as exc:
        print("TEMP | read error |", exc)

def service_background(allow_web=True):
    # ADC(4) reads are deferred whenever a timing-sensitive acquisition calls
    # service_background(False).
    service_temperature(allow_web and current_device_mode not in ("STARTUP", "MENU"))
    global next_web_start_ms

    if state_store is not None:
        state_store.update_uptime()

    if network_manager is None:
        return

    connected = network_manager.poll()
    sync_wifi_state()

    if web_service is None:
        return

    if not connected:
        web_service.stop()
        return

    if web_service.server is None:
        now = time.ticks_ms()
        if (
            next_web_start_ms is None
            or time.ticks_diff(now, next_web_start_ms) >= 0
        ):
            if web_service.start():
                next_web_start_ms = None
            else:
                next_web_start_ms = time.ticks_add(now, 10000)

    if allow_web:
        web_service.poll()


def initialize_network():
    global network_manager, web_service, next_web_start_ms

    if wifi_manager is None:
        return

    set_device_mode("WIFI SETUP")
    clear()
    center_text("WiFi connecting", 18)
    center_text("Local mode ready", 42)
    oled.show()

    try:
        network_manager = wifi_manager.WiFiManager()
        connected = network_manager.connect()
        sync_wifi_state()

        if web_server is not None and state_store is not None:
            web_service = web_server.WebServer(state_store, experiment_log)

        clear()
        if connected:
            center_text("WiFi connected", 14)
            center_text(network_manager.ip or "IP unavailable", 36)
            if web_service is not None and not web_service.start():
                next_web_start_ms = time.ticks_add(time.ticks_ms(), 10000)
        else:
            center_text("WiFi offline", 14)
            center_text("Local mode OK", 36)
        oled.show()
        time.sleep_ms(900)
    except Exception as exc:
        network_manager = None
        web_service = None
        if state_store is not None:
            state_store.set_wifi(False, status="startup error")
        print("WIFI | startup error |", exc)
        clear()
        center_text("WiFi offline", 14)
        center_text("Local mode OK", 36)
        oled.show()
        time.sleep_ms(900)


def safe_show_error(line1, line2=None):
    clear()
    center_text(line1, 16)
    if line2:
        center_text(line2, 40)
    oled.show()


def wait_for_button_release():
    while button.value() == 0:
        time.sleep_ms(4)
    time.sleep_ms(20)


# ============================================================
# BUTTON HANDLING
# ============================================================

def button_event(
    long_ms=LONG_PRESS_MS,
    debounce_ms=DEBOUNCE_MS,
    poll_ms=4,
    min_valid_ms=18
):
    service_background()

    if button.value() != 0:
        return None

    press_start = time.ticks_ms()
    while (
        button.value() == 0
        and time.ticks_diff(time.ticks_ms(), press_start) < debounce_ms
    ):
        time.sleep_ms(poll_ms)

    if button.value() != 0:
        return None

    start = time.ticks_ms()
    while button.value() == 0:
        time.sleep_ms(poll_ms)

    duration = time.ticks_diff(time.ticks_ms(), start)
    time.sleep_ms(debounce_ms)

    if duration < min_valid_ms:
        return None
    if duration >= long_ms:
        return "LONG"
    return "SHORT"


def button_event_diode_mode():
    return button_event(
        long_ms=DIODE_MODE_LONG_MS,
        debounce_ms=DIODE_MODE_DEBOUNCE_MS,
        poll_ms=3,
        min_valid_ms=14
    )


def diode_button_event():
    return button_event_diode_mode()


def wait_for_any_press():
    while True:
        if button_event() is not None:
            return
        time.sleep_ms(5)


# ============================================================
# STARTUP SCREEN
# ============================================================

def startup_screen():
    clear()
    center_text("EE LAB TOOL", 0)
    center_text("Press START", 20)
    center_text("Short: next", 38)
    center_text("Long: select", 52)
    oled.show()

    # Do not enter the main menu until the user presses and
    # releases the button once.
    wait_for_any_press()
    wait_for_button_release()


# ============================================================
# INA219 FUNCTIONS
# ============================================================

def read16(register):
    data = i2c.readfrom_mem(INA219, register, 2)
    return (data[0] << 8) | data[1]


def configure_ina219():
    # 32 V bus range, +/-320 mV shunt, 12-bit continuous mode.
    i2c.writeto_mem(INA219, 0x00, bytes([0x39, 0x9F]))
    time.sleep_ms(200)


def read_power_measurement():
    raw_shunt = read16(0x01)
    if raw_shunt & 0x8000:
        raw_shunt -= 65536

    shunt_mV = raw_shunt * 0.01
    current_mA = shunt_mV / SHUNT_OHMS
    current_A = current_mA / 1000.0

    raw_bus = read16(0x02)
    raw_voltage = (raw_bus >> 3) * 0.004
    voltage = raw_voltage * V_SLOPE + V_OFFSET

    return voltage, current_A, raw_voltage


def averaged_power_measurement():
    voltage_sum = 0.0
    current_sum = 0.0
    raw_sum = 0.0

    for _ in range(POWER_SAMPLES):
        voltage, current, raw = read_power_measurement()
        voltage_sum += voltage
        current_sum += current
        raw_sum += raw
        time.sleep_ms(20)

    voltage = voltage_sum / POWER_SAMPLES
    current = current_sum / POWER_SAMPLES
    raw_voltage = raw_sum / POWER_SAMPLES
    power = voltage * current

    return voltage, current, power, raw_voltage


def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, secs)
    return "{:02d}:{:02d}".format(minutes, secs)


# ============================================================
# POWER AND ENERGY MONITOR
# ============================================================

def power_monitor():
    set_device_mode("POWER MONITOR")
    charge_pin.init(Pin.IN)
    discharge_pin.value(0)

    try:
        configure_ina219()
    except OSError:
        monitor_faults(ina_ok=False)
        safe_show_error("INA219 ERROR", "Hold = Back")
        while True:
            if button_event() == "LONG":
                return

    page = 0
    charge_mAh = 0.0
    energy_Wh = 0.0
    min_voltage = None
    peak_current = 0.0
    peak_power = 0.0
    voltage_sum = 0.0
    current_sum = 0.0
    power_sum = 0.0
    measurement_count = 0
    voltage = None
    current = None
    power = None
    elapsed_s = 0.0
    avg_voltage = None
    avg_current = None
    avg_power = None

    session_start = time.ticks_ms()
    last_measurement = session_start
    last_user_activity = session_start

    while True:
        try:
            voltage, current, power, raw = averaged_power_measurement()
            monitor_faults(
                voltage=voltage,
                current=current,
                power=power,
                ina_ok=True,
            )
        except OSError:
            monitor_faults(ina_ok=False)
            safe_show_error("INA219 LOST", "Hold = Back")
            while True:
                if button_event() == "LONG":
                    log_power_session(
                        session_start, measurement_count, elapsed_s,
                        voltage, current, power, min_voltage,
                        peak_current, peak_power, avg_voltage,
                        avg_current, avg_power, charge_mAh, energy_Wh,
                        "sensor_lost",
                    )
                    return

        now = time.ticks_ms()
        dt_ms = time.ticks_diff(now, last_measurement)
        dt_s = dt_ms / 1000.0
        last_measurement = now

        safe_current = max(0.0, current)
        safe_power = max(0.0, power)

        charge_mAh += safe_current * dt_s / 3.6
        energy_Wh += safe_power * dt_s / 3600.0

        if min_voltage is None or voltage < min_voltage:
            min_voltage = voltage
        if current > peak_current:
            peak_current = current
        if power > peak_power:
            peak_power = power

        voltage_sum += voltage
        current_sum += current
        power_sum += power
        measurement_count += 1

        avg_voltage = voltage_sum / measurement_count
        avg_current = current_sum / measurement_count
        avg_power = power_sum / measurement_count

        elapsed_ms = time.ticks_diff(now, session_start)
        elapsed_s = elapsed_ms / 1000.0

        if state_store is not None:
            state_store.update_power(
                voltage,
                current,
                power,
                charge_mAh,
                energy_Wh,
                elapsed_s,
                min_voltage,
                peak_current,
                peak_power,
                avg_voltage,
                avg_current,
                avg_power,
            )

        clear()
        if page == 0:
            center_text("POWER MONITOR", 0)
            oled.text("V: {:.3f} V".format(voltage), 0, 17)
            oled.text("I: {:.3f} A".format(current), 0, 32)
            oled.text("P: {:.3f} W".format(power), 0, 47)
        elif page == 1:
            center_text("ENERGY", 0)
            oled.text("Q:{:.2f} mAh".format(charge_mAh), 0, 18)
            oled.text("E:{:.4f} Wh".format(energy_Wh), 0, 34)
            oled.text("T:{}".format(format_time(elapsed_s)), 0, 50)
        elif page == 2:
            center_text("PEAK STATS", 0)
            oled.text("MinV:{:.3f}".format(min_voltage), 0, 18)
            oled.text("PkI:{:.3f} A".format(peak_current), 0, 34)
            oled.text("PkP:{:.3f} W".format(peak_power), 0, 50)
        else:
            center_text("AVERAGES", 0)
            oled.text("V:{:.3f} V".format(avg_voltage), 0, 18)
            oled.text("I:{:.3f} A".format(avg_current), 0, 34)
            oled.text("P:{:.3f} W".format(avg_power), 0, 50)
        oled.show()
        service_background()

        print(
            "V:", round(voltage, 3),
            "V | I:", round(current, 3),
            "A | P:", round(power, 3),
            "W | mAh:", round(charge_mAh, 3),
            "| Wh:", round(energy_Wh, 5),
            "| RAW:", round(raw, 3)
        )

        event = button_event()
        if event == "SHORT":
            page = (page + 1) % 4
            last_user_activity = time.ticks_ms()
        elif event == "LONG":
            log_power_session(
                session_start, measurement_count, elapsed_s,
                voltage, current, power, min_voltage,
                peak_current, peak_power, avg_voltage,
                avg_current, avg_power, charge_mAh, energy_Wh,
            )
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, last_user_activity) >= POWER_AUTO_SCROLL_MS:
            page = (page + 1) % 4
            last_user_activity = now


# ============================================================
# RC ANALYZER
# ============================================================

def capacitor_voltage():
    return adc.read_u16() * VREF / 65535


GRAPH_TOP = 16
GRAPH_BOTTOM = 63
GRAPH_RIGHT = 127


def voltage_to_y(voltage):
    voltage = max(0, min(VREF, voltage))
    height = GRAPH_BOTTOM - GRAPH_TOP
    return GRAPH_BOTTOM - int(voltage / VREF * height)


def time_to_x(t):
    return int(t / 6.0 * GRAPH_RIGHT)


def draw_live_graph(points, t, voltage, mode):
    clear()
    oled.text(mode, 0, 0)
    oled.text("{:.1f}s {:.2f}V".format(t, voltage), 55, 0)
    oled.line(0, GRAPH_TOP, 0, GRAPH_BOTTOM, 1)
    oled.line(0, GRAPH_BOTTOM, 127, GRAPH_BOTTOM, 1)

    for i in range(1, len(points)):
        t1, v1 = points[i - 1]
        t2, v2 = points[i]
        oled.line(
            time_to_x(t1),
            voltage_to_y(v1),
            time_to_x(t2),
            voltage_to_y(v2),
            1
        )
    oled.show()


def draw_dual_graph(charge_points, discharge_points):
    clear()
    oled.text("CHG", 1, 0)
    oled.text("DIS", 67, 0)
    oled.line(63, 10, 63, 63, 1)
    oled.line(0, 63, 61, 63, 1)
    oled.line(65, 63, 127, 63, 1)

    for i in range(1, len(charge_points)):
        t1, v1 = charge_points[i - 1]
        t2, v2 = charge_points[i]
        x1 = int((t1 / 6.0) * 61)
        x2 = int((t2 / 6.0) * 61)
        y1 = 63 - int((v1 / VREF) * 50)
        y2 = 63 - int((v2 / VREF) * 50)
        oled.line(x1, y1, x2, y2, 1)

    for i in range(1, len(discharge_points)):
        t1, v1 = discharge_points[i - 1]
        t2, v2 = discharge_points[i]
        x1 = 65 + int((t1 / 6.0) * 61)
        x2 = 65 + int((t2 / 6.0) * 61)
        y1 = 63 - int((v1 / VREF) * 50)
        y2 = 63 - int((v2 / VREF) * 50)
        oled.line(x1, y1, x2, y2, 1)

    oled.show()


def rc_analyzer():
    set_device_mode("RC ANALYZER")
    clear()
    center_text("RC ANALYZER", 12)
    center_text("Resetting...", 34)
    oled.show()

    charge_pin.init(Pin.IN)
    discharge_pin.value(1)
    time.sleep(5)
    discharge_pin.value(0)

    charge_points = []
    charge_pin.init(Pin.OUT)
    charge_pin.value(1)

    start = time.ticks_ms()
    while True:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start)
        if elapsed_ms >= CHARGE_TIME_MS:
            break

        t = elapsed_ms / 1000.0
        voltage = capacitor_voltage()
        charge_points.append((t, voltage))
        draw_live_graph(charge_points, t, voltage, "CHARGE")
        print("CHARGE", round(t, 2), "s |", round(voltage, 3), "V")
        service_background(allow_web=False)
        time.sleep_ms(RC_SAMPLE_MS)

    charge_pin.init(Pin.IN)
    time.sleep_ms(200)
    v0 = capacitor_voltage()
    target_voltage = v0 / math.e

    discharge_points = []
    tau = None
    previous_t = None
    previous_v = None

    discharge_pin.value(1)
    start = time.ticks_ms()

    while True:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start)
        if elapsed_ms >= DISCHARGE_TIME_MS:
            break

        t = elapsed_ms / 1000.0
        voltage = capacitor_voltage()
        discharge_points.append((t, voltage))
        print("DISCHARGE", round(t, 2), "s |", round(voltage, 3), "V")

        if (
            tau is None
            and previous_v is not None
            and previous_v > target_voltage
            and voltage <= target_voltage
        ):
            fraction = (previous_v - target_voltage) / (previous_v - voltage)
            tau = previous_t + fraction * (t - previous_t)

        previous_t = t
        previous_v = voltage
        draw_live_graph(discharge_points, t, voltage, "DISCHARGE")
        service_background(allow_web=False)
        time.sleep_ms(RC_SAMPLE_MS)

    discharge_pin.value(0)
    draw_dual_graph(charge_points, discharge_points)
    time.sleep(4)

    clear()
    center_text("RC RESULT", 0)
    capacitance_uF = None

    if tau is not None:
        capacitance_uF = tau / R_DISCHARGE * 1000000
        oled.text("Tau:{:.3f}s".format(tau), 0, 20)
        oled.text("C:{:.0f} uF".format(capacitance_uF), 0, 37)
        center_text("Returning...", 53)
        print("Tau:", round(tau, 3), "s")
        print("Capacitance:", round(capacitance_uF), "uF")
    else:
        center_text("Tau not found", 27)
        center_text("Returning...", 49)

    if state_store is not None:
        state_store.update_rc(
            tau, capacitance_uF, charge_points, discharge_points
        )

    log_experiment(
        "RC",
        {
            "tau_s": tau,
            "capacitance_uF": capacitance_uF,
            "charge_resistance_ohm": R_CHARGE,
            "discharge_resistance_ohm": R_DISCHARGE,
        },
        "completed" if tau is not None else "tau_not_found",
    )

    oled.show()
    time.sleep(5)

    charge_pin.init(Pin.IN)
    discharge_pin.value(0)


# ============================================================
# DIODE ANALYZER
# ============================================================

def avg_adc_voltage(adc_obj, samples=DIODE_SAMPLES):
    total = 0
    for _ in range(samples):
        total += adc_obj.read_u16()
        time.sleep_ms(4)
    return (total / samples) * VREF / 65535.0


def diode_source_safe_low():
    diode_source_pin.value(0)


def read_diode_single_measurement():
    diode_source_pin.value(1)
    time.sleep_ms(DIODE_SETTLE_MS)

    vs = avg_adc_voltage(diode_vs_adc)
    vf = avg_adc_voltage(diode_vf_adc)
    diode_source_pin.value(0)

    vr = max(0.0, vs - vf)
    id_mA = (vr / R_TEST) * 1000.0
    return vs, vf, vr, id_mA


def classify_diode(vf, id_mA):
    if id_mA < DIODE_OPEN_MA_THRESHOLD or vf <= 0.01:
        return "NO CONDUCTION"
    if vf < DIODE_LOW_VF_SHORT_MAX:
        return "LOW Vf / SHORT?"
    if vf < 0.50:
        return "SCHOTTKY"
    if vf < 0.90:
        return "SILICON"
    return "HIGH Vf / UNKNOWN"


def draw_diode_result(vf, id_mA, vs, label):
    clear()
    center_text("DIODE ANALYZER", 0)
    oled.text("Vf: {:.3f} V".format(vf), 0, 18)
    oled.text("I: {:.2f} mA".format(id_mA), 0, 30)
    oled.text("Vtest:{:.3f} V".format(vs), 0, 42)

    if label == "NO CONDUCTION":
        center_text("Check polarity", 54)
    else:
        center_text(label, 54)
    oled.show()


def draw_diode_single_prompt():
    clear()
    center_text("DIODE ANALYZER", 0)
    center_text("Insert diode", 16)
    center_text("Hold to test", 32)
    oled.show()


def draw_diode_mode_prompt(mode_index):
    clear()
    center_text("DIODE ANALYZER", 0)

    oled.text(">" if mode_index == 0 else " ", 0, 18)
    oled.text(trim_text("SINGLE TEST", MENU_ITEM_CHARS), MENU_ITEM_X, 18)

    oled.text(">" if mode_index == 1 else " ", 0, 34)
    oled.text(trim_text("I-V SWEEP", MENU_ITEM_CHARS), MENU_ITEM_X, 34)

    oled.text(">" if mode_index == 2 else " ", 0, 50)
    oled.text(trim_text("BACK TO MAIN", MENU_ITEM_CHARS), MENU_ITEM_X, 50)
    oled.show()

def draw_diode_iv_progress(step, total, vs, vf, id_mA):
    clear()
    center_text("I-V SWEEP", 0)
    oled.text("Step {}/{}".format(step, total), 0, 12)
    oled.text("Vs:{:.3f} V".format(vs), 0, 24)
    oled.text("Vf:{:.3f} V".format(vf), 0, 34)
    oled.text("I:{:.2f} mA".format(id_mA), 0, 44)
    oled.text("Measuring...", 0, 56)
    oled.show()


def draw_diode_iv_graph(points):
    if not points:
        safe_show_error("I-V SWEEP", "No data")
        return

    max_i = max(p[2] for p in points)
    if max_i < 0.001:
        max_i = 0.001

    clear()
    oled.text("I-V SWEEP", 0, 0)

    graph_left = 8
    graph_right = 127
    graph_top = 14
    graph_bottom = 56
    x_len = graph_right - graph_left
    y_len = graph_bottom - graph_top

    oled.line(graph_left, graph_top, graph_left, graph_bottom, 1)
    oled.line(graph_left, graph_bottom, graph_right, graph_bottom, 1)

    for i in range(1, len(points)):
        p_prev = points[i - 1]
        p_curr = points[i]

        x1 = graph_left + int((p_prev[2] / max_i) * x_len)
        y1 = graph_bottom - int((p_prev[1] / VREF) * y_len)
        x2 = graph_left + int((p_curr[2] / max_i) * x_len)
        y2 = graph_bottom - int((p_curr[1] / VREF) * y_len)
        oled.line(x1, y1, x2, y2, 1)

    oled.show()


def draw_diode_iv_stats(points):
    max_i = max(p[2] for p in points)
    max_vf = max(p[1] for p in points)
    max_vs = max(p[0] for p in points)

    clear()
    oled.text("I-V SWEEP", 0, 0)
    oled.text("Pts: {}".format(len(points)), 0, 15)
    oled.text("Vmax:{:.3f} V".format(max_vs), 0, 24)
    oled.text("Vfmax:{:.3f} V".format(max_vf), 0, 33)
    oled.text("Imax:{:.2f} mA".format(max_i), 0, 42)
    oled.text("No Q class", 0, 52)
    oled.show()


def read_diode_iv_curve():
    points = []
    pwm = PWM(diode_source_pin)
    pwm.freq(DIODE_IV_PWM_FREQ)

    try:
        total = len(DIODE_IV_PWM_STEPS)
        for idx, duty in enumerate(DIODE_IV_PWM_STEPS, 1):
            pwm.duty_u16(duty)
            time.sleep_ms(DIODE_IV_SETTLE_MS)

            vs = avg_adc_voltage(diode_vs_adc)
            vf = avg_adc_voltage(diode_vf_adc)
            id_mA = max(0.0, (vs - vf) / R_TEST * 1000.0)

            points.append((vs, vf, id_mA))
            draw_diode_iv_progress(idx, total, vs, vf, id_mA)

            print(
                "IV | step:", idx,
                "Vs:{:.3f}".format(vs),
                "Vf:{:.3f}".format(vf),
                "I:{:.3f}mA".format(id_mA)
            )
            service_background(allow_web=False)
            time.sleep_ms(DIODE_IV_PROGRESS_REFRESH_MS)
    finally:
        pwm.deinit()
        diode_source_safe_low()

    return points


def show_diode_iv_results(points):
    if not points:
        safe_show_error("I-V SWEEP", "No data")
        time.sleep(1)
        return

    page = 0
    last_flip = time.ticks_ms()

    while True:
        service_background()
        now = time.ticks_ms()

        if page == 0:
            draw_diode_iv_graph(points)
        else:
            draw_diode_iv_stats(points)

        event = diode_button_event()
        if event == "SHORT":
            page = (page + 1) % DIODE_IV_GRAPH_PAGES
            last_flip = now
            continue
        if event == "LONG":
            return "MODE"

        if time.ticks_diff(now, last_flip) >= DIODE_IV_SLIDESHOW_MS:
            page = (page + 1) % DIODE_IV_GRAPH_PAGES
            last_flip = now

        time.sleep_ms(5)


def diode_single_mode():
    set_device_mode("DIODE SINGLE")
    while True:
        draw_diode_single_prompt()
        event = diode_button_event()

        if event == "SHORT":
            wait_for_button_release()
            return "MODE"

        if event == "LONG":
            vs, vf, vr, id_mA = read_diode_single_measurement()
            label = classify_diode(vf, id_mA)

            print(
                "DIODE | Vs:", "{:.3f} V".format(vs),
                "| Vf:", "{:.3f} V".format(vf),
                "| Vr:", "{:.3f} V".format(vr),
                "| I:", "{:.2f} mA".format(id_mA),
                "| Type:", label
            )

            draw_diode_result(vf, id_mA, vs, label)

            if state_store is not None:
                state_store.update_diode(vf, id_mA, label, vs)

            log_experiment(
                "DIODE_SINGLE",
                {
                    "test_voltage_v": vs,
                    "forward_voltage_v": vf,
                    "resistor_drop_v": vr,
                    "diode_current_mA": id_mA,
                    "classification": label,
                },
            )

            while True:
                result_event = diode_button_event()
                if result_event == "LONG":
                    return "MODE"
                if result_event == "SHORT":
                    break
                time.sleep_ms(5)


def diode_iv_mode():
    set_device_mode("DIODE I-V")
    while True:
        clear()
        center_text("I-V SWEEP", 0)
        center_text("Insert diode", 16)
        center_text("Hold to test", 32)
        oled.show()

        event = diode_button_event()
        if event == "SHORT":
            wait_for_button_release()
            return "MODE"
        if event == "LONG":
            points = read_diode_iv_curve()
            point_records = [
                {
                    "source_voltage_v": point[0],
                    "forward_voltage_v": point[1],
                    "diode_current_mA": point[2],
                }
                for point in points
            ]
            log_experiment(
                "DIODE_IV",
                {
                    "point_count": len(points),
                    "max_source_voltage_v": max(
                        [point[0] for point in points] or [0.0]
                    ),
                    "max_forward_voltage_v": max(
                        [point[1] for point in points] or [0.0]
                    ),
                    "max_current_mA": max(
                        [point[2] for point in points] or [0.0]
                    ),
                    "points": point_records,
                    "quantitative_classification": False,
                },
                "display_only" if points else "no_data",
            )

            # PWM sweep is display-only. It is not used for
            # quantitative diode classification.
            destination = show_diode_iv_results(points)
            if destination == "MAIN":
                return "MAIN"
            return "MODE"

        time.sleep_ms(5)


def diode_analyzer():
    set_device_mode("DIODE SELECTOR")
    mode = 0
    wait_for_button_release()

    while True:
        draw_diode_mode_prompt(mode)
        event = diode_button_event()

        if event == "SHORT":
            mode = (mode + 1) % 3
            time.sleep_ms(40)
            continue

        if event == "LONG":
            if mode == 2:
                diode_source_safe_low()
                return

            clear()
            if mode == 0:
                center_text("SINGLE TEST", 0)
                oled.show()
                destination = diode_single_mode()
            elif mode == 1:
                center_text("I-V SWEEP", 0)
                oled.show()
                destination = diode_iv_mode()

            if destination == "MAIN":
                diode_source_safe_low()
                return

            wait_for_button_release()
            set_device_mode("DIODE SELECTOR")
            draw_diode_mode_prompt(mode)

        time.sleep_ms(5)


# ============================================================
# GUIDED SOURCE CHARACTERIZATION
# ============================================================

def source_test_mode():
    set_device_mode("SOURCE TEST")
    wait_for_button_release()

    if source_test_session is None:
        safe_show_error("SOURCE TEST", "Module missing")
        time.sleep(2)
        return

    source_test_session.reset()
    if state_store is not None:
        try:
            state_store.update_source_test(source_test_session.preview(), "collecting")
        except Exception:
            pass

    try:
        configure_ina219()
        monitor_faults(ina_ok=True)
    except OSError:
        monitor_faults(ina_ok=False)
        safe_show_error("INA219 ERROR", "Hold = Back")
        while button_event() != "LONG":
            time.sleep_ms(10)
        return

    while True:
        clear()
        center_text("SOURCE TEST", 0)
        oled.text("Points: {}".format(len(source_test_session.points)), 0, 18)
        center_text("Short: capture", 34)
        center_text("Long: finish", 50)
        oled.show()
        service_background()

        event = button_event()
        if event == "SHORT":
            try:
                voltage, current, power, raw = averaged_power_measurement()
                monitor_faults(
                    voltage=voltage,
                    current=current,
                    power=power,
                    ina_ok=True,
                )
                accepted, message = source_test_session.add_point(
                    voltage, current
                )
            except OSError:
                monitor_faults(ina_ok=False)
                accepted, message = False, "INA219 lost"

            if state_store is not None:
                try:
                    state_store.update_source_test(
                        source_test_session.preview(), "collecting"
                    )
                except Exception:
                    pass

            clear()
            center_text("POINT CAPTURE", 0)
            center_text(message, 18)
            if accepted:
                oled.text("V:{:.3f} V".format(voltage), 0, 34)
                oled.text("I:{:.3f} A".format(current), 0, 49)
            oled.show()
            time.sleep(1.2)

        elif event == "LONG":
            if len(source_test_session.points) < 2:
                safe_show_error("SOURCE TEST", "Need 2 points")
                time.sleep(1.5)
                continue
            try:
                result = source_test_session.result()
                status = result.get("status", "completed")
            except Exception as exc:
                result = source_test_session.preview()
                result["error"] = str(exc)
                status = "failed"

            if state_store is not None:
                try:
                    state_store.update_source_test(result, status)
                except Exception:
                    pass
            log_experiment("SOURCE TEST", result, status)

            clear()
            if status == "completed":
                center_text("SOURCE RESULT", 0)
                oled.text("Voc:{:.3f} V".format(result["voc_v"]), 0, 18)
                oled.text(
                    "Rs:{:.3f} ohm".format(
                        result["source_resistance_ohm"]
                    ),
                    0,
                    34,
                )
                oled.text("R2:{:.3f}".format(result["r_squared"]), 0, 50)
            elif status == "invalid":
                center_text("SOURCE INVALID", 0)
                center_text("Fit rejected", 22)
                center_text(
                    trim_text(result.get("reason", "Invalid result"), 14),
                    38,
                )
                center_text("See dashboard", 54)
            else:
                center_text("SOURCE RESULT", 0)
                center_text("Fit failed", 26)
                center_text("Returning...", 46)
            oled.show()
            time.sleep(6)
            return

        time.sleep_ms(20)

# ============================================================
# TEMPERATURE MONITOR
# ============================================================

def temperature_monitor():
    set_device_mode("MCU TEMP")
    wait_for_button_release()
    last_draw_ms = time.ticks_add(time.ticks_ms(), -500)

    while True:
        service_background()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_draw_ms) >= 500:
            clear()
            center_text("MCU TEMP", 2)
            if latest_temperature_c is None:
                center_text("Reading...", 25)
            else:
                center_text("{:.1f} C".format(latest_temperature_c), 25)
            center_text("INTERNAL DIE", 48)
            oled.show()
            last_draw_ms = now

        if button_event() == "LONG":
            return

        time.sleep_ms(20)

# ============================================================
# MAIN MENU
# ============================================================

MENU_ITEMS = [
    "POWER MONITOR",
    "RC ANALYZER",
    "DIODE ANALYZER",
    "MCU TEMP",
    "SOURCE TEST"
]
MENU_PAGE_SIZE = 2


def draw_menu(selected):
    clear()
    page = selected // MENU_PAGE_SIZE
    page_start = page * MENU_PAGE_SIZE
    page_count = (len(MENU_ITEMS) + MENU_PAGE_SIZE - 1) // MENU_PAGE_SIZE
    center_text(
        "EE LAB TOOL {}/{}".format(page + 1, page_count),
        0
    )

    y_positions = [24, 44]
    for row in range(MENU_PAGE_SIZE):
        idx = page_start + row
        if idx >= len(MENU_ITEMS):
            break
        oled.text(">" if selected == idx else " ", 0, y_positions[row])
        oled.text(
            trim_text(MENU_ITEMS[idx], MENU_ITEM_CHARS),
            MENU_ITEM_X,
            y_positions[row]
        )

    # Button hints intentionally appear only on startup.
    oled.show()

def menu():
    set_device_mode("MENU")
    selected = 0
    draw_menu(selected)

    while True:
        service_background()
        event = button_event()

        if event == "SHORT":
            selected = (selected + 1) % len(MENU_ITEMS)
            draw_menu(selected)

        elif event == "LONG":
            clear()
            center_text("SELECTED", 12)
            center_text(trim_text(MENU_ITEMS[selected], MENU_ITEM_CHARS), 34)
            oled.show()
            time.sleep_ms(350)

            if selected == 0:
                power_monitor()
            elif selected == 1:
                rc_analyzer()
            elif selected == 2:
                diode_analyzer()
            elif selected == 3:
                temperature_monitor()
            elif selected == 4:
                source_test_mode()

            wait_for_button_release()
            set_device_mode("MENU")
            draw_menu(selected)

        time.sleep_ms(20)


# ============================================================
# PROGRAM START
# ============================================================

charge_pin.init(Pin.IN)
discharge_pin.value(0)
diode_source_safe_low()

sync_logging_state()
sync_fault_state()
set_device_mode("STARTUP")
startup_screen()
initialize_network()
menu()
