#!/usr/bin/env python3
"""Local service wrapper for starting/stopping the SMR control tower."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "10_logs" / "control_tower"
CONTROL_TOWER_MARKER = "08_scripts/dashboard/run_control_tower.py"


def pid_path(port: int) -> Path:
    return LOG_DIR / f"control_tower_{port}.pid"


def log_path(port: int) -> Path:
    return LOG_DIR / f"control_tower_{port}.log"


def run_script_path() -> Path:
    return ROOT / "08_scripts" / "dashboard" / "run_control_tower.py"


def read_pid(path: Path):
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def process_exists(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def command_for_pid(pid: int | None) -> str:
    if not pid:
        return ""
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def is_control_tower_pid(pid: int | None) -> bool:
    return CONTROL_TOWER_MARKER in command_for_pid(pid)


def listener_pids(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []

    seen = set()
    values = []
    for line in result.stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            pid = int(text)
        except ValueError:
            continue
        if pid in seen:
            continue
        seen.add(pid)
        values.append(pid)
    return values


def control_tower_listener_pid(port: int) -> int | None:
    for pid in listener_pids(port):
        if is_control_tower_pid(pid):
            return pid
    return None


def adopt_running_listener(pid_file: Path, port: int) -> int | None:
    pid = control_tower_listener_pid(port)
    if not pid:
        return None
    pid_file.write_text(f"{pid}\n", encoding="utf-8")
    return pid


def wait_until_listening(host: str, port: int, timeout_seconds: float = 8.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.2)
    return False


def start_service(host: str, port: int, refresh_seconds: int):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    pid_file = pid_path(port)
    existing_pid = read_pid(pid_file)
    if process_exists(existing_pid) and is_control_tower_pid(existing_pid) and is_port_open(host, port):
        print(f"control tower already running: pid={existing_pid} url=http://{host}:{port}")
        return 0

    adopted_pid = adopt_running_listener(pid_file, port)
    if adopted_pid and is_port_open(host, port):
        print(f"control tower already running: pid={adopted_pid} url=http://{host}:{port}")
        return 0

    if is_port_open(host, port):
        port_pid = listener_pids(port)
        foreign_pid = port_pid[0] if port_pid else None
        foreign_command = command_for_pid(foreign_pid)
        print(f"port {port} is already in use by pid={foreign_pid or '-'}", file=sys.stderr)
        if foreign_command:
            print(f"command={foreign_command}", file=sys.stderr)
        return 1

    log_file = log_path(port)
    with log_file.open("ab") as handle:
        process = subprocess.Popen(
            [
                sys.executable,
                str(run_script_path()),
                "--host",
                host,
                "--port",
                str(port),
                "--refresh-seconds",
                str(refresh_seconds),
            ],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
            close_fds=True,
        )

    pid_file.write_text(f"{process.pid}\n", encoding="utf-8")
    if wait_until_listening(host, port) and process_exists(process.pid):
        print(f"control tower started: pid={process.pid} url=http://{host}:{port}")
        print(f"log_file={log_file}")
        return 0

    try:
        os.kill(process.pid, signal.SIGTERM)
    except OSError:
        pass
    if pid_file.exists():
        pid_file.unlink()
    print(f"control tower failed to start on http://{host}:{port}", file=sys.stderr)
    print(f"log_file={log_file}", file=sys.stderr)
    return 1


def stop_service(host: str, port: int):
    pid_file = pid_path(port)
    pid = read_pid(pid_file)
    if not (process_exists(pid) and is_control_tower_pid(pid)):
        pid = control_tower_listener_pid(port)
    if not process_exists(pid):
        if pid_file.exists():
            pid_file.unlink()
        print("control tower not running")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    deadline = time.time() + 5
    while time.time() < deadline:
        if not process_exists(pid):
            break
        time.sleep(0.2)
    if process_exists(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    if pid_file.exists():
        pid_file.unlink()
    print(f"control tower stopped: pid={pid}")
    if is_port_open(host, port):
        print(f"warning: port {port} is still open after stop", file=sys.stderr)
    return 0


def status_service(host: str, port: int):
    pid_file = pid_path(port)
    pid = read_pid(pid_file)
    running = process_exists(pid) and is_control_tower_pid(pid)
    adopted = False
    if not running:
        adopted_pid = adopt_running_listener(pid_file, port)
        if adopted_pid:
            pid = adopted_pid
            running = True
            adopted = True
    listening = is_port_open(host, port)
    owner = "control_tower" if running else ("foreign" if listener_pids(port) else "none")
    print(
        f"control tower status: running={'yes' if running else 'no'} "
        f"listening={'yes' if listening else 'no'} "
        f"pid={pid or '-'} owner={owner} adopted={'yes' if adopted else 'no'} "
        f"url=http://{host}:{port}"
    )
    print(f"log_file={log_path(port)}")
    return 0 if running and listening else 1


def main():
    parser = argparse.ArgumentParser(description="Manage the local SMR control tower service")
    parser.add_argument("command", choices=["start", "stop", "restart", "status"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8877, type=int)
    parser.add_argument("--refresh-seconds", default=60, type=int)
    args = parser.parse_args()

    if args.command == "start":
        raise SystemExit(start_service(args.host, args.port, args.refresh_seconds))
    if args.command == "stop":
        raise SystemExit(stop_service(args.host, args.port))
    if args.command == "restart":
        stop_service(args.host, args.port)
        raise SystemExit(start_service(args.host, args.port, args.refresh_seconds))
    raise SystemExit(status_service(args.host, args.port))


if __name__ == "__main__":
    main()
