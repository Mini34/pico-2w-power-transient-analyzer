import time


HISTORY_CAPACITY = 180
HISTORY_INTERVAL_MS = 1000
TEMPERATURE_HISTORY_CAPACITY = 180
TEMPERATURE_HISTORY_INTERVAL_MS = 10000

_boot_ms = time.ticks_ms()
_history = [None] * HISTORY_CAPACITY
_history_start = 0
_history_count = 0
_last_history_ms = None

_temperature_history = [None] * TEMPERATURE_HISTORY_CAPACITY
_temperature_history_start = 0
_temperature_history_count = 0
_last_temperature_history_ms = None

_rc_charge_history = []
_rc_discharge_history = []


instrument_state = {
    "system": {
        "temperature_c": None,
        "temperature_adc_v": None,
        "temperature_raw": None,
        "temperature_updated_ms": None,
    },
    "device": {
        "mode": "STARTUP",
        "uptime_s": 0,
    },
    "wifi": {
        "connected": False,
        "ssid": None,
        "ip": None,
        "status": "offline",
    },
    "power": {
        "voltage_v": None,
        "current_a": None,
        "power_w": None,
        "charge_mAh": None,
        "energy_Wh": None,
        "elapsed_s": None,
        "min_voltage_v": None,
        "peak_current_a": None,
        "peak_power_w": None,
        "avg_voltage_v": None,
        "avg_current_a": None,
        "avg_power_w": None,
        "timestamp_ms": None,
    },
    "rc": {
        "tau_s": None,
        "capacitance_uF": None,
        "last_run_ms": None,
    },
    "diode": {
        "forward_voltage_v": None,
        "current_mA": None,
        "classification": None,
        "test_voltage_v": None,
        "last_run_ms": None,
    },
    "logging": {
        "available": False,
        "last_error": None,
        "records_written": 0,
        "last_record": None,
    },
    "source_test": {
        "status": "idle",
        "voc_v": None,
        "source_resistance_ohm": None,
        "r_squared": None,
        "point_count": 0,
        "points": [],
        "reason": None,
        "warning": None,
        "last_run_ms": None,
    },
    "faults": {
        "overall": "OK",
        "states": {},
        "recent_events": [],
    },
}


def _uptime_ms():
    return time.ticks_diff(time.ticks_ms(), _boot_ms)


def update_uptime():
    instrument_state["device"]["uptime_s"] = _uptime_ms() // 1000


def set_mode(mode):
    instrument_state["device"]["mode"] = mode
    update_uptime()


def set_wifi(connected, ssid=None, ip=None, status=None):
    wifi = instrument_state["wifi"]
    wifi["connected"] = bool(connected)
    wifi["ssid"] = ssid
    wifi["ip"] = ip
    wifi["status"] = status or ("connected" if connected else "offline")


def _append_power_history(now, voltage, current, power):
    global _history_start, _history_count, _last_history_ms
    if (
        _last_history_ms is not None
        and time.ticks_diff(now, _last_history_ms) < HISTORY_INTERVAL_MS
    ):
        return
    sample = (
        round(_uptime_ms() / 1000.0, 1),
        round(voltage, 4),
        round(current, 4),
        round(power, 4),
    )
    if _history_count < HISTORY_CAPACITY:
        index = (_history_start + _history_count) % HISTORY_CAPACITY
        _history_count += 1
    else:
        index = _history_start
        _history_start = (_history_start + 1) % HISTORY_CAPACITY
    _history[index] = sample
    _last_history_ms = now


def _append_temperature_history(now, temperature_c):
    global _temperature_history_start, _temperature_history_count
    sample = (now, temperature_c)
    if _temperature_history_count < TEMPERATURE_HISTORY_CAPACITY:
        index = (
            _temperature_history_start + _temperature_history_count
        ) % TEMPERATURE_HISTORY_CAPACITY
        _temperature_history_count += 1
    else:
        index = _temperature_history_start
        _temperature_history_start = (
            _temperature_history_start + 1
        ) % TEMPERATURE_HISTORY_CAPACITY
    _temperature_history[index] = sample


def update_temperature(temperature_c, adc_voltage, raw):
    global _last_temperature_history_ms
    now = _uptime_ms()
    system = instrument_state["system"]
    system["temperature_c"] = temperature_c
    system["temperature_adc_v"] = adc_voltage
    system["temperature_raw"] = raw
    system["temperature_updated_ms"] = now
    if (
        _last_temperature_history_ms is None
        or time.ticks_diff(now, _last_temperature_history_ms)
        >= TEMPERATURE_HISTORY_INTERVAL_MS
    ):
        _append_temperature_history(now, temperature_c)
        _last_temperature_history_ms = now


