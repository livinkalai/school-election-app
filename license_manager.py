import hashlib
import hmac
import importlib.util
import json
import os
import socket
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


class LicenseError(Exception):
    """Raised when runtime license validation fails."""


_RUNTIME_CONTEXT: Dict[str, Any] = {}
_LAST_STATE_WRITE_TS: float = 0.0
_CLOCK_SKEW_TOLERANCE = timedelta(minutes=5)
_STATE_FORMAT_VERSION = 1


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hmac_hex(secret: str, payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _parse_iso_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _safe_write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _split_secret_parts(secret: str) -> List[str]:
    if not secret:
        return []
    chunks = []
    idx = 0
    while idx < len(secret):
        chunks.append(secret[idx: idx + 8])
        idx += 8
    return chunks


def _license_embed_candidates(application_path: str, external_path: str) -> List[str]:
    return [
        os.path.join(application_path, "build", "license_embed.py"),
        os.path.join(external_path, "build", "license_embed.py"),
        os.path.join(external_path, "license_embed.py"),
    ]


def _load_embed_module(application_path: str, external_path: str) -> Optional[Any]:
    for path in _license_embed_candidates(application_path, external_path):
        if not os.path.isfile(path):
            continue
        spec = importlib.util.spec_from_file_location("runtime_license_embed", path)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return None


def _build_state_paths(external_path: str, license_id: str) -> Tuple[str, str]:
    local_state = os.path.join(external_path, ".election_app_license")
    local_appdata = os.environ.get("LOCALAPPDATA", external_path)
    state_name = f"{hashlib.sha256(license_id.encode('utf-8')).hexdigest()[:24]}.lic"
    appdata_state = os.path.join(local_appdata, "SchoolElectionApp", state_name)
    return local_state, appdata_state


def _state_signing_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state_version": int(state.get("state_version", _STATE_FORMAT_VERSION)),
        "license_id": state.get("license_id", ""),
        "machine_hint": state.get("machine_hint", ""),
        "first_run_utc": state.get("first_run_utc", ""),
        "last_seen_utc": state.get("last_seen_utc", ""),
    }


def _format_display_utc(iso_value: str) -> str:
    if not iso_value:
        return "—"
    try:
        dt = _parse_iso_utc(iso_value)
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return iso_value


