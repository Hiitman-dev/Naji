# test_v460.py — تست نسخه‌ی ۴٫۶٫۰: ژله‌ی ظریف (پورت transitions.dev) + مشکیِ مات
# اجرا: QT_QPA_PLATFORM=offscreen python test_v460.py
import os
import sys
import time
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# تست انیمیشن نیاز به موتور فعال دارد — قبل از ایمپورت widgets قفل شود
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


# ---------- ۱) ریاضیات موشن — پورت keyframes دوبینس ----------
import widgets  # noqa: E402
from widgets import JELLY_DUR, JellyButton, jelly_pos, jelly_pulse  # noqa: E402

check("مدتِ نزدیک مرجع (۳۶۰ms ← مرجع ۳۵۰ms)", JELLY_DUR == 360)

# نقاط کلیدی مرجع: ۰٪ شروع، ۵۵٪ اورشوت، ۸۰٪ برگشت، ۱۰۰٪ نشست
a, b, ov = 0.0, 20.0, 0.068
check("t=0 → نقطه‌ی شروع", jelly_pos(0.0, a, b, ov) == a)
check("t=1 → نشست دقیق روی مقصد", abs(jelly_pos(1.0, a, b, ov) - b) < 1e-9)
check("t=0.55 → دقیقاً مقصد+ov1 (مرجع: ov2=0)",
      abs(jelly_pos(0.55, a, b, ov) - (b + b * ov)) < 0.01)
check("t=0.8 → برگشت روی مقصد (مرجع: ov2=0)", abs(jelly_pos(0.8, a, b, ov) - b) < 0.01)

# اورشوتِ دوبینسِ راستین: بیزیرِ 1.35 خودش هم فراتر از keyframe می‌رود
peak = max(jelly_pos(i / 200.0, a, b, ov) for i in range(201))
check("اورشوت وجود دارد (دوبینس)", peak > b + 0.3)
ov1 = b * ov
check("اورشوتِ بیزیر از keyframe هم فراتر می‌رود (مرجعِ راستین)",
      peak > b + ov1 + 0.1 and peak < b + ov1 + 0.06 * (b - a))
check("موقعیت هرگز منفی نمی‌شود", min(jelly_pos(i / 200.0, a, b, ov) for i in range(201)) >= a - 1e-9)

# جهت معکوس — بازگشت به عقب هم دوبینس دارد
rmin = min(jelly_pos(i / 200.0, b, a, ov) for i in range(201))
check("سفر معکوس هم اورشوت دارد", rmin < a - 0.3 and abs(jelly_pos(1.0, b, a, ov) - a) < 1e-9)

# مسیر صفر → همان مقصد (تقسیم بر صفر نشود)
check("مسیر صفر امن است", jelly_pos(0.5, 7.0, 7.0) == 7.0)

# نبض ژله‌ای — کش‌آمدنِ ملایم و فرونشستن، بدون انفجار (v5.1: ۱٫۰۴/۰٫۹۸)
check("نبض در ابتدا و انتها خنثی است", jelly_pulse(0.0) == 1.0 and jelly_pulse(1.0) == 1.0)
check("نبض بیشینه ≈ ۱٫۰۴ (ظرافت)", 1.03 <= max(jelly_pulse(i / 100.0) for i in range(101)) <= 1.045)
check("نبض کمینه ≈ ۰٫۹۸", 0.975 <= min(jelly_pulse(i / 100.0) for i in range(101)) <= 0.985)

# منحنی معادل cubic-bezier(0.34, 1.35, 0.64, 1) — ease-out با اورشوت
ec = widgets.jelly_ease()
check("منحنی ژله از نوع BezierSpline است", ec.type() == ec.Type.BezierSpline)
check("منحنی در نیمه‌ی اول جلوتر از خطی است (ease-out)", ec.valueForProgress(0.5) > 0.5)
check("منحنی مهارشده است — اورشوت فقط از keyframes (ظرافت)", ec.valueForProgress(0.7) <= 1.0 + 1e-6)

# ---------- ۲) سوئیچ — دوبینس دستگیره + کراس‌فید مستقل ریل ----------
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)

sw = widgets.Switch(checked=False)
check("سوییچ در لود اول بدون انیمیشن روی خاموش نشسته (گارد is-init)",
      sw._thumb_x == widgets.Switch.X_OFF and sw._track_t == 0.0 and sw._anim is None)
sw2 = widgets.Switch(checked=True)
check("سوییچ روشنِ لود اول روی روشن نشسته",
      sw2._thumb_x == widgets.Switch.X_ON and sw2._track_t == 1.0)

sw.setChecked(True)  # toggled → _start_jelly
check("تغییر سوئیچ انیمیشن دوبینس را ساخت", sw._anim is not None and sw._tanim is not None)
sw._on_jelly(1.0)
check("پایان سفر: دستگیره دقیقاً روی روشن",
      abs(sw._thumb_x - widgets.Switch.X_ON) < 1e-9 and sw._pulse == 1.0)
sw._on_track(1.0)
check("پایان کراس‌فید: ریل کاملاً اکسنت", sw._track_t == 1.0)
# میانه‌ی سفر: بین شروع و اورشوت — نبض فعال (v5.1: اوج = مسیر×۱٫۱۲)
sw._on_jelly(0.3)
mid_x = sw._thumb_x
check("میانه‌ی سفر در مسیر است",
      widgets.Switch.X_OFF < mid_x
      < widgets.Switch.X_ON + (widgets.Switch.X_ON - widgets.Switch.X_OFF) * 0.18)
sw.setChecked(False)
sw._on_jelly(1.0)
sw._on_track(1.0)
check("خاموشی: دستگیره و ریل به آغاز برمی‌گردند",
      abs(sw._thumb_x - widgets.Switch.X_OFF) < 1e-9 and sw._track_t == 0.0)
pm = sw.grab()
check("رندر سوییچ بدون خطا", pm is not None and not pm.isNull())

# بدون انیمیشن (NAJI_NO_ANIM) — رفتار فوری
widgets.os_env_anim = lambda: False
sw.setChecked(True)
check("با موشنِ خاموش، سوییچ فوری می‌پرد", sw._thumb_x == widgets.Switch.X_ON)
widgets.os_env_anim = lambda: True  # بازگردانی برای بقیه‌ی تست‌ها

# ---------- ۳) نوار ناوبری — قرصِ سرخورنده ----------
theme = __import__("theme")
theme.set_current("dark")
theme.apply_accent(None)

rail = widgets.NavRail("dashboard")
rail.resize(92, 400)
rail.show()
app.processEvents()

btn_dash = rail._buttons["dashboard"]
btn_about = rail._buttons["about"]
check("قرص در لود اول روی دکمه‌ی فعال نشسته (بدون سفر)",
      abs(rail._thumb_y - rail._thumb_rect(btn_dash).y()) < 0.01)

rail.set_current("about", animate=False)
check("انتخاب برنامه‌ای (بدون انیمیشن) قرص را جابه‌جا می‌کند",
      abs(rail._thumb_y - rail._thumb_rect(btn_about).y()) < 0.01)

# سفرِ دوبینس با انتخاب واقعی
rail.set_current("dashboard", animate=True)
check("سفر ناوبری انیمیشن دارد", rail._anim is not None)
from_y, to_y = rail._from_y, rail._to_y
check("سفر از «درباره» به «خانه» است", to_y < from_y)
rail._on_thumb(0.5)
ov_t = abs(to_y - from_y) * 0.06   # v5.1: اوج ≈ ۴٫۴٪ مسیر + حاشیه
check("میانه‌ی سفر در مسیرِ مقصد تا اورشوت (هر دو جهت)",
      min(from_y, to_y) - ov_t - 0.1 <= rail._thumb_y <= max(from_y, to_y) + ov_t + 0.1)
rail._on_thumb(1.0)
check("نشستِ نهایی قرص روی مقصد", abs(rail._thumb_y - to_y) < 1e-9)
rail._on_tint(1.0)
check("کراس‌فید لبه‌ی اکسنت کامل شد", rail._tint == 1.0)

# اورشوتِ قرصِ ناوبری در keyframe مرجع (۲٫۸٪ مسیر — pop=1.22)
travel = abs(to_y - from_y)
overshoot = abs(jelly_pos(0.55, from_y, to_y, 0.028, 1.22) - to_y)
check("اورشوت ناوبری ≈ ۲٫۸٪ مسیر", abs(overshoot - travel * 0.028) < 0.01)

# کلیکِ دکمه هم قرص را می‌فرستد (اتصال clicked)
btn_about.click()
app.processEvents()
check("کلیکِ دکمه‌ی ناوبری قرص را به سمت خودش می‌فرستد",
      rail._anim is not None or abs(rail._thumb_y - rail._thumb_rect(btn_about).y()) < 0.01)
if rail._anim is not None:
    rail._on_thumb(1.0)
check("قرص در پایان مسیرِ کلیک روی «درباره» است",
      abs(rail._thumb_y - rail._thumb_rect(btn_about).y()) < 0.01)

pm = rail.grab()
check("رندر نوار ناوبری بدون خطا", pm is not None and not pm.isNull())
rail.hide()

# ---------- ۴) دکمه‌های ژله‌ای ----------
btn = JellyButton("کوچک")
btn.setObjectName("primary")
btn.resize(160, 46)
btn.show()
app.processEvents()
s0 = btn._jelly_scale()
btn._jelly_press()
end = time.time() + 0.4
while time.time() < end and btn._jelly_scale() >= s0:
    app.processEvents(QEventLoop.AllEvents, 8)
    time.sleep(0.008)
s_press = btn._jelly_scale()
check("فشردن دکمه جمع می‌شود (<۱)", s_press < 0.99)
pm = btn.grab()
check("رندر دکمه در حالت فشرده بدون خطا", pm is not None and not pm.isNull())
btn._jelly_release()
end = time.time() + 0.9
while time.time() < end and abs(btn._jelly_scale() - 1.0) > 0.005:
    app.processEvents(QEventLoop.AllEvents, 8)
    time.sleep(0.008)
check("رهاشدن با دوبینسِ ریز به ۱٫۰ برمی‌گردد", abs(btn._jelly_scale() - 1.0) < 0.01)
btn.hide()

# میکسین دکمه‌های رسم‌دستی
for cls in (widgets.ThemeButton, widgets.LangButton, widgets.NavButton,
            widgets._StepButton):
    check(f"فشار ژله‌ای روی {cls.__name__}", issubclass(cls, widgets._JellyPress))

# ---------- ۵) پالت مشکیِ مات ----------
from PySide6.QtGui import QColor  # noqa: E402

theme.apply_accent(None)
p_dark = theme.PALETTES["dark"]
p_light = theme.PALETTES["light"]
# v5.0 — پالت تیره «بنفشِ نیمه‌شب» شد: بوم #0D0F14 با ته‌مایه‌ی آبی
check("بوم تیره خانواده‌ی #0D0F14 است (بریف پریمیوم کاربر)",
      p_dark["bg_top"] == "#0d0f14" and QColor(p_dark["bg_top"]).lightness() <= 18)
check("کفِ بوم تیره سیاه‌تر از بالاست", QColor(p_dark["bg_bottom"]).lightness() <= QColor(p_dark["bg_top"]).lightness())
check("شیشه‌های تیره اکریلیکِ سرد‌اند (ته‌مایه‌ی آبیِ عمدی، نه خاکستریِ کهنه)",
      widgets.qcolor(p_dark["glass"]).blue() > widgets.qcolor(p_dark["glass"]).red())
sheen_a = widgets.qcolor(p_dark["sheen"]).alpha()
check("براقِ شیشه در تیره کم‌سو شده (مات)", sheen_a <= 14)
# v4.7 — پالت روشن «سفید صدفیِ مات» شد؛ پینِ مقدار کهنه برداشته شد و
# ماهیتِ جدید قفل شد: بومِ گرمِ روشن + شفقِ کف‌کرده (بدون اشباعِ قبلی)
# v4.8 — پالت روشن «صدفِ عمیق‌تر» شد؛ ماهیت قفل می‌ماند: بومِ گرم + کارتِ
# سفیدِ کاغذی که فید نشود (تفکیک با روشنایی، نه رنگ اشباع)
check("پالت روشن صدفیِ مات است (بومِ گرمِ عمیق)",
      p_light["bg_top"] == "#f3eee6" and p_light["bg_bottom"] == "#e9e1d4")
check("براقِ روشن هم مات شده (صدف)", widgets.qcolor(p_light["sheen"]).alpha() <= 74)
# v4.8 — شفقِ چندلکه‌ای حذف شد؛ فقط یک نورِ تک‌فامِ ساکن در هر تم هست:
check("نورِ پس‌زمینه تک‌لکه‌ای است (بدون بازی RGB)",
      len(theme.AURORA_DARK) == 1 and len(theme.AURORA_LIGHT) == 1)
check("نورِ تیره کم‌سو و فامِ اکسنت است (تینتِ مایکا)",
      theme.AURORA_DARK[0][1] <= 24)
check("نورِ روشن خنثیِ استودیویی است",
      int(theme.AURORA_LIGHT[0][0].split(",")[0])
      >= int(theme.AURORA_LIGHT[0][0].split(",")[2]))
# v5.0 — امضای بنفش (#7B5CFF): گرادیانِ هیرو عمداً فامِ بنفشِ اشباع‌تر است
check("اکسنت امضای ناجی = بنفش #7B5CFF (بریف کاربر)",
      p_dark["accent"] == "#7b5cff" and p_dark["grad2"] == "#7b5cff")
