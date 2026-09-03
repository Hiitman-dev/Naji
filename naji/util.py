# util.py — ابزارهای مشترک: اعداد، تاریخ شمسی، پارس خاموشی، برچسب روز دوزبانه
import re
from datetime import datetime

import jdatetime
import i18n

# ارقام فارسی و عربی → لاتین
PERSIAN_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
# لاتین → فارسی (برای نمایش)
LATIN_TO_PERSIAN = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_latin_digits(s) -> str:
    return str(s or "").translate(PERSIAN_MAP).strip()


def to_persian_digits(s) -> str:
    return str(s or "").translate(LATIN_TO_PERSIAN)


def num(s) -> str:
    """رقم‌سازی مطابق زبان فعال — در نسخه‌ی انگلیسی لاتین می‌ماند"""
    return i18n.num(s)


def day_label_key(raw) -> tuple:
    """کلید برچسب روز نسبی برای تاریخ شمسی: (کلید, پارامتر, فاصله)
    کلیدها: today | tomorrow | after | in_n | past | no_date"""
    d = parse_jalali_date(raw)
    if not d:
        return ("no_date", None, None)
    try:
        diff = (jdatetime.date(*d) - jdatetime.date.today()).days
    except Exception:
        return ("no_date", None, None)
    if diff < 0:
        return ("past", None, diff)
    if diff == 0:
        return ("today", None, diff)
    if diff == 1:
        return ("tomorrow", None, diff)
    if diff == 2:
        return ("after", None, diff)
    return ("in_n", diff, diff)


def jalali_day_label(raw):
    """برچسب روز نسبی بوم‌سازی‌شده: (متن, فاصله)"""
    key, param, diff = day_label_key(raw)
    if key == "in_n":
        return (i18n.t("day.in_n", n=num(param)), diff)
    return (i18n.t("day." + key), diff)


def jalali_today() -> str:
    d = jdatetime.date.today()
    return f"{d.year}/{d.month:02d}/{d.day:02d}"


def jalali_plus(days: int) -> str:
    d = jdatetime.date.today() + jdatetime.timedelta(days=days)
    return f"{d.year}/{d.month:02d}/{d.day:02d}"


def parse_jalali_date(raw):
    """'1404/06/07' یا '۱۴۰۴-۶-۷' → (1404, 6, 7) | None"""
    s = to_latin_digits(raw).replace("-", "/").replace(".", "/")
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        jdatetime.date(y, mo, d)
    except ValueError:
        return None
    return (y, mo, d)


def parse_time(raw):
    """'10:30' یا '۱۰:۳۰:۰۰' → (10, 30) | None"""
    s = to_latin_digits(raw).replace(".", ":").replace(" ", "")
    m = re.match(r"^(\d{1,2}):(\d{1,2})", s)
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    if hh > 23 or mm > 59:
        return None
    return (hh, mm)


# ---------- آدرس خاموشی — استخراجِ بردبار + ردپای دیباگ ----------
# گزارش کاربر: با داده‌ی واقعی، آدرس‌ها نوشته نمی‌شوند. از این‌جا که دسترسی
# به برق‌من ممکن نیست (IP خارج از ایران بسته است)، استخراج چند-کلیدی می‌کنیم
# و شکل واقعی رکورد را در APPDATA/Naji/debug.log ثبت می‌کنیم تا اگر باز هم
# آدرسی پیدا نشد، از لاگِ خودِ کاربر دقیق تشخیص داده شود.

_ADDR_EXACT = (
    "outage_address", "outageAddress", "blackout_address", "blackoutAddress",
    "address", "address_name", "addressName", "full_address", "fullAddress",
    "addr", "place", "place_name", "placeName", "outage_place", "outagePlace",
    "location", "outage_location", "area", "area_name", "areaName",
    "outage_area", "outageArea", "street", "neighborhood", "neighbourhood",
)
_ADDR_HINTS = ("address", "addr", "place", "location", "area",
               "street", "zone", "region", "mahal", "mantaghe", "khiaban")
_ADDR_WORDS = ("خیابان", "کوچه", "بلوار", "بولوار", "میدان", "پلاک",
               "شهرک", "جاده", "اتوبان", "بزرگراه", "فلکه", "چهارراه",
               "سه راه", "سه‌راه", "تقاطع", "محله", "منطقه")

_debug_seen = set()


def debug_note(msg: str):
    """ردپای تشخیصی در APPDATA/Naji/debug.log — تشخیص داده‌ی واقعی برق‌من"""
    try:
        import os
        from pathlib import Path
        base = os.environ.get("APPDATA") or str(Path.home())
        d = os.path.join(base, "Naji")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "debug.log")
        try:
            if os.path.getsize(p) > 262144:   # سقف ۲۵۶KB — از نو شروع کن
                os.remove(p)
        except OSError:
            pass
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")
    except Exception:
        pass


def _debug_once(tag: str, detail: str):
    if tag in _debug_seen:
        return
    _debug_seen.add(tag)
    debug_note(detail)


def outage_addr(o: dict) -> str:
    """آدرس خاموشی را از هر شکلی از رکورد برق‌من بیرون می‌کشد.
    اگر هیچ‌کجا نبود، رشته‌ی خالی برمی‌گرداند (تماس‌گیرنده placeholder
    می‌گذارد) و کلیدهای واقعی رکورد را برای دیباگ ثبت می‌کند."""
    if not isinstance(o, dict):
        return ""
    # رکورد اصلی + هر دیکشنری تودرتو (یک سطح)
    scopes = [o] + [v for v in o.values() if isinstance(v, dict)]
    # ۱) کلیدهای شناخته‌شده
    for scope in scopes:
        for k in _ADDR_EXACT:
            v = scope.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    # ۲) هر کلیدی که نامش بوی آدرس می‌دهد
    for scope in scopes:
        for k, v in scope.items():
            if isinstance(v, str) and v.strip() \
                    and any(h in str(k).lower() for h in _ADDR_HINTS):
                _debug_once(f"key:{k}", f"addr-fallback key={k!r}")
                return v.strip()
    # ۳) هر رشته‌ای که محتوایش آدرس است
    for scope in scopes:
        for k, v in scope.items():
            if isinstance(v, str) and len(v.strip()) >= 10 \
                    and any(w in v for w in _ADDR_WORDS):
                _debug_once(f"content:{k}", f"addr-content key={k!r}")
                return v.strip()
    # هیچ‌کجا نبود — شکل واقعی رکورد در لاگ ثبت شود
    try:
        sig = ",".join(sorted(str(k) for k in o.keys()))
        _debug_once("missing:" + sig, "addr-missing keys=" + sig)
    except Exception:
        pass
    return ""


def outage_key(o: dict) -> str:
    """کلید یکتا برای dedupe هشدارها — با برچسب قبض که چند-قبضی‌ها قاطی نشوند"""
    return "|".join(
        str(o.get(k, "?") or "?")
        for k in ("_bill", "outage_date", "outage_start_time",
                  "outage_stop_time", "outage_address")
    )


# ---------- لحظه‌ی خاموشی — بردبار چندکلیدی + پارس بی‌سخت‌گیری ----------
# باگ «هشدار ۵۰ دقیقه‌ای شلیک نشد» (v4.4.6): outage_datetime قبلاً فقط دو
# کلید دقیق outage_date/outage_start_time را می‌شناخت و پارسش سخت‌گیرانه
# بود (کل رشته باید دقیقاً «۱۴۰۴/۶/۱۱» می‌بود). اگر برق‌من شکل رکورد را
# کمی عوض می‌کرد (پسوند روز هفته، کلید متفاوت، «ساعت ۱۰:۳۰»)، پارس None
# می‌داد و چرخ هشدار رکورد را «بی‌صدا» رد می‌کرد — کاربر هم هیچ‌وقت
# نمی‌فهمید چرا اعلان نیامد. حالا: چند کلید + جست‌وجوی الگو در هر رشته +
# ثبت امضای رکورد در debug.log برای تشخیص از لاگ خود کاربر.

