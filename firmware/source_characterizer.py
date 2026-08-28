MAX_SOURCE_POINTS = 20
CURRENT_DISTINCT_EPSILON_A = 0.0005
POINT_DUPLICATE_VOLTAGE_EPSILON_V = 0.002
MIN_CURRENT_SPAN_A = 0.001
CURRENT_POLARITY_TOLERANCE_A = 0.0005
MIN_SOURCE_RESISTANCE_OHM = 0.001
MIN_PLAUSIBLE_VOC_V = 0.0
MAX_PLAUSIBLE_VOC_V = 30.0
RECOMMENDED_SOURCE_POINTS = 3


def _valid_number(value):
    try:
        value = float(value)
        return value == value and abs(value) < 1000000000.0
    except Exception:
        return False


def _base_result(points):
    result = {
        "voc_v": None,
        "source_resistance_ohm": None,
        "r_squared": None,
        "point_count": len(points),
        "min_current_a": None,
        "max_current_a": None,
        "min_voltage_v": None,
        "max_voltage_v": None,
        "points": points,
        "status": "invalid",
        "reason": None,
        "warning": None,
    }
    if points:
        result["min_current_a"] = min(point["current_a"] for point in points)
        result["max_current_a"] = max(point["current_a"] for point in points)
        result["min_voltage_v"] = min(point["voltage_v"] for point in points)
        result["max_voltage_v"] = max(point["voltage_v"] for point in points)
    return result


def _invalid_result(points, reason, result=None):
    if result is None:
        result = _base_result(points)
    result["status"] = "invalid"
    result["reason"] = reason
    result["warning"] = reason
    return result


def fit_source(points):
    normalized = []
    for point in points or ():
        if isinstance(point, dict):
            voltage = point.get("voltage_v")
            current = point.get("current_a")
        else:
            voltage, current = point[0], point[1]
        if not _valid_number(voltage) or not _valid_number(current):
            continue
        normalized.append({
            "voltage_v": float(voltage),
            "current_a": float(current),
        })

    if len(normalized) < 2:
        return _invalid_result(normalized, "at least two valid points required")

    if any(
        point["current_a"] < -CURRENT_POLARITY_TOLERANCE_A
        for point in normalized
    ):
        return _invalid_result(
            normalized,
            "negative current conflicts with expected load-current polarity",
        )

    min_current = min(point["current_a"] for point in normalized)
    max_current = max(point["current_a"] for point in normalized)
    if max_current - min_current < MIN_CURRENT_SPAN_A:
        return _invalid_result(
            normalized,
            "current span is too small for a stable fit",
        )

    count = len(normalized)
    mean_i = sum(point["current_a"] for point in normalized) / count
    mean_v = sum(point["voltage_v"] for point in normalized) / count
    denominator = sum(
        (point["current_a"] - mean_i) ** 2
        for point in normalized
    )
    if denominator <= CURRENT_DISTINCT_EPSILON_A ** 2:
        return _invalid_result(
            normalized,
            "current values are too similar for a stable fit",
        )

    numerator = sum(
        (point["current_a"] - mean_i) * (point["voltage_v"] - mean_v)
        for point in normalized
    )
    slope = numerator / denominator
    intercept = mean_v - slope * mean_i

    residual_sum = 0.0
    total_sum = 0.0
    for point in normalized:
        predicted = intercept + slope * point["current_a"]
        residual_sum += (point["voltage_v"] - predicted) ** 2
        total_sum += (point["voltage_v"] - mean_v) ** 2
    if total_sum <= 0.000000000001:
        r_squared = 1.0 if residual_sum <= 0.000000000001 else 0.0
    else:
        r_squared = 1.0 - residual_sum / total_sum

    result = _base_result(normalized)
    result["voc_v"] = intercept
    result["source_resistance_ohm"] = -slope
    result["r_squared"] = r_squared

    if slope >= -MIN_SOURCE_RESISTANCE_OHM:
        return _invalid_result(
            normalized,
            "fit slope must be negative for V = Voc - I*Rs",
            result,
        )
    if result["source_resistance_ohm"] < 0:
        return _invalid_result(
            normalized,
            "negative fitted source resistance",
            result,
        )
    if not (MIN_PLAUSIBLE_VOC_V <= intercept <= MAX_PLAUSIBLE_VOC_V):
        return _invalid_result(
            normalized,
            "fitted open-circuit voltage is outside the configured range",
            result,
        )

    result["status"] = "completed"
    result["reason"] = None
    if count < RECOMMENDED_SOURCE_POINTS:
        result["warning"] = "three or more points recommended"
    return result


class GuidedSourceTest:
    def __init__(self, max_points=MAX_SOURCE_POINTS):
        self.max_points = max_points
        self.points = []

    def reset(self):
        self.points = []

    def add_point(self, voltage_v, current_a):
        if not _valid_number(voltage_v) or not _valid_number(current_a):
            return False, "invalid measurement"
        voltage_v = float(voltage_v)
        current_a = float(current_a)
        if current_a < -CURRENT_POLARITY_TOLERANCE_A:
            return False, "check current polarity"
        for point in self.points:
            if abs(point["current_a"] - current_a) < CURRENT_DISTINCT_EPSILON_A:
                if (
                    abs(point["voltage_v"] - voltage_v)
                    < POINT_DUPLICATE_VOLTAGE_EPSILON_V
                ):
                    return False, "duplicate point"
                return False, "current too similar"
        if len(self.points) >= self.max_points:
            return False, "point limit reached"
        self.points.append({
            "voltage_v": voltage_v,
            "current_a": current_a,
        })
        return True, "captured"

    def preview(self):
        return {
            "point_count": len(self.points),
            "points": list(self.points),
        }

    def result(self):
        return fit_source(self.points)


# Future load-controller hardware can call GuidedSourceTest.add_point after
# setting and settling a load state. No load switching or GPIO is defined here.
