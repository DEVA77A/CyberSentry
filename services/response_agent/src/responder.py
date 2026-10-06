"""CyberSentry response-agent service entrypoint."""
import os
import sys
import time


def main():
    print("[response-agent] service starting...")
    max_auto = os.getenv("AUTO_CONTAIN_MAX_SEVERITY", "medium")
    print(f"[response-agent] ready. auto_contain_max_severity: {max_auto}")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
