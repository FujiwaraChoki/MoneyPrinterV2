import json
import os
from datetime import datetime

from etsy.contracts import validate_run_status


RUN_SUBDIRECTORIES = ("artifacts", "product", "mockups", "listing")


def create_run_directory(base_dir: str, slug: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(base_dir, f"{timestamp}-{slug}")

    os.makedirs(run_dir, exist_ok=False)

    for subdirectory in RUN_SUBDIRECTORIES:
        os.makedirs(os.path.join(run_dir, subdirectory), exist_ok=True)

    return run_dir


def initialize_run_status(run_dir: str) -> str:
    status_path = os.path.join(run_dir, "artifacts", "run_status.json")
    write_json(
        status_path,
        {
            "run_id": os.path.basename(run_dir),
            "status": "in_progress",
            "current_stage": "",
            "last_successful_stage": "",
            "failure_message": "",
        },
    )
    return status_path


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def update_run_status(run_dir: str, **changes: str) -> dict:
    status_path = os.path.join(run_dir, "artifacts", "run_status.json")
    payload = read_json(status_path)
    payload.update(changes)
    validate_run_status(payload)
    write_json(status_path, payload)
    return payload


def discover_runs(base_dir: str) -> list[dict]:
    if not os.path.isdir(base_dir):
        return []

    discovered_runs = []

    for directory_name in sorted(os.listdir(base_dir), reverse=True):
        run_dir = os.path.join(base_dir, directory_name)
        if not os.path.isdir(run_dir):
            continue

        status_path = os.path.join(run_dir, "artifacts", "run_status.json")
        if not os.path.exists(status_path):
            continue

        try:
            payload = read_json(status_path)
            validate_run_status(payload)
        except (OSError, ValueError, json.JSONDecodeError):
            continue

        discovered_runs.append(
            {
                "run_id": payload["run_id"],
                "run_dir": run_dir,
                "status": payload["status"],
                "current_stage": payload["current_stage"],
                "last_successful_stage": payload["last_successful_stage"],
                "failure_message": payload["failure_message"],
            }
        )

    return discovered_runs