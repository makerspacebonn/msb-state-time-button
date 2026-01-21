import math
import random
import time

import secrets

from machine import Pin, I2C
import machine

import sh1106
#import ssd1306

from MSBDisplay import MSBDisplay
from button_handler import ButtonHandler
from mqtt_service import MQTTService
from rotary_irq_esp import RotaryIRQ
import ntptime
from utime import localtime

from state_manager import StateManager

# Logging configuration
LOG_LEVEL = 1  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR
LOG_LEVELS = {0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR"}

def log(level, component, message):
    """Simple logging function for MicroPython"""
    if level >= LOG_LEVEL:
        level_name = LOG_LEVELS.get(level, "INFO")
        print(f"[{level_name}] [{component}] {message}")

def log_debug(component, message):
    log(0, component, message)

def log_info(component, message):
    log(1, component, message)

def log_warn(component, message):
    log(2, component, message)

def log_error(component, message):
    log(3, component, message)


def get_cet_offset():
    """
    Returns the correct offset for Central European Time in seconds.
    CET (winter): UTC+1 = 3600 seconds
    CEST (summer): UTC+2 = 7200 seconds

    DST rules for Central Europe:
    - Starts: Last Sunday of March at 2:00 UTC
    - Ends: Last Sunday of October at 3:00 UTC (2:00 UTC standard)
    """
    now = time.gmtime()
    year, month, day, hour = now[0], now[1], now[2], now[3]

    # Calculate last Sunday of March
    # March has 31 days, find what day of week March 31 is
    march_31 = time.mktime((year, 3, 31, 0, 0, 0, 0, 0))
    march_31_weekday = time.localtime(march_31)[6]  # 0=Monday, 6=Sunday
    dst_start_day = 31 - ((march_31_weekday + 1) % 7)

    # Calculate last Sunday of October
    # October has 31 days
    oct_31 = time.mktime((year, 10, 31, 0, 0, 0, 0, 0))
    oct_31_weekday = time.localtime(oct_31)[6]
    dst_end_day = 31 - ((oct_31_weekday + 1) % 7)

    # DST start: last Sunday of March at 2:00 UTC
    dst_start = time.mktime((year, 3, dst_start_day, 2, 0, 0, 0, 0))
    # DST end: last Sunday of October at 1:00 UTC (3:00 local becomes 2:00)
    dst_end = time.mktime((year, 10, dst_end_day, 1, 0, 0, 0, 0))

    current_time = time.time()

    if dst_start <= current_time < dst_end:
        return 2 * 3600  # CEST: UTC+2
    else:
        return 1 * 3600  # CET: UTC+1


from wifi_manager import WifiManager


wifi_access = secrets.wifi_access
API_KEY = secrets.API_key

log_info("INIT", "Starting MSB State Time Button")
log_info("INIT", f"Device ID: {machine.unique_id().hex()}")

log_debug("INIT", "Initializing I2C bus")
i2c = I2C(0, scl=Pin(7), sda=Pin(6))

log_debug("INIT", "Initializing button handler on pin 8")
button = ButtonHandler(8, cooldown_period=1000)

log_debug("INIT", "Initializing rotary encoder on pins 2, 1")
rotary = RotaryIRQ(2, 1, pull_up=True, reverse=True, min_val=0, max_val=80, range_mode=RotaryIRQ.RANGE_BOUNDED)

log_debug("INIT", "Initializing SH1106 OLED display (128x64)")
oledDisplay = sh1106.SH1106_I2C(128, 64, i2c)
display = MSBDisplay(i2c=i2c, display=oledDisplay)

log_debug("INIT", "Initializing state manager")
stateManager = StateManager(API_KEY)

display.rotate(True)
log_info("INIT", "Display rotated 180 degrees")

log_debug("INIT", "Initializing MQTT service")
mqtt_service = MQTTService(secrets.mqtt_server, secrets.mqtt_user, secrets.mqtt_pass, "msb_timing_button"  + machine.unique_id().hex())

log_debug("INIT", "Initializing WiFi manager")
wifi_manager = WifiManager(wifi_access)

log_info("INIT", "Hardware initialization complete")



mode = 'normal'
lastAction = None
lastActivity = time.time()  # Track last user activity for screensaver
screensaverFrame = 0
SCREENSAVER_TIMEOUT = 300  # 5 minutes in seconds

def rotary_turned(value):
    global mode, lastAction, lastActivity
    lastActivity = time.time()  # Reset screensaver timer
    log_debug("ROTARY", f"Rotary turned, value={value}, current mode={mode}")
    if mode == 'screensaver':
        log_info("MODE", "Exiting screensaver via rotary")
        mode = 'normal'
        return
    mode = 'setting time'
    lastAction = time.time()
    time_from_counter(value)
    log_debug("ROTARY", f"Mode changed to 'setting time'")

def button_clicked():
    global counter, mode, selectedTimeString, display, lastActivity
    lastActivity = time.time()  # Reset screensaver timer
    log_debug("BUTTON", f"Button clicked, current mode={mode}")
    if mode == 'screensaver':
        log_info("MODE", "Exiting screensaver via button")
        mode = 'normal'
        return
    if mode != 'setting time':
        log_debug("BUTTON", f"Ignoring click - not in 'setting time' mode")
        return
    counter = counter+1
    log_info("BUTTON", f"Setting time to {selectedTimeString}")
    display.message('setting time until ' + selectedTimeString)
    stateManager.sendTime(selectedTimeString)
    mode = 'requestSent'
    log_debug("MODE", "Mode changed to 'requestSent'")

def mqtt_status_changed(status = None):
    global mode
    log_info("MQTT", f"Status changed: {status}")
    if mode == 'requestSent':
        log_info("MODE", "Request confirmed, returning to normal mode")
        mode = 'normal'

log_debug("INIT", "Registering event listeners")
rotary.add_listener(rotary_turned)
button.add_listener(button_clicked)
mqtt_service.add_listener(mqtt_status_changed)
log_info("INIT", "Event listeners registered")

display.logo()
time.sleep(1)

log_info("WIFI", "Starting WiFi connection")
display.message('Initializing')
wifi_manager.addListener(lambda message: display.message(message))
wifi_manager.connect_wifi()
log_info("WIFI", "WiFi connected")

log_info("MQTT", "Connecting to MQTT broker")
display.message('Connecting to MQTT')
mqtt_service.connect_and_subscribe()
log_info("MQTT", "MQTT connected and subscribed")


selectedTimeString = ""

def time_from_counter(counter):
    global selectedTimeString
    now = time.localtime(time.time() + get_cet_offset() + (counter + 2) * 60*15)
    x = (now[0],now[1],now[2],now[3],math.floor(now[4]/15)*15,now[5],now[6],now[7])
    now = time.localtime(time.mktime(x))
    log_debug("TIME", f"Calculated time tuple: {now}")
    selectedTimeString = "{:02d}:{:02d}".format(now[3],now[4])
    log_debug("TIME", f"Selected time string: {selectedTimeString}")
    return selectedTimeString


log_info("NTP", "Syncing time with NTP server")
ntptime.settime()

dateTimeObj = localtime()
Dyear, Dmonth, Dday, Dhour, Dmin, Dsec, Dweekday, Dyearday = (dateTimeObj)
log_info("NTP", f"Time synced: {Dday}/{Dmonth}/{Dyear} {Dhour}:{Dmin}")

def getTimeString():
    now = time.localtime(time.time() + get_cet_offset())
    timeString = "{:02d}:{:02d}".format(now[3], now[4])
    return timeString

time_from_counter(0)


def should_execute():
    return random.randint(1, 1000) == 1

log_info("MAIN", "Entering main loop")
counter = 0
last_logged_mode = None
last_status_log = 0
STATUS_LOG_INTERVAL = 60  # Log status every 60 seconds

while True:
    if lastAction is not None and lastAction + 5 < time.time():
        lastAction = None
        log_debug("MODE", "Timeout - returning to normal mode")
        mode = 'normal'
        rotary.reset()

    # Check for screensaver activation (5 minutes of inactivity)
    if mode == 'normal' and time.time() - lastActivity > SCREENSAVER_TIMEOUT:
        log_info("MODE", "Activating screensaver after inactivity")
        mode = 'screensaver'
        screensaverFrame = 0  # Reset animation

    wifi_manager.check_and_reconnect()

    mqtt_service.check_msg()
    status = mqtt_service.get_state()

    # Log mode changes
    if mode != last_logged_mode:
        log_info("MODE", f"Mode: {mode}")
        last_logged_mode = mode

    # Periodic status logging (every 60 seconds in normal mode)
    current_time = time.time()
    if mode == 'normal' and current_time - last_status_log > STATUS_LOG_INTERVAL:
        log_debug("STATUS", f"Time: {getTimeString()}, MQTT status: {status}")
        last_status_log = current_time

    if mode == 'screensaver':
        display.screensaver(screensaverFrame, status)
        screensaverFrame += 1
    elif mode == 'normal':
        display.status(getTimeString(), status)
    elif mode == 'requestSent':
        display.message('setting time until ' + selectedTimeString)
    else:
        display.selectTime(selectedTimeString)





