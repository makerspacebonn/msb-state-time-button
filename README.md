# MSB State Time Button

An ESP32-based device for displaying and setting the Makerspace Bonn open/closed status. Features an OLED display showing current time and status, with a rotary encoder for setting closing times.

## Features

- **Status Display**: Shows current time and makerspace open/closed status
- **Time Setting**: Use rotary encoder to select closing time in 15-minute increments
- **MQTT Integration**: Receives real-time status updates via MQTT
- **NTP Time Sync**: Automatic time synchronization with DST support (CET/CEST)
- **Screensaver**: Bouncing logo animation with configurable timeout to prevent OLED burn-in
- **Auto-Reconnect**: Robust WiFi and MQTT reconnection handling
- **Configurable Brightness**: Separate brightness levels for init, normal, and screensaver modes
- **Logging System**: Centralized logging with configurable levels (DEBUG/INFO/WARN/ERROR)

## Hardware

| Component | Specification |
|-----------|---------------|
| Microcontroller | ESP32 |
| Display | SH1106 128x64 OLED (I2C) |
| Input | Rotary encoder with push button |

### Pin Configuration

| Function | GPIO Pin |
|----------|----------|
| I2C SCL | 7 |
| I2C SDA | 6 |
| Button | 8 |
| Rotary A | 2 |
| Rotary B | 1 |

## Installation

1. Flash MicroPython to your ESP32

2. Create `src/secrets.py` with your credentials:
   ```python
   wifi_access = {
       "YourSSID": "YourPassword",
       # Add multiple networks for fallback
   }

   mqtt_server = "your.mqtt.server"
   mqtt_user = "username"
   mqtt_pass = "password"

   API_key = "your-api-key"
   ```

3. Upload all files from `src/` to the ESP32

4. Reset the device

## Configuration

Settings are defined at the top of `main.py`:

```python
# Logging
LOG_LEVEL = 1  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR

# Screensaver
SCREENSAVER_TIMEOUT = 300  # Seconds of inactivity (300 = 5 min)

# Display brightness (0-255)
BRIGHTNESS_INIT = 50        # During startup
BRIGHTNESS_NORMAL = 200     # Normal operation
BRIGHTNESS_SCREENSAVER = 5  # Screensaver mode
```

## Usage

### Normal Mode
- Display shows current time and makerspace status (open/closed)
- If open, shows closing time

### Setting Closing Time
1. Turn rotary encoder to select desired closing time
2. Press button to confirm
3. Device sends new closing time to the API

### Screensaver
- Activates after configurable timeout (default 5 minutes)
- Shows bouncing MSB logo with lock status icon
- Reduced brightness to save power and reduce burn-in
- Any input (rotation or button press) wakes the display

## Project Structure

```
src/
├── main.py              # Main application loop and configuration
├── logger.py            # Centralized logging module
├── MSBDisplay.py        # Display rendering (status, screensaver)
├── mqtt_service.py      # MQTT client with auto-reconnect
├── wifi_manager.py      # WiFi connection management
├── state_manager.py     # API communication
├── button_handler.py    # Button input with debouncing
├── rotary_irq_esp.py    # Rotary encoder driver
├── enhanced_display.py  # Extended display functions
├── sh1106.py            # SH1106 OLED driver
├── packed_font.py       # Custom font rendering
├── *.pbm                # Bitmap images (logo, icons)
├── *.pf                 # Packed font files
└── secrets.py           # Credentials (not in repo)
```

## Dependencies

- MicroPython (ESP32 port)
- `umqtt.simple` (included in MicroPython)
- `urequests` (included in MicroPython)

## License

MIT License