def _format_time_remaining(expires_at: datetime, now: datetime) -> str:
    remaining = expires_at - now
    if remaining.total_seconds() <= 0:
        return "Expired"
    days = int(remaining.total_seconds() // 86400)
    hours = int((remaining.total_seconds() % 86400) // 3600)
    if days > 0:
        return f"{days} day(s), {hours} hour(s)"
    minutes = int((remaining.total_seconds() % 3600) // 60)
    if hours > 0:
        return f"{hours} hour(s), {minutes} minute(s)"
    return f"{minutes} minute(s)"


def _sign_state(state: Dict[str, Any], secret: str) -> str:
    payload = _canonical_json(_state_signing_payload(state))
    return _hmac_hex(secret, payload)


def _verify_state(state: Dict[str, Any], secret: str) -> bool:
    sig = str(state.get("state_sig", "")).strip()
    if not sig:
        return False
    expected = _sign_state(state, secret)
    return hmac.compare_digest(sig, expected)


def _validate_state_timestamps(state: Dict[str, Any], now: datetime) -> None:
    first_run = _parse_iso_utc(str(state.get("first_run_utc", "")))
    last_seen = _parse_iso_utc(str(state.get("last_seen_utc", "")))
    if first_run > (now + _CLOCK_SKEW_TOLERANCE):
        raise LicenseError("License state timestamp is in the future.")
    if last_seen > (now + _CLOCK_SKEW_TOLERANCE):
        raise LicenseError("License state timestamp is in the future.")
    if last_seen < (first_run - _CLOCK_SKEW_TOLERANCE):
        raise LicenseError("License state timestamps are inconsistent.")


def _read_state(paths: Tuple[str, str], secret: str, now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Read, verify, and reconcile license state from dual storage locations."""
    now = now or _utc_now()
    parsed: List[Tuple[str, Optional[Dict[str, Any]], bool]] = []
    for path in paths:
        state = _safe_read_json(path)
        if not state:
            parsed.append((path, None, False))
            continue
        if not _verify_state(state, secret):
            parsed.append((path, state, False))
            continue
        try:
            _validate_state_timestamps(state, now)
        except LicenseError:
            parsed.append((path, state, False))
            continue
        parsed.append((path, state, True))

    valid = [(path, state) for path, state, ok in parsed if ok and state is not None]
    invalid_present = any(state is not None and not ok for _, state, ok in parsed)

    if not valid:
        if invalid_present:
            raise LicenseError("License state signature invalid (possible tampering).")
        return None

    first_runs = {str(s.get("first_run_utc", "")).strip() for _, s in valid}
    if len(first_runs) > 1:
        raise LicenseError("License state mismatch between storage locations.")

    license_ids = {str(s.get("license_id", "")).strip() for _, s in valid}
    if len(license_ids) > 1:
        raise LicenseError("License state mismatch between storage locations.")

    valid.sort(key=lambda item: str(item[1].get("last_seen_utc", "")), reverse=True)
    canonical = dict(valid[0][1])
    for path in paths:
        state = _safe_read_json(path)
        if state and _verify_state(state, secret):
            try:
                _validate_state_timestamps(state, now)
                if (
                    str(state.get("first_run_utc", "")) == canonical.get("first_run_utc")
                    and str(state.get("license_id", "")) == canonical.get("license_id")
                ):
                    continue
            except LicenseError:
                pass
        try:
            _safe_write_json(path, canonical)
        except Exception:
            continue
    return canonical


def _write_state_both(paths: Tuple[str, str], state: Dict[str, Any]) -> None:
    for p in paths:
        try:
            _safe_write_json(p, state)
        except Exception:
            continue


def _build_dev_context(external_path: str) -> Dict[str, Any]:
    now = _utc_now()
    return {
        "enforced": False,
        "license_id": "dev-mode",
        "school_name": "Development Build",
        "valid_days": 36500,
        "issued_at": _to_iso_utc(now),
        "first_run_utc": _to_iso_utc(now),
        "expires_at": _to_iso_utc(now + timedelta(days=36500)),
        "developer_name": "EmpowerID",
        "developer_contact": "",
        "state_paths": _build_state_paths(external_path, "dev-mode"),
        "secret": "dev-only",
    }


def initialize_runtime_license(application_path: str, external_path: str, is_frozen: bool) -> Dict[str, Any]:
    """
    Initialize runtime license. In non-frozen mode, license enforcement is disabled.
    In frozen mode, requires a generated build/license_embed.py.
    """
    global _RUNTIME_CONTEXT
    if not is_frozen:
        _RUNTIME_CONTEXT = _build_dev_context(external_path)
        return dict(_RUNTIME_CONTEXT)

    embed = _load_embed_module(application_path, external_path)
    if embed is None:
        raise LicenseError("Missing embedded license. Rebuild using package-release.ps1.")

    payload = getattr(embed, "LICENSE_PAYLOAD", None)
    signature = str(getattr(embed, "LICENSE_SIGNATURE", "")).strip()
    secret_parts = getattr(embed, "LICENSE_SECRET_PARTS", None)

    if not isinstance(payload, dict) or not signature or not isinstance(secret_parts, list):
        raise LicenseError("Corrupt embedded license payload.")

    secret = "".join([str(p) for p in secret_parts])
    if not secret:
        raise LicenseError("Corrupt embedded license secret.")

    canonical_payload = _canonical_json(payload)
    expected_sig = _hmac_hex(secret, canonical_payload)
    if not hmac.compare_digest(signature, expected_sig):
        raise LicenseError("Embedded license signature mismatch.")

    license_id = str(payload.get("license_id", "")).strip()
    school_name = str(payload.get("school_name", "")).strip()
    valid_days = int(payload.get("valid_days", 0))
    issued_at = str(payload.get("issued_at", "")).strip()
    developer_name = str(payload.get("developer_name", "EmpowerID")).strip() or "EmpowerID"
    developer_contact = str(payload.get("developer_contact", "")).strip()
    if not license_id or not school_name or valid_days <= 0:
        raise LicenseError("Invalid embedded license values.")

    state_paths = _build_state_paths(external_path, license_id)
    machine_hint = socket.gethostname().strip()
    state = _read_state(state_paths, secret)
    now = _utc_now()

    if state is None:
        state = {
            "state_version": _STATE_FORMAT_VERSION,
            "license_id": license_id,
            "machine_hint": machine_hint,
            "first_run_utc": _to_iso_utc(now),
            "last_seen_utc": _to_iso_utc(now),
        }
        state["state_sig"] = _sign_state(state, secret)
        _write_state_both(state_paths, state)
    else:
        if str(state.get("license_id", "")).strip() != license_id:
            raise LicenseError("License state does not match embedded license.")

    first_run_utc = _parse_iso_utc(str(state.get("first_run_utc", "")))
    expires_at = first_run_utc + timedelta(days=valid_days)

    _RUNTIME_CONTEXT = {
        "enforced": True,
        "license_id": license_id,
        "school_name": school_name,
        "valid_days": valid_days,
        "issued_at": issued_at,
        "first_run_utc": _to_iso_utc(first_run_utc),
        "expires_at": _to_iso_utc(expires_at),
        "developer_name": developer_name,
        "developer_contact": developer_contact,
        "state_paths": state_paths,
        "secret": secret,
    }
    enforce_license_or_raise()
    return dict(_RUNTIME_CONTEXT)


def enforce_license_or_raise() -> Dict[str, Any]:
    """Validate runtime license state and update last_seen_utc safely."""
    global _LAST_STATE_WRITE_TS
    if not _RUNTIME_CONTEXT:
        raise LicenseError("License not initialized.")
    if not _RUNTIME_CONTEXT.get("enforced"):
        return get_license_status()

    secret = str(_RUNTIME_CONTEXT.get("secret", ""))
    state_paths = _RUNTIME_CONTEXT.get("state_paths")
    if not secret or not state_paths:
        raise LicenseError("Invalid runtime license context.")

    state = _read_state(state_paths, secret)
    if state is None:
        raise LicenseError("License state missing or tampered.")

    now = _utc_now()
    last_seen = _parse_iso_utc(str(state.get("last_seen_utc", "")))
    if now < (last_seen - timedelta(minutes=5)):
        raise LicenseError("System clock rollback detected.")

    first_run = _parse_iso_utc(str(state.get("first_run_utc", "")))
    expires_at = first_run + timedelta(days=int(_RUNTIME_CONTEXT.get("valid_days", 0)))
    if now >= expires_at:
        raise LicenseError(f"License expired on {_to_iso_utc(expires_at)}")

    now_ts = now.timestamp()
    if (now_ts - _LAST_STATE_WRITE_TS) >= 60:
        state["last_seen_utc"] = _to_iso_utc(now)
        state["state_sig"] = _sign_state(state, secret)
        _write_state_both(state_paths, state)
        _LAST_STATE_WRITE_TS = now_ts

    _RUNTIME_CONTEXT["first_run_utc"] = _to_iso_utc(first_run)
    _RUNTIME_CONTEXT["expires_at"] = _to_iso_utc(expires_at)
    return get_license_status()


def get_license_status() -> Dict[str, Any]:
    now = _utc_now()
    expires = _parse_iso_utc(str(_RUNTIME_CONTEXT.get("expires_at", _to_iso_utc(now + timedelta(days=36500)))))
    first_run = str(_RUNTIME_CONTEXT.get("first_run_utc", ""))
    issued_at = str(_RUNTIME_CONTEXT.get("issued_at", ""))
    remaining = expires - now
    days_remaining = max(0, int(remaining.total_seconds() // 86400))
    return {
        "enforced": bool(_RUNTIME_CONTEXT.get("enforced")),
        "license_id": str(_RUNTIME_CONTEXT.get("license_id", "")),
        "school_name": str(_RUNTIME_CONTEXT.get("school_name", "")),
        "developer_name": str(_RUNTIME_CONTEXT.get("developer_name", "EmpowerID")),
        "developer_contact": str(_RUNTIME_CONTEXT.get("developer_contact", "")),
        "issued_at": issued_at,
        "first_run_utc": first_run,
        "expires_at": str(_RUNTIME_CONTEXT.get("expires_at", "")),
        "days_remaining": days_remaining,
        "first_run_display": _format_display_utc(first_run),
        "expires_display": _format_display_utc(str(_RUNTIME_CONTEXT.get("expires_at", ""))),
        "issued_at_display": _format_display_utc(issued_at),
        "time_remaining": _format_time_remaining(expires, now),
    }


def get_license_template_context() -> Dict[str, Any]:
    status = get_license_status()
    return {
        "license_enforced": status["enforced"],
        "license_id": status["license_id"],
        "licensed_school": status["school_name"],
        "license_first_run": status["first_run_utc"],
        "license_first_run_display": status["first_run_display"],
        "license_expires": status["expires_at"],
        "license_expires_display": status["expires_display"],
        "license_issued_at_display": status["issued_at_display"],
        "license_days_remaining": status["days_remaining"],
        "license_time_remaining": status["time_remaining"],
        "developer_name": status["developer_name"],
        "developer_contact": status["developer_contact"],
    }

