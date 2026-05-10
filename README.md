# Amazon Price Monitoring Windows App

This Tkinter-based GUI application monitors prices on Amazon for computer parts and sends Discord webhook notifications when prices change.

## Setup Steps

1. **Install Python**: Ensure Python 3.7+ is installed on your system.

2. **Clone or Download the Project**: Place the project files in a directory.

3. **Create Virtual Environment** (optional but recommended):
   - Run `python -m venv .venv`
   - Activate: `.venv\Scripts\activate` (Windows)

4. **Install Dependencies**:
   - Run `pip install -r requirements.txt`

5. **Run the App**:
   - Execute `python main.py`
   - The GUI window will open.

## Optional Config File

- You can use `config.json` to prefill the app fields.
- The app loads `webhook_url`, `queries`, `max_results`, and `check_interval_minutes` from `config.json`.

## Using the App

1. Enter your Discord Webhook URL in the first field.
2. Enter Amazon search queries, one per line (for example: `pc parts`, `gpu`, `cpu`, `motherboard`).
3. Set the maximum number of products per query to monitor.
4. Set the check interval in minutes (default 60).
5. Click "Start Monitoring" to begin.
6. View logs in the bottom text area.
7. Click "Stop Monitoring" to halt.

## How It Works

- The app searches Amazon for your queries and collects product result URLs.
- It monitors the top search results from each query, instead of requiring manual product links.
- Prices are tracked in memory and updated during each check.
- On price changes, notifications are sent to Discord and logged in the app.
- Initial product prices are recorded and notified when monitoring starts.

## Packaging as Executable (Optional)

To create a standalone .exe for the app itself:

1. Install PyInstaller: `pip install pyinstaller`
2. Run: `pyinstaller --onefile --windowed main.py`
3. The .exe will be in the `dist` folder.

## Adding a Launcher / Updater

If you want an executable that can launch the latest `main.py` and optionally pull updates before starting:

1. Keep `main.py`, `launcher.py`, `version.txt`, and `update_config.json` in the same folder.
2. Build the launcher with:
   - `pyinstaller --onefile --name PriceMonitorLauncher launcher.py`
3. Put `PriceMonitorLauncher.exe` in the project folder alongside `main.py`.

The launcher will:

- read `update_config.json`
- optionally check a remote version file and download updates if configured
- run the latest `main.py` from disk

### Example `update_config.json`

```json
{
  "remote_version_url": "https://example.com/price-monitor/version.txt",
  "remote_update_url": "https://example.com/price-monitor/update.zip"
}
```

If you don’t use remote updates, the launcher still works as a stable entrypoint and always runs the current `main.py`.

## Troubleshooting

- If prices aren't detected, Amazon may have changed their HTML; update the selector in `main.py`.
- For blocking issues, the script uses a user-agent; consider proxies if needed.
- Check the log area for errors.

## Files

- `main.py`: Main GUI application
- `requirements.txt`: Dependencies