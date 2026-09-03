# wininfo.py — هماهنگی با ظاهر ویندوز: رنگ اکسنت + تم روشن/تیره‌ی سیستم
# ----------------------------------------------------------------------
# v4.4.5 — باگ ریشه‌ایِ سینک رنگ:
#   همه‌ی خواندن‌های قبلی با ریشه‌ی None انجام می‌شد؛ در حالی که None فقط
#   برای آرگومان computer_name در ConnectRegistry مجاز است و به‌عنوان ریشه‌ی
#   OpenKey استثنا می‌دهد → هر سه‌ی خواندن (اکسنت و دارک/لایت) همیشه شکست
#   می‌خورد، رنگ امضای بنفش می‌ماند و تم سیستم دیده نمی‌شد.
#   حالا: ریشه‌ی صریح HKEY_CURRENT_USER + فال‌بکِ QStyleHints.colorScheme
#   (Qt ۶٫۵+) برای دارک/لایت.
#
# منابع رجیستری (همه HKCU):
#   • Software\Microsoft\Windows\DWM\ColorizationColor  (0xAARRGGBB)
#   • Software\Microsoft\Windows\CurrentVersion\Explorer\Accent\AccentColorMenu
#     (COLORREF با آلفای FF → بایت‌ها BB GG RR)
#   • Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme
#     (1=روشن، 0=تیره)
import sys

_cached = {"accent": None, "dark": None}


def _read_reg(path, name):
    """خواندن DWORD از HKCU با ریشه‌ی صریح؛ هر خطایی → None (هرگز نپاشد)"""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as k:
            val, _type = winreg.QueryValueEx(k, name)
            return val
    except Exception:
        return None


def _dwm_colorization():
    """رنگ DWM — مقدار 0xAARRGGBB (در برخی نسخه‌ها با آلفای کمتر از FF)"""
    v = _read_reg(r"Software\Microsoft\Windows\DWM", "ColorizationColor")
    if v is None:
        return None
    try:
        v = int(v) & 0xFFFFFFFF
        r, g, b = (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF
        return (r, g, b)
    except Exception:
        return None


def _accent_menu_colorref():
    """AccentColorMenu — COLORREF بسته‌بندی‌شده؛ بایت کم‌ارزش = آبی... نه:
    قالب واقعی 0xFF|BB|GG|RR است؛ یعنی بایت کم‌ارزش = R و بایت بالا = B.
    نمونه‌ی شاهد: آبی پیش‌فرض #0078D7 در رجیستری 0xFFD77800 ذخیره می‌شود →
    r = 0x00, g = 0x78, b = 0xD7 ✓"""
    v = _read_reg(r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent",
                  "AccentColorMenu")
    if v is None:
        return None
    try:
        v = int(v) & 0xFFFFFF
        r, g, b = v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF
        return (r, g, b)
    except Exception:
        return None


def _accent_argb():
    """AccentColor (کلید جدیدتر) — DWORD با قالب 0xAARRGGBB"""
    v = _read_reg(r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent",
                  "AccentColor")
    if v is None:
        return None
    try:
        v = int(v) & 0xFFFFFFFF
        r, g, b = (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF
        return (r, g, b)
    except Exception:
        return None


def _sat_ok(rgb) -> bool:
    """آیا رنگ قابل قبول است تا به‌عنوان اکسنت اعمال شود؟
    v4.4 — تقریباً همه‌چیز پاس می‌شود: انتخابِ کاربر محترم است و هرچه
    در شخصی‌سازی ویندوز بگذارد باید عیناً روی برنامه بنشیند. فقط سیاهِ
    تقریباً-خالص رد می‌شود (مقدار صفرِ رجیستری/کلید نبودن) چون هیچ
    کنتراستی روی UI نمی‌گذارد."""
    if not rgb:
        return False
    return max(rgb) >= 32


def accent_rgb():
    """(r, g, b) رنگ اکسنت ویندوز؛ غیر ویندوز یا ناموفق → None"""
    cands = []
    a = _accent_menu_colorref()
    if _sat_ok(a):
        cands.append(a)
    n = _accent_argb()
    if _sat_ok(n):
        cands.append(n)
    d = _dwm_colorization()
    if _sat_ok(d):
        cands.append(d)
    if cands:
        return cands[0]
    return None


def _qt_color_scheme():
    """پاسخ خود کوانت از تم سیستم (Qt ۶٫۵+) → 'dark' | 'light' | None"""
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtCore import Qt
        if QGuiApplication.instance() is None:
            return None
        cs = QGuiApplication.styleHints().colorScheme()
        if cs == Qt.ColorScheme.Dark:
            return "dark"
        if cs == Qt.ColorScheme.Light:
            return "light"
    except Exception:
        pass
    return None


def apps_dark() -> bool:
    """آیا اپ‌های ویندوز روی تم تیره‌اند؟
    اول رجیستری (AppsUseLightTheme) و اگر نبود، فال‌بکِ خود کوانت.
    در محیط‌های بدون کوانت/رجیستری → False"""
    v = _read_reg(r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                  "AppsUseLightTheme")
    if v is not None:
        try:
            return int(v) == 0
        except Exception:
            pass
    return _qt_color_scheme() == "dark"


def snapshot() -> tuple:
    """(accent_rgb, apps_dark) — برای مقایسه و کشف تغییر"""
    return (accent_rgb(), apps_dark())


def changed_since_previous() -> bool:
    """کشف تغییر ظاهر ویندوز از آخرین فراخوانی؛ اولین فراخوانی همیشه False"""
    now = snapshot()
    if _cached["accent"] is None and _cached["dark"] is None:
        _cached["accent"], _cached["dark"] = now
        return False
    changed = (now != (_cached["accent"], _cached["dark"]))
    _cached["accent"], _cached["dark"] = now
    return changed
