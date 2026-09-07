#!/usr/bin/env python3
"""W6 — Beacon Flood (offscreen generator + detector).

Builds many distinct, byte-exact 802.11 beacon frames across N fake BSSIDs
(lab OUI 00:11:22 only, `lab-*` SSIDs) into a pcap fixture, and detects the
resulting flood: unique-BSSID counts, per-window beacon rates, and SSID
confusion. All frame work is pure bytes; no radio is ever driven — a simulated
"emission latch" is exposed only behind a full safety gate and is disabled in
this build.

Use for authorized wireless testing and WIDS/fingerprint research only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    from firmware import frame_core as fc
except ImportError:
    try:
        import frame_core as fc
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "firmware"))
        import frame_core as fc

SAFETY_FLAG = "--i-understand-this-is-an-offline-lab-simulation-with-no-radio-emission"
LAB_OUI = "00:11:22"
SAFE_PREFIX = "lab-"
START_TS = 1700000000.0


# ----------------------------------------------------------------------
# Byte-exact beacon generator over distinct (fake) BSSIDs
# ----------------------------------------------------------------------

def wide_mac(index: int) -> str:
    """00:11:22:zz:yy:xx from an integer index (lab OUI only)."""
    if not 0 <= index < 0xFFFFFF:
        raise ValueError("beacon index out of lab-OUI range")
    return ":".join(f"{b:02x}" for b in bytes([0x00, 0x11, 0x22,
                                               (index >> 16) & 0xFF,
                                               (index >> 8) & 0xFF,
                                               index & 0xFF]))


def build_flood_frames(ssids: list, mac_count: int, per_ap: int = 4,
                       base_time: float = START_TS) -> list[dict]:
    """Generate `per_ap` beacon frames for each of `mac_count` fake BSSIDs."""
    frames = []
    seq = 0
    drop = set()
    for i in range(mac_count):
        bssid = wide_mac(i + 3)          # skip 00:11:22:00:00:00/1/2
        ssid = ssids[i % len(ssids)]
        for k in range(per_ap):
            seq = (seq + 1) & 0xFFFF
            b = fc.build_beacon(bssid, ssid=ssid, timestamp=1000 + k + i,
                                beacon_interval=100, seq_num=seq)
            frames.append({"ts": base_time + 0.1 * (i + k), "bssid": bssid,
                           "ssid": ssid, "data": b + fc.fcs(b), "seq": seq})
    return frames


def write_flood_fixture(path: str, ssids: list, mac_count: int, per_ap: int = 4) -> int:
    frames = build_flood_frames(ssids, mac_count, per_ap)
    fc.write_pcap(path, [f["data"] for f in frames], ts=frames[0]["ts"])
    return len(frames)


# ----------------------------------------------------------------------
# Flood detector (takes any pcap; detects phishing/lab-flood fingerprints)
# ----------------------------------------------------------------------

def analyze_beacons(frames: list[bytes]) -> dict:
    ap_beacons = {}
    for data in frames:
        if not fc.verify_fcs(data):
            continue
        payload = data[:-4]
        try:
            fields, _ = fc.parse_mgmt_header(payload)
            if fields["subtype_val"] != fc.FC_SUBTYPE_BEACON:
                continue
            p, _ = fc.parse_beacon(payload)
        except ValueError:
            continue
        bssid = fields["bssid"]
        ap_beacons.setdefault(bssid, {"count": 0, "ssids": set(), "first_seq": fields["seq_num"]})
        ap_beacons[bssid]["count"] += 1
        ap_beacons[bssid]["ssids"].add(p["ssid"])
    return ap_beacons


def detect_flood(ap_beacons: dict, flood_bssid_threshold: int = 8,
                 confusion_threshold: int = 2) -> dict:
    unique_bssids = len(ap_beacons)
    total = sum(v["count"] for v in ap_beacons.values())
    confusions = {b: sorted(v["ssids"]) for b, v in ap_beacons.items()
                  if len(v["ssids"]) >= confusion_threshold}
    # approximate rate: assume 100ms fixture spacing, per the deterministic generator
    span = 0.1 * max((v["count"] for v in ap_beacons.values()), default=1)
    rate = total / max(span, 0.001)
    verdict = "benign"
    if unique_bssids > flood_bssid_threshold or confusions:
        verdict = "flood-or-confusion"
    return {
        "unique_bssids": unique_bssids,
        "total_beacons": total,
        "approximate_rate_bps": round(rate, 2),
        "flood_bssid_threshold": flood_bssid_threshold,
        "ssid_confusion": confusions,
        "verdict": verdict,
    }


# ----------------------------------------------------------------------
# Simulated emission latch (safety-gated; inert build)
# ----------------------------------------------------------------------

class EmissionLatch:
    """A simulated OTA path. Not wired to any radio in this build."""

    def __init__(self, confirm: bool):
        if not confirm:
            raise SystemExit(
                f"REFUSED: real-air beacon flood is not available in this tool.\n"
                f"To run the OFF-CAMPUS SIMULATION (no radio), pass {SAFETY_FLAG}.")
        self.armed = bool(confirm)

    def pulse(self) -> None:
        if not self.armed:
            return
        print("[emit] simulated latch pulse — no physical radio driven in this build")


# ----------------------------------------------------------------------
# CLI / demo
# ----------------------------------------------------------------------

def build_args_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="w6-beacon-flood",
        description="Beacon flood generator + detector: distinct fake-BSSID beacons "
                    "(lab OUI, lab-* SSIDs) to pcap, then flood/confusion detection. "
                    "Pure-stdlib bytes; offline; radio emission not available.")
    p.add_argument("--count", type=int, default=16, help="fake BSSID count (default 16)")
    p.add_argument("--ssids", nargs="+", default=["lab-flood-a", "lab-flood-b", "lab-flood-c"],
                   help="SSIDs (must start with lab-)")
    p.add_argument("--pcap", metavar="PATH", help="pcap fixture to analyze")
    p.add_argument("--gen-fixture", metavar="PATH", help="write flood fixture pcap")
    p.add_argument("--json", metavar="PATH", help="write JSON report")
    p.add_argument(SAFETY_FLAG, dest="confirm", action="store_true",
                   help="acknowledge this is an offline simulation with no radio emission")
    return p


def main(argv=None) -> int:
    args = build_args_parser().parse_args(argv)
    for ssid in args.ssids:
        if not ssid.startswith(SAFE_PREFIX):
            raise SystemExit(f"REFUSED: SSID {ssid!r} does not start with {SAFE_PREFIX!r}"
                             " (lab only)")
    if args.gen_fixture:
        d = os.path.dirname(args.gen_fixture)
        if d:
            os.makedirs(d, exist_ok=True)
        n = write_flood_fixture(args.gen_fixture, args.ssids, args.count)
        print(f"[+] flood fixture -> {args.gen_fixture} ({n} distinct beacons, "
              f"{args.count} fake BSSIDs)")
    print("=" * 62)
    print(" W6 — Beacon Flood (offscreen generator + detector)")
    print("=" * 62)
    if args.pcap:
        frames = [r["data"] for r in fc.read_pcap(args.pcap)]
    else:
        frames = [f["data"] for f in build_flood_frames(args.ssids, args.count)]
    if not args.pcap:
        print(f"[+] built {len(frames)} beacon frames across {args.count} lab BSSIDs")
    ap = analyze_beacons(frames)
    det = detect_flood(ap)
    print(f"\n[+] unique BSSIDs: {det['unique_bssids']}   "
          f"beacons: {det['total_beacons']}   "
          f"rate~{det['approximate_rate_bps']}/s")
    for bssid, ssids in det["ssid_confusion"].items():
        print(f"    confusion {bssid}: {sorted(ssids)}")
    print(f"[+] verdict: {det['verdict']}")
    if args.confirm:
        EmissionLatch(args.confirm).pulse()
    else:
        print("[!] no radio path exercised (emission latch offline); nothing was transmitted")
    report = {"name": "w6-beacon-flood", "radio_emitted": False,
              "beacons": det["total_beacons"], "fake_bssids": det["unique_bssids"],
              "verdict": det["verdict"], "ssid_confusion": det["ssid_confusion"]}
    if args.json:
        d = os.path.dirname(args.json)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2, default=str)
    print("=" * 62)
    return 0


def run_demo() -> int:
    return main([])


if __name__ == "__main__":
    raise SystemExit(main())