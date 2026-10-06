"""CyberSentry normalizer service entrypoint."""
import os
import sys
import time


def main():
    print("[normalizer] service starting...")
    topic_raw = os.getenv("TOPIC_RAW", "sec.raw")
    topic_normalized = os.getenv("TOPIC_NORMALIZED", "sec.normalized")
    print(f"[normalizer] listening on {topic_raw}, output to {topic_normalized}")
    # In M1, service stands ready
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
