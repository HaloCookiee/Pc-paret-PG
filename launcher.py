import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE_DIR = Path(__file__).resolve().parent
MAIN_SCRIPT = BASE_DIR / "main.py"
VERSION_FILE = BASE_DIR / "version.txt"
CONFIG_FILE = BASE_DIR / "update_config.json"


def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_local_version():
    if not VERSION_FILE.exists():
        return "0.0.0"
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def download_text(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8")


def download_file(url, target_path):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response, open(target_path, "wb") as out_file:
        out_file.write(response.read())


def version_tuple(value):
    return tuple(int(part) for part in value.split(".") if part.isdigit())


def run_main_script():
    if not MAIN_SCRIPT.exists():
        print(f"Missing main script: {MAIN_SCRIPT}")
        return 1
    command = [sys.executable, str(MAIN_SCRIPT)]
    return subprocess.call(command)


def check_for_updates(config):
    version_url = config.get("remote_version_url")
    update_url = config.get("remote_update_url")
    if not version_url or not update_url:
        return False

    try:
        remote_version = download_text(version_url).strip()
        local_version = get_local_version()
        if version_tuple(remote_version) > version_tuple(local_version):
            print(f"Update available: {local_version} -> {remote_version}")
            zip_path = BASE_DIR / "update.zip"
            download_file(update_url, zip_path)
            import zipfile
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(BASE_DIR)
            zip_path.unlink(missing_ok=True)
            VERSION_FILE.write_text(remote_version, encoding="utf-8")
            print("Update completed.")
            return True
    except (URLError, HTTPError) as err:
        print(f"Update check failed: {err}")
    except Exception as err:
        print(f"Could not apply update: {err}")
    return False


def main():
    config = load_config()
    if check_for_updates(config):
        print("Restarting with updated code...")
    return run_main_script()


if __name__ == "__main__":
    sys.exit(main())
