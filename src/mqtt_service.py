import json

from umqtt.simple import MQTTClient

class MQTTService:

    def __init__(self, server, user, password, client_id):
        self.listeners = []
        self.user = user
        self.password = password
        self.server = server
        self.subscribe_topic = "msb/state"
        self.client = MQTTClient(client_id, server, user=user, password=password, keepalive=0)
        self.state = None

    def sub_cb(self, topic, msg):
        print("Received message: " + msg.decode())
        data = json.loads(msg.decode())
        self.state = data
        self.inform(self.state)
        print(data)

    def connect_and_subscribe(self):
        self.client.connect()
        self.client.set_callback(self.sub_cb)
        self.client.subscribe(self.subscribe_topic, qos=0)

    def check_msg(self):
        try:
            self.client.check_msg()
        except Exception as e:
            self.connect_and_subscribe()
            print("Error in check_msg:", e)

    def get_state(self):
        return self.state

    def add_listener(self, listener):
        self.listeners.append(listener)

    def inform(self, state):
        for listener in self.listeners:
            listener(state)



