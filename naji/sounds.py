# sounds.py — طرح‌های صدای هشدار (v6.0)
# --------------------------------------------------------------------
# اولویت ۳ بریف: به‌جای فقط صدای سیستمی، چند گزینه‌ی صدا + بی‌صدایی موقت.
# پیاده‌سازی با winsound (خودِ ویندوز، بدون هیچ وابستگی جدید) و پخش در
# رشته‌ی جدا تا هیچ‌وقت رابط کاربری برای بوق بلاک نشود.
import time

try:
    import winsound  # فقط ویندوز
except ImportError:  # توسعه/تست روی سیستم‌های دیگر — همه‌چیز بی‌صدا
    winsound = None

# کلیدهای طرح صدا — باید با storage._sanitize هم‌خوان باشد
SCHEMES = ("system", "gentle", "urgent", "silent")


def schemes_for_combo() -> list:
    """(کلید، کلید ترجمه) برای کامبوی تنظیمات — از i18n ترجمه می‌شود"""
    return [(k, f"sound.scheme_{k}") for k in SCHEMES]


def is_muted(settings: dict) -> bool:
    """بی‌صدایی موقت فعال است؟ (mute_until = epoch ثانیه)"""
    try:
        until = int(float(settings.get("mute_until", 0) or 0))
    except (TypeError, ValueError):
        return False
    return until > time.time()


def _beep(freq: int, ms: int):
    if winsound is not None:
        try:
            winsound.Beep(int(freq), int(ms))
        except Exception:
            pass


def _run_scheme(key: str):
    if winsound is None:
        return
    if key == "system":
        # صدای استاندارد ویندوز — همان چیزی که کاربر در سیستم‌ش تنظیم کرده
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
    elif key == "gentle":
        # دو نُت ملایم بالا رونده — «چای آماده‌ست، برق داره می‌ره»
        _beep(880, 160)
        time.sleep(0.06)
        _beep(1174, 220)
    elif key == "urgent":
        # سه پالس تکراری بالا — بدون چرت‌زدن بیدار می‌کند
        for _ in range(3):
            _beep(1318, 130)
            time.sleep(0.09)
    # silent: هیچ


def play(key: str, settings: dict = None, force: bool = False):
    """پخش طرح صدا در رشته‌ی جدا (UI بلاک نمی‌شود)؛
    مگر این‌که بی‌صدایی موقت فعال باشد یا طرح «silent» باشد.
    force=True (آزمایش صدا) از بی‌صدایی عبور می‌کند."""
    key = key if key in SCHEMES else "system"
    if key == "silent":
        return
    if not force and settings and is_muted(settings):
        return

    import threading
    t = threading.Thread(target=_run_scheme, args=(key,), daemon=True)
    t.start()
