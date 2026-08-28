import time

try:
    import ujson as json
except ImportError:
    import json

try:
    import uos as os
except ImportError:
    import os


LOG_DIRECTORY = "/logs"
EXPERIMENT_FILE = "experiments.jsonl"
FAULT_FILE = "faults.jsonl"
MAX_LOG_BYTES = 49152
RECENT_RECORD_LIMIT = 30

CSV_COLUMNS = (
    "record_id",
    "timestamp",
    "uptime_s",
    "type",
    "status",
    "start_uptime_s",
    "elapsed_s",
    "voltage_v",
    "current_a",
    "power_w",
    "min_voltage_v",
    "peak_current_a",
    "peak_power_w",
    "avg_voltage_v",
    "avg_current_a",
    "avg_power_w",
    "charge_mAh",
    "energy_Wh",
    "tau_s",
    "capacitance_uF",
    "test_voltage_v",
    "forward_voltage_v",
    "resistor_drop_v",
    "diode_current_mA",
    "classification",
    "voc_v",
    "source_resistance_ohm",
    "r_squared",
    "point_count",
    "fault_code",
    "fault_state",
    "measured_value",
    "threshold",
    "mode",
    "points_json",
)


class ExperimentLogger:
    def __init__(self, directory=LOG_DIRECTORY, max_log_bytes=MAX_LOG_BYTES):
        self.directory = directory
        self.max_log_bytes = max_log_bytes
        self.sequence = 0
        self.available = True
        self.last_error = None
        self.records_written = 0
        self.last_record = None
        self._ensure_directory()

    def _path(self, kind):
        filename = FAULT_FILE if kind == "faults" else EXPERIMENT_FILE
        return self.directory + "/" + filename

    def _ensure_directory(self):
        try:
            os.stat(self.directory)
        except OSError:
            try:
                os.mkdir(self.directory)
            except OSError as exc:
                self.available = False
                self.last_error = str(exc)
                print("LOG  | directory error |", exc)

    def _file_size(self, path):
        try:
            return os.stat(path)[6]
        except OSError:
            return 0

    def _rotate_if_needed(self, path):
        if self._file_size(path) < self.max_log_bytes:
            return
        old_path = path + ".old"
        try:
            os.remove(old_path)
        except OSError:
            pass
        try:
            os.rename(path, old_path)
            print("LOG  | rotated |", path)
        except OSError as exc:
            print("LOG  | rotation error |", exc)

    def _time_fields(self):
        uptime_s = time.ticks_ms() // 1000
        timestamp = None
        try:
            candidate = int(time.time())
            if candidate >= 1700000000:
                timestamp = candidate
        except Exception:
            pass
        return timestamp, uptime_s

    def _new_id(self, uptime_s):
        self.sequence = (self.sequence + 1) % 10000
        return "{:010d}-{:04d}".format(int(uptime_s), self.sequence)

    def append_record(self, kind, record_type, data=None, status="completed"):
        try:
            self._ensure_directory()
            path = self._path(kind)
            self._rotate_if_needed(path)
            timestamp, uptime_s = self._time_fields()
            record = {
                "record_id": self._new_id(uptime_s),
                "timestamp": timestamp,
                "uptime_s": uptime_s,
                "type": record_type,
                "status": status,
                "data": data or {},
            }
            line = json.dumps(record)
            with open(path, "a") as handle:
                handle.write(line)
                handle.write("\n")
            self.available = True
            self.last_error = None
            self.records_written += 1
            self.last_record = record
            print("LOG  | wrote |", record_type, record["record_id"])
            return record
        except Exception as exc:
            self.available = False
            self.last_error = str(exc)
            print("LOG  | write error |", exc)
            return None

    def append_experiment(self, record_type, data=None, status="completed"):
        return self.append_record("experiments", record_type, data, status)

    def append_fault(self, fault_code, fault_state, value, threshold, mode):
        return self.append_record(
            "faults",
            "FAULT",
            {
                "fault_code": fault_code,
                "fault_state": fault_state,
                "measured_value": value,
                "threshold": threshold,
                "mode": mode,
            },
            fault_state,
        )

    def _read_records(self, kind, limit=None):
        records = []
        path = self._path(kind)
        try:
            with open(path, "r") as handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                        if isinstance(record, dict):
                            records.append(record)
                            if limit is not None and len(records) > limit:
                                records.pop(0)
                    except Exception:
                        continue
        except OSError:
            return []
        except Exception as exc:
            self.last_error = str(exc)
            print("LOG  | read error |", exc)
        return records

    def recent(self, kind="experiments", limit=RECENT_RECORD_LIMIT):
        return self._read_records(kind, max(1, int(limit)))

    def recent_combined(self, limit=RECENT_RECORD_LIMIT):
        records = self.recent("experiments", limit)
        records.extend(self.recent("faults", limit))
        try:
            records.sort(key=lambda item: item.get("uptime_s", 0))
        except Exception:
            pass
        if len(records) > limit:
            records = records[-limit:]
        return records

    def export_json(self, kind="experiments"):
        try:
            return json.dumps(self._read_records(kind))
        except Exception as exc:
            print("LOG  | JSON export error |", exc)
            return "[]"

    def _data_value(self, data, column):
        aliases = {
            "voltage_v": ("ending_voltage_v", "voltage_v"),
            "current_a": ("ending_current_a", "current_a"),
            "power_w": ("ending_power_w", "power_w"),
            "diode_current_mA": ("diode_current_mA", "current_mA"),
            "source_resistance_ohm": ("source_resistance_ohm", "rs_ohm"),
        }
        for key in aliases.get(column, (column,)):
            if key in data:
                return data[key]
        return None

    def _csv_value(self, value):
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        text = str(value)
        if "," in text or '"' in text or "\n" in text or "\r" in text:
            return '"' + text.replace('"', '""') + '"'
        return text

    def export_csv(self, kind="experiments"):
        lines = [",".join(CSV_COLUMNS)]
        try:
            for record in self._read_records(kind):
                data = record.get("data") or {}
                row = []
                for column in CSV_COLUMNS:
                    if column in ("record_id", "timestamp", "uptime_s", "type", "status"):
                        value = record.get(column)
                    elif column == "points_json":
                        value = data.get("points")
                    else:
                        value = self._data_value(data, column)
                    row.append(self._csv_value(value))
                lines.append(",".join(row))
        except Exception as exc:
            print("LOG  | CSV export error |", exc)
        return "\r\n".join(lines) + "\r\n"

    def status(self):
        return {
            "available": self.available,
            "last_error": self.last_error,
            "records_written": self.records_written,
            "last_record": self.last_record,
        }