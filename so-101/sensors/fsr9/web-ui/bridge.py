#!/usr/bin/env python3
import argparse
import http.server
import os
import queue
import socketserver
import threading
import time
from urllib.parse import urlparse

try:
    import serial
except ImportError:
    serial = None


BAUD_RATE = 115200
CLIENT_QUEUE_SIZE = 300


class SerialBridge:
    def __init__(self, port):
        self.port = port
        self.serial = None
        self.clients = set()
        self.clients_lock = threading.Lock()
        self.write_lock = threading.Lock()

    def start(self):
        thread = threading.Thread(target=self._read_forever, daemon=True)
        thread.start()

    def subscribe(self):
        client_queue = queue.Queue(maxsize=CLIENT_QUEUE_SIZE)
        with self.clients_lock:
            self.clients.add(client_queue)
        client_queue.put("STATUS,bridge_connected")
        return client_queue

    def unsubscribe(self, client_queue):
        with self.clients_lock:
            self.clients.discard(client_queue)

    def send_command(self, command):
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("serial port is not connected")

        with self.write_lock:
            self.serial.write(f"{command}\n".encode("utf-8"))
            self.serial.flush()

    def publish(self, line):
        with self.clients_lock:
            clients = list(self.clients)

        for client_queue in clients:
            try:
                client_queue.put_nowait(line)
            except queue.Full:
                try:
                    client_queue.get_nowait()
                    client_queue.put_nowait(line)
                except queue.Empty:
                    pass

    def _read_forever(self):
        if serial is None:
            self.publish("STATUS,bridge_error,pyserial is not installed")
            return

        while True:
            try:
                with serial.Serial(self.port, BAUD_RATE, timeout=1) as serial_port:
                    self.serial = serial_port
                    self.publish("STATUS,bridge_connected")
                    while True:
                        raw_line = serial_port.readline()
                        if not raw_line:
                            continue
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if line:
                            self.publish(line)
            except Exception as error:
                self.serial = None
                self.publish(f"STATUS,bridge_error,{type(error).__name__}: {error}")
                time.sleep(2)


def make_handler(bridge, root_dir):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root_dir, **kwargs)

        def log_message(self, fmt, *args):
            print(f"{self.address_string()} - {fmt % args}")

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/events":
                self._serve_events()
                return
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

        def do_POST(self):
            path = urlparse(self.path).path
            if path != "/calibrate-idle":
                self.send_error(404, "Unknown command")
                return

            try:
                bridge.send_command("IDLE")
            except RuntimeError as error:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(str(error).encode("utf-8"))
                return

            self.send_response(204)
            self.end_headers()

        def _serve_events(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            client_queue = bridge.subscribe()
            try:
                while True:
                    line = client_queue.get()
                    payload = line.replace("\r", " ").replace("\n", " ")
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                bridge.unsubscribe(client_queue)

    return Handler


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(description="Serve the FSR web UI and bridge serial data.")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial device path")
    parser.add_argument("--http-port", type=int, default=8090, help="HTTP port for the UI")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    bridge = SerialBridge(args.port)
    bridge.start()

    server = ThreadingHTTPServer(
        ("127.0.0.1", args.http_port),
        make_handler(bridge, root_dir),
    )
    print(f"FSR web UI serving http://127.0.0.1:{args.http_port}", flush=True)
    print(f"Serial bridge reading {args.port} at {BAUD_RATE} baud", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
