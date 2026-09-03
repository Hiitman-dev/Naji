# test_v500.py — قفل‌های v5.0.0 «بنفشِ نیمه‌شب / پریمیوم 2.5D»
# -------------------------------------------------------------
# بریف کاربر: بوم #0D0F14، اکسنت #7B5CFF، آیکون‌های Lucide (خط ۱٫۷۵)،
# حس 2.5D، نوار پایین با دکمه‌ی درشت، چیپ موقعیت سربرگ، شمارش درشت هیرو
import ctypes
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("NAJI_NO_ANIM", "1")

fake_winreg = types.ModuleType("winreg")
fake_winreg.HKEY_CURRENT_USER = 0x80000001
fake_winreg.KEY_SET_VALUE = 2
fake_winreg.REG_SZ = 1


class _K:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def SetValueEx(self, *a):
        pass

    def DeleteValue(self, *a):
        pass

    def Close(self):
        pass


fake_winreg.OpenKey = lambda *a: _K()
sys.modules["winreg"] = fake_winreg
_wd = types.SimpleNamespace()
_wd.crypt32 = types.SimpleNamespace(CryptProtectData=lambda *a: 0, CryptUnprotectData=lambda *a: 0)
_wd.kernel32 = types.SimpleNamespace(LocalFree=lambda p: 0)
_wd.powrprof = types.SimpleNamespace(SetSuspendState=lambda *a: 1)
ctypes.windll = _wd
import subprocess  # noqa: E402
if not hasattr(subprocess, "CREATE_NO_WINDOW"):
    subprocess.CREATE_NO_WINDOW = 0
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="naji_test_v500_")

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
app.setStyle("Fusion")

import i18n  # noqa: E402
import icons  # noqa: E402
import storage  # noqa: E402
import theme  # noqa: E402
import widgets  # noqa: E402
import main_window  # noqa: E402
MW_VERSION_EXPECTED = main_window.VERSION
from main_window import MainWindow  # noqa: E402
from util import jalali_plus, jalali_today  # noqa: E402

theme.load_fonts()

_n = [0]


def check(name, cond):
    _n[0] += 1
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        _n.append(name)


# ---------- ۱) پالت امضا — بریف کاربر ----------
theme.apply_accent(None)
pd = theme.PALETTES["dark"]
pl = theme.PALETTES["light"]
check("بوم تیره = #0D0F14 (بریف)", pd["bg_top"] == "#0d0f14")
check("کف بوم تیره عمیق‌تر است", pd["bg_bottom"] == "#090b0f")
check("اکسنت تیره = #7B5CFF (بریف)", pd["accent"] == "#7b5cff")
check("هاور/فشار بنفش هم‌خانواده‌اند", pd["accent_hover"] == "#8f75ff"
      and pd["accent_pressed"] == "#6a4be0")
check("هاله‌ی اکسنت = بنفش ۱۲۳,۹۲,۲۵۵", pd["glow"] == "123,92,255")
check("گرادیان هیرو بنفشِ هم‌خانواده است", pd["grad2"] == "#7b5cff")
check("اکسنت لایت بنفشِ خوانا روی صدف است", pl["accent"] == "#6d50f0")
check("سبزِ وصلیم نرم است (بریف: soft green)", pd["ok"] == "#34d399")
check("نورِ بومِ تیره فامِ بنفشِ کم‌سو (تینتِ مایکا)",
      theme.AURORA_DARK[0][0] == "123,92,255" and theme.AURORA_DARK[0][1] <= 24)
check("نورِ بومِ روشن خنثی ماند",
      theme.AURORA_LIGHT[0][0] == "255,252,244")
check("چیپِ امضا (indigo) بنفش شد",
      theme.CHIPS["indigo"]["fg"] == "#6d50f0"
      and theme.CHIPS_DARK["indigo"]["fg"] == "#bfa4ff")

