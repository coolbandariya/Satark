"""Bounded, deterministic JSON/CSV event ingestion for FIRSTLIGHT.

Uploaded records are treated as untrusted data. This module performs no network
requests and never interprets imported text as instructions.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from typing import Any

MAX_ARTIFACT_BYTES = 5 * 1024 * 1024
MAX_RECORDS = 10_000
MAX_TEXT_CHARS = 4_096
MAX_DETAILS_BYTES = 16 * 1024

_FIELD_ALIASES = {
    "event_id": ("event_id", "evidence_id", "id"),
    "timestamp": ("timestamp", "time", "datetime", "event_time"),
    "source": ("source", "provider", "category"),
    "kind": ("kind", "type", "event_type"),
    "summary": ("summary", "message", "description", "name"),
    "details": ("details", "payload", "attributes", "data"),
}


class IngestError(ValueError):
    """Raised when an uploaded artifact cannot be safely ingested."""


def _first(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for name in aliases:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _text(value: Any, field: str, *, required: bool = True) -> str:
    if value is None:
        if required:
            raise ValueError(f"missing required field: {field}")
        return ""
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError(f"field {field} must be a string or number")
    result = str(value).strip()
    if required and not result:
        raise ValueError(f"missing required field: {field}")
    if len(result) > MAX_TEXT_CHARS:
        raise ValueError(f"field {field} exceeds {MAX_TEXT_CHARS} characters")
    return result


def _utc_timestamp(value: Any) -> tuple[str, bool]:
    raw = _text(value, "timestamp")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601 (for example 2026-10-10T09:15:00Z)") from exc
    assumed_utc = parsed.tzinfo is None
    if assumed_utc:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(), assumed_utc


def _parse_details(value: Any) -> dict[str, Any]:
    if value in (None, ""):
        details: Any = {}
    elif isinstance(value, dict):
        details = value
    elif isinstance(value, str):
        try:
            details = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("details must be a JSON object when supplied as text") from exc
    else:
        raise ValueError("details must be a JSON object")
    if not isinstance(details, dict):
        raise ValueError("details must be a JSON object")
    try:
        encoded = json.dumps(details, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("details must contain JSON-compatible values") from exc
    if len(encoded) > MAX_DETAILS_BYTES:
        raise ValueError(f"details exceeds {MAX_DETAILS_BYTES} bytes")
    return details


def _normalize_row(row: dict[str, Any], index: int, seen_ids: set[str]) -> tuple[dict[str, Any], bool]:
    if not isinstance(row, dict):
        raise ValueError("record must be a JSON object")
    normalized: dict[str, Any] = {}
    for field in ("timestamp", "source", "kind", "summary"):
        value = _first(row, _FIELD_ALIASES[field])
        if field == "timestamp":
            normalized[field], assumed_utc = _utc_timestamp(value)
        else:
            normalized[field] = _text(value, field)
    supplied_id = _first(row, _FIELD_ALIASES["event_id"])
    event_id = _text(supplied_id, "event_id") if supplied_id is not None else f"IMP-{index:06d}"
    if len(event_id) > 128:
        raise ValueError("event_id exceeds 128 characters")
    if event_id in seen_ids:
        raise ValueError(f"duplicate event_id: {event_id}")
    normalized["details"] = _parse_details(_first(row, _FIELD_ALIASES["details"]))
    normalized["event_id"] = event_id
    seen_ids.add(event_id)
    return normalized, assumed_utc


def ingest_event_artifact(data: bytes, filename: str = "events.json") -> dict[str, Any]:
    """Parse bounded JSON or CSV into normalized UTC events with provenance."""
    if not isinstance(data, bytes):
        raise IngestError("artifact must be supplied as bytes")
    artifact_hash = hashlib.sha256(data).hexdigest()
    if not data:
        raise IngestError("artifact is empty")
    if len(data) > MAX_ARTIFACT_BYTES:
        raise IngestError(f"artifact exceeds the {MAX_ARTIFACT_BYTES // (1024 * 1024)} MiB limit")
    if not isinstance(filename, str) or len(filename) > 255:
        raise IngestError("filename is invalid")
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix not in {"json", "csv"}:
        raise IngestError("only .json and .csv event files are supported")
    try:
        decoded = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestError("artifact must be UTF-8 encoded") from exc

    if suffix == "json":
        try:
            document = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise IngestError(f"invalid JSON: {exc.msg}") from exc
        except RecursionError as exc:
            raise IngestError("JSON nesting is too deep to process safely") from exc
        if isinstance(document, dict):
            rows = document.get("events")
        else:
            rows = document
        if not isinstance(rows, list):
            raise IngestError("JSON must be an array of events or an object with an events array")
    else:
        try:
            reader = csv.DictReader(io.StringIO(decoded, newline=""))
            if not reader.fieldnames:
                raise IngestError("CSV must include a header row")
            rows = list(reader)
        except csv.Error as exc:
            raise IngestError(f"invalid CSV: {exc}") from exc

    if len(rows) > MAX_RECORDS:
        raise IngestError(f"artifact contains more than {MAX_RECORDS} records")
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        try:
            event, assumed_utc = _normalize_row(row, index, seen_ids)
            events.append(event)
            if assumed_utc:
                warnings.append(f"Record {index} has no timezone; UTC was assumed.")
        except (ValueError, TypeError) as exc:
            errors.append({"record": index, "error": str(exc)})
    if not events:
        first_error = errors[0]["error"] if errors else "no records found"
        raise IngestError(f"no valid event records: {first_error}")
    return {
        "filename": filename,
        "format": suffix,
        "artifact_sha256": artifact_hash,
        "artifact_bytes": len(data),
        "record_count": len(events),
        "rejected_count": len(errors),
        "events": events,
        "errors": errors[:100],
        "warnings": sorted(set(warnings))[:100],
    }


def detect_event_patterns(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply small, explainable rules to normalized events; findings cite event IDs."""
    ordered = sorted(
        (event for event in events if isinstance(event, dict)),
        key=lambda event: str(event.get("timestamp", "")),
    )
    findings: list[dict[str, Any]] = []

    def emit(rule_id: str, title: str, explanation: str, severity: str, refs: list[str]) -> None:
        evidence_ids = list(dict.fromkeys(ref for ref in refs if ref))
        findings.append({
            "finding_id": f"DET-{len(findings) + 1:03d}",
            "rule_id": rule_id,
            "title": title,
            "explanation": explanation,
            "severity": severity,
            "confidence": "medium" if len(evidence_ids) > 1 else "low",
            "evidence_ids": evidence_ids,
            "state": "supported" if evidence_ids else "unverified",
        })

    process_events: list[dict[str, Any]] = []
    login_by_account: dict[str, list[dict[str, Any]]] = {}
    for event in ordered:
        details = event.get("details") if isinstance(event.get("details"), dict) else {}
        kind = str(event.get("kind", "")).lower()
        summary = str(event.get("summary", "")).lower()
        event_id = str(event.get("event_id", ""))
        process = str(details.get("process", "")).lower()
        parent = str(details.get("parent", "")).lower()
        if kind in {"authentication", "login", "signin", "sign-in"}:
            account = str(details.get("account", "")).lower()
            if details.get("result") == "success":
                login_by_account.setdefault(account, []).append(event)
            if details.get("result") == "success" and details.get("novel_source") is True:
                emit("FL-ID-001", "Successful login from a novel source",
                     "The source event explicitly marks a successful login as novel. Novelty alone does not prove compromise.",
                     "high", [event_id])
        if kind in {"process", "process_start", "process-start"}:
            process_events.append(event)
            suspicious_process = any(token in process for token in ("powershell", "wscript", "cscript", "mshta", "rundll32"))
            office_parent = any(token in parent for token in ("outlook", "winword", "excel", "powerpnt", "winword.exe"))
            if suspicious_process and office_parent:
                emit("FL-END-001", "Script-capable process launched by an office application",
                     "A process and parent pair matches a high-signal heuristic; validate command line, signer and process telemetry.",
                     "high", [event_id])
        if kind in {"file", "file_create", "file-created", "filesystem"}:
            path = str(details.get("path", details.get("name", ""))).lower()
            if any(path.endswith(ext) for ext in (".zip", ".7z", ".rar", ".cab")) or "archive" in summary:
                emit("FL-END-002", "Possible archive staging",
                     "An archive-like file event was observed. Its contents and any transfer are not established.",
                     "medium", [event_id])

    # Correlate suspicious process events with later network activity on the same host.
    for process_event in process_events:
        pd = process_event.get("details") if isinstance(process_event.get("details"), dict) else {}
        process = str(pd.get("process", "")).lower()
        if not any(token in process for token in ("powershell", "wscript", "cscript", "mshta", "rundll32")):
            continue
        try:
            ptime = datetime.fromisoformat(str(process_event["timestamp"]).replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        host = str(pd.get("host", "")).lower()
        if not host:
            continue
        for network_event in ordered:
            if str(network_event.get("kind", "")).lower() not in {"connection", "network", "network_connection"}:
                continue
            nd = network_event.get("details") if isinstance(network_event.get("details"), dict) else {}
            if str(nd.get("host", "")).lower() != host:
                continue
            try:
                ntime = datetime.fromisoformat(str(network_event["timestamp"]).replace("Z", "+00:00"))
            except (KeyError, ValueError):
                continue
            elapsed = (ntime - ptime).total_seconds()
            if 0 <= elapsed <= 1800:
                emit("FL-COR-001", "Network activity followed a script-capable process",
                     "A connection occurred within 30 minutes of a suspicious process on the same host. This is temporal correlation, not proof of causation.",
                     "medium", [str(process_event.get("event_id", "")), str(network_event.get("event_id", ""))])
                break

    for account, account_events in login_by_account.items():
        if not account:
            continue
        session_events = [
            event for event in ordered
            if str(event.get("kind", "")).lower() in {"session", "session_created", "token_issued"}
            and str((event.get("details") or {}).get("account", "")).lower() == account
        ]
        if account_events and session_events:
            emit("FL-ID-002", "Identity login followed by session issuance",
                 "Login and session events reference the same account. Confirm session provenance and timing before response.",
                 "medium", [str(account_events[-1].get("event_id", "")), str(session_events[-1].get("event_id", ""))])
    return findings
