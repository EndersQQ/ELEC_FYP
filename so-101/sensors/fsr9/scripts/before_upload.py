import os
import shutil
import subprocess
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
    web_ui_script = os.path.join(project_dir, "scripts", "web_ui.sh")

    if not os.path.exists(web_ui_script):
        print()
        print(f"FSR UI helper not found: {web_ui_script}")
        print()
        return

    subprocess.run([web_ui_script, "restart", port], cwd=project_dir, check=False)


env.AddPostAction("upload", start_ui_bridge)
