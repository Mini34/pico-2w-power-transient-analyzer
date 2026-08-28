import time

try:
    import network
except ImportError:
    network = None

try:
    from secrets import WIFI_SSID, WIFI_PASSWORD
except ImportError:
    WIFI_SSID = None
    WIFI_PASSWORD = None


CONNECT_TIMEOUT_MS = 15000
RECONNECT_INTERVAL_MS = 5000


class WiFiManager:
    def __init__(self):
        self.wlan = None
        self.connected = False
        self.connecting = False
        self.ssid = WIFI_SSID
        self.ip = None
        self.status = "offline"
        self._attempt_started_ms = None
        self._next_retry_ms = None

    def credentials_available(self):
        return bool(self.ssid and WIFI_PASSWORD)

    def _ensure_interface(self):
        if network is None:
            self.status = "network unavailable"
            return False
        if self.wlan is None:
            self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        return True

    def _refresh_connection(self):
        try:
            self.connected = bool(self.wlan and self.wlan.isconnected())
        except Exception:
            self.connected = False

        if self.connected:
            try:
                self.ip = self.wlan.ifconfig()[0]
            except Exception:
                self.ip = None
            self.connecting = False
            self.status = "connected"
        else:
            self.ip = None

    def _begin_connect(self):
        if not self.credentials_available():
            self.status = "credentials missing"
            return False
        if not self._ensure_interface():
            return False

        try:
            self.wlan.connect(self.ssid, WIFI_PASSWORD)
            self.connecting = True
            self.status = "connecting"
            self._attempt_started_ms = time.ticks_ms()
            print("WIFI | connecting...")
            return True
        except Exception as exc:
            self.connecting = False
            self.status = "connect error"
            self._next_retry_ms = time.ticks_add(
                time.ticks_ms(), RECONNECT_INTERVAL_MS
            )
            print("WIFI | connect error |", exc)
            return False

    def connect(self, timeout_ms=CONNECT_TIMEOUT_MS):
        if not self._begin_connect():
            print("WIFI | offline |", self.status)
            return False

        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            self._refresh_connection()
            if self.connected:
                print("WIFI | connected |", self.ip)
                return True
            time.sleep_ms(100)

        self.connecting = False
        self.status = "connection timeout"
        self._next_retry_ms = time.ticks_add(
            time.ticks_ms(), RECONNECT_INTERVAL_MS
        )
        print("WIFI | offline | connection timeout")
        return False

    def poll(self):
        if self.wlan is not None:
            self._refresh_connection()
            if self.connected:
                return True

        if not self.credentials_available() or network is None:
            return False

        now = time.ticks_ms()

        if self.connecting:
            if time.ticks_diff(now, self._attempt_started_ms) >= CONNECT_TIMEOUT_MS:
                self.connecting = False
                self.status = "connection timeout"
                self._next_retry_ms = time.ticks_add(now, RECONNECT_INTERVAL_MS)
                print("WIFI | offline | connection timeout")
            return False

        if (
            self._next_retry_ms is None
            or time.ticks_diff(now, self._next_retry_ms) >= 0
        ):
            self._begin_connect()

        return False
