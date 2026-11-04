"""Read-only, contract-mapped session evidence audit; never accesses hardware."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def read_json(path):
    def reject(value):
        raise ValueError("non-finite JSON value: " + value)
    def decimal(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON decimal: " + value)
        return result
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject,
                      parse_float=decimal, object_pairs_hook=unique)


def number(value, integer=False):
    # bool is an int subclass, but a flag is not a measurement or count.
    return (type(value) is int if integer else
            type(value) in (int, float) and math.isfinite(value))


def at(document, path):
    if not isinstance(path, list) or not path or any(type(k) is not str or not k for k in path):
        raise ValueError("field path must be a nonempty list of object keys")
    for key in path:
        if not isinstance(document, dict) or key not in document:
            raise ValueError("missing field: " + ".".join(path))
        document = document[key]
    return document


def audit(contract, session):
    """PASS means consistency under this contract, not whole-system acceptance."""
    out = dict(status="FAIL", evidence_level="static", board_execution=False,
               errors=[], metrics={}, conclusions={
                   "mechanical_arrival": "NOT_DETERMINED",
                   "unrecorded_pcm_continuity": "NOT_DETERMINED",
                   "recognition_accuracy": "NOT_DETERMINED"})
    errors, metrics = out["errors"], out["metrics"]

    def require(ok, message):
        if not ok:
            errors.append(message)

    try:
        if not isinstance(contract, dict) or type(contract.get("schema_version")) is not int or contract["schema_version"] != 1:
            raise ValueError("unsupported audit contract")
        required = {"schema_version", "success", "zero", "empty", "true", "counters", "duration"}
        allowed = required | {"tail", "recent_results", "statistics"}
        if not required <= set(contract) or set(contract) - allowed:
            raise ValueError("missing or unknown contract fields")
        rule = contract["success"]
        choices = rule["allowed"]
        if not isinstance(choices, list) or not choices or any(type(x) is not str for x in choices):
            raise ValueError("success.allowed must contain strings")
        value = at(session, rule["path"])
        require(type(value) is str and value in choices, "session did not finish with an allowed result")
        for group in ("zero", "empty", "true", "counters"):
            if not isinstance(contract[group], list):
                raise ValueError(group + " must be a list")
        for path in contract["zero"]:
            value = at(session, path)
            require(number(value, True) and value == 0, "nonzero or invalid counter: " + ".".join(path))
        for path in contract["empty"]:
            value = at(session, path)
            require(value is None or type(value) is list and not value, "nonempty error field: " + ".".join(path))
        for path in contract["true"]:
            require(at(session, path) is True, "stop confirmation is not true: " + ".".join(path))
        seconds = at(session, contract["duration"])
        require(number(seconds) and seconds > 0, "duration must be finite and positive")
        metrics["elapsed_seconds"] = seconds if number(seconds) else None
        seen = {"elapsed_seconds", "final_status", "recent_result_count", "session_statistics"}
        for item in contract["counters"]:
            name = item["name"]
            if type(name) is not str or not name or name in seen or name in metrics:
                raise ValueError("duplicate or invalid metric name")
            seen.add(name)
            start, end = at(session, item["start"]), at(session, item["end"])
            valid = number(start, True) and number(end, True) and 0 <= start <= end
            require(valid, "counter decreased or is invalid: " + name)
            metrics[name] = end - start if valid else None
        if "tail" in contract:
            tail = contract["tail"]
            state, mask = at(session, tail["path"]), tail["allowed_mask"]
            stops = tail["stop_values"]
            if not number(mask, True) or mask < 0 or not isinstance(stops, list) or not stops or any(type(x) is not str for x in stops):
                raise ValueError("invalid tail mask or stop_values")
            stop = at(session, tail["stop_path"])
            valid = number(state, True) and state >= 0 and state & ~mask == 0
            # A nonzero final status is permitted only for the declared stop.
            require(valid and (state == 0 or type(stop) is str and stop in stops),
                    "unexpected final fault or stop reason")
            metrics["final_status"] = state if number(state, True) else None
        if "recent_results" in contract:
            rows = at(session, contract["recent_results"])
            if not isinstance(rows, list):
                raise ValueError("recent_results must be a list")
            metrics["recent_result_count"] = len(rows)
            metrics["session_statistics"] = None
        if "statistics" in contract:
            stats = at(session, contract["statistics"])
            if not isinstance(stats, dict) or type(stats.get("enabled")) is not bool:
                raise ValueError("statistics.enabled must be boolean")
            metrics["session_statistics"] = None
            if stats["enabled"]:
                count, passes = stats["successful_calculations"], stats["threshold_passes"]
                total, avg, maximum = (stats[k] for k in
                                       ("total_compute_seconds", "average_compute_seconds", "max_compute_seconds"))
                valid = number(count, True) and count >= 0 and number(total) and total >= 0
                valid = valid and (passes is None or number(passes, True) and 0 <= passes <= count)
                if valid and count == 0:
                    valid = total == 0 and avg is None and maximum is None
                elif valid:
                    valid = (number(avg) and number(maximum) and 0 <= avg <= maximum <= total + 1e-9
                             and math.isclose(avg, total / count, rel_tol=1e-6, abs_tol=1e-9))
                require(valid, "inconsistent whole-session inference statistics")
                if valid:
                    metrics["session_statistics"] = {k: stats[k] for k in
                        ("successful_calculations", "threshold_passes", "total_compute_seconds",
                         "average_compute_seconds", "max_compute_seconds")}
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        errors.append("incomplete or malformed input: " + str(exc))
    out["status"] = "FAIL" if errors else "PASS"
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a new report")
    try:
        result = audit(read_json(args.contract), read_json(args.input))
    except (OSError, ValueError) as exc:
        result = dict(status="FAIL", evidence_level="static", board_execution=False, errors=[str(exc)])
    result["reproduce"] = "python -B scripts/audit_session.py --contract <contract.json> --input <session.json> --output <new-report.json>"
    result["input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest() if args.input.is_file() else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=True, allow_nan=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "board_execution": False}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

