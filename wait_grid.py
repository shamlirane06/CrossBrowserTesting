
import json
import time
import urllib.request
import urllib.error

STATUS_URL = "http://127.0.0.1:4444/status"
TIMEOUT_SECONDS = 180
start_time = time.time()

while time.time() - start_time < TIMEOUT_SECONDS:
    try:
        request = urllib.request.Request(
            STATUS_URL,
            headers={"Connection": "close"}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        value = data.get("value", {})
        nodes = value.get("nodes", [])

        browsers = {
            node.get("stereotype", {}).get("browserName")
            for node in nodes
            if node.get("availability") == "UP"
        }

        if value.get("ready") and {"chrome", "firefox"}.issubset(browsers):
            print(
                "Selenium Grid is ready: "
                "Chrome and Firefox are registered."
            )
            break

        print(
            f"Grid is not ready yet. "
            f"Registered browsers: {browsers}"
        )

    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(f"Waiting for Selenium Grid: {error}")

    time.sleep(3)

else:
    raise TimeoutError(
        "Selenium Grid did not become ready within 180 seconds."
    )
