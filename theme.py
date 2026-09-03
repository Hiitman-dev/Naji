# theme.py — دیزاین‌سیستم «ناجی / Aura Glass» (نسخه‌ی ۴)
# ------------------------------------------------------------------
# زبان بصری: «ماتِ آرام» (Calm Matte) — بر پایه‌ی راهنمای مایکروسافت برای
#   متریال Mica و اصول اِلیویشن تم تیره:
#   • بوم پس‌زمینه: لایه‌ی پایه‌ی اوپکِ ساکن — گرادیان مات + یک نورِ تک‌فام
#     در بالای بوم + وینیتِ نرم + دانه‌ی فیلم (BackdropCanvas در widgets.py).
#     هیچ لکه‌ی متحرکِ چندفامی وجود ندارد؛ حرکتی که دیده می‌شود فقط حرکتِ
#     کنترل‌هاست (قرص ناوبری، سوییچ، دکمه‌ها) نه پس‌زمینه.
#   • تفکیک بخش‌ها با «ارتفاع» می‌آید نه رنگ اشباع: در تیره سطوحِ خنثیِ
#     روشن‌تر از بوم و در روشن سطوحِ سفیدتر از بوم صدفی + هِیرلاین مرزی.
#   • هماهنگی با ویندوز: رنگ اکسنت و تم روشن/تیره‌ی سیستم خوانده و روی
#     پالت اعمال می‌شود (wininfo.py) — در نبود ویندوز، رنگ امضای ناجی.
#   • تایپوگرافی چهارصدایی (همه OFL و باندل‌شده):
#       Estedad        → تیترها، اعداد درشت، شمارش معکوس (هندسیِ مدرن)
#       Vazirmatn      → متن بدنه
#       Shabnam        → کپشن‌ها و متن‌های کمکی (گردتر و دوستانه‌تر)
#       Space Grotesk  → میکرو‌لیبل‌های لاتین حرف‌به‌حرف‌فاصله‌دار (امضای استودیویی)
#   • آیکون‌ها: SVGهای اختصاصی دودوتونه (icons.py) — بدون ایموجی.
import colorsys
import copy
import os
import sys

from PySide6.QtGui import QFont, QFontDatabase

import i18n  # برای قواعد قلم زبان‌آگاه (خلوص زبان v4.4.4)

# ---------- فونت‌ها ----------

FONT_DISPLAY = "Estedad"        # بعد از load_fonts() مطمئن می‌شود
FONT_BODY = "Vazirmatn"
FONT_SOFT = "Shabnam"
FONT_LATIN = "Space Grotesk"

# پس از تعمیر متادیتا (scripts/fix_fonts.py) هر وزن استعداد خانواده‌ی
# تک‌فایلی مخصوص خودش را دارد؛ تطبیق وزنِ مبهم ویندوز دیگر در کار نیست —
# هر نقشِ نمایشی دقیقاً همان یک فایل را می‌گیرد (v4.3)
ESTEDAD_BY_WEIGHT = {
    400: "Estedad",
    500: "Estedad Medium",
    600: "Estedad SemiBold",
    700: "Estedad Bold",
    800: "Estedad ExtraBold",
    900: "Estedad Black",
}


def display_family(weight: int = 800) -> str:
    """خانواده‌ی دقیقِ استعداد برای وزن خواسته‌شده؛ اگر فایل‌های استعداد
    باندل نباشند FONT_DISPLAY جایگزین امن شده و همان برگردانده می‌شود."""
    if FONT_DISPLAY != "Estedad":
        return FONT_DISPLAY
    return ESTEDAD_BY_WEIGHT.get(int(weight) or 800, "Estedad ExtraBold")

_FONT_FILES = (
    # Estedad — نمایشی
    "Estedad-Medium.ttf", "Estedad-SemiBold.ttf", "Estedad-Bold.ttf",
    "Estedad-ExtraBold.ttf", "Estedad-Black.ttf",
    # وزیرمتن — بدنه
    "Vazirmatn-Regular.ttf", "Vazirmatn-Medium.ttf",
    "Vazirmatn-SemiBold.ttf", "Vazirmatn-Bold.ttf",
    "Vazirmatn-ExtraBold.ttf", "Vazirmatn-Black.ttf",
    # شبنم — کمکی
    "Shabnam-Medium.ttf", "Shabnam-Bold.ttf",
    # Space Grotesk — میکرولیبل لاتین
    "SpaceGrotesk-Medium.ttf", "SpaceGrotesk-Bold.ttf",
)


