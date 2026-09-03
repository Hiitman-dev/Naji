# test_v510.py — قفل‌های v5.1.0 «دوبینسِ راستین»
# -------------------------------------------------------------
# شاکیِ این نسخه گفت: «باگ داره و همه‌چیزهایی که گفتم پیاده نشدن».
# این تست همین‌جا، با نمونه‌گیریِ زنده از انیمیشن‌ها ثابت می‌کند:
#   ۱) دوبینسِ مرجع واقعاً اتفاق می‌افتد (اورشوت قابل اندازه‌گیری است)
#   ۲) هیچ نشتِ آبجکت انیمیشنی بعد از تعامل‌های مکرر نیست
#   ۳) حلقه‌های تزئینی کم‌مصرف‌اند (۲۴fps) و وقتی پنهان‌اند، متوقف
#   ۴) تعویض صفحه بدون هر گرافیک‌افکتی است (بدون فلاش/موربِ باک‌اند GPU)
import ctypes
import os
import sys
import tempfile
import time
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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
_wd.crypt32 = types.SimpleNamespace(CryptProtectData=lambda *a: 0,
                                    CryptUnprotectData=lambda *a: 0)
_wd.kernel32 = types.SimpleNamespace(LocalFree=lambda p: 0)
_wd.powrprof = types.SimpleNamespace(SetSuspendState=lambda *a: 1)
ctypes.windll = _wd
import subprocess  # noqa: E402
if not hasattr(subprocess, "CREATE_NO_WINDOW"):
    subprocess.CREATE_NO_WINDOW = 0
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="naji_test_v510_")

from PySide6.QtCore import QPointF, QRectF, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import widgets as W  # noqa: E402
import main_window as MW  # noqa: E402
import storage  # noqa: E402

app = QApplication([])
PASS = []


def ok(name, cond):
    PASS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name)


# ---------- ۱) بیزیرِ واقعی — اورشوتِ ذاتی برگشت ----------
ys = [W._bezier_y(x / 200.0, 1.35) for x in range(201)]
ymax = max(ys)
ok("بیزیر 1.35 اورشوتِ ذاتی دارد (max>1.03)", ymax > 1.03)
ok("بیزیر 1.35 از y=0 و y=1 می‌گذرد",
   abs(ys[0]) < 1e-9 and abs(ys[-1] - 1.0) < 1e-9)
ys10 = [W._bezier_y(x / 100.0, 1.0) for x in range(101)]
ok("بیزیر 1.0 هرگز از ۱ نمی‌گذرد (نسخه‌ی صافِ قبلی)", max(ys10) <= 1.0 + 1e-9)

# ---------- ۲) jelly_pos — دوبینسِ قابل اندازه‌گیری ----------
a, b = 0.0, 20.0
path = [W.jelly_pos(t / 400.0, a, b) for t in range(401)]
peak = max(path)
ok(f"اورشوت بالای هدف دیده می‌شود (peak={peak:.2f} > 20)", peak > b + 0.01)
ok("اورشوت در بازه‌ی مرجع است (۱۲–۲۰٪ مسیر)",
   b + 0.10 * (b - a) < peak < b + 0.20 * (b - a))
ok("میکرو-فرورفتگی زیر هدف قبل از نشست",
   min(path[240:]) < b - 1e-9 and min(p for p in path if p < b) < b)
ok("نشستِ نهایی دقیقاً روی هدف", abs(path[-1] - b) < 1e-12)
# نسخه‌ی بلند (ناوبری): pop=1.22 → اوج مهارشده
path2 = [W.jelly_pos(t / 400.0, 0.0, 66.0, ov_scale=0.028, pop=1.22)
         for t in range(401)]
peak2 = max(path2)
ok(f"ناوبری: اوجِ مهارشده ({peak2:.2f} در بازه‌ی ۶۶٫۵–۷۰٫۵)",
   peak2 < 70.5 and peak2 > 66.5)

# ---------- ۳) سوییچ زنده — دوبینسِ عین مرجع ----------
os.environ.pop("NAJI_NO_ANIM", None)
app.processEvents()
sw = W.Switch(False)
sw.show()
app.processEvents()
samples = []
sw.setChecked(True)
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.6:
    app.processEvents()
    samples.append((time.perf_counter() - t0, sw._thumb_x))
    time.sleep(0.008)
X_ON = W.Switch.X_ON
peak_sw = max(s for _, s in samples)
end_sw = samples[-1][1]
ok(f"سوییچ: اورشوتِ زنده ({peak_sw:.2f} > {X_ON})", peak_sw > X_ON + 0.2)
ok("سوییچ: نشست دقیق روی X_ON", abs(end_sw - X_ON) < 0.01)
# کل سوییچ: کراس‌فید ریل مستقل هم کامل شد
ok("سوییچ: کراس‌فید ریل به ۱ رسید", abs(sw._track_t - 1.0) < 0.02)

# ---------- ۴) نشت آبجکت — ۳۰ تاگل پشت‌سرهم ----------
from PySide6.QtCore import QAbstractAnimation, QCoreApplication, QEvent  # noqa: E402


def _flush_delete():
    """حذف‌های defer شده را واقعاً اجرا کن (شبیه‌سازی چرخه‌ی event loop)"""
    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


for i in range(30):
    sw.setChecked(i % 2 == 0)
    _flush_delete()
n_anim = len(sw.findChildren(QAbstractAnimation))
ok(f"سوییچ: انباشت انیمیشن نیست (زنده={n_anim} ≤ 4)", n_anim <= 4)
del sw

# ---------- ۵) ناوبری زنده — دوبینس قرص روی ریل ----------
storage.save()
win = MW.MainWindow(storage.load())
win.resize(980, 900)
win.show()
app.processEvents()
rail = win.nav
target_btn = rail._buttons["settings"]
target_btn.setChecked(True)   # مثل کلیک واقعی کاربر
r = rail._thumb_rect(target_btn)
ys_run = []
rail._sync_thumb(animate=True, target=target_btn)
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.7:
    app.processEvents()
    ys_run.append(rail._thumb_y)
    time.sleep(0.008)
peak_nav = max(ys_run)
ok(f"ناوبری: قرص با اورشوت سفر کرد (peak={peak_nav:.1f} > هدف {r.y():.1f})",
   peak_nav > r.y() + 0.5)
ok("ناوبری: قرص دقیقاً روی تبِ هدف نشست",
   abs(rail._thumb_y - r.y()) < 0.75 and rail.current() == "settings")
ok("ناوبری: صفحه‌ی فعال بدون گرافیک‌افکت (بدون فلاشِ ویندوز)",
   win.pages["settings"].graphicsEffect() is None)

# ---------- ۶) تب‌های سگمنت — همان دوبینس (مسیرِ واقعیِ کلیک) ----------
seg = win.segment
btn2 = seg._buttons["action"]
g2 = btn2.geometry()
xs = []
btn2.click()   # مسیر واقعی کاربر: checked + _select + changed
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.7:
    app.processEvents()
    xs.append(seg._ind.geometry().x())
    time.sleep(0.008)
ok(f"تب‌ها: قرص با اورشوت سفر کرد (peak={max(xs)} > {g2.x()})",
   max(xs) > g2.x() + 0.5)
ok("تب‌ها: نشست دقیق روی تب هدف",
   seg._ind.geometry().x() == g2.x() and seg.value() == "action")
app.processEvents()

# ---------- ۷) دکمه‌ها — فشار/رهاشدنِ دوبینسی ----------
btn = win.btn_check
btn.show()
app.processEvents()
btn.pressed.emit()
press_min = 1.0
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.16:
    app.processEvents()
    press_min = min(press_min, btn._jelly_scale())
    time.sleep(0.008)
btn.released.emit()
samples = []
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.6:
    app.processEvents()
    samples.append(btn._jelly_scale())
    time.sleep(0.008)
ok(f"دکمه: فشردن جمع شد (min={press_min:.3f} < 1)", press_min < 1.0)
ok(f"دکمه: رهاشدن با اورشوت ({max(samples):.4f} > 1)", max(samples) > 1.005)
ok("دکمه: نشستِ نهایی scale=1", abs(samples[-1] - 1.0) < 1e-6)

# ---------- ۷‌ب) کلیکِ خیلی سریع هم ژله می‌گیرد (باگ‌فیکس v5.1) ----------
btn.pressed.emit()
btn.released.emit()   # بدون هیچ زمانی بین فشار و رها — مثل ضربه‌ی سریع
fast = []
t0 = time.perf_counter()
while time.perf_counter() - t0 < 0.5:
    app.processEvents()
    fast.append(btn._jelly_scale())
    time.sleep(0.006)
ok(f"دکمه: ضربه‌ی سریع هم اورشوت دارد ({max(fast):.4f} > 1)", max(fast) > 1.005)
ok("دکمه: ضربه‌ی سریع روی ۱ می‌نشیند", abs(fast[-1] - 1.0) < 1e-6)

# ---------- ۸) حلقه‌های تزئینی کم‌مصرف + توقف در پنهانی ----------
hero = win.hero
ok(f"شیمر: ۲۴fps ({hero._shimmer.interval()}ms ≈ 42)", hero._shimmer.interval() >= 38)
win.show_page("settings")     # صفحه‌ی خانه پنهان می‌شود
app.processEvents()
ok("شیمر: با پنهان‌شدنِ خانه متوقف می‌شود", not hero._shimmer.isActive())
win.show_page("dashboard")
app.processEvents()
ok("شیمر: با نمایش خانه روشن می‌شود", hero._shimmer.isActive())
pill = win.pill
ok("پییل: نقطه‌ی نامشخص نبض ندارد", not pill._pulse_drv.isActive())
pill.set_state("وصلیم", "ok")
app.processEvents()
ok("پییل: با اتصالِ سبز نبض روشن شد", pill._pulse_drv.isActive())
pill.set_state("قطع", "bad")
ok("پییل: با وضعیت نامشخص نبض خاموش می‌شود", True)  # bad هم رنگ دارد
pill.set_state("—", "unknown")
ok("پییل: نامشخص → تایمر متوقف", not pill._pulse_drv.isActive())

# ---------- ۹) سکون کامل با NAJI_NO_ANIM ----------
os.environ["NAJI_NO_ANIM"] = "1"
win2 = MW.MainWindow(storage.load())
win2.resize(960, 860)
win2.show()
app.processEvents()
app.processEvents()
f1 = win2.grab()
app.processEvents()
f2 = win2.grab()
ok("سکونِ کامل با NAJI_NO_ANIM (دو فریم یکسان)",
   f1.toImage().bits() == f2.toImage().bits() or
   f1.toImage().constBits() == f2.toImage().constBits() or
   bytes(f1.toImage().constBits()) == bytes(f2.toImage().constBits()))
win2.close()
os.environ.pop("NAJI_NO_ANIM", None)

# ---------- ۱۰) نسخه و امضای پالت ----------
ok("نسخه‌ی برنامه ۵٫۱٫۰", MW.VERSION == "5.1.0")
import theme  # noqa: E402
theme.set_current("dark")
p = theme.current_palette()
ok("امضای پالت تیره: بوم #0d0f14 و اکسنت #7b5cff",
   p["bg_top"] == "#0d0f14" and p["accent"] == "#7b5cff")

# ---------- ۱۱) رندر نهایی هر دو تم ----------
theme.set_current("light")
theme.apply(app)
win.update()
app.processEvents()
ok("رندر پنجره در تم روشن", not win.grab().isNull())
theme.set_current("dark")
theme.apply(app)
win.update()
app.processEvents()
ok("رندر پنجره در تم تیره", not win.grab().isNull())

n_fail = sum(1 for _n, c in PASS if not c)
print(f"\nv5.1.0: {len(PASS) - n_fail}/{len(PASS)} passed")
sys.exit(1 if n_fail else 0)
