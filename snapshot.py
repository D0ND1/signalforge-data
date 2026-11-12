"""Daily public-data snapshot (stdlib only). Writes dated JSON so the history exists even when the laptop and the server are off.

  data/recalls/YYYY-MM-DD.json   CPSC consumer-product recalls + openFDA food/drug/device enforcement reports (last 14 days)
  data/releases/YYYY-MM-DD.json  latest GitHub release of each repo in watch.json

Sources are official public APIs (checked 2026-11-11: CPSC saferproducts.gov RestWebServices and api.fda.gov both answered with no key).
We store the agencies' own fields and the link, never copied page text. Every file keeps `fetched_at` and its `source`.
Run:  python snapshot.py            (GITHUB_TOKEN from the environment raises GitHub's limit from 60 to 5,000 requests an hour)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "signalforge-data-snapshot/1.0 (+https://github.com/; contact: repo owner)"
DAYS = 14


def get(url: str, headers: dict[str, str] | None = None, tries: int = 3):
    last: Exception | None = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # openFDA answers 404 when a date window has no matches
            last = e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = e
        time.sleep(2 * (i + 1))
    print(f"WARN {url.split('?')[0]}: {last}", file=sys.stderr)
    return None


def recalls(now: datetime) -> dict:
    start = (now - timedelta(days=DAYS)).strftime("%Y-%m-%d")
    cpsc = get(f"https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallDateStart={start}") or []
    out: dict = {"fetched_at": now.isoformat(), "window_days": DAYS, "cpsc": {"source": "saferproducts.gov", "items": cpsc}}
    a, b = (now - timedelta(days=DAYS)).strftime("%Y%m%d"), now.strftime("%Y%m%d")
    for kind in ("food", "drug", "device"):
        q = urllib.parse.urlencode({"search": f"report_date:[{a} TO {b}]", "limit": 100}, safe=":[]")
        res = get(f"https://api.fda.gov/{kind}/enforcement.json?{q}") or {}
        out[f"fda_{kind}"] = {"source": "api.fda.gov", "items": res.get("results", [])}
    return out


def releases(now: datetime) -> dict:
    repos = json.loads((ROOT / "watch.json").read_text())["repos"]
    tok = os.environ.get("GITHUB_TOKEN")
    hdr = {"Authorization": f"Bearer {tok}"} if tok else {}
    items = {}
    for repo in repos:
        r = get(f"https://api.github.com/repos/{repo}/releases/latest", hdr)
        if r:
            items[repo] = {k: r.get(k) for k in ("tag_name", "name", "published_at", "html_url", "prerelease")}
    return {"fetched_at": now.isoformat(), "source": "api.github.com", "items": items}


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)  # atomic, like the main pipeline


def main() -> int:
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")
    rec, rel = recalls(now), releases(now)
    # never overwrite a good day with an empty one (an API outage must not erase history)
    if any(v.get("items") for k, v in rec.items() if isinstance(v, dict)):
        write(ROOT / "data" / "recalls" / f"{day}.json", rec)
    if rel["items"]:
        write(ROOT / "data" / "releases" / f"{day}.json", rel)
    write(ROOT / "data" / "latest.json", {"updated": now.isoformat(), "recalls": f"recalls/{day}.json", "releases": f"releases/{day}.json"})
    print(f"{day}: cpsc={len(rec['cpsc']['items'])} fda={sum(len(rec[k]['items']) for k in rec if k.startswith('fda_'))} releases={len(rel['items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
