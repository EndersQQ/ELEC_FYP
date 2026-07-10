import os
import shutil
import subprocess
import sys
import time

Import("env")


def stop_port_readers(source, target, env):
    port = env.GetProjectOption("upload_port", "/dev/ttyUSB0")

    if os.path.exists(port) and shutil.which("fuser"):
        subprocess.run(["fuser", "-k", port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    if os.path.exists(port) and not os.access(port, os.R_OK | os.W_OK):
        print()
        print(f"Cannot access {port}.")
        print("Fix it once with:")
        print(f"  sudo usermod -a -G dialout {os.environ.get('USER', 'enders')}")
        print("Then log out and log back in, or reboot.")
        print()
        env.Exit(1)


env.AddPreAction("upload", stop_port_readers)


def start_ui_bridge(source, target, env):
    project_dir = env.subst("$PROJECT_DIR")
    port = env.GetProjectOption("upload_port", "/dev/ttyUSB0")
    pid_path = os.path.join(project_dir, ".ui-bridge.pid")
    log_path = os.path.join(project_dir, ".ui-bridge.log")
    bridge_path = os.path.join(project_dir, "web-ui", "bridge.py")
    web_ui_dir = os.path.join(project_dir, "web-ui")

    with open(log_path, "ab", buffering=0) as log:
        process = subprocess.Popen(
            [sys.executable, bridge_path, "--port", port, "--http-port", "8090"],
            cwd=web_ui_dir,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    with open(pid_path, "w", encoding="utf-8") as pid_file:
        pid_file.write(str(process.pid))

    print()
    print("FSR UI bridge restarted:")
    print("  http://127.0.0.1:8090")
    print()


env.AddPostAction("upload", start_ui_bridge)