# ---------- ۲) آیکون‌های Lucide — وزن واحد، بدون لکه‌ی نرم ----------
check("همه‌ی گلیف‌های قدیمی سرِ جایشان‌اند",
      all(icons.has_icon(k) for k in (
          "bolt", "clock", "bell", "refresh", "calendar", "check", "moon",
          "moonstars", "faen", "snow", "power", "sun", "shield", "signal",
          "logout", "alert", "gauge", "timer", "help", "bill", "lock",
          "spark", "home", "orbit", "gear", "chevron", "users")))
check("گلیف تازه‌ی پین نقشه هست", icons.has_icon("mappin"))
soft_filled = [k for k, raw in icons._SVGS.items() if 'fill="@SOFT@"' in raw]
check("هیچ گلیفی لکه‌ی پرشِ نرم ندارد (منبع حس چیپ حذف شد)", not soft_filled)
import re as _re  # noqa: E402

bad_width = []
for k, raw in icons._SVGS.items():
    for m in _re.finditer(r'stroke-width="([\d.]+)"', raw):
        if m.group(1) != "1.75":
            bad_width.append((k, m.group(1)))
    strokes = len(_re.findall(r'stroke="', raw))
    widths = len(_re.findall(r'stroke-width="', raw))
    if strokes != widths:
        bad_width.append((k, "count-mismatch"))
check("وزن خطِ همه‌ی گلیف‌ها دقیقاً ۱٫۷۵ است", not bad_width)
ink_ok = True
for k in icons.ALL_ICONS:
    img = icons.icon_pixmap(k, 40, "#7b5cff", "rgba(123,92,255,0.4)")
    ink = sum(1 for x in range(0, 40, 2) for y in range(0, 40, 2)
              if img.pixelColor(x, y).alpha() > 20)
    if k != "faen" and ink < 15:
        ink_ok = False
check("همه‌ی گلیف‌ها واقعاً رندر می‌شوند (جوهر دارند)", ink_ok)

# ---------- ۳) 2.5D — اِلیویشن کارت و هاله‌ی ناوبری ----------
src_card = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "widgets.py"), encoding="utf-8").read()
check("کارت شیشه‌ای گرادیان اِلیویشن دارد", "elev = QLinearGradient" in src_card)
check("کارت شیشه‌ای لبه‌ی ضخامتِ کف دارد (حس اسلب)", "thick = QLinearGradient" in src_card)
check("قرصِ فعالِ ناوبری هاله‌ی نرم دارد", "هاله‌ی نرمِ فعال" in src_card
      and "glow.setColorAt(0.35, gc)" in src_card)
check("چیپ موقعیت سربرگ وجود دارد", hasattr(widgets, "LocationChip"))

# ---------- ۴) پنجره‌ی اصلی — چیدمان بریف ----------
check("نسخه‌ی برنامه (دینامیک)", main_window.VERSION == MW_VERSION_EXPECTED)

import jdatetime  # noqa: E402

BASE = {"mobile": "۰۹۱۲۳۴۵۶۷۸۹", "bill_title": "قبض خانگی", "bill_id": "1234567890",
        "bills": [{"bill_id": "1234567890", "bill_title": "قبض خانگی"},
                  {"bill_id": "9876543210", "bill_title": "مغازه"}],
        "active_bill": "1234567890"}
storage._state = storage.load() | dict(BASE)
storage.save()

today = jdatetime.date.today()
occurred = {"outage_date": today.strftime("%Y/%m/%d"), "outage_start_time": "08:30",
            "outage_stop_time": "09:15", "outage_address": "خیابان آزادی"}
pl_today = {"outage_date": today.strftime("%Y/%m/%d"), "outage_start_time": "18:00",
            "outage_stop_time": "19:30", "outage_address": "بلوار امام، فاز ۲ صنعتی"}
