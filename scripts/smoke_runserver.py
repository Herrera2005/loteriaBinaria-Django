#!/usr/bin/env python3
"""Inicia runserver temporalmente y comprueba que la landing responde.

Este smoke test usa el servidor de desarrollo únicamente durante la prueba.
No sustituye pruebas funcionales ni debe usarse como servidor de producción.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = int(os.environ.get("SMOKE_PORT", "8765"))
URL = f"http://{HOST}:{PORT}/"
EXPECTED_MARKERS = (
    "Lotería Binaria",
    "Simulación académica",
    "Octal",
    "Decimal",
    "Hexadecimal",
)


def port_is_available() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((HOST, PORT))
        except OSError:
            return False
    return True


def stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.terminate()
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def main() -> int:
    if not port_is_available():
        print(f"SMOKE RUNSERVER: puerto ocupado: {HOST}:{PORT}", file=sys.stderr)
        return 2

    command = [
        sys.executable,
        "manage.py",
        "runserver",
        f"{HOST}:{PORT}",
        "--noreload",
    ]
    process_kwargs: dict[str, object] = {
        "cwd": ROOT,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
    }
    if os.name != "nt":
        process_kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **process_kwargs)
    deadline = time.monotonic() + 25
    last_error = "sin respuesta"

    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                print(output, file=sys.stderr)
                print("SMOKE RUNSERVER: el servidor terminó antes de responder.", file=sys.stderr)
                return 1
            try:
                with urllib.request.urlopen(URL, timeout=2) as response:
                    charset = response.headers.get_content_charset() or "utf-8"
                    body = response.read().decode(charset, errors="replace")
                    if response.status != 200:
                        last_error = f"HTTP {response.status}"
                    else:
                        missing = [marker for marker in EXPECTED_MARKERS if marker not in body]
                        if missing:
                            last_error = "faltan marcadores: " + ", ".join(missing)
                        else:
                            print(f"SMOKE RUNSERVER: OK - {URL} respondió HTTP 200.")
                            return 0
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last_error = str(exc)
            time.sleep(0.4)

        print(f"SMOKE RUNSERVER: FALLÓ - {last_error}", file=sys.stderr)
        if process.stdout:
            output = process.stdout.read()
            if output:
                print(output, file=sys.stderr)
        return 1
    finally:
        stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
