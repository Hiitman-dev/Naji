# test_smoke.py — تست دود: بدون نیاز به لاگین واقعی
# اجرا: python test_smoke.py
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_ok = True


def check(name, cond):
    global _ok
    print(("PASS  " if cond else "FAIL  ") + name)
    _ok = _ok and bool(cond)


# ---------- util ----------
from util import (  # noqa: E402
    fmt_outage_line, jalali_plus, jalali_today, outage_datetime,
    outage_key, parse_jalali_date, parse_time, to_latin_digits,
)

check("ارقام فارسی → لاتین", to_latin_digits("۱۴۰۴/۰۶/۰۷") == "1404/06/07")
check("تاریخ شمسی با خط تیره", parse_jalali_date("۱۴۰۴-۶-۷") == (1404, 6, 7))
check("رد تاریخ نامعتبر", parse_jalali_date("1404/13/01") is None)
check("پارس ساعت", parse_time("۱۰:۳۰:۰۰") == (10, 30))
check("رد ساعت نامعتبر", parse_time("25:00") is None)

fake = {"outage_date": "1404/06/07", "outage_start_time": "10:30",
        "outage_stop_time": "12:00", "outage_address": "خیابان آزادی"}
dt = outage_datetime(fake)
check("تبدیل خاموشی به datetime", dt is not None and dt.hour == 10 and dt.minute == 30)
check("کلید یکتای خاموشی (v4: با برچسب قبض)", outage_key(fake).endswith("1404/06/07|10:30|12:00|خیابان آزادی"))
check("کلید چند-قبضی متمایز است",
      outage_key({**fake, "_bill": "111"}) != outage_key({**fake, "_bill": "222"}))
check("امروز شمسی", jalali_today().count("/") == 2 and jalali_plus(5) > jalali_today())

# ---------- storage / DPAPI ----------
import storage  # noqa: E402

settings = storage.load()
from storage import DEFAULTS  # noqa: E402
check("لود تنظیمات (همه کلیدها موجود)", all(k in settings for k in DEFAULTS))
check("مقادیر ذخیره‌شده معتبرند",
      settings["mode"] in ("notify", "notify_action", "action")
      and settings["default_action"] in ("shutdown", "sleep", "hibernate")
      and 1 <= int(settings["lead_minutes"]) <= 120
      and 1 <= int(settings["poll_minutes"]) <= 240)
enc = storage.dpapi_protect("token-secret-۱۲۳".encode("utf-8"))
check("DPAPI protect/unprotect", storage.dpapi_unprotect(enc).decode("utf-8") == "token-secret-۱۲۳")
storage.set_token("abc")
check("توکن ذخیره/بازیابی شد", storage.get_token() == "abc")
storage.reset_session()
check("خروج از حساب توکن را پاک می‌کند", storage.get_token() == "")

# ---------- api: مسیریابی هوشمند (تست زنده شبکه) ----------
import api  # noqa: E402

print("کارت‌های شبکه:", api.local_ipv4_candidates())
try:
    api.ensure_route()
    print("مسیر فعال:", api.active_source())
    check("مسیر سالم به برق‌من پیدا شد", True)
except api.VpnBlocked as e:
    print("بلاک (VPN):", str(e)[:70].replace("\n", " "))
    check("مسیر سالم به برق‌من پیدا شد", False)

# ---------- UI (آفسکرین) ----------
import jdatetime  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
from login_dialog import LoginDialog  # noqa: E402
from main_window import MainWindow  # noqa: E402
from warn_dialog import WarnDialog  # noqa: E402

settings = storage.load()
w = MainWindow(settings)
w.update_identity()
future = (jdatetime.date.today() + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")
snap = {"occurred": [fake], "planned": [{**fake, "outage_date": future}],
        "checked_at": "12:00:00", "from": jalali_today(), "to": jalali_plus(5)}
w.update_snapshot(snap)
check("پنجره اصلی + کارت خاموشی‌ها", w.outage_list.count() == 2)

dlg = LoginDialog()
check("دیالوگ ورود (۳ گام + راهنمای قبض ثبت‌نشده)", dlg is not None and dlg.stack.count() == 4)

future_dt_ok = outage_datetime({**fake, "outage_date": future}) is not None
# v4.4.4+ — حلقه، ثانیه‌های «تایمر اعلان» کاربر را می‌شمارد (پیش‌فرض ۱۵ث)
wd = WarnDialog({**fake, "outage_date": future}, "shutdown") if future_dt_ok else None
_count = wd.ring.count.text() if wd else ""
check("پنجره هشدار + حلقه شمارش ثانیه‌ای تایمر اعلان",
      wd is not None and _count and any(ch.isdigit() for ch in _count) and ":" not in _count)

# رگرسیون ایمنی (به‌روزِ v4.4.4+): ساخت پنجره‌ی هشدار برای خاموشیِ گذشته
# «همین لحظه» هیچ اقدام قدرت اجرا نمی‌کند — تایمر اعلان فقط بعد از تمام‌شدن
# ثانیه‌ها (که این‌جا هنوز نرسیده) اقدام می‌دهد؛ و تضمین سطح کنترلر این است
# که چرخ هشدار برای گذشته اصلاً پنجره نمی‌سازد (مسیر late فقط خبر است —
# تست‌های test_v446 این را پوشش می‌دهند)
import power as power_mod  # noqa: E402
fired = {"n": 0}
def _fired(*a, **k):  # noqa: E306
    fired["n"] += 1
power_mod.shutdown = _fired
power_mod.sleep_now = _fired
power_mod.hibernate_now = _fired
yesterday = (jdatetime.date.today() - jdatetime.timedelta(days=1)).strftime("%Y/%m/%d")
wd_past = WarnDialog({**fake, "outage_date": yesterday, "outage_start_time": "23:59"}, "shutdown")
check("هشدار برای خاموشیِ گذشته همان لحظه اقدامی انجام نمی‌دهد",
      fired["n"] == 0 and wd_past.executed is None
      and any(ch.isdigit() for ch in wd_past.ring.count.text()))

# تم
import theme  # noqa: E402
theme.load_fonts()
print("فونت فعال:", theme.FONT_BODY, "| نمایشی:", theme.FONT_DISPLAY)
check("QSS تم ساخته شد", len(theme.build_qss(theme.PALETTES["dark"])) > 1000)

print()
print("SMOKE", "OK ✅" if _ok else "FAILED ❌")
sys.exit(0 if _ok else 1)