def asset_dir() -> str:
    base = getattr(sys, "_MEIPASS", None)  # اجرا از exe تک‌فایلی PyInstaller
    root = base if base else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, "assets")


def load_fonts() -> str:
    """ثبت همه‌ی خانواده‌های باندل‌شده؛ هر خانواده در نبود فایل حذف می‌شود.
    v4.3: تشخیص با پیشوند نام — چون وزن‌های استعداد حالا خانواده‌های
    «Estedad Medium/…Black» هم دارند و نباید اشتباهی جایگزین‌شان کنیم."""
    global FONT_DISPLAY, FONT_SOFT, FONT_LATIN
    fdir = os.path.join(asset_dir(), "fonts")
    fams = set()
    try:
        if os.path.isdir(fdir):
            for name in _FONT_FILES:
                path = os.path.join(fdir, name)
                if not os.path.exists(path):
                    continue
                fid = QFontDatabase.addApplicationFont(path)
                fams |= set(QFontDatabase.applicationFontFamilies(fid))
    except Exception:
        pass

    def _has(prefix: str) -> bool:
        return any(fam == prefix or fam.startswith(prefix + " ") for fam in fams)

    if not _has("Estedad"):
        FONT_DISPLAY = FONT_BODY          # جایگزین امن
    if not _has("Shabnam"):
        FONT_SOFT = FONT_BODY
    if not _has("Space Grotesk"):
        FONT_LATIN = FONT_BODY
    return FONT_BODY


def app_font(size: float = 10, weight=None, family: str = None) -> QFont:
    f = QFont(family or FONT_BODY)
    f.setPointSizeF(size)
    if weight is not None:
        f.setWeight(weight)
    # v4.3: رندر نرم — فونت‌های فارسی باندل‌شده hinting ندارند؛ hinting کامل
    # گوتی روی ویندوز ساق‌ها را ناهمگون تیز می‌کند (یک کلمه پُر، یکی نازک
    # و لبه‌های پیکسلی). NoHinting خطوط را آزاد مقیاس می‌دهد و صاف رندر می‌شود.
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return f


# ---------- ابزار رنگ ----------

def _tint(rgb: str, alpha: int) -> str:
    return f"rgba({rgb},{alpha})"