future = (today + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")
pl_future = {"outage_date": future, "outage_start_time": "10:30",
             "outage_stop_time": "12:00", "outage_address": "شهرک صنعتی"}
SNAP = {"occurred": [occurred], "planned": [pl_today, pl_future],
        "per_bill": {}, "multi_bills": True, "checked_at": "12:34:56",
        "from": jalali_today(), "to": jalali_plus(5)}

ok_all = True
for name in ("dark", "light"):
    theme.set_current(name)
    theme.apply_accent(None)
    theme.apply(app)
    app.setFont(theme.app_font(11))
    w = MainWindow(storage.load())
    w.update_identity()
    w.set_connection(i18n.t("conn.connected", src=i18n.t("conn.default_route")), True)
    w.show()
    for _ in range(4):
        app.processEvents()
    w.update_snapshot(SNAP)
    for _ in range(4):
        app.processEvents()
    # نوار پایین: خلاصه + دکمه‌ی درشت با هاله
    check(f"[{name}] دکمه‌ی به‌روزرسانی فوری در نوار پایین درشت است",
          w.btn_check.minimumHeight() >= 50 and w.btn_check.minimumWidth() >= 220)
    check(f"[{name}] خلاصه‌ی نوار پایین پرمحتواست",
          "در راهه" in w.lbl_upcoming.text() or "مورد" in w.lbl_upcoming.text()
          or w.lbl_upcoming.text() != "")
    check(f"[{name}] پایش چند-قبضی در نوار پایین نشان داده می‌شود",
          "قبض" in w.lbl_footer_bill.text())
    # چیپ موقعیت — داده‌محور (آدرسِ نزدیک‌ترین خاموشیِ آینده؛ مستقل از ساعتِ اجرا)
    check(f"[{name}] چیپ موقعیت با آدرسِ واقعی دیده می‌شود",
          w.loc.isVisible() and len(w.loc._addr) > 3
          and w.loc._addr in ("بلوار امام، فاز ۲ صنعتی", "شهرک صنعتی"))
    # بدون داده پنهان می‌شود
    w.loc.set_address("")
    check(f"[{name}] چیپ موقعیت بدون داده پنهان است", not w.loc.isVisible())
    w.loc.set_address("بلوار امام، فاز ۲ صنعتی")
    # هیرو: شمارش درشت‌تر
    px = w.hero._fit_px("۰۰:۰۰:۰۰", 44, 21, 400)
    check(f"[{name}] سقف قلم شمارش هیرو ۴۴px است", px <= 44 and px > 21)
    # رندر دو تم
    pm = w.grab()
    ok_all &= not pm.isNull()
    if name == "dark":
        img = pm.toImage()
        # هاله‌ی بنفش زیر قرص فعال ناوبری — ناحیه‌ی قرص باید ته‌رنگ بنفش داشته باشد
        thumb = w.nav._thumb_rect(w.nav._buttons["dashboard"])
        cx = int(thumb.center().x()) + (w.width() - w.nav.width())
        cy = int(thumb.center().y())
        found_violet = False
        for dy in range(-38, 39, 4):
            for dx in range(-30, 31, 4):
                c = img.pixelColor(cx + dx, cy + dy)
                if c.blue() > 90 and c.blue() > c.green() + 18 and c.red() > c.green():
                    found_violet = True
                    break
            if found_violet:
                break
        check("[dark] هاله‌ی بنفشِ دور قرصِ ناوبری فعال دیده می‌شود", found_violet)
    w.hide()
    w.deleteLater()
    for _ in range(2):
        app.processEvents()

# ---------- ۵) i18n — کلید تازه و خلوص زبان ----------
i18n.set_lang("fa")
check("کلید موقعیت فارسی", i18n.t("hdr.location") == "موقعیت")
i18n.set_lang("en")
check("کلید موقعیت انگلیسی", i18n.t("hdr.location") == "Location")
i18n.set_lang("fa")

print(f"\n{_n[0] - (len(_n) - 1)}/{_n[0]} ALL PASS" if len(_n) == 1
      else f"\nFAILED: {len(_n) - 1}")
sys.exit(0 if len(_n) == 1 else 1)
