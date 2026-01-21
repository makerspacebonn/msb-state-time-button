import urequests as requests
import logger

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
        logger.debug("API", f"Sending request: {url}")
        r = requests.get(url, headers=headers)
        logger.info("API", f"Response: {r.status_code}")
        logger.debug("API", f"Response body: {r.text}")
        r.close()

    def urlencode(self, value):
        return value.replace(':', '%3A')
