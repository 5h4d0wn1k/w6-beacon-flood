#!/usr/bin/env python3
"""Byte-exact unit tests for w6-beacon-flood."""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from firmware import beacon_flood as bf
from firmware import frame_core as fc


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.frames = bf.build_flood_frames(["lab-a", "lab-b"], 6, per_ap=4)

    def test_distinct_bssids_lab_oui(self):
        bssids = {f["bssid"] for f in self.frames}
        self.assertEqual(len(bssids), 6)
        for b in bssids:
            self.assertTrue(b.startswith("00:11:22"))

    def test_all_frames_fcs_valid(self):
        for f in self.frames:
            self.assertTrue(fc.verify_fcs(f["data"]))

    def test_beacons_parse_back_ssid(self):
        for f in self.frames:
            p, _ = fc.parse_beacon(f["data"][:-4])
            self.assertTrue(p["ssid"].startswith("lab-"))


class DetectorTest(unittest.TestCase):
    def test_flood_verdict(self):
        frames = bf.build_flood_frames(["lab-a", "lab-b"], 16, per_ap=4)
        ap = bf.analyze_beacons([f["data"] for f in frames])
        det = bf.detect_flood(ap)
        self.assertEqual(det["unique_bssids"], 16)
        self.assertIn(det["verdict"], ("flood-or-confusion",))

    def test_confusion_detected(self):
        frames = []
        for s in ("lab-a", "lab-b", "lab-c"):
            b = fc.build_beacon(bf.wide_mac(5), ssid=s)
            frames.append({"data": b + fc.fcs(b)})
        ap = bf.analyze_beacons([f["data"] for f in frames])
        det = bf.detect_flood(ap, confusion_threshold=2)
        vals = det["ssid_confusion"]
        self.assertTrue(any("lab-a" in v for v in vals.values()))

    def test_benign_small(self):
        frames = bf.build_flood_frames(["lab-a"], 2, per_ap=1)
        ap = bf.analyze_beacons([f["data"] for f in frames])
        det = bf.detect_flood(ap)
        self.assertEqual(det["verdict"], "benign")


class SafetyTest(unittest.TestCase):
    def test_bad_ssid_refused(self):
        with self.assertRaises(SystemExit):
            bf.main(["--ssids", "corp-wifi"])

    def test_emission_latch_requires_flag(self):
        with self.assertRaises(SystemExit):
            bf.EmissionLatch(confirm=False)

    def test_emission_latch_armed_ok(self):
        bf.EmissionLatch(confirm=True)


class CLITest(unittest.TestCase):
    def test_demo_exit_zero(self):
        self.assertEqual(bf.run_demo(), 0)

    def test_fixture_and_detect(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "flood.pcap")
            rc = bf.main(["--gen-fixture", path, "--pcap", path, "--json",
                          os.path.join(tmp, "o.json")])
            self.assertEqual(rc, 0)
            data = json.load(open(os.path.join(tmp, "o.json")))
            self.assertFalse(data["radio_emitted"])


if __name__ == "__main__":
    unittest.main()