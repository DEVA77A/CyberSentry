"""CyberSentry correlation-agent service entrypoint."""
import os
import sys
import time


def main():
    print("[correlation-agent] service starting...")
    topic_in = os.getenv("TOPIC_DETECTIONS", "sec.detections")
    window = os.getenv("CORRELATION_WINDOW_MINUTES", "60")
    print(f"[correlation-agent] listening on {topic_in}, window: {window}m")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
