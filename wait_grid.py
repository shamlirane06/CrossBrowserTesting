import json
import time
import urllib.request

STATUS_URL = "http://localhost:4444/status"
TIMEOUT_SECONDS = 120
start_time = time.time()

while time.time() - start_time < TIMEOUT_SECONDS:
    try:
        with urllib.request.urlopen(STATUS_URL, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        value = data.get("value", {})
        nodes = value.get("nodes", [])
        browsers = [
            node.get("stereotype", {}).get("browserName")
            for node in nodes
        ]

        if value.get("ready") and "chrome" in browsers and "firefox" in browsers:
            print("Selenium Grid is ready: Chrome and Firefox are registered.")
            break

    except Exception as error:
        print(f"Waiting for Selenium Grid: {error}")

    time.sleep(3)
else:
    raise TimeoutError("Selenium Grid did not become ready within 120 seconds.")