"""Synthetic schema/negative cases; no board or model execution."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_session.py"
SPEC = importlib.util.spec_from_file_location("session_audit", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class SessionAuditTests(unittest.TestCase):
    def setUp(self):
        self.contract = MOD.read_json(ROOT / "references/example-audit.json")
        self.session = dict(result="PASS", error=None, cleanup_errors=[], dma_halted=True,
                            elapsed_seconds=12.0, stop_reason="user_stop",
                            runtime=dict(faults=0, evictions_start=7, evictions_end=12),
                            hardware=dict(stream_errors=0, fault=64),
                            inference=dict(recent_results=[{"score": 0.9}], statistics={"enabled": False}))

    def run_audit(self):
        return MOD.audit(self.contract, self.session)

    def test_latest_snapshot_evictions_not_stream_loss(self):
        report = self.run_audit()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["metrics"]["snapshot_evictions"], 5)
        self.assertEqual(report["conclusions"]["unrecorded_pcm_continuity"], "NOT_DETERMINED")

    def test_recent_results_cannot_supply_session_statistics(self):
        self.assertIsNone(self.run_audit()["metrics"]["session_statistics"])

    def test_success_marker_cannot_hide_runtime_fault(self):
        self.session["runtime"]["faults"] = 8
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_cleanup_failure_is_not_clean_stop(self):
        self.session["cleanup_errors"] = ["DMA still active"]
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_expected_stop_bit_only_for_declared_stop(self):
        for reason, state, expected in (("user_stop", 64, "PASS"), ("overflow", 64, "FAIL"),
                                       ("user_stop", 72, "FAIL"), ("user_stop", 0, "PASS")):
            with self.subTest(reason=reason, state=state):
                self.session["stop_reason"] = reason
                self.session["hardware"]["fault"] = state
                self.assertEqual(self.run_audit()["status"], expected)

    def test_missing_fields_do_not_become_zero(self):
        del self.session["hardware"]["stream_errors"]
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_boolean_is_not_numeric_counter(self):
        self.session["runtime"]["faults"] = False
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_nonfinite_duration_rejected(self):
        for seconds in (float("nan"), float("inf"), 0, -1, True):
            self.session["elapsed_seconds"] = seconds
            self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_counter_reset_not_invented_as_wrap(self):
        self.session["runtime"]["evictions_end"] = 2
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_hardware_stop_confirmation_required(self):
        self.session["dma_halted"] = 1
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_mapping_supports_another_schema(self):
        self.session["other_name"] = self.session.pop("result")
        self.contract["success"]["path"] = ["other_name"]
        self.assertEqual(self.run_audit()["status"], "PASS")

    def test_whole_session_stats_not_recent_subset(self):
        stats = dict(enabled=True, successful_calculations=100, threshold_passes=70,
                     total_compute_seconds=200.0, average_compute_seconds=2.0, max_compute_seconds=3.0)
        self.session["inference"]["statistics"] = stats
        out = self.run_audit()
        self.assertEqual(out["status"], "PASS")
        self.assertEqual(out["metrics"]["session_statistics"]["successful_calculations"], 100)
        self.assertEqual(out["metrics"]["recent_result_count"], 1)

    def test_invalid_statistics_fail(self):
        self.session["inference"]["statistics"] = dict(enabled=True, successful_calculations=1,
            threshold_passes=2, total_compute_seconds=3.0, average_compute_seconds=3.0,
            max_compute_seconds=3.0)
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_zero_inferences_has_no_mean(self):
        self.session["inference"]["statistics"] = dict(enabled=True, successful_calculations=0,
            threshold_passes=None, total_compute_seconds=0.0, average_compute_seconds=None,
            max_compute_seconds=None)
        self.assertEqual(self.run_audit()["status"], "PASS")
        self.session["inference"]["statistics"]["average_compute_seconds"] = 0
        self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_malformed_contracts_fail(self):
        for key, value in (("schema_version", 2), ("zero", "any"),
                           ("success", {"path": "__import__('os')", "allowed": ["PASS"]}),
                           ("surprise", True)):
            c = copy.deepcopy(self.contract)
            c[key] = value
            self.assertEqual(MOD.audit(c, self.session)["status"], "FAIL")

    def test_cli_preserves_input_and_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, contract, output = (base / n for n in ("session.json", "contract.json", "audit.json"))
            source.write_text(json.dumps(self.session), encoding="utf-8")
            contract.write_text(json.dumps(self.contract), encoding="utf-8")
            before = source.read_bytes()
            cmd = [sys.executable, "-B", str(SCRIPT), "--contract", str(contract),
                   "--input", str(source), "--output", str(output)]
            result = subprocess.run(cmd, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = output.read_bytes()
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), data)
            self.assertEqual(source.read_bytes(), before)

    def test_duplicate_keys_cannot_hide_fault(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            path.write_text('{"runtime":{"faults":8,"faults":0}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                MOD.read_json(path)

    def test_reserved_metric_names_cannot_be_overwritten(self):
        for name in ("elapsed_seconds", "final_status", "recent_result_count", "session_statistics"):
            self.contract["counters"][0]["name"] = name
            self.assertEqual(self.run_audit()["status"], "FAIL")

    def test_overflow_decimal_cli_emits_complete_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, output = base / "input.json", base / "failure.json"
            source.write_text('{"elapsed_seconds":1e309}', encoding="utf-8")
            cmd = [sys.executable, "-B", str(SCRIPT), "--contract",
                   str(ROOT / "references/example-audit.json"), "--input", str(source),
                   "--output", str(output)]
            result = subprocess.run(cmd, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(output.read_text())["status"], "FAIL")
            self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

