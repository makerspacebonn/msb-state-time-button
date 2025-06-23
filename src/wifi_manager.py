import time
import network


class WifiManager:


    def __init__(self, wifi_access, hostname = "IoT Button"):
        self.listeners = []
        self.hostname = hostname
        self.wifi_access = wifi_access
        self.ssid = ''
        self.password = ''

    def addListener(self, listener):
        self.listeners.append(listener)

    def inform(self, message):
        for listener in self.listeners:
            listener(message)

    def connect_wifi(self):
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)
        self.inform("Scanning wifi network...")
        print("Scanning wifi network...")
        wlans = self.sta_if.scan()
        for wlan in wlans:
            ssid = wlan[0].decode()
            print("trying SSID: " + ssid)
            if ssid in self.wifi_access.keys():
                self.ssid = ssid
                self.password = self.wifi_access[ssid]
                break

        if self.ssid == '':
            self.inform("!!!!! No SSID passwords found !!!!")
            print("!!!!! No SSID passwords found !!!!")
            return
        self.inform('connecting to ' + self.ssid)
        print("SSID to connect to: " + self.ssid)
        print("Wifi Key to use: " + 'NotGonnaTellYou')

        if not self.sta_if.isconnected():
            print('Connecting to Wifi: ', end="")
            time.sleep_us(100)
            self.sta_if.config(dhcp_hostname=self.hostname)
            self.sta_if.connect(self.ssid, self.password)
            while not self.sta_if.isconnected():
                print('.', end="")
                time.sleep(1)
        print("*")
        self.inform('connected to ' + self.ssid)
        print('Network config:', self.sta_if.ifconfig())
        print('hostname:', self.sta_if.config('dhcp_hostname'), '\n')

    def check_wifi(self):
        return "to " + self.sta_if.config("ssid") if self.sta_if.isconnected() else "offline"

    def is_connected(self):
        return self.sta_if.isconnected()

    def reconnect(self):
        self.connect_wifi()

    def check_and_reconnect(self):
        if not self.is_connected():
            self.reconnect()

    def disconnect(self):
        self.sta_if.disconnect()
