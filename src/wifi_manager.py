import time
import network
import logger


class WifiManager:

    CONNECTION_TIMEOUT = 30  # seconds to wait for connection
    MAX_RETRIES = 3  # max connection attempts per reconnect call

    def __init__(self, wifi_access, hostname = "IoT Button"):
        self.listeners = []
        self.hostname = hostname
        self.wifi_access = wifi_access
        self.ssid = ''
        self.password = ''
        self.sta_if = None

    def addListener(self, listener):
        self.listeners.append(listener)

    def inform(self, message):
        for listener in self.listeners:
            listener(message)

    def _scan_for_known_network(self):
        """Scan and return (ssid, password) for first known network, or (None, None)."""
        self.inform("Scanning wifi network...")
        logger.info("WIFI", "Scanning for networks...")
        try:
            wlans = self.sta_if.scan()
        except OSError as e:
            logger.error("WIFI", f"Scan failed: {e}")
            return None, None

        for wlan in wlans:
            ssid = wlan[0].decode()
            logger.debug("WIFI", f"Found SSID: {ssid}")
            if ssid in self.wifi_access.keys():
                return ssid, self.wifi_access[ssid]

        return None, None

    def _attempt_connection(self, ssid, password):
        """Attempt connection with timeout. Returns True if successful."""
        try:
            logger.debug("WIFI", f"Connecting to {ssid}...")
            time.sleep_us(100)
            self.sta_if.config(dhcp_hostname=self.hostname)
            self.sta_if.connect(ssid, password)

            start_time = time.time()
            while not self.sta_if.isconnected():
                if time.time() - start_time > self.CONNECTION_TIMEOUT:
                    logger.warn("WIFI", f"Connection timeout after {self.CONNECTION_TIMEOUT}s")
                    self.sta_if.disconnect()
                    return False
                time.sleep(1)

            logger.info("WIFI", f"Connected to {ssid}")
            return True
        except OSError as e:
            logger.error("WIFI", f"Connection error: {e}")
            return False

    def connect_wifi(self):
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)

        # Scan for known networks (don't use stale values)
        ssid, password = self._scan_for_known_network()

        if ssid is None:
            self.inform("!!!!! No known networks found !!!!")
            logger.error("WIFI", "No known networks found")
            return False

        self.ssid = ssid
        self.password = password
        self.inform('connecting to ' + self.ssid)
        logger.info("WIFI", f"Selected network: {self.ssid}")

        if not self.sta_if.isconnected():
            if not self._attempt_connection(self.ssid, self.password):
                self.inform('connection failed')
                return False

        self.inform('connected to ' + self.ssid)
        logger.info("WIFI", f"Network config: {self.sta_if.ifconfig()}")
        logger.debug("WIFI", f"Hostname: {self.sta_if.config('dhcp_hostname')}")
        return True

    def check_wifi(self):
        if self.sta_if is None:
            return "offline"
        return "to " + self.sta_if.config("ssid") if self.sta_if.isconnected() else "offline"

    def is_connected(self):
        return self.sta_if is not None and self.sta_if.isconnected()

    def reconnect(self):
        """Attempt reconnection with retries."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info("WIFI", f"Reconnection attempt {attempt}/{self.MAX_RETRIES}")
            self.inform(f"Reconnecting ({attempt}/{self.MAX_RETRIES})...")
            if self.connect_wifi():
                return True
            time.sleep(2)  # Brief pause between retries

        logger.error("WIFI", "All reconnection attempts failed")
        self.inform("Reconnection failed")
        return False

    def check_and_reconnect(self):
        if not self.is_connected():
            return self.reconnect()
        return True

    def disconnect(self):
        if self.sta_if is not None:
            self.sta_if.disconnect()
