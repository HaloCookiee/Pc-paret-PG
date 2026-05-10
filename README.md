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
