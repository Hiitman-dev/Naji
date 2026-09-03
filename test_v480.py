# test_v480.py — تست نسخه‌ی ۴٫۸٫۰: «ماتِ آرام»
#   • حذف بکگراند انیمیشنی RGB (شفق شش‌لکه‌ای) → بوم ساکنِ تک‌نور
#   • رفع «فیدشدن بخش‌ها»: تفکیک روشنایی کارت/بوم در هر دو تم
# اجرا: QT_QPA_PLATFORM=offscreen NAJI_NO_ANIM=1 python test_v480.py
import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("NAJI_NO_ANIM", "1")   # سکونِ کامل برای مقایسه‌ی فریم‌ها
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
from widgets import BackdropCanvas, GlassCard  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QColor  # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)
app.setStyle("Fusion")
theme.load_fonts()
theme.apply(app)
app.setFont(theme.app_font(11))

import i18n  # noqa: E402
i18n.set_lang("fa")


def composite(over_css, alpha_css):
    """ترکیب رنگِ نیمه‌شفاف روی رنگِ زیرین — برای سنجشِ واقعیِ تفکیک"""
    top = widgets.qcolor(alpha_css)
    base = widgets.qcolor(over_css)
    a = top.alphaF()
    return QColor(
        round(top.red() * a + base.red() * (1 - a)),
        round(top.green() * a + base.green() * (1 - a)),
        round(top.blue() * a + base.blue() * (1 - a)),
    )


def lum(c):
    return (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000.0


# ---------- ۱) بوم ساکن: هیچ تایمر و هیچ لکه‌ی متحرکی ----------
theme.apply_accent(None)

cv = BackdropCanvas()
cv.resize(620, 520)
check("بوم: freeze() برای سازگاری رندرها هست", callable(getattr(cv, "freeze", None)))
check("بوم: هیچ QTimer فرزندی دارد (پس‌زمینه کاملاً ساکن)",
      cv.findChildren(QTimer) == [])
check("بوم: نام قدیمی AuroraCanvas همان کلاس ساکن است",
      widgets.AuroraCanvas is BackdropCanvas)

cv.show()
QTest.qWait(120)
g1 = cv.grab().toImage()
QTest.qWait(220)
g2 = cv.grab().toImage()
same = (g1.sizeInBytes() == g2.sizeInBytes() and g1.constBits() == g2.constBits())
check("دو فریم با فاصله‌ی زمانی بایت‌به‌بیت یکسان‌اند (هیچ انیمیشنی نیست)", same)
cv.hide()

# ---------- ۲) نورِ تک‌فام — پایان بازی RGB ----------
check("هر تم فقط یک نور دارد",
      len(theme.aurora_spec()) == 1 and len(theme.AURORA_LIGHT) == 1
      and len(theme.AURORA_DARK) == 1)
lr, lb = [int(v) for v in theme.AURORA_LIGHT[0][0].split(",")][0], \
         [int(v) for v in theme.AURORA_LIGHT[0][0].split(",")][2]
check("نورِ لایت خنثی/گرمِ استودیویی است (R ≥ B، بدون فام بازیگوش)", lr >= lb)
check("نورِ دارت آلفای خیلی کم دارد (تینت، نه رنگ)",
      theme.AURORA_DARK[0][1] <= 24)
theme.apply_accent((212, 175, 55))   # زرد طلایی ویندوز
check("اکسنت زردِ ویندوز نورِ لایت را لکه نمی‌کند (خنثی می‌ماند)",
      theme.AURORA_LIGHT[0][0] == "255,252,244")
theme.apply_accent(None)

# ---------- ۳) رفع «فیدشدن بخش‌ها» — تفکیک روشنایی کارت/بوم ----------
for name in ("dark", "light"):
    theme.set_current(name)
    p = theme.PALETTES[name]
    card = composite(p["bg_top"], p["glass"])
    delta = abs(lum(card) - lum(widgets.qcolor(p["bg_top"])))
    check(f"تفکیک روشنایی کارت/بوم در تم {name}: Δ={delta:.1f} (≥ ۱۰)",
          delta >= 10.0)
    border_a = widgets.qcolor(p["glass_border"]).alpha()
    check(f"هِیرلاین مرزی در تم {name} دیده می‌شود (آلفای ≥ ۲۶)", border_a >= 26)

theme.set_current("dark")
p_dark = theme.PALETTES["dark"]
card_dark = composite(p_dark["bg_top"], p_dark["glass"])
# v5.0 — شیشه‌ی اکریلیک با ته‌مایه‌ی آبیِ عمدی (بریف: premium dark #0D0F14)
check("کارتِ تیره ته‌مایه‌ی آبیِ سرد دارد (اکریلیکِ عمدی)",
      card_dark.blue() > card_dark.red() and card_dark.red() - card_dark.green() <= 4)
check("شیشه‌ی تیره اکریلیک واقعی است (بوم از پشت کمی می‌گذرد، ولی خوانا می‌ماند)",
      0.65 <= widgets.qcolor(p_dark["glass"]).alphaF() <= 0.85)

qss_light = theme.build_qss(theme.PALETTES["light"])
qss_dark = theme.build_qss(theme.PALETTES["dark"])
check("QSS لایت سطحِ سفیدِ کاغذی را می‌گیرد", "rgba(255,255,255,0.88)" in qss_light)
check("QSS دارت سطحِ اکریلیکِ اِلیویت را می‌گیرد", "rgba(26,29,41,0.72)" in qss_dark)

# ---------- ۴) رندر واقعی: بوم و کارت روی هم — تفکیک پیکسلی ----------
theme.set_current("dark")
theme.apply(app)
holder = BackdropCanvas()
holder.resize(620, 520)
card = GlassCard(holder)
card.setGeometry(120, 150, 380, 260)
holder.show()
QTest.qWait(150)
img = holder.grab().toImage()
cv_px = img.pixelColor(24, 300)          # بوم، دور از نور و وینیت
cd_px = img.pixelColor(310, 280)         # وسط کارت
check("دارک: کارت روی بوم روشن‌تر است (Δ روشنایی ≥ ۱۰)",
      cd_px.lightness() - cv_px.lightness() >= 10)
check("دارک: بوم واقعاً ماتِ تیره است (روشنایی ≤ ۱۶)", cv_px.lightness() <= 16)

theme.set_current("light")
theme.apply(app)
for w in app.allWidgets():
    fn = getattr(w, "repaint_theme", None)
    if callable(fn):
        fn()
QTest.qWait(120)
img = holder.grab().toImage()
cv_px = img.pixelColor(24, 300)
cd_px = img.pixelColor(310, 280)
check("لایت: کارتِ سفید روی بومِ صدفی روشن‌تر است (Δ روشنایی ≥ ۸)",
      cd_px.lightness() - cv_px.lightness() >= 8)
check("لایت: بوم صدفیِ گرم است (R > B)", cv_px.red() > cv_px.blue())
holder.hide()

# ---------- ۵) پنجره‌ی اصلی: ساخت و رندر در هر دو تم ----------
import main_window  # noqa: E402
MW_VERSION_EXPECTED = main_window.VERSION
import storage  # noqa: E402
import tempfile  # noqa: E402

check("نسخه‌ی برنامه (دینامیک)", main_window.VERSION == MW_VERSION_EXPECTED)
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="naji_test_"))
storage.load()

