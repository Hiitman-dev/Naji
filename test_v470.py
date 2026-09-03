# test_v470.py — تست نسخه‌ی ۴٫۷٫۰: صدفِ ماتِ لایت + دکمه‌ی خروجِ گوشه +
# اصلاح باگ سلکشن تب‌ها (توقف انیمیشن کهنه) + ممیزی سایز آیکون‌ها
# اجرا: QT_QPA_PLATFORM=offscreen python test_v470.py
import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.pop("NAJI_NO_ANIM", None)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# winreg فقط ویندوزی است — استابِ حداقلی برای ایمپورت storage در لینوکس
if not sys.platform.startswith("win") and "winreg" not in sys.modules:
    _wr = types.ModuleType("winreg")
    _wr.HKEY_CURRENT_USER = 0x80000001
    _wr.KEY_SET_VALUE = 0x2
    _wr.KEY_READ = 0x20019
    _wr.REG_SZ = 1

    class _FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def QueryValueEx(self, *a):
            raise FileNotFoundError

        def SetValueEx(self, *a):
            pass

        def DeleteValue(self, *a):
            pass

    _wr.OpenKey = lambda *a, **k: _FakeKey()
    sys.modules["winreg"] = _wr

_ok = True


def check(name, cond):
    global _ok
    print(("PASS  " if cond else "FAIL  ") + name)
    _ok = _ok and bool(cond)


import theme  # noqa: E402
import widgets  # noqa: E402
from widgets import Segmented, NavRail  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtGui import QColor, QPixmap  # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)
app.setStyle("Fusion")
theme.load_fonts()
theme.apply(app)
app.setFont(theme.app_font(11))

import i18n  # noqa: E402
i18n.set_lang("fa")

# ---------- ۱) سفید صدفیِ مات — پالت روشن ----------
theme.apply_accent(None)
p_light = theme.PALETTES["light"]

check("بوم صدفی: بالای گرمِ عمیق (#f3eee6)", p_light["bg_top"] == "#f3eee6")
check("بوم صدفی: کفِ گرم‌تر از بالاست (گرادیان لطیف)",
      QColor(p_light["bg_bottom"]).lightness() < QColor(p_light["bg_top"]).lightness())
check("بدون ته‌مایه‌ی سرمه‌ایِ قدیم (قرمز ≈ آبی در بوم)",
      abs(QColor(p_light["bg_top"]).red() - QColor(p_light["bg_top"]).blue()) >= 2)
check("براقِ صدفیِ مات (sheen کف‌کرده)", widgets.qcolor(p_light["sheen"]).alpha() <= 74)
check("لبه‌ی شیشه گرم است (نه سرمه‌ای)",
      QColor(p_light["glass_edge"]).red() >= QColor(p_light["glass_edge"]).blue())
check("متنِ گرمِ زغالی (R > B)",
      QColor(p_light["text"]).red() > QColor(p_light["text"]).blue())
check("سایه‌ی صدفیِ گرم", QColor("#a69b8a").lightness() > 100
      and p_light["shadow"] == "166,155,138")
check("پاپ‌آپ صدفی", p_light["popup_bg"] == "#fffdfa")

# v4.8 — نورِ تک‌لکه‌ایِ ساکن: کارت‌های سفیدِ اوپک باید از بوم جدا باشند
theme.apply_accent((0, 120, 215))
check("اکسنت ویندوز فقط نورِ تیره را تینت می‌کند (نورِ روشن خنثی می‌ماند)",
      theme.AURORA_LIGHT[0][0] == "255,252,244"
      and theme.AURORA_DARK[0][0] == "0,120,215")
theme.apply_accent(None)
check("ریست اکسنت: نورها به امضای ناجی برمی‌گردند",
      theme.AURORA_LIGHT[0][0] == "255,252,244"
      and theme.AURORA_DARK[0][0] == "123,92,255")

# ---------- ۲) دکمه‌ی خروج در گوشه‌ی سربرگ ----------
import main_window  # noqa: E402
MW_VERSION_EXPECTED = main_window.VERSION
import storage  # noqa: E402
import tempfile  # noqa: E402

check("نسخه‌ی برنامه (دینامیک)", main_window.VERSION == MW_VERSION_EXPECTED)
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="naji_test_"))
storage.load()

win = main_window.MainWindow({
    "theme": "dark", "theme_mode": "dark", "matte_done": True,
    "sync_windows": False, "lang": "fa",
})
win.resize(880, 860)
win.show()
QTest.qWait(250)

lo = win.btn_logout
check("دکمه‌ی خروج وجود دارد و در سربرگ است", lo is not None and lo.isVisible())
check("دکمه‌ی خروج objectName=signout (استایل کم‌رنگِ گوشه)",
      lo.objectName() == "signout")
check("دکمه‌ی خروج بالای صفحه است (گوشه‌ی سربرگ، نه ته داشبورد)",
      lo.mapTo(win, lo.rect().topLeft()).y() < 80)
check("دکمه‌ی خروج فشرده است (ارتفاع < ۴۴ — ابزار، نه CTA)",
      lo.height() < 44)
check("داشبورد دیگر دکمه‌ی خروجِ بزرگ ندارد (فقط CTA بررسی)",
      all(not (isinstance(b, widgets.JellyButton) and b.objectName() == "ghost"
               and b.text() == i18n.t("dash.logout"))
          for b in win.pages["dashboard"].findChildren(widgets.JellyButton)))

