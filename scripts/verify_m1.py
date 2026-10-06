#!/usr/bin/env python
"""M1 acceptance checks for CyberSentry."""
from __future__ import annotations

import os
import subprocess
import sys
import urllib.request

import psycopg

OS_URL = os.getenv('OPENSEARCH_URL', 'http://localhost:9200')

EXPECTED_TABLES = {
    'assets', 'identities', 'attack_tactics', 'attack_techniques', 'detection_rules',
    'detections', 'incidents', 'incident_detections', 'incident_notes', 'playbooks',
    'response_actions', 'action_approvals', 'audit_log',
}

failures: list[str] = []


def get_db_connection(**kwargs):
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME', 'cybersentry')
    user = os.getenv('DB_USER', 'sentry')
    password = os.getenv('DB_PASS', 'sentry_dev_2026')

    candidates: list[str] = []
    env_host = os.getenv('DB_HOST')
    if env_host and env_host != 'postgres':
        candidates.append(env_host)
    candidates.extend(['localhost', '127.0.0.1', '172.23.68.112'])

    try:
        out = subprocess.check_output(
            ['wsl', '-d', 'docker-desktop', '-u', 'root', 'sh', '-c', 'ip addr show eth0'],
            text=True, timeout=2, stderr=subprocess.DEVNULL
        )
        for line in out.splitlines():
            if 'inet ' in line:
                ip = line.strip().split()[1].split('/')[0]
                if ip not in candidates:
                    candidates.append(ip)
    except Exception:
        pass

    seen = set()
    last_exc = None
    for host in candidates:
        if host in seen:
            continue
        seen.add(host)
        dsn = f"host={host} port={port} dbname={dbname} user={user} password={password}"
        try:
            return psycopg.connect(dsn, connect_timeout=3, **kwargs)
        except Exception as exc:
            last_exc = exc
    raise last_exc or psycopg.OperationalError("Unable to connect to database")


def check(label: str, ok: bool, detail: str = '') -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def main() -> int:
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'")
        found = {r[0] for r in cur.fetchall()}
        missing = EXPECTED_TABLES - found
        check('schema: all 13 tables present', not missing,
              f'missing {sorted(missing)}' if missing else '13/13')

        cur.execute('SELECT count(*) FROM attack_techniques')
        check('reference: ATT&CK techniques loaded', cur.fetchone()[0] >= 11)

        cur.execute('SELECT count(*) FROM detection_rules')
        check('catalogue: detection rules seeded', cur.fetchone()[0] >= 8)

        cur.execute('SELECT count(*) FROM detection_rules WHERE technique_id IS NULL')
        check('catalogue: every rule maps to an ATT&CK technique', cur.fetchone()[0] == 0)

        cur.execute('SELECT count(*) - count(DISTINCT dedup_key) FROM detections')
        check('integrity: no duplicate detections', cur.fetchone()[0] == 0)

        cur.execute('SELECT count(*) FROM assets')
        n = cur.fetchone()[0]
        check('estate: assets seeded', n >= 60, f'{n} assets')

        cur.execute("SELECT count(*) FROM playbooks WHERE requires_approval")
        check('safety: destructive playbooks require approval', cur.fetchone()[0] >= 2)

    try:
        req = urllib.request.Request(f'{OS_URL}/_index_template/sentry-events')
        with urllib.request.urlopen(req, timeout=8) as r:
            check('opensearch: index template applied', r.status == 200)
    except Exception as exc:
        check('opensearch: index template applied', False, str(exc))

    rc = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-q', '-p', 'no:cacheprovider'], capture_output=True, text=True)
    check('domain: unit tests', rc.returncode == 0, rc.stdout.strip() or rc.stderr.strip())

    print()
    if failures:
        print(f'M1 NOT COMPLETE — {len(failures)} check(s) failed')
        return 1
    print('M1 COMPLETE — safe to tag v0.1.0-M1')
    return 0


if __name__ == '__main__':
    sys.exit(main())
