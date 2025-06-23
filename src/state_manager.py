
import urequests as requests

class StateManager:
    base_url = "https://status.makerspacebonn.de/api"
    time_url = base_url + "/msb/state/openUntil/"

    def __init__(self, api_key = None):
        self.api_key = api_key


    def sendTime(self, time):
        headers = {
            "msb-key": self.api_key,
        }
        url = self.time_url + time
        print(url)
        r = requests.get(url, headers=headers)
        print(r.status_code)
        print(r.text)
        r.close()

    def urlencode(self, value):
        return value.replace(':', '%3A')