def _hex_of(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _shift_hue(rgb, dh: float, sv: float = 1.0, vv: float = 1.0):
    """جابه‌جایی فام رنگ در فضای HSV — برای ساخت خانواده‌ی گرادیانی اکسنت"""
    r, g, b = [v / 255.0 for v in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + dh / 360.0) % 1.0
    s = max(0.0, min(1.0, s * sv))
    v = max(0.0, min(1.0, v * vv))
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return (int(r2 * 255), int(g2 * 255), int(b2 * 255))


# چیپ‌های آیکونی — (پرش نرم دودوتونه، خط اصلی)
CHIPS = {
    "indigo": {"bg": _tint("123,92,255", 28),  "fg": "#6d50f0"},
    "rose":   {"bg": _tint("244,89,108", 30),  "fg": "#e8455c"},
    "amber":  {"bg": _tint("235,150,50", 34),  "fg": "#d8820a"},
    "sky":    {"bg": _tint("56,152,236", 30),  "fg": "#2b7fca"},
    "teal":   {"bg": _tint("32,190,166", 30),  "fg": "#0f9b85"},
    "violet": {"bg": _tint("150,110,250", 30), "fg": "#7c4df0"},
}

CHIPS_DARK = {
    "indigo": {"bg": _tint("176,148,255", 40), "fg": "#bfa4ff"},
    "rose":   {"bg": _tint("255,107,125", 44), "fg": "#ff8fa0"},
    "amber":  {"bg": _tint("242,176,74", 46),  "fg": "#f8c476"},
    "sky":    {"bg": _tint("86,164,235", 46),  "fg": "#82b8f5"},
    "teal":   {"bg": _tint("56,214,187", 42),  "fg": "#5fdcc4"},
    "violet": {"bg": _tint("170,132,255", 44), "fg": "#b795ff"},
}

# نورِ پس‌زمینه — تک‌لکه‌ای و ساکن: (رنگ، آلفا، اندازه‌ی نسبی، x, y)
# v4.8 — «ماتِ آرام»: به‌جای شش لکه‌ی متحرکِ چندفام (حس RGB/چیپ)، فقط یک
#   نورِ ساکن در بالای بوم — آنالوگِ تینتِ مایکا. در تیره فامِ اکسنت با
#   آلفای خیلی کم، در روشن نورِ خنثیِ استودیویی؛ هرگز اشباع و هرگز متحرک.
# v5.0 — فامِ پیش‌فرض تیره به بنفشِ امضای ناجی (#7B5CFF) عوض شد.
AURORA_LIGHT = [
    ("255,252,244", 120, 1.30, 0.50, -0.20),
]
AURORA_DARK = [
    ("123,92,255", 22, 1.35, 0.50, -0.18),
]

PALETTES = {
    "light": {
        # v4.8 — صدفِ عمیق‌تر + کاغذِ سفیدتر: بوم گرم و کمی تیره‌تر از قبل
        # تا کارت‌های سفیدِ اوپک «بشینند» و فید نشوند (راهنمای متریال:
        # تفکیک سطح با روشنایی، نه رنگ اشباع)
        "bg_top": "#f3eee6",
        "bg_bottom": "#e9e1d4",
        "vignette": "188,174,152",
        # سطوح — سفیدِ کاغذیِ تقریباً اوپک
        "glass": "rgba(255,255,255,0.88)",
        "glass_strong": "rgba(255,255,255,0.97)",
        "glass_soft": "rgba(255,255,255,0.52)",
        "glass_border": "rgba(255,255,255,0.95)",
        "glass_edge": "rgba(114,100,82,0.16)",
        "sheen": "rgba(255,255,255,0.28)",
        "input_glass": "rgba(255,255,255,0.92)",
        "input_border": "rgba(114,100,82,0.20)",
        # متن
        "text": "#332e2b",
        "text2": "#6f6a66",
        "text3": "#a7a19c",
        # اکسنت — v5.0: بنفشِ امضای ناجی هم‌خانواده‌ی تم تیره
        "accent": "#6d50f0",
        "accent_hover": "#5f44e4",
        "accent_pressed": "#5238ce",
        "on_accent": "#ffffff",
        "accent_tint": _tint("109,80,240", 24),
        "grad1": "#8a6bf5",
        "grad2": "#7b5cff",
        "grad3": "#5a3ed6",
        "accent2": "#22b8a6",
        "accent2_tint": _tint("34,184,166", 26),
        # وضعیت
        "ok": "#0f9d6c",
        "ok_tint": _tint("20,157,112", 26),
        "warn": "#c67c04",
        "warn_tint": _tint("232,152,28", 30),
        "danger": "#e8455c",
        "danger_hover": "#dc3650",
        "danger_pressed": "#c22a43",
        "danger_tint": _tint("244,89,108", 26),
        "hero_text": "#ffffff",
        "hero_sub": "rgba(255,255,255,0.80)",
        # v6.0 — قاب نمایشِ شمارش معکوس روی هیرو: فرورفته، تیره و کاملاً
        # جدا از پس‌زمینه تا شمارش «بشیند» و هیچ‌وقت در گرادیان فید نشود
        "hero_disp": "rgba(24,14,66,0.50)",
        "hero_disp_edge": "rgba(255,255,255,0.30)",
        # سطوح سرِپا (پاپ‌آپ/تولتیپ) — توپر تا گوشه‌ی سیاهِ پنجره‌ی سرِپا نسازد
        "popup_bg": "#fffdfa",
        # اسکرول‌بار — دسته‌ی نیمه‌شفاف ظریف (قبلاً خاکستریِ توپرِ تمام‌قد بود
        # و مثل یک خط تیره‌ی عجیب کنار صفحه دیده می‌شد)
        "scroll": "rgba(111,105,121,0.30)",
        "scroll_hover": "rgba(124,98,245,0.55)",
        # دیسک داخلی حلقه‌ی هشدار — بستر متن شمارش معکوس
        "ring_fill": "rgba(255,255,255,0.55)",
        # سایه — گرمِ صدفی، نه سرمه‌ای
        "shadow": "166,155,138",
        "glow": "109,80,240",
    },
    "dark": {
        # v5.0 — «بنفشِ نیمه‌شب» بریفتِ پریمیوم کاربر: بوم #0D0F14 عمیق با
        # ته‌مایه‌ی آبی، اکسنت بنفش #7B5CFF، سطوح اکریلیکِ اِلیویت — شیشه
        # واقعی (بوم از پشت کارت کمی می‌گذرد) با خواناییِ حفظ‌شده
        "bg_top": "#0d0f14",
        "bg_bottom": "#090b0f",
        "vignette": "0,0,0",
        "glass": "rgba(26,29,41,0.72)",
        "glass_strong": "rgba(33,37,52,0.88)",
        "glass_soft": "rgba(255,255,255,0.05)",
        "glass_border": "rgba(255,255,255,0.10)",
        "glass_edge": "rgba(0,0,0,0.50)",
        "sheen": "rgba(255,255,255,0.05)",
        "input_glass": "rgba(255,255,255,0.06)",
        "input_border": "rgba(255,255,255,0.12)",
        "text": "#eceef7",
        "text2": "#9aa0b8",
        "text3": "#5f6680",
        "accent": "#7b5cff",
        "accent_hover": "#8f75ff",
        "accent_pressed": "#6a4be0",
        "on_accent": "#ffffff",
        "accent_tint": _tint("123,92,255", 34),
        "grad1": "#8f6fff",
        "grad2": "#7b5cff",
        "grad3": "#4a35c2",
        "accent2": "#3ad4bc",
        "accent2_tint": _tint("58,212,188", 30),
        "ok": "#34d399",
        "ok_tint": _tint("52,211,153", 30),
        "warn": "#f5b851",
        "warn_tint": _tint("245,184,81", 32),
        "danger": "#ff6b7d",
        "danger_hover": "#ff5569",
        "danger_pressed": "#e63f53",
        "danger_tint": _tint("255,107,125", 32),
        "hero_text": "#ffffff",
        "hero_sub": "rgba(255,255,255,0.74)",
        # v6.0 — قاب نمایشِ شمارش معکوس روی هیرو (توضیح: نسخه‌ی روشن)
        "hero_disp": "rgba(16,9,46,0.48)",
        "hero_disp_edge": "rgba(255,255,255,0.30)",
        "popup_bg": "#1b1e29",
        "scroll": "rgba(255,255,255,0.16)",
        "scroll_hover": "rgba(160,140,255,0.55)",
        "ring_fill": "rgba(255,255,255,0.05)",
        "shadow": "0,0,0",
        "glow": "123,92,255",
    },
}

# نسخه‌ی دست‌نخورده برای ریست اکسنت
_PALETTES_DEFAULT = copy.deepcopy(PALETTES)

_current = "light"


def set_current(name: str):
    global _current
    _current = "dark" if name == "dark" else "light"


def current_name() -> str:
    return _current


def current_palette() -> dict:
    return PALETTES[_current]


# ---------- هماهنگی رنگ با ویندوز ----------

def _yiq(rgb) -> float:
    """روشنایی ادراکی (YIQ) — برای انتخاب رنگِ متنِ رویِ اکسنت"""
    r, g, b = rgb
    return (r * 299 + g * 587 + b * 114) / 1000.0


# متنِ تیره برای اکسنت‌های روشن (زرد، نارنجی روشن و مانند آن)
_ON_ACCENT_DARK = "#1f2430"


def apply_accent(rgb):
    """رنگ اکسنت ویندوز را روی هر دو پالت سوار می‌کند؛ None → رنگ امضای ناجی.
    v4.4 — پاسِ وفادار: همان رنگی که کاربر در شخصی‌سازی ویندوز انتخاب کرده
    عیناً روی برنامه می‌نشیند (آبی همان آبی، قرمز همان قرمز — بدون شست‌وشوی
    پاستلی). فقط رنگِ متنِ رویِ اکسنت (on_accent) بر اساس روشنایی ادراکی
    انتخاب می‌شود تا روی اکسنت‌های روشن مثل زرد ویندوز، متن سیاه و خوانا بماند.
    فامِ اکسنت به گرادیان هیرو، هاله‌ها، سوییچ‌ها و نورِ بوم در تم تیره هم می‌ریزد."""
    if rgb is None:
        PALETTES.clear()
        PALETTES.update(copy.deepcopy(_PALETTES_DEFAULT))
        AURORA_LIGHT[0] = ("255,252,244", 120, 1.30, 0.50, -0.20)
        AURORA_DARK[0] = ("123,92,255", 22, 1.35, 0.50, -0.18)
        _tint_chips(None)
        return False
    for name in ("light", "dark"):
        p = PALETTES[name]
        dark = name == "dark"
        acc = rgb
        if dark:
            # در تاریکی فقط اکسنت‌های خیلی تیره (سرمه‌ای و مانند آن) کمی
            # روشن می‌شوند تا روی شیشه‌ی تیره دیده شوند؛ بقیه عیناً پاس می‌شوند
            r, g, b = [x / 255 for x in acc]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            if v < 0.45:
                r2, g2, b2 = colorsys.hsv_to_rgb(h, min(s, 0.85), 0.65)
                acc = (int(round(r2 * 255)), int(round(g2 * 255)),
                       int(round(b2 * 255)))
            if v >= 0.90:
                # اکسنتِ خیلی روشن: هاور با کمی تیره‌شدن حس می‌شود
                acc_h = _shift_hue(acc, 0, 1.0, 0.94)
                acc_p = _shift_hue(acc, -5, 1.05, 0.88)
            else:
                acc_h = _shift_hue(acc, 0, 1.0, 1.08)
                acc_p = _shift_hue(acc, -5, 1.04, 0.90)
        else:
            # تم روشن: پاسِ خالص — رنگ ویندوز دست‌نخورده می‌ماند
            acc_h = _shift_hue(acc, 0, 1.0, 0.94)
            acc_p = _shift_hue(acc, -5, 1.05, 0.86)
        p["accent"] = _hex_of(acc)
        p["accent_hover"] = _hex_of(acc_h)
        p["accent_pressed"] = _hex_of(acc_p)
        p["on_accent"] = "#ffffff" if _yiq(acc) < 150 else _ON_ACCENT_DARK
        ar, ag, ab = acc
        p["accent_tint"] = _tint(f"{ar},{ag},{ab}", 40 if dark else 26)
        p["glow"] = f"{ar},{ag},{ab}"
        g1 = _shift_hue(acc, 14, 0.94, 0.62 if dark else 0.98)
        g2 = _shift_hue(acc, 30, 0.92 if dark else 1.0, 0.58 if dark else 0.97)
        g3 = _shift_hue(acc, -10, 1.02 if dark else 1.08, 0.40 if dark else 0.78)
        p["grad1"], p["grad2"], p["grad3"] = _hex_of(g1), _hex_of(g2), _hex_of(g3)
    # v4.8 — تنها در تیره، نورِ تک‌لکه‌ی بالای بوم فامِ اکسنت می‌گیرد
    # (تینتِ مایکا)؛ نورِ تم روشن خنثیِ استودیویی می‌ماند تا اکسنت‌های
    # اشباع مثل زردِ ویندوز روی بوم لکه نزنند
    ar, ag, ab = rgb
    AURORA_DARK[0] = (f"{ar},{ag},{ab}", 20, 1.35, 0.50, -0.18)
    _tint_chips(rgb)
    return True


def _tint_chips(rgb):
    """چیپ indigo (امضای آیکون‌ها) هم‌فام با اکسنت می‌شود؛ بقیه چیپ‌ها سرِ جای‌شان"""
    if rgb is None:
        CHIPS["indigo"] = {"bg": _tint("123,92,255", 28), "fg": "#6d50f0"}
        CHIPS_DARK["indigo"] = {"bg": _tint("176,148,255", 40), "fg": "#bfa4ff"}
        return
    # اکسنت روشن (زرد و مانند آن)؟ متنِ چیپ تیره می‌شود تا خوانا بماند
    fg_v = 0.45 if _yiq(rgb) >= 150 else 0.86
    light_fg = _hex_of(_shift_hue(rgb, 0, 1.0, fg_v))
    dark_fg = _hex_of(_shift_hue(rgb, 0, 0.55, 1.0))
    CHIPS["indigo"] = {"bg": _tint(f"{rgb[0]},{rgb[1]},{rgb[2]}", 30), "fg": light_fg}
    CHIPS_DARK["indigo"] = {
        "bg": _tint(f"{dark_fg[1:3]},{dark_fg[3:5]},{dark_fg[5:7]}", 46),
        "fg": _hex_of(_shift_hue(rgb, 0, 0.5, 1.05)),
    }


def aurora_spec() -> list:
    """مشخصات نورِ پس‌زمینه برای تم فعال — تک‌لکه و ساکن (v4.8)"""
    return AURORA_DARK if _current == "dark" else AURORA_LIGHT


def chips() -> dict:
    return CHIPS_DARK if _current == "dark" else CHIPS


# ---------- QSS ----------

def build_qss(p: dict = None, font: str = None) -> str:
    p = p or current_palette()
    f = font or FONT_BODY
    disp900 = display_family(900)
    disp800 = display_family(800)
    soft, latin = FONT_SOFT, FONT_LATIN
    # v4.4.4 — میکرولیبلِ ابرو زبان‌آگاه شد:
    #   فارسی → قلم فارسیِ دوستانه، بدون letter-spacing (فاصله‌ی حروف، اتصال
    #   حروف فارسی را می‌شکند و همان «فونت داغون»ی است که کاربر دید)
    #   انگلیسی → Space Grotesk با فاصله‌ی حرفی — امضای استودیویی
    if i18n.is_rtl():
        eyebrow_css = (
            f"QLabel#eyebrow {{\n"
            f"    font-family: \"{soft}\";\n"
            f"    color: {p['text3']};\n"
            f"    font-size: 11.5px;\n"
            f"    font-weight: 700;\n"
            f"}}"
        )
    else:
        eyebrow_css = (
            f"QLabel#eyebrow {{\n"
            f"    font-family: \"{latin}\";\n"
            f"    color: {p['text3']};\n"
            f"    font-size: 10px;\n"
            f"    font-weight: 600;\n"
            f"    letter-spacing: 3px;\n"
            f"}}"
        )
    return f"""
* {{
    font-family: "{f}";
    outline: none;
}}
QMainWindow, QDialog {{ background: transparent; }}
QWidget#central {{ background: transparent; }}
QLabel {{ color: {p['text']}; background: transparent; }}

/* ---------- تایپوگرافی — درشت و خوانا ---------- */
QLabel#h1 {{ font-family: "{disp900}"; font-size: 24px; font-weight: 900; }}
QLabel#h2 {{ font-family: "{disp800}"; font-size: 17.5px; font-weight: 800; }}
{eyebrow_css}
QLabel#muted {{ color: {p['text2']}; font-size: 14.5px; }}
QLabel#hint {{ color: {p['text3']}; font-size: 13.5px; }}
QLabel#body {{ color: {p['text2']}; font-size: 15px; }}
QLabel#fieldLabel {{ color: {p['text2']}; font-size: 14.5px; font-weight: 700; }}

/* ---------- کارت شیشه‌ای (رسم در paintEvent) ---------- */
QFrame#glass, QFrame#stat {{ background: transparent; border: none; }}
QFrame#hline {{ color: {p['glass_edge']}; max-height: 1px; border: none;
               background: {p['glass_edge']}; }}
QLabel#statCaption {{ color: {p['text2']}; font-size: 13.5px; font-weight: 600; }}
QLabel#statValue {{ font-family: "{disp800}"; color: {p['text']};
                   font-size: 20px; font-weight: 800; }}

/* ---------- نوار کناری ---------- */
QWidget#navRail {{ background: transparent; }}
QPushButton#navItem {{
    background: transparent;
    color: {p['text2']};
    border: none;
    border-radius: 14px;
    padding: 8px 6px 6px 6px;
    font-size: 12px;
    font-weight: 700;
}}
QPushButton#navItem:hover {{ background: {p['glass_soft']}; color: {p['text']}; }}
QPushButton#navItem:checked {{
    background: {p['glass_strong']};
    color: {p['accent']};
    font-weight: 800;
    border: 1px solid {p['glass_border']};
}}

/* ---------- چیپ‌ها ---------- */
QLabel#chip {{
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 12.5px;
    font-weight: 800;
}}
QLabel#chip[kind="today"] {{ color: {p['danger']}; background: {p['danger_tint']}; }}
QLabel#chip[kind="soon"]  {{ color: {p['warn']};   background: {p['warn_tint']}; }}
QLabel#chip[kind="later"] {{ color: {p['accent']}; background: {p['accent_tint']}; }}
QLabel#chip[kind="done"]  {{ color: {p['text2']};  background: {p['glass_edge']}; }}
QLabel#chip[kind="bill"]  {{ color: {p['text2']};  background: {p['glass_edge']}; }}
QFrame#legendDot {{ border-radius: 4px; }}
QFrame#legendDot[tone="violet"] {{ background: {p['grad2']}; }}
QFrame#legendDot[tone="teal"] {{ background: {p['accent2']}; }}
QFrame#legendDot[tone="amber"] {{ background: #e0982e; }}
QFrame#legendDot[tone="rose"] {{ background: {p['danger']}; }}
QFrame#legendDot[tone="indigo"] {{ background: {p['accent']}; }}
QLabel#timeRange {{ font-family: "{disp800}"; font-size: 16px; font-weight: 800; }}

/* ---------- دکمه‌ها ---------- */
QPushButton {{
    background: {p['glass_strong']};
    color: {p['text']};
    border: 1px solid {p['glass_border']};
    border-radius: 13px;
    padding: 9px 16px;
    font-weight: 700;
    font-size: 14.5px;
}}
QPushButton:hover {{ background: {p['glass']}; border-color: {p['accent']}; }}
QPushButton:pressed {{ background: {p['accent_tint']}; }}
QPushButton:disabled {{ color: {p['text3']}; background: {p['glass_soft']}; border-color: {p['glass_edge']}; }}
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['grad1']}, stop:0.55 {p['grad2']}, stop:1 {p['grad3']});
    color: {p['on_accent']};
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 14px;
    padding: 11px 18px;
    font-size: 15.5px;
    font-weight: 800;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['accent_hover']}, stop:1 {p['grad2']});
}}
QPushButton#primary:pressed {{ background: {p['accent_pressed']}; }}
QPushButton#primary:disabled {{ background: {p['glass_soft']}; border-color: {p['glass_edge']}; color: {p['text3']}; }}
QPushButton#danger {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['danger']}, stop:1 {p['danger_pressed']});
    color: #ffffff; border: 1px solid rgba(255,255,255,0.22); border-radius: 13px;
    font-size: 14px;
}}
QPushButton#danger:hover {{ background: {p['danger_hover']}; }}
QPushButton#danger:pressed {{ background: {p['danger_pressed']}; }}
QPushButton#ghost {{ background: transparent; border-color: transparent; color: {p['text2']}; }}
QPushButton#ghost:hover {{ background: {p['glass_soft']}; border-color: {p['glass_border']}; color: {p['text']}; }}
QPushButton#ghost:pressed {{ background: {p['glass_edge']}; }}

/* خروج از حساب — ابزارِ گوشه‌ی سربرگ: در حالت عادی نامحسوس است تا کلیکِ
   اشتباه نشود؛ فقط هاور، رنگِ خطر نشان می‌دهد (v4.7 — به گوشه رفت) */
QPushButton#signout {{
    background: transparent;
    color: {p['text3']};
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 7px 13px;
    font-size: 12.5px;
    font-weight: 700;
}}
QPushButton#signout:hover {{
    color: {p['danger']};
    background: {p['danger_tint']};
}}
QPushButton#signout:pressed {{ background: {p['glass_edge']}; }}

/* ---------- سوییچر قبض‌ها (v6.0) ---------- */
QPushButton#billTab {{
    background: {p['glass_soft']};
    color: {p['text2']};
    border: 1px solid {p['glass_border']};
    border-radius: 15px;
    padding: 8px 16px;
    font-size: 13.5px;
    font-weight: 700;
}}
QPushButton#billTab:hover {{
    color: {p['text']};
    border-color: {p['accent']} ;
}}
QPushButton#billTabOn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['grad1']}, stop:0.55 {p['grad2']}, stop:1 {p['grad3']});
    color: {p['on_accent']};
    border: 1px solid rgba(255,255,255,0.26);
    border-radius: 15px;
    padding: 8px 16px;
    font-size: 13.5px;
    font-weight: 800;
}}
QPushButton#billAdd {{
    background: {p['accent_tint']};
    color: {p['accent']};
    border: 1px dashed {p['accent']};
    border-radius: 15px;
    padding: 8px 14px;
    font-size: 14px;
    font-weight: 800;
}}
QPushButton#billAdd:hover {{ background: {p['accent']}; color: {p['on_accent']}; }}

/* ---------- بنر وضعیت سرویس (v6.0) ---------- */
QLabel#svcTitle {{ font-family: "{disp800}"; font-size: 15px; font-weight: 800; }}
QLabel#svcBody {{ color: {p['text2']}; font-size: 13px; }}

/* سگمنت — قاب شیشه‌ای رسم سفارشی است */
QWidget#segment {{ background: transparent; border: none; }}
QWidget#segment QFrame#segInd {{ background: transparent; border: none; }}
QWidget#segment QPushButton#seg {{
    background: transparent;
    color: {p['text2']};
    border: none;
    border-radius: 11px;
    padding: 8px 8px;
    font-weight: 700;
    font-size: 14px;
}}
QWidget#segment QPushButton#seg[active="true"] {{
    color: {p['accent']};
    font-weight: 800;
}}
QWidget#segment QPushButton#seg:hover:!active {{ color: {p['text']}; }}

/* ---------- ورودی‌های شیشه‌ای ---------- */
QLineEdit, QSpinBox, QComboBox {{
    background: {p['input_glass']};
    color: {p['text']};
    border: 1.5px solid {p['input_border']};
    border-radius: 12px;
    padding: 7px 12px;
    font-size: 15px;
    selection-background-color: {p['accent']};
    selection-color: {p['on_accent']};
    min-height: 18px;
}}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{ border-color: {p['text3']}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1.5px solid {p['accent']};
}}
QLineEdit:disabled {{ background: {p['glass_soft']}; color: {p['text3']}; }}
QComboBox::drop-down {{ border: none; width: 34px; }}
QComboBox::down-arrow {{ width: 0; height: 0; border: none; }}
/* پاپ‌آپ کامبو: پس‌زمینه‌ی توپر — شفافیت/گردی در پنجره‌های سرِپا گوشه‌ی سیاه می‌سازد */
QComboBox QAbstractItemView {{
    background: {p['popup_bg']};
    color: {p['text']};
    border: 1px solid {p['glass_border']};
    selection-background-color: {p['accent_tint']};
    selection-color: {p['text']};
    outline: 0;
    padding: 4px;
    font-size: 14.5px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: transparent; border: none; width: 16px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: transparent; }}
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 0; height: 0; border: none; background: none;
}}

/* ---------- لیست و بدنه‌ی اسکرول‌شونده ---------- */
QListWidget {{
    background: transparent;
    border: none;
    color: {p['text']};
    outline: 0;
    font-size: 14.5px;
}}
QListWidget::item {{ border: none; }}
QScrollArea#contentScroll, QScrollArea#contentScroll > QWidget > QWidget {{
    background: transparent; border: none;
}}

/* اسکرول‌بار — باریک، شیشه‌ای و ظریف؛ دسته فقط وقتی لازم است دیده می‌شود */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {p['scroll']};
    border-radius: 3px;
    min-height: 36px;
}}
QScrollBar::handle:vertical:hover {{ background: {p['scroll_hover']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{
    background: {p['scroll']}; border-radius: 3px; min-width: 36px;
}}
QScrollBar::handle:horizontal:hover {{ background: {p['scroll_hover']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}

/* ---------- متفرقه ---------- */
QToolTip {{
    background: {p['popup_bg']};
    color: {p['text']};
    border: 1px solid {p['glass_border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13.5px;
}}
QMessageBox {{ background: {p['bg_top']}; }}
QMessageBox QLabel {{ color: {p['text']}; background: transparent; font-size: 14.5px; }}
QMessageBox QPushButton {{ min-width: 84px; padding: 8px 14px; }}
QMenu {{
    background: {p['glass_strong']};
    color: {p['text']};
    border: 1px solid {p['glass_border']};
    border-radius: 12px;
    padding: 6px;
}}
QMenu::item {{ padding: 8px 22px 8px 12px; border-radius: 8px; font-size: 14px; }}
QMenu::item:selected {{ background: {p['accent_tint']}; color: {p['text']}; }}
QMenu::separator {{ height: 1px; background: {p['glass_edge']}; margin: 4px 8px; }}

/* ---------- پنجره‌ی هشدار ---------- */
QLabel#warnBanner {{
    font-family: "{disp900}";
    color: {p['danger']};
    font-size: 19px;
    font-weight: 900;
}}
QLabel#warnCount {{
    font-family: "{disp900}";
    font-size: 32px; font-weight: 900; color: {p['danger']};
}}
QLabel#warnHint {{ font-size: 13.5px; color: {p['text2']}; }}

/* ---------- ورود ---------- */
QLabel#stepChip {{
    font-family: "{disp800}";
    border-radius: 13px;
    font-size: 13.5px;
    font-weight: 800;
    padding: 0px;
}}
QLabel#stepChip[state="active"] {{ background: {p['accent']}; color: {p['on_accent']}; }}
QLabel#stepChip[state="done"]   {{ background: {p['accent_tint']}; color: {p['accent']}; }}
QLabel#stepChip[state="todo"]   {{ background: {p['glass_edge']}; color: {p['text3']}; }}
QLabel#stepLine {{ background: {p['glass_edge']}; max-height: 2px; border: none; }}
"""


def apply(app, name: str | None = None):
    """اعمال تم روی کل اپلیکیشن (روشن/تیره)"""
    if name:
        set_current(name)
    app.setStyleSheet(build_qss(current_palette(), FONT_BODY))
    # ویجت‌های سفارشی‌رنگ‌شده (شیشه، شفق، حلقه، هیرو) به QSS گوش نمی‌دهند؛
    # بازرسم صریحِ همه‌ی ویجت‌ها لازم است وگرنه رنگ‌های تم قبلی می‌مانند.
    try:
        from PySide6.QtWidgets import QApplication as _QA
        for w in _QA.allWidgets():
            fn = getattr(w, "repaint_theme", None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    pass
            w.update()
    except Exception:
        pass
