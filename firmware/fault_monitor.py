# USER-CONFIGURABLE MONITORING THRESHOLDS.
# These values are software alerts, not hardware safety ratings or cutoffs.
FAULT_UNDERVOLTAGE_V = 2.50
FAULT_OVERCURRENT_A = 1.00
FAULT_OVERPOWER_W = 3.00
FAULT_MCU_TEMP_C = 75.0

FAULT_DEBOUNCE_SAMPLES = 2
VOLTAGE_HYSTERESIS_V = 0.05
CURRENT_HYSTERESIS_A = 0.05
POWER_HYSTERESIS_W = 0.10
TEMPERATURE_HYSTERESIS_C = 2.0
RECENT_EVENT_LIMIT = 12


class FaultMonitor:
    def __init__(self, logger=None):
        self.logger = logger
        self.states = {
            "UNDERVOLTAGE": self._new_state(FAULT_UNDERVOLTAGE_V),
            "OVERCURRENT": self._new_state(FAULT_OVERCURRENT_A),
            "OVERPOWER": self._new_state(FAULT_OVERPOWER_W),
            "MCU_TEMP_HIGH": self._new_state(FAULT_MCU_TEMP_C),
            "INA219_LOST": self._new_state(None),
        }
        self.recent_events = []

    def _new_state(self, threshold):
        return {
            "active": False,
            "value": None,
            "threshold": threshold,
            "pending": 0,
        }

    def _desired_high(self, value, threshold, active, hysteresis):
        if threshold is None or value is None:
            return active
        if active:
            return value >= threshold - hysteresis
        return value > threshold

    def _desired_low(self, value, threshold, active, hysteresis):
        if threshold is None or value is None:
            return active
        if active:
            return value <= threshold + hysteresis
        return value < threshold

    def _event_code(self, key, active):
        if key == "INA219_LOST":
            return "INA219_LOST" if active else "INA219_RESTORED"
        return key + ("_ACTIVE" if active else "_CLEARED")

    def _transition(self, key, active, value, mode):
        state = self.states[key]
        state["active"] = active
        state["pending"] = 0
        event = {
            "fault_code": self._event_code(key, active),
            "fault_state": "active" if active else "cleared",
            "measured_value": value,
            "threshold": state["threshold"],
            "mode": mode,
        }
        self.recent_events.append(event)
        if len(self.recent_events) > RECENT_EVENT_LIMIT:
            self.recent_events.pop(0)
        print("FAULT |", event["fault_code"], "|", value)
        if self.logger is not None:
            try:
                self.logger.append_fault(
                    event["fault_code"],
                    event["fault_state"],
                    value,
                    state["threshold"],
                    mode,
                )
            except Exception as exc:
                print("FAULT | log error |", exc)

    def _update_state(self, key, desired, value, mode):
        state = self.states[key]
        state["value"] = value
        if desired == state["active"]:
            state["pending"] = 0
            return
        state["pending"] += 1
        if state["pending"] >= FAULT_DEBOUNCE_SAMPLES:
            self._transition(key, desired, value, mode)

    def update(
        self,
        voltage=None,
        current=None,
        power=None,
        temperature_c=None,
        ina_ok=None,
        mode=None,
    ):
        mode = mode or "UNKNOWN"

        if voltage is not None:
            state = self.states["UNDERVOLTAGE"]
            desired = self._desired_low(
                voltage,
                state["threshold"],
                state["active"],
                VOLTAGE_HYSTERESIS_V,
            )
            self._update_state("UNDERVOLTAGE", desired, voltage, mode)

        if current is not None:
            state = self.states["OVERCURRENT"]
            desired = self._desired_high(
                current,
                state["threshold"],
                state["active"],
                CURRENT_HYSTERESIS_A,
            )
            self._update_state("OVERCURRENT", desired, current, mode)

        if power is not None:
            state = self.states["OVERPOWER"]
            desired = self._desired_high(
                power,
                state["threshold"],
                state["active"],
                POWER_HYSTERESIS_W,
            )
            self._update_state("OVERPOWER", desired, power, mode)

        if temperature_c is not None:
            state = self.states["MCU_TEMP_HIGH"]
            desired = self._desired_high(
                temperature_c,
                state["threshold"],
                state["active"],
                TEMPERATURE_HYSTERESIS_C,
            )
            self._update_state("MCU_TEMP_HIGH", desired, temperature_c, mode)

        if ina_ok is not None:
            self._update_state("INA219_LOST", not bool(ina_ok), bool(ina_ok), mode)

        return self.snapshot()

    def snapshot(self):
        states = {}
        any_active = False
        for key in self.states:
            source = self.states[key]
            states[key] = {
                "active": source["active"],
                "value": source["value"],
                "threshold": source["threshold"],
            }
            if source["active"]:
                any_active = True
        return {
            "overall": "MONITORING ALERT" if any_active else "OK",
            "states": states,
            "recent_events": list(self.recent_events),
        }