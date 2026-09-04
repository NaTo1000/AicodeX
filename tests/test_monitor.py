"""Standard-library tests for the AicodeX Edition 2 realtime monitor."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.monitor import MetricSample, MonitorSystem

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
MON_CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["monitor"]


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class ValveTests(unittest.TestCase):
    def test_open_valve_batches_samples(self) -> None:
        monitor = MonitorSystem()
        valve = monitor.valve("conductor")
        valve.send(MetricSample("conductor", "latency", 12.0))
        self.assertEqual(len(valve.pending), 1)

    def test_closed_valve_drops_samples(self) -> None:
        monitor = MonitorSystem()
        valve = monitor.valve("hive")
        valve.open = False
        valve.send(MetricSample("hive", "throughput", 5.0))
        self.assertEqual(len(valve.pending), 0)

    def test_flush_drains_pending(self) -> None:
        monitor = MonitorSystem()
        valve = monitor.valve("metrics")
        valve.send(MetricSample("metrics", "tokens", 100.0))
        batch = valve.flush()
        self.assertEqual(len(batch), 1)
        self.assertEqual(valve.pending, [])


class MonitorTickTests(unittest.TestCase):
    def test_tick_forwards_to_conductor_and_db(self) -> None:
        received_conductor, received_db = [], []
        monitor = MonitorSystem(conductor=received_conductor.append,
                                db_analyzer=received_db.append)
        monitor.valve("conductor").send(MetricSample("conductor", "x", 1.0))
        monitor.tick()
        self.assertEqual(len(received_conductor), 1)
        self.assertEqual(len(received_db), 1)
        self.assertEqual(received_conductor[0][0].name, "x")

    def test_tick_stamps_timestamp(self) -> None:
        clock = FakeClock()
        monitor = MonitorSystem(clock=clock)
        monitor.valve("hive").send(MetricSample("hive", "y", 2.0))
        batch = monitor.tick()
        self.assertEqual(batch[0].timestamp, 0.0)
        clock.advance(1.0)
        monitor.valve("hive").send(MetricSample("hive", "z", 3.0))
        batch = monitor.tick()
        self.assertEqual(batch[0].timestamp, 1.0)

    def test_due_respects_refresh_interval(self) -> None:
        clock = FakeClock()
        monitor = MonitorSystem(refresh_interval=0.5, clock=clock)
        self.assertTrue(monitor.due())            # first tick always due
        monitor.tick()
        self.assertFalse(monitor.due())           # just ticked
        clock.advance(0.4)
        self.assertFalse(monitor.due())           # not yet 0.5s
        clock.advance(0.1)
        self.assertTrue(monitor.due())            # now due

    def test_run_once_only_when_due(self) -> None:
        clock = FakeClock()
        monitor = MonitorSystem(refresh_interval=0.5, clock=clock)
        monitor.valve("metrics").send(MetricSample("metrics", "a", 1.0))
        first = monitor.run_once()
        self.assertIsNotNone(first)
        # Not due yet; second call returns None even with pending samples.
        monitor.valve("metrics").send(MetricSample("metrics", "b", 2.0))
        self.assertIsNone(monitor.run_once())
        clock.advance(0.5)
        self.assertIsNotNone(monitor.run_once())

    def test_default_refresh_interval_is_half_second(self) -> None:
        self.assertEqual(MonitorSystem().refresh_interval, 0.5)
        self.assertEqual(MON_CFG["refresh_interval_seconds"], 0.5)

    def test_invalid_interval_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MonitorSystem(refresh_interval=0)


class MonitorRenderTests(unittest.TestCase):
    def test_render_display(self) -> None:
        monitor = MonitorSystem()
        for component in MON_CFG["valves"]:
            monitor.valve(component)
        text = monitor.render()
        self.assertIn("Realtime Monitor", text)
        self.assertIn("0.50s", text)
        self.assertIn("conductor", text)


class CliTests(unittest.TestCase):
    def test_monitor_flag(self) -> None:
        self.assertEqual(cli_main(["--monitor", "--config", str(CONFIG_PATH)]), 0)


if __name__ == "__main__":
    unittest.main()
