import time
import network


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
        print("Scanning wifi network...")
        try:
            wlans = self.sta_if.scan()
        except OSError as e:
            print(f"Scan failed: {e}")
            return None, None

        for wlan in wlans:
            ssid = wlan[0].decode()
            print("trying SSID: " + ssid)
            if ssid in self.wifi_access.keys():
                return ssid, self.wifi_access[ssid]

        return None, None

    def _attempt_connection(self, ssid, password):
        """Attempt connection with timeout. Returns True if successful."""
        try:
            print('Connecting to Wifi: ', end="")
            time.sleep_us(100)
            self.sta_if.config(dhcp_hostname=self.hostname)
            self.sta_if.connect(ssid, password)

            start_time = time.time()
            while not self.sta_if.isconnected():
                if time.time() - start_time > self.CONNECTION_TIMEOUT:
                    print(" timeout!")
                    self.sta_if.disconnect()
                    return False
                print('.', end="")
                time.sleep(1)

            print("*")
            return True
        except OSError as e:
            print(f" connection error: {e}")
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
            print("!!!!! No known networks found !!!!")
            return False

        self.ssid = ssid
        self.password = password
        self.inform('connecting to ' + self.ssid)
        print("SSID to connect to: " + self.ssid)
        print("Wifi Key to use: " + 'NotGonnaTellYou')

        if not self.sta_if.isconnected():
            if not self._attempt_connection(self.ssid, self.password):
                self.inform('connection failed')
                return False

        self.inform('connected to ' + self.ssid)
        print('Network config:', self.sta_if.ifconfig())
        print('hostname:', self.sta_if.config('dhcp_hostname'), '\n')
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
            print(f"Reconnection attempt {attempt}/{self.MAX_RETRIES}")
            self.inform(f"Reconnecting ({attempt}/{self.MAX_RETRIES})...")
            if self.connect_wifi():
                return True
            time.sleep(2)  # Brief pause between retries

        print("All reconnection attempts failed")
        self.inform("Reconnection failed")
        return False

    def check_and_reconnect(self):
        if not self.is_connected():
            return self.reconnect()
        return True

    def disconnect(self):
        if self.sta_if is not None:
            self.sta_if.disconnect()
