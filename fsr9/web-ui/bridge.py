#!/usr/bin/env python3
import argparse
import glob
import os
import queue
import threading
import time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

import serial


clients = set()
clients_lock = threading.Lock()
latest_line = ""
active_serial = None
active_serial_lock = threading.Lock()


def find_port():
    ports = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
    return ports[0] if ports else None


def broadcast(line):
    global latest_line
    latest_line = line
    with clients_lock:
        dead_clients = []
        for client in clients:
            try:
                while not client.empty():
                    client.get_nowait()
                client.put_nowait(line)
            except queue.Full:
                dead_clients.append(client)
        for client in dead_clients:
            clients.discard(client)


def serial_worker(port_name, baud_rate):
    global active_serial
    while True:
        try:
            with serial.Serial(port_name, baud_rate, timeout=1) as port:
                with active_serial_lock:
                    active_serial = port
                try:
                    broadcast("STATUS,bridge_connected")
                    while True:
                        line = port.readline().decode("utf-8", errors="ignore").strip()
                        if line:
                            broadcast(line)
                finally:
                    with active_serial_lock:
                        active_serial = None
        except serial.SerialException as error:
            broadcast(f"STATUS,bridge_error,{error}")
            time.sleep(1)


class BridgeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            client = queue.Queue(maxsize=2)
            with clients_lock:
                clients.add(client)

            if latest_line:
                client.put(latest_line)

            try:
                while True:
                    line = client.get()
                    payload = f"data: {line}\n\n".encode("utf-8")
                    self.wfile.write(payload)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with clients_lock:
                    clients.discard(client)
            return

        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        commands = {
            "/calibrate": b"IDLE\n",
            "/calibrate-idle": b"IDLE\n",
            "/tare": b"IDLE\n",
            "/calibrate-max": b"MAX\n",
        }

        if path not in commands:
            self.send_error(404)
            return

        with active_serial_lock:
            port = active_serial

        if not port or not port.is_open:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"serial port is not open")
            return

        try:
            port.write(commands[path])
            port.flush()
            self.send_response(204)
            self.end_headers()
        except serial.SerialException as error:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(error).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="FSR 9 array browser UI serial bridge")
    parser.add_argument("--port", default=find_port(), help="Serial device, for example /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--http-port", type=int, default=8090)
    args = parser.parse_args()

    if not args.port:
        raise SystemExit("No serial port found. Plug in the ESP32-S3 and try again.")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    thread = threading.Thread(target=serial_worker, args=(args.port, args.baud), daemon=True)
    thread.start()

    server = ThreadingHTTPServer(("127.0.0.1", args.http_port), BridgeHandler)
    print(f"FSR UI: http://127.0.0.1:{args.http_port}")
    print(f"Serial: {args.port} at {args.baud} baud")
    server.serve_forever()


if __name__ == "__main__":
    main()
