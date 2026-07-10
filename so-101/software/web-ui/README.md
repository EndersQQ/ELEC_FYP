# Browser UI

The browser monitor lives here.

- `bridge.py` reads ESP32 serial data and sends it to the browser with server-sent events.
- `index.html` displays the live 9-zone pressure grid and calibration controls.

Start it from the project root:

```bash
./scripts/start_ui.sh /dev/ttyUSB0
```

Then open:

```text
http://127.0.0.1:8090
```
