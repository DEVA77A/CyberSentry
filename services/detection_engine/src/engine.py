"""CyberSentry detection-engine service entrypoint."""
import os
import sys
import time


def main():
    print("[detection-engine] service starting...")
    topic_in = os.getenv("TOPIC_NORMALIZED", "sec.normalized")
    topic_out = os.getenv("TOPIC_DETECTIONS", "sec.detections")
    print(f"[detection-engine] listening on {topic_in}, emitting to {topic_out}")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
