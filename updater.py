# updater.py — چک نسخه‌ی جدید + تغییرات هر نسخه (v6.0)
# --------------------------------------------------------------------
# اولویت ۲ بریف: وقتی نسخه‌ی جدید می‌آید خودش خبر بدهد و لیست تغییرات را
# نشان بدهد. منبع: GitHub Releases — بدون هیچ سرویس ابریِ جدید.
#
# ⚠️ برای فعال‌شدن آپدیتر، آدرس ریپو را اینجا ست کنید:
#    مثال: REPO = "my-user/bargh-monitor"
import re

import requests

VERSION = "6.1.0"          # با main_window.VERSION هم‌گام نگه داشته شود
REPO = "USERNAME/bargh-monitor"   # ← آدرس ریپو گیت‌هاب را اینجا قرار دهید
TIMEOUT = 10

_UA = {"User-Agent": "Naji-Updater/" + VERSION}


def releases_url() -> str:
    return f"https://github.com/{REPO}/releases/latest"


def parse_version(v: str) -> tuple:
    """'v6.2.1' یا '6.2.1-beta' → (6, 2, 1) — برای مقایسه‌ی عددی"""
    m = re.search(r"(\d+(?:\.\d+)*)", str(v or ""))
    if not m:
        return ()
    return tuple(int(x) for x in m.group(1).split("."))


def is_newer(remote: str, local: str) -> bool:
    """مقایسه‌ی عددی پاره‌های نسخه — '6.10.0' > '6.9.3'"""
    a, b = parse_version(remote), parse_version(local)
    if not a:
        return False
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a > b


def fetch_latest() -> dict:
    """آخرین ریلیز گیت‌هاب → {version, notes, url}
    هر خطای شبکه‌ای بالا می‌آید — فراخواننده (رشته‌ی جدا) هندل می‌کند"""
    r = requests.get(
        f"https://api.github.com/repos/{REPO}/releases/latest",
        headers=_UA, timeout=TIMEOUT,
    )
    r.raise_for_status()
    j = r.json()
    tag = str(j.get("tag_name") or "").strip()
    notes = str(j.get("body") or "").strip()
    # متن‌های خیلی بلند برای دیالوگ درون‌برنامه‌ای کوتاه می‌شود
    if len(notes) > 2200:
        notes = notes[:2200].rstrip() + "\n…"
    return {
        "version": tag.lstrip("vV") or tag,
        "raw_tag": tag,
        "notes": notes,
        "url": str(j.get("html_url") or releases_url()),
    }