# رفتار واقعی: کلیک → پنجره‌ی تأیید → بدون تأیید، خروج انجام نمی‌شود
from PySide6.QtWidgets import QMessageBox  # noqa: E402
fired = []
win.logout_requested.connect(lambda: fired.append(1))
orig_exec = QMessageBox.exec
QMessageBox.exec = lambda self: QTest.qWait(10)
lo.click()
QMessageBox.exec = orig_exec
check("کلیک خروج پنجره‌ی تأیید می‌آورد و بدون تأیید خارج نمی‌شود",
      len(fired) == 0)

# ---------- ۳) باگ سلکشن تب‌ها — ریشه: انیمیشنِ توقف‌نشده ----------
seg = Segmented([("a", "AA"), ("b", "BB"), ("c", "CC")], "a")
seg.resize(420, 44)
seg.show()
QTest.qWait(150)

# کلیک وسط سفر + resize حین انیمیشن — سناریوی اصلی باگ
seg._buttons["b"].click()
QTest.qWait(50)
seg.resize(560, 44)          # انیمیشن کهنه باید بی‌درنگ بمیرد
QTest.qWait(600)
g_ind, g_tgt = seg._ind.geometry(), seg._buttons["b"].geometry()
check("resize حین سفر قرص: قرص روی تبِ درست می‌نشیند",
      seg.value() == "b" and g_ind.topLeft() == g_tgt.topLeft()
      and g_ind.size() == g_tgt.size())

# کلیک‌های اَبَرسریق — آخرین کلیک برنده است
seg._buttons["c"].click()
seg._buttons["a"].click()
seg._buttons["b"].click()
QTest.qWait(700)
g_ind, g_tgt = seg._ind.geometry(), seg._buttons["b"].geometry()
check("سه کلیک اَبَرسریق: نشستِ نهایی روی آخرین تب",
      seg.value() == "b" and g_ind.topLeft() == g_tgt.topLeft())

# کلیک روی همان تب فعال — انیمیشنِ بیهوده ساخته نمی‌شود (گاردِ هندسه برابر)
seg._buttons["b"].click()
QTest.qWait(320)
check("کلیکِ دوباره روی تب فعال: قرص سر جایش می‌ماند",
      seg._ind.geometry().topLeft() == seg._buttons["b"].geometry().topLeft())

# ---------- ۴) ممیزی سایز آیکون‌ها (جست‌وجوی منابع: گلیف ۱۶–۲۲px) ----------
check("کاشی آمار: چیپ ۳۴px", win.stat_planned.chip.width() == 34)
out_card = widgets.OutageCard(
    {"outage_start_time": "08:00", "outage_stop_time": "10:00"},
    "planned", "امروز", "today")
check("کارت خاموشی: چیپ ۳۶px (بود ۴۲)", out_card.icon.width() == 36)
check("دکمه‌ی تم: قرص ۳۶px (بود ۴۰)", win.nav.btn_theme.width() == 36)
check("دکمه‌ی زبان: قرص ۳۶px (بود ۴۰)", win.nav.btn_lang.width() == 36)
check("لوگوی سربرگ: ۴۰px (بود ۴۸)", win.logo.width() == 40)
check("نشان «درباره»: ۵۶px (بود ۷۰)",
      win.pages["about"].findChildren(widgets.LogoChip)[0].width() == 56)
check("دکمه‌ی ناوبری: برچسب ۷۶×۶۲ دست‌نخورده (هدفِ لمس سالم)",
      win.nav._buttons["dashboard"].width() == 76)

# EmptyState — هنرِ کوچک‌شده
es = win.empty_state
es.repaint_theme()
pm = es._art.pixmap()
check("هنرِ حالت خالی کوچک‌تر شد (بوم ۹۲×۶۴، بود ۱۲۰×۸۴)",
      pm is not None and pm.width() == 92 and pm.height() == 64)

# ---------- ۵) هویت رنگی بخش‌ها (نقطه‌ی رنگی + ابروی رنگی) ----------
qss = theme.build_qss(theme.PALETTES["dark"])
for tone in ("amber", "rose", "indigo"):
    check(f"نقطه‌ی رنگی tone={tone} در QSS هست", f'legendDot[tone="{tone}"]' in qss)
check("استایل دکمه‌ی گوشه‌ای خروج در QSS هست", "QPushButton#signout" in qss)
check("ابروی رنگی: رنگ چیپ را می‌گیرد",
      main_window.eyebrow("test", "teal").styleSheet() != ""
      and "color:" in main_window.eyebrow("test", "teal").styleSheet())
check("ابروی بی‌tone: بدون استایل درون‌خطی",
      main_window.eyebrow("test").styleSheet() == "")

# ---------- ۶) رندر کامل هر دو تم — بدون خطا ----------
ok_render = True
try:
    theme.set_current("light")
    theme.apply(app)
    QTest.qWait(120)
    win.grab().save("/tmp/naji_v470_light.png")
    theme.set_current("dark")
    theme.apply(app)
    QTest.qWait(120)
    win.grab().save("/tmp/naji_v470_dark.png")
except Exception as e:  # noqa: BLE001
    ok_render = False
    print("   render error:", e)
check("رندر کامل پنجره در هر دو تم (صدف + مشکیِ مات)", ok_render)

# نمونه‌گیری پیکسلی صدف: بوم باید گرم و روشن باشد (R > B)
img = QPixmap("/tmp/naji_v470_light.png").toImage()
c1 = img.pixelColor(700, 700)
check("بومِ صدفیِ واقعاً گرم و روشن (R>B و روشنایی بالا)",
      c1.red() > c1.blue() and c1.lightness() > 200)

print()
print("ALL PASS" if _ok else "SOME FAILED")
sys.exit(0 if _ok else 1)
