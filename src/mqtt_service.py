import json
import time

from umqtt.simple import MQTTClient

class MQTTService:

    def __init__(self, server, user, password, client_id):
        self.listeners = []
        self.connection_listeners = []
        self.user = user
        self.password = password
        self.server = server
        self.client_id = client_id
        self.subscribe_topic = "msb/state"
        self.client = None
        self.state = None
        self.connected = False
        self.last_reconnect_attempt = 0
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        self.current_reconnect_delay = self.reconnect_delay
        self.consecutive_failures = 0

    def _create_client(self):
        self.client = MQTTClient(
            self.client_id,
            self.server,
            user=self.user,
            password=self.password,
            keepalive=60
        )
        self.client.set_callback(self.sub_cb)

    def sub_cb(self, topic, msg):
        print("Received message: " + msg.decode())
        try:
            data = json.loads(msg.decode())
            self.state = data
            self.inform(self.state)
            print(data)
        except Exception as e:
            print("Error parsing MQTT message:", e)

    def connect_and_subscribe(self):
        try:
            if self.client is not None:
                try:
                    self.client.disconnect()
                except:
                    pass

            self._create_client()
            self.client.connect()
            self.client.subscribe(self.subscribe_topic, qos=0)
            self.consecutive_failures = 0
            self.current_reconnect_delay = self.reconnect_delay
            self._set_connected(True)
            print("MQTT connected successfully")
            return True
        except Exception as e:
            print("MQTT connection failed:", e)
            self._set_connected(False)
            return False

    def _should_attempt_reconnect(self):
        now = time.time()
        if now - self.last_reconnect_attempt >= self.current_reconnect_delay:
            return True
        return False

    def _handle_reconnect(self):
        if not self._should_attempt_reconnect():
            return False

        self.last_reconnect_attempt = time.time()
        self.consecutive_failures += 1

        print(f"MQTT reconnecting (attempt {self.consecutive_failures}, delay was {self.current_reconnect_delay}s)...")

        success = self.connect_and_subscribe()

        if not success:
            self.current_reconnect_delay = min(
                self.current_reconnect_delay * 2,
                self.max_reconnect_delay
            )

        return success

    def check_msg(self):
        if not self.connected or self.client is None:
            self._handle_reconnect()
            return

        try:
            self.client.check_msg()
        except Exception as e:
            print("Error in check_msg:", e)
            self._set_connected(False)
            self._handle_reconnect()

    def ping(self):
        if not self.connected or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception as e:
            print("MQTT ping failed:", e)
            self._set_connected(False)
            return False

    def is_connected(self):
        return self.connected

    def get_state(self):
        return self.state

    def add_listener(self, listener):
        self.listeners.append(listener)

    def add_connection_listener(self, listener):
        self.connection_listeners.append(listener)

    def inform(self, state):
        for listener in self.listeners:
            listener(state)

    def _set_connected(self, connected):
        if self.connected != connected:
            self.connected = connected
            self._inform_connection(connected)

    def _inform_connection(self, connected):
        for listener in self.connection_listeners:
            try:
                listener(connected)
            except Exception as e:
                print("Error in connection listener:", e)



