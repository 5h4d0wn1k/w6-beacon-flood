# W6 — Beacon Flood

Generate hundreds of fake WiFi access points to overwhelm nearby devices.

## Overview

This project implements a beacon flood attack that:
- Generates 100+ fake WiFi access points
- Uses realistic SSID names (Free_WiFi, CoffeeShop, Hotel_WiFi, etc.)
- Hops across all WiFi channels
- Overwhelms WiFi scanning on nearby devices

**WARNING: Educational use only. Test on your own lab network.**

## Hardware

| Component | Connection | Role |
|-----------|------------|------|
| ESP32-C6 | Main board | Fake AP generator |

## How It Works

1. **SSID Generation**: Creates 100 fake SSIDs with realistic names
2. **Beacon Broadcasting**: Sends 802.11 beacon frames for each SSID
3. **Channel Hopping**: Rotates through channels 1-14
4. **Flooding**: Overwhelms WiFi scanners with fake networks

## Serial Output

```
=== W6 — Beacon Flood ===
Generated 100 fake SSIDs
Starting beacon flood...

[BEACON #100] SSID: Free_WiFi_42 | Channel: 7
[BEACON #200] SSID: CoffeeShop_18 | Channel: 11
[BEACON #300] SSID: Guest_Network_5 | Channel: 3
```

## Build & Flash

```bash
arduino-cli compile --fqbn esp32:esp32:esp32c6 w6_beacon_flood
arduino-cli upload --fqbn esp32:esp32:esp32c6 --port /dev/ttyACM0 w6_beacon_flood
```

## Research Value

- **W6 — Beacon Flood**: This project
- **W8 — Evil Portal**: Combine with credential capture
- **X5 — MITM Suite**: Network interception tools

## References

- IEEE 802.11 Management Frames
- WiFi Beacon Frame Structure

## License

MIT
