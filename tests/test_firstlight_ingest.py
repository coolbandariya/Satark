"""Tests for bounded FIRSTLIGHT event ingestion and deterministic detection."""
import json
import unittest

from firstlight_ingest import (
    MAX_ARTIFACT_BYTES,
    IngestError,
    detect_event_patterns,
    ingest_event_artifact,
)


class FirstlightIngestTests(unittest.TestCase):
    def test_json_normalizes_aliases_and_timezone(self):
        payload = json.dumps({
            "events": [{
                "id": "A-1",
                "time": "2026-10-10T12:00:00+02:00",
                "provider": "identity",
                "event_type": "authentication",
                "message": "Login succeeded",
                "attributes": {"result": "success", "novel_source": True},
            }]
        }).encode()
        result = ingest_event_artifact(payload, "events.json")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["events"][0]["timestamp"], "2026-10-10T10:00:00+00:00")
        self.assertEqual(result["events"][0]["event_id"], "A-1")
        self.assertEqual(len(result["artifact_sha256"]), 64)
        findings = detect_event_patterns(result["events"])
        self.assertEqual(findings[0]["rule_id"], "FL-ID-001")
        self.assertEqual(findings[0]["evidence_ids"], ["A-1"])

    def test_csv_import_and_naive_timestamp_warning(self):
        payload = (
            "event_id,timestamp,source,kind,summary,details\n"
            'C-1,2026-10-10T09:00:00,identity,authentication,Login,"{""result"": ""success"", ""novel_source"": true}"\n'
        ).encode()
        result = ingest_event_artifact(payload, "events.csv")
        self.assertEqual(result["record_count"], 1)
        self.assertTrue(any("UTC was assumed" in warning for warning in result["warnings"]))

    def test_rejects_unsupported_format_and_invalid_json(self):
        with self.assertRaises(IngestError):
            ingest_event_artifact(b"{}", "events.exe")
        with self.assertRaises(IngestError):
            ingest_event_artifact(b"{broken", "events.json")

    def test_rejects_empty_and_oversized_artifact(self):
        with self.assertRaises(IngestError):
            ingest_event_artifact(b"", "events.json")
        with self.assertRaisesRegex(IngestError, "5 MiB"):
            ingest_event_artifact(b"x" * (MAX_ARTIFACT_BYTES + 1), "events.csv")

    def test_duplicate_ids_are_rejected_without_losing_other_rows(self):
        payload = json.dumps([
            {"event_id": "same", "timestamp": "2026-10-10T09:00:00Z", "source": "x", "kind": "login", "summary": "first"},
            {"event_id": "same", "timestamp": "2026-10-10T09:01:00Z", "source": "x", "kind": "login", "summary": "duplicate"},
            {"event_id": "other", "timestamp": "2026-10-10T09:02:00Z", "source": "x", "kind": "login", "summary": "third"},
        ]).encode()
        result = ingest_event_artifact(payload, "events.json")
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["rejected_count"], 1)
        self.assertIn("duplicate event_id", result["errors"][0]["error"])

    def test_rules_correlate_process_and_network_with_evidence_refs(self):
        events = [
            {"event_id": "PROC", "timestamp": "2026-10-10T09:00:00+00:00", "source": "endpoint", "kind": "process", "summary": "script", "details": {"process": "powershell.exe", "parent": "outlook.exe", "host": "WS-1"}},
            {"event_id": "NET", "timestamp": "2026-10-10T09:10:00+00:00", "source": "network", "kind": "connection", "summary": "connection", "details": {"host": "WS-1"}},
        ]
        findings = detect_event_patterns(events)
        refs = [finding["evidence_ids"] for finding in findings]
        self.assertIn(["PROC"], refs)
        self.assertIn(["PROC", "NET"], refs)
        for finding in findings:
            self.assertTrue(finding["evidence_ids"])
            self.assertIn("explanation", finding)

    def test_bad_rows_are_reported_and_untrusted_details_are_bounded(self):
        payload = json.dumps([
            {"timestamp": "not-a-date", "source": "x", "kind": "x", "summary": "bad"},
            {"timestamp": "2026-10-10T09:00:00Z", "source": "x", "kind": "x", "summary": "ok", "details": {"note": "ok"}},
        ]).encode()
        result = ingest_event_artifact(payload, "events.json")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["rejected_count"], 1)
        too_large_details = json.dumps([{
            "timestamp": "2026-10-10T09:00:00Z", "source": "x", "kind": "x", "summary": "ok",
            "details": {"note": "x" * 17000},
        }]).encode()
        with self.assertRaisesRegex(IngestError, "no valid event records"):
            ingest_event_artifact(too_large_details, "events.json")  # all-invalid input fails closed


if __name__ == "__main__":
    unittest.main()
