import json, os, pathlib, urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup

NTFY_TOPIC = os.environ["NTFY_TOPIC"]
URL = "https://nrl.vau.edu.vn/events"
SELECTOR = 'a[href^="/events/"]'
STATE = pathlib.Path("state.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) event-watch/1.0"}


def fetch_events():
    req = urllib.request.Request(URL, headers=UA)
    html = urllib.request.urlopen(req, timeout=30).read()
    soup = BeautifulSoup(html, "html.parser")
    events = {}
    for a in soup.select(SELECTOR):
        link = urljoin(URL, a["href"])
        text = " | ".join(s.strip() for s in a.stripped_strings) or link
        events[link] = text[:300]
    return events


def notify(text, link):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=text.encode("utf-8"),
        headers={"Title": "New event", "Click": link, "Tags": "calendar"},
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    events = fetch_events()
    if not events:
        print("No events matched.")
        return
    first_run = not STATE.exists()
    seen = set() if first_run else set(json.loads(STATE.read_text()))
    if first_run:
        print(f"First run: saved {len(events)} existing events, no alerts sent.")
    else:
        for link, text in events.items():
            if link not in seen:
                notify(text, link)
                print("Notified:", text)
    STATE.write_text(json.dumps(sorted(seen | set(events))))


if __name__ == "__main__":
    main()
