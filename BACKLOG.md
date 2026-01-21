# MSB State Time Button - Backlog

## Planned Features

### Status Icons for Connectivity
**Priority:** High

Add visual status icons for WLAN and MQTT connection state on the display.

**Requirements:**
- [ ] Create small icons for WLAN status (connected/disconnected)
- [ ] Create small icons for MQTT status (connected/disconnected)
- [ ] Display icons in normal view (status screen)
- [ ] Display icons in screensaver mode (bouncing with content)
- [ ] Icons should be unobtrusive but clearly visible
- [ ] Consider icon placement (corner of screen recommended)

**Technical Notes:**
- Icons should be small PBM files (e.g., 8x8 or 10x10 pixels)
- `wifi_manager.is_connected()` provides WLAN status
- `mqtt_service.is_connected()` provides MQTT status
- Update `MSBDisplay.status()` for normal view
- Update `MSBDisplay.screensaver()` for screensaver mode

---

## Completed Features

- [x] Logging system with configurable levels
- [x] Screensaver with bouncing logo
- [x] Configurable screensaver timeout
- [x] Configurable display brightness (init/normal/screensaver)
- [x] Dynamic screensaver block width based on content
