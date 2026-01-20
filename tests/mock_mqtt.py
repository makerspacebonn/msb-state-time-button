"""Mock MQTT client for testing purposes."""


class MockMQTTClient:
    """Mock implementation of umqtt.simple.MQTTClient."""

    _global_connect_should_fail = False
    _global_check_msg_should_fail = False
    _global_ping_should_fail = False

    def __init__(self, client_id, server, user=None, password=None, keepalive=0):
        self.client_id = client_id
        self.server = server
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.callback = None
        self.subscriptions = []
        self.connected = False
        self.messages = []

        self.connect_should_fail = MockMQTTClient._global_connect_should_fail
        self.check_msg_should_fail = MockMQTTClient._global_check_msg_should_fail
        self.ping_should_fail = MockMQTTClient._global_ping_should_fail
        self.disconnect_should_fail = False

        self.connect_call_count = 0
        self.disconnect_call_count = 0
        self.subscribe_call_count = 0
        self.check_msg_call_count = 0
        self.ping_call_count = 0

    @classmethod
    def set_global_connect_fail(cls, should_fail):
        """Set global flag for all new clients to fail on connect."""
        cls._global_connect_should_fail = should_fail

    @classmethod
    def set_global_check_msg_fail(cls, should_fail):
        """Set global flag for all new clients to fail on check_msg."""
        cls._global_check_msg_should_fail = should_fail

    @classmethod
    def set_global_ping_fail(cls, should_fail):
        """Set global flag for all new clients to fail on ping."""
        cls._global_ping_should_fail = should_fail

    @classmethod
    def reset_global_flags(cls):
        """Reset all global failure flags."""
        cls._global_connect_should_fail = False
        cls._global_check_msg_should_fail = False
        cls._global_ping_should_fail = False

    def connect(self):
        self.connect_call_count += 1
        if self.connect_should_fail:
            raise OSError("Connection refused")
        self.connected = True

    def disconnect(self):
        self.disconnect_call_count += 1
        if self.disconnect_should_fail:
            raise OSError("Disconnect failed")
        self.connected = False

    def set_callback(self, callback):
        self.callback = callback

    def subscribe(self, topic, qos=0):
        self.subscribe_call_count += 1
        if not self.connected:
            raise OSError("Not connected")
        self.subscriptions.append((topic, qos))

    def check_msg(self):
        self.check_msg_call_count += 1
        if self.check_msg_should_fail:
            raise OSError("Connection lost")
        if not self.connected:
            raise OSError("Not connected")

        if self.messages and self.callback:
            topic, msg = self.messages.pop(0)
            self.callback(topic, msg)

    def ping(self):
        self.ping_call_count += 1
        if self.ping_should_fail:
            raise OSError("Ping failed")
        if not self.connected:
            raise OSError("Not connected")

    def simulate_message(self, topic, msg):
        """Helper to simulate an incoming MQTT message."""
        if isinstance(topic, str):
            topic = topic.encode()
        if isinstance(msg, str):
            msg = msg.encode()
        self.messages.append((topic, msg))

    def reset_counts(self):
        """Reset all call counters."""
        self.connect_call_count = 0
        self.disconnect_call_count = 0
        self.subscribe_call_count = 0
        self.check_msg_call_count = 0
        self.ping_call_count = 0

    def reset_failures(self):
        """Reset all failure flags."""
        self.connect_should_fail = False
        self.check_msg_should_fail = False
        self.ping_should_fail = False
        self.disconnect_should_fail = False
        MockMQTTClient.reset_global_flags()