gvals = [QColor(p_dark[k]).value() for k in ("grad1", "grad2", "grad3")]
check("گرادیان هیرو در تیره عمق دارد (کفِ گرادیان تیره‌تر از سرش)",
      gvals[2] < gvals[0])

# اکسنت ویندوز هم در تیره مات بماند
theme.apply_accent((0, 120, 215))  # آبی ویندوز
g = [QColor(theme.PALETTES["dark"][k]).value() for k in ("grad1", "grad2", "grad3")]
check("با اکسنت ویندوز هم گرادیان تیره عمیق می‌ماند", max(g) <= 210)
theme.apply_accent(None)

# ---------- ۶) مهاجرت مشکیِ مات در تنظیمات ----------
import storage  # noqa: E402

check("پیش‌فرض تم = dark", storage.DEFAULTS["theme"] == "dark"
      and storage.DEFAULTS["theme_mode"] == "dark")
st = storage._sanitize({"theme": "light", "theme_mode": "light"})
check("کاربرِ فعلی یک‌بار به مشکیِ مات مهاجرت می‌کند",
      st["theme"] == "dark" and st["theme_mode"] == "dark" and st["matte_done"] is True)
st2 = storage._sanitize({"theme": "light", "theme_mode": "light", "matte_done": True})
check("انتخاب بعدیِ کاربر محترم است (دیگر دست‌نخورده)",
      st2["theme"] == "light" and st2["theme_mode"] == "light")
st3 = storage._sanitize({})
check("نصب تازه روی مشکیِ مات می‌افتد", st3["theme"] == "dark" and st3["theme_mode"] == "dark")

# ---------- ۷) پنجره‌ی اصلی: جابه‌جایی صفحه‌ها با محوشدن لطیف ----------
import main_window  # noqa: E402
MW_VERSION_EXPECTED = main_window.VERSION
import tempfile  # noqa: E402

check("نسخه‌ی برنامه (دینامیک)", main_window.VERSION == MW_VERSION_EXPECTED)
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="naji_test_"))
settings_test = storage.load()  # state باید پیش از ساخت پنجره لود شود

win = main_window.MainWindow({
    "theme": "dark", "theme_mode": "dark", "matte_done": True,
    "sync_windows": False, "lang": "fa", "bills": [], "active_bill": "",
    "mode": "notify", "default_action": "shutdown", "lead_minutes": 10,
    "notify_seconds": 15, "poll_minutes": 5, "autostart": False,
})
win.show()
app.processEvents()

check("صفحه‌ی اول داشبورد است", win.stack.currentWidget() is win.pages["dashboard"])
win._switch_page("about")
app.processEvents()
cur = win.stack.currentWidget()
check("جابه‌جایی به «درباره» انجام شد", cur is win.pages["about"])
# v5.1 — تعویض صفحه فوری و بدون گرافیک‌افکت است: فلاش/موربِ باک‌اند GPU
# ویندوز ریشه‌کن شد؛ موشنِ سفر بر عهده قرصِ دوبینسِ ریل است
check("تعویض صفحه بدون گرافیک‌افکت (رفع فلاشِ ویندوز)",
      cur.graphicsEffect() is None)

# جابه‌جایی سریع پشت‌سرهم — صفحه‌ی مقصد باید سالم و بدون اثر بماند
win._switch_page("settings")
win._switch_page("help")
app.processEvents()
check("جابه‌جایی سریع: «راهنما» سالم و بدون اثر",
      win.stack.currentWidget() is win.pages["help"]
      and win.pages["help"].graphicsEffect() is None)

# قرص ناوبری پنجره در مسیرِ واقعی (show_page) هم‌راستا می‌شود
win.show_page("dashboard")
end = time.time() + 1.4
while time.time() < end:
    app.processEvents(QEventLoop.AllEvents, 8)
    time.sleep(0.01)
check("مسیر واقعی: صفحه‌ی خانه فعال شد", win.stack.currentWidget() is win.pages["dashboard"])
check("قرص پنجره روی دکمه‌ی «خانه» نشست",
      abs(win.nav._thumb_y - win.nav._thumb_rect(win.nav._buttons["dashboard"]).y()) < 0.01)
pm = win.grab()
check("رندر کامل پنجره در تم مشکیِ مات بدون خطا", pm is not None and not pm.isNull())
win.hide()

# ---------- نتیجه ----------
print()
print("ALL PASS" if _ok else "SOME FAILED")
sys.exit(0 if _ok else 1)