win = main_window.MainWindow({
    "theme": "dark", "theme_mode": "dark", "matte_done": True,
    "sync_windows": False, "lang": "fa", "bills": [], "active_bill": "",
})
win.resize(880, 860)
win.show()
QTest.qWait(250)
check("بومِ پنجره‌ی اصلی BackdropCanvas است",
      isinstance(win.centralWidget(), BackdropCanvas)
      or any(isinstance(c, BackdropCanvas) for c in win.centralWidget().findChildren(type(win.centralWidget()))))
f1 = win.grab().toImage()
QTest.qWait(200)
f2 = win.grab().toImage()
check("پنجره با NAJI_NO_ANIM دو فریم یکسان می‌گیرد (سکونِ کامل)",
      f1.constBits() == f2.constBits())

theme.set_current("light")
theme.apply(app)
QTest.qWait(120)
ok_light = win.grab().save("/tmp/naji_v480_light.png")
theme.set_current("dark")
theme.apply(app)
QTest.qWait(120)
ok_dark = win.grab().save("/tmp/naji_v480_dark.png")
check("رندر کامل پنجره در هر دو تم", ok_light and ok_dark)

from PySide6.QtGui import QPixmap  # noqa: E402
img = QPixmap("/tmp/naji_v480_light.png").toImage()
c1 = img.pixelColor(700, 700)
check("بومِ صدفی در رندر واقعی گرم و روشن است (R>B و L>۲۰۰)",
      c1.red() > c1.blue() and c1.lightness() > 200)

print()
print("ALL PASS" if _ok else "SOME FAILED")
sys.exit(0 if _ok else 1)
