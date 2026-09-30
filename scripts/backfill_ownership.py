#!/usr/bin/env python3
"""
Backfill ownership (Central PSU / State PSU / MNC Subsidiary / Private (Indian))
and HQ city+state for tickers in data/work/ownership_backfill_todo.csv, using
screener.in's company page (About/Key Points text) plus its shareholders API
for promoter names.

Writes data/work/ownership_backfill_result.csv incrementally (append-as-you-go)
so progress survives interruption. Rows already present in the output are
skipped on re-run.
"""
import csv
import html
import os
import re
import sys
import threading
import time
import urllib.parse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODO = os.path.join(ROOT, "data/work/ownership_backfill_todo.csv")
OUT = os.path.join(ROOT, "data/work/ownership_backfill_result.csv")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

NUM_THREADS = 8
DELAY = 0.4  # small delay between requests per thread

# ---- ownership heuristics -------------------------------------------------

CENTRAL_KEYWORDS = [
    "president of india", "ministry of", "government of india", "union of india",
]

INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal", "delhi", "jammu and kashmir", "puducherry", "chandigarh",
]
STATE_GOV_RE = re.compile(
    r"govern(?:ment|or)\s+of\s+(" + "|".join(INDIAN_STATES) + r")", re.I
)
# e.g. "Gujarat State Petroleum Corporation", "Maharashtra State Electricity..."
STATE_ENTITY_RE = re.compile(
    r"(" + "|".join(INDIAN_STATES) + r")\s+state\b", re.I
)

# Well-known central PSUs that themselves act as promoters of subsidiaries
KNOWN_CENTRAL_PSU_PARENTS = [
    "oil and natural gas corporation", "ongc", "coal india", "ntpc",
    "gail (india)", "gail india", "bharat heavy electricals",
    "steel authority of india", "indian oil corporation",
    "hindustan petroleum corporation", "bharat petroleum corporation",
    "national mineral development corporation", "nmdc",
    "power grid corporation of india", "rural electrification corporation",
    "recl", "nhpc", "container corporation of india", "concor",
    "life insurance corporation of india", "general insurance corporation",
    "bharat electronics", "hindustan aeronautics", "mazagon dock",
    "cochin shipyard", "garden reach shipbuilders", "rashtriya chemicals",
    "national fertilizers", "engineers india", "mmtc limited",
    "bharat sanchar nigam", "iti limited", "airports authority of india",
    "national aluminium company", "nalco", "neyveli lignite corporation",
    "sjvn limited", "thdc india", "numaligarh refinery",
    "chennai petroleum", "specified undertaking of unit trust",
    "punjab national bank", "state bank of india", "canara bank",
    "bank of baroda", "bank of india", "union bank of india",
    "indian bank", "central bank of india", "food corporation of india",
    "hindustan copper", "hindustan zinc",  # note: hz later privatised, kept as weak signal
]

FOREIGN_TOKENS = [
    "mauritius", "singapore pte", "pte. ltd", "pte ltd", " b.v.", " bv,",
    " b v ", " s.a.", "s.a,", " sarl", " gmbh", " s.p.a", " ag,", " n.v.",
    " nv,", " inc.", " inc,", " llc", "cayman", "luxembourg", "netherlands",
    "switzerland", " japan", " korea", "ireland", "hong kong", " plc",
    " sa,", "overseas", "international b.v", "cooperatief", "coöperatief",
    "france", "germany", "usa", "u.s.a", "sweden", "netherland",
]

FOREIGN_KNOWN_NAMES = [
    "nestle", "procter", "gillette", "honeywell", "siemens", "bosch",
    "bayer", "whirlpool", "samsung", "unilever", "philips", "schneider",
    "johnson & johnson", "colgate", "glaxo", "gsk", "pfizer", "novartis",
    "sanofi", "castrol", "cummins", "timken", "skf", "thermax", "abb ",
    "3m ", "akzo", "linde", "hyundai", "toyota", "honda motor", "yamaha",
    "suzuki", "daimler", "hail mauritius", "kellanova", "kellogg",
    "cargill", "cisco", "oracle", "microsoft", "ibm", "dow",
]

CENTRAL_RE = re.compile("|".join(re.escape(k) for k in CENTRAL_KEYWORDS), re.I)
CENTRAL_PARENT_RE = re.compile(
    "|".join(re.escape(k) for k in KNOWN_CENTRAL_PSU_PARENTS), re.I
)
FOREIGN_TOKEN_RE = re.compile(
    "|".join(re.escape(k) for k in FOREIGN_TOKENS), re.I
)
FOREIGN_NAME_RE = re.compile(
    "|".join(re.escape(k) for k in FOREIGN_KNOWN_NAMES), re.I
)