_DATE_EXACT = ("outage_date", "outageDate", "blackout_date", "date", "day",
               "start_date", "startDate", "outage_day")
_TIME_EXACT = ("outage_start_time", "outageStartTime", "blackout_start_time",
               "start_time", "startTime", "start", "from_time", "fromTime")
_DATE_HINT = "date"
_TIME_HINTS = ("start", "from", "begin")


def _collect_raw(o: dict, exact, hint_or_hints) -> list:
    """رشته‌های نامزد برای پارس: اول کلیدهای دقیق، بعد هر کلیدی که نامش
    بوی همان مفهوم می‌دهد (بدون Break زودهنگام — همه‌ی نامزدها را جمع کن
    تا اولینِ قابل‌پارس برنده شود)"""
    hints = hint_or_hints if isinstance(hint_or_hints, tuple) else (hint_or_hints,)
    raws, seen = [], set()
    for k in exact:
        v = o.get(k)
        if isinstance(v, str) and v.strip() and v not in seen:
            seen.add(v)
            raws.append(v)
    for k, v in o.items():
        if isinstance(v, str) and v.strip() and v not in seen:
            kl = str(k).lower()
            if any(h in kl for h in hints):
                seen.add(v)
                raws.append(v)
    return raws


_RE_JALALI = re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})")
_RE_TIME = re.compile(r"(\d{1,2}):(\d{2})")


def _find_jalali(raw) -> tuple:
    """اولین تاریخ شمسی داخل هر رشته‌ای — «۱۴۰۴/۶/۱۱ - سه‌شنبه» هم پارس می‌شود"""
    m = _RE_JALALI.search(to_latin_digits(raw))
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        jdatetime.date(y, mo, d)
    except ValueError:
        return None
    return (y, mo, d)


def _find_time(raw) -> tuple:
    """اولین ساعت داخل هر رشته‌ای — «ساعت ۱۰:۳۰:۰۰» و «۱۰:۳۰» هر دو"""
    m = _RE_TIME.search(to_latin_digits(raw))
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    if hh > 23 or mm > 59:
        return None
    return (hh, mm)


def outage_datetime(o: dict):
    """لحظه‌ی شروع خاموشی به‌صورت datetime محلی؛ None اگر قابل پارس نباشد.
    بردبار: چند کلید شناخته‌شده + هر کلید دیت/استارت‌نما + الگویابی
    بی‌سخت‌گیری داخل رشته؛ شکست پارس در debug.log ثبت می‌شود."""
    if not isinstance(o, dict):
        return None
    d = t = None
    for raw in _collect_raw(o, _DATE_EXACT, _DATE_HINT):
        d = _find_jalali(raw)
        if d:
            break
    for raw in _collect_raw(o, _TIME_EXACT, _TIME_HINTS):
        t = _find_time(raw)
        if t:
            break
    if not d or not t:
        try:
            sig = ",".join(sorted(str(k) for k in o.keys()))
            _debug_once("when-missing:" + sig,
                        f"when-parse-failed keys={sig} "
                        f"date={o.get('outage_date')!r} start={o.get('outage_start_time')!r}")
        except Exception:
            pass
        return None
    try:
        g = jdatetime.date(*d).togregorian()
    except Exception:
        return None
    return datetime(g.year, g.month, g.day, t[0], t[1])


def fmt_outage_line(o: dict, index: int) -> str:
    d = to_latin_digits(o.get("outage_date", "؟"))
    s = to_latin_digits(o.get("outage_start_time", "؟"))
    e = to_latin_digits(o.get("outage_stop_time", "؟"))
    addr = outage_addr(o) or "بدون آدرس"
    return f"{index}. {d} — از {s} تا {e}\n    محل: {addr}"


def outage_summary(o: dict) -> str:
    s = num(str(o.get("outage_start_time", "؟")))
    e = num(str(o.get("outage_stop_time", "؟")))
    d = to_latin_digits(o.get("outage_date", "؟"))
    return f"{d} {i18n.t('time.range', s=s, e=e)}"