def update_power(
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
):
    now = time.ticks_ms()
    data = instrument_state["power"]
    data["voltage_v"] = voltage
    data["current_a"] = current
    data["power_w"] = power
    data["charge_mAh"] = charge_mAh
    data["energy_Wh"] = energy_Wh
    data["elapsed_s"] = elapsed_s
    data["min_voltage_v"] = min_voltage
    data["peak_current_a"] = peak_current
    data["peak_power_w"] = peak_power
    data["avg_voltage_v"] = avg_voltage
    data["avg_current_a"] = avg_current
    data["avg_power_w"] = avg_power
    data["timestamp_ms"] = _uptime_ms()
    update_uptime()
    _append_power_history(now, voltage, current, power)


def _normalize_rc_points(points):
    result = []
    for point in points or ():
        try:
            elapsed_s, voltage_v = point
            result.append((
                round(float(elapsed_s), 3),
                round(float(voltage_v), 4),
            ))
        except (TypeError, ValueError):
            pass
    return result


def update_rc(
    tau_s,
    capacitance_uF,
    charge_points=None,
    discharge_points=None,
):
    global _rc_charge_history, _rc_discharge_history
    data = instrument_state["rc"]
    data["tau_s"] = tau_s
    data["capacitance_uF"] = capacitance_uF
    data["last_run_ms"] = _uptime_ms()
    _rc_charge_history = _normalize_rc_points(charge_points)
    _rc_discharge_history = _normalize_rc_points(discharge_points)
    update_uptime()


def update_diode(forward_voltage_v, current_mA, classification, test_voltage_v):
    data = instrument_state["diode"]
    data["forward_voltage_v"] = forward_voltage_v
    data["current_mA"] = current_mA
    data["classification"] = classification
    data["test_voltage_v"] = test_voltage_v
    data["last_run_ms"] = _uptime_ms()
    update_uptime()


def update_logging(status):
    data = instrument_state["logging"]
    data["available"] = bool(status.get("available"))
    data["last_error"] = status.get("last_error")
    data["records_written"] = status.get("records_written", 0)
    data["last_record"] = status.get("last_record")


def update_source_test(result=None, status="idle"):
    result = result or {}
    data = instrument_state["source_test"]
    data["status"] = status
    data["voc_v"] = result.get("voc_v")
    data["source_resistance_ohm"] = result.get("source_resistance_ohm")
    data["r_squared"] = result.get("r_squared")
    data["point_count"] = result.get("point_count", 0)
    data["points"] = result.get("points", [])
    data["reason"] = result.get("reason")
    data["warning"] = result.get("warning")
    if status in ("completed", "invalid", "failed"):
        data["last_run_ms"] = _uptime_ms()


def update_faults(snapshot):
    data = instrument_state["faults"]
    data["overall"] = snapshot.get("overall", "OK")
    data["states"] = snapshot.get("states", {})
    data["recent_events"] = snapshot.get("recent_events", [])


def snapshot():
    update_uptime()
    return {
        "mode": instrument_state["device"]["mode"],
        "uptime_s": instrument_state["device"]["uptime_s"],
        "wifi": instrument_state["wifi"],
        "system": instrument_state["system"],
        "power": instrument_state["power"],
        "rc": instrument_state["rc"],
        "diode": instrument_state["diode"],
        "logging": instrument_state["logging"],
        "source_test": instrument_state["source_test"],
        "faults": instrument_state["faults"],
    }


def power_history():
    result = []
    for offset in range(_history_count):
        index = (_history_start + offset) % HISTORY_CAPACITY
        sample = _history[index]
        if sample is not None:
            result.append({
                "t": sample[0],
                "v": sample[1],
                "i": sample[2],
                "p": sample[3],
            })
    return result


def rc_history():
    return {
        "charge": [
            {"t": point[0], "v": point[1]}
            for point in _rc_charge_history
        ],
        "discharge": [
            {"t": point[0], "v": point[1]}
            for point in _rc_discharge_history
        ],
    }


def temperature_history():
    result = []
    for offset in range(_temperature_history_count):
        index = (
            _temperature_history_start + offset
        ) % TEMPERATURE_HISTORY_CAPACITY
        sample = _temperature_history[index]
        if sample is not None:
            result.append({
                "t": sample[0] / 1000,
                "temp_c": sample[1],
            })
    return result