HQ_RE = re.compile(
    r"(?:headquarter(?:ed|s)?\s+(?:in|at)|based\s+(?:in|out of)|"
    r"registered\s+office\s+(?:is\s+)?(?:in|at))\s+"
    r"([A-Z][A-Za-z.\-]+(?:\s+[A-Z][A-Za-z.\-]+){0,3}"
    r"(?:,\s*[A-Z][A-Za-z.\-]+(?:\s+[A-Z][A-Za-z.\-]+){0,3})?)",
)

COMPANY_ID_RE = re.compile(r'data-company-id="(\d+)"')
ABOUT_RE = re.compile(
    r'class="sub show-more-box about"[^>]*>(.*?)</div>', re.S
)
KEYPOINTS_RE = re.compile(
    r'class="sub commentary always-show-more-box">(.*?)<div class="show-more-button"',
    re.S,
)
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(seg):
    return html.unescape(TAG_RE.sub(" ", seg)).strip()


def classify_ownership(promoter_name):
    if not promoter_name:
        return ""
    name = promoter_name.lower()
    if CENTRAL_RE.search(name):
        return "Central PSU"
    m = STATE_GOV_RE.search(name)
    if m:
        return "State PSU"
    if "governor of" in name:
        return "State PSU"
    if STATE_ENTITY_RE.search(name):
        return "State PSU"
    if CENTRAL_PARENT_RE.search(name):
        return "Central PSU"
    if FOREIGN_TOKEN_RE.search(name) or FOREIGN_NAME_RE.search(name):
        return "MNC Subsidiary"
    return ""


def guess_hq(text):
    m = HQ_RE.search(text)
    if m:
        val = m.group(1).strip().rstrip(".")
        # discard obviously bad / too-short matches
        if len(val) >= 3:
            return val
    return ""


def top_promoter(investors_json):
    best_name, best_pct = "", -1.0
    for name, periods in investors_json.items():
        if not isinstance(periods, dict):
            continue
        pct = None
        for k, v in periods.items():
            if k == "setAttributes":
                continue
            try:
                pct = float(v)
            except (TypeError, ValueError):
                continue
        if pct is not None and pct > best_pct:
            best_pct = pct
            best_name = name
    return best_name


def fetch_company(session, ticker):
    url = "https://www.screener.in/company/" + urllib.parse.quote(ticker, safe="") + "/"
    ownership, hq = "", ""
    for attempt in range(4):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 429:
                time.sleep(15 * (attempt + 1))
                continue
            if r.status_code != 200:
                return ownership, hq, f"http{r.status_code}"
            page = r.text
            break
        except requests.RequestException:
            time.sleep(3)
    else:
        return ownership, hq, "err_fetch"

    about_m = ABOUT_RE.search(page)
    kp_m = KEYPOINTS_RE.search(page)
    text = ""
    if about_m:
        text += clean_text(about_m.group(1)) + " "
    if kp_m:
        text += clean_text(kp_m.group(1))
    hq = guess_hq(text)

    cid_m = COMPANY_ID_RE.search(page)
    status = "ok"
    if cid_m:
        cid = cid_m.group(1)
        inv_url = f"https://www.screener.in/api/3/{cid}/investors/promoters/quarterly/"
        try:
            r2 = session.get(inv_url, timeout=20)
            if r2.status_code == 200 and r2.text.strip().startswith("{"):
                data = r2.json()
                if isinstance(data, dict) and data:
                    promoter = top_promoter(data)
                    ownership = classify_ownership(promoter)
        except Exception:
            status = "err_investors"
    else:
        status = "no_company_id"

    return ownership, hq, status


def main():
    with open(TODO, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    tickers = [r["ticker"] for r in rows if r.get("ticker")]

    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add(r["ticker"])
    else:
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["ticker", "ownership", "hq"])

    todo = [t for t in dict.fromkeys(tickers) if t not in done]
    print(f"total={len(tickers)} already_done={len(done)} todo={len(todo)}", flush=True)

    lock = threading.Lock()
    it = iter(todo)
    counter = {"n": 0}

    def worker():
        session = requests.Session()
        session.headers["User-Agent"] = UA
        while True:
            with lock:
                try:
                    ticker = next(it)
                except StopIteration:
                    return
            ownership, hq, status = fetch_company(session, ticker)
            with lock:
                with open(OUT, "a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([ticker, ownership, hq])
                counter["n"] += 1
                if counter["n"] % 25 == 0:
                    print(f"progress {counter['n']}/{len(todo)} last={ticker} status={status}", flush=True)
            time.sleep(DELAY)

    threads = [threading.Thread(target=worker) for _ in range(NUM_THREADS)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print("finished", flush=True)


if __name__ == "__main__":
    main()
