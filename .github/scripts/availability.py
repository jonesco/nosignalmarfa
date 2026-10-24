"""Write availability.json from the Airbnb calendar export.

Reads the private feed URL from AIRBNB_ICAL_URL and keeps only the blocked
date ranges: no reservation links, guest details or event text reach the repo.
Each range is [first night, checkout day], so the end date is bookable.
"""
import datetime
import json
import os
import re
import sys
import urllib.request

URL = os.environ["AIRBNB_ICAL_URL"]
OUT = "availability.json"

req = urllib.request.Request(URL, headers={"User-Agent": "nosignalmarfa.com availability"})
with urllib.request.urlopen(req, timeout=30) as resp:
    feed = resp.read().decode("utf-8")
if "BEGIN:VCALENDAR" not in feed:
    sys.exit("Not an iCalendar feed; leaving availability.json unchanged.")

today = datetime.date.today()
ranges = []
for event in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", feed, re.S):
    start = re.search(r"^DTSTART;VALUE=DATE:(\d{8})", event, re.M)
    end = re.search(r"^DTEND;VALUE=DATE:(\d{8})", event, re.M)
    if not (start and end):
        continue
    s = datetime.datetime.strptime(start.group(1), "%Y%m%d").date()
    e = datetime.datetime.strptime(end.group(1), "%Y%m%d").date()
    if e > today:
        ranges.append([s.isoformat(), e.isoformat()])

ranges.sort()
with open(OUT, "w") as f:
    rows = ",\n".join("  " + json.dumps(r) for r in ranges)
    f.write('{"blocked": [\n' + rows + "\n]}\n")
print(f"{len(ranges)} blocked ranges")
