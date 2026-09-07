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

## Legal Disclaimer

**IMPORTANT: Read before use.**

This project is provided for **educational and authorized security testing purposes only**. 

### Authorization Requirements
- You MUST have explicit written permission from the network owner before using this tool
- Unauthorized interception of network communications is illegal under federal and state laws
- This tool should ONLY be used on networks you own or have written authorization to test

### Legal Framework
- **Computer Fraud and Abuse Act (CFAA)**: Unauthorized access to computer systems is a federal crime
- **Wiretap Act (18 U.S.C. § 2511)**: Interception of electronic communications without consent is illegal
- **State Laws**: Many states have additional computer crime and wiretapping statutes
- **GDPR/CCPA**: Data collection may be subject to privacy regulations

### Acceptable Use
- Testing security of your own networks
- Authorized penetration testing with written scope
- Academic research in controlled lab environments
- Security education and training

### Prohibited Use
- Intercepting communications on networks you do not own
- Transmitting fake beacons on any real channel outside a licensed, authorized, shield-attenuated lab
- Any activity that violates applicable laws or regulations — this build cannot emit radio, period
- Commercial use without proper licensing

### Regulatory Framework
- **Federal Communications Act (47 U.S.C. § 333)**: Willful interference with authorized radio communications is prohibited.
- **47 CFR Part 15**: Unauthorized intentional radiators are regulated; this tool is byte-level only and emits nothing.
- **CFAA (18 U.S.C. § 1030)**: Injecting traffic or impersonating access points on networks you don't own is a federal crime.
- **ECPA/Wiretap Act**: Monitoring or interacting with wireless networks without authorization may violate interception laws.

## Live Lab Test Plan

Offline (this repo, no radio):
1. `python3 firmware/beacon_flood.py` — build 16 distinct lab BSSIDs with `lab-*` SSIDs and run
   the flood detector; verdict `flood-or-confusion`, exit 0.
2. `python3 firmware/beacon_flood.py --gen-fixture reports/flood.pcap --pcap reports/flood.pcap
   --json reports/w6.json` — fixture round-trip + report (exit 0).
3. `python3 firmware/beacon_flood.py --ssids corp-wifi` — REFUSED (non-lab SSID, exit 2).
4. `python3 -m unittest discover -s tests` — byte-exact FCS/build/parse confirmed (exit 0).

Authorized lab (only with written scope + shield + authorized channel):
5. Re-transmit the exact fixture bytes from an authorized SDR/module in a shielded enclosure and
   confirm the flood detector flags >= 9 unique BSSIDs playing the same `lab-*` SSID.
6. `green = permitted`: generating/poking pcap fixtures offline or, with written lab scope, in a
   shielded enclosure; never on networks you don't own.

## Metrics

- Beacon builder: distinct fake BSSIDs on lab OUI 00:11:22 only; FCS appended and verified
- IE/SSID: `lab-*` enforced at CLI (non-lab SSID -> exit 2); beacon interval 100; seq monotonic
- Detector: unique-BSSID count vs threshold (default 8), SSID-confusion cardinality (>=2 ssids/AP)
- pcap classic (linktype 105) fixture generate + analyze; captures/ and reports/ gitignored
- Offline: all 802.11 frames synthesized as bytes via frame_core; no radio, no wall-clock data

- Test suite: `python3 -m unittest discover -s tests`
- Reports: `reports/` (gitignored)

## License

MIT
