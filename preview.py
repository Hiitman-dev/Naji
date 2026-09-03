# preview.py — پیش‌نمایش بصری با داده‌ی قلابی (برای تست طراحی، بدون لاگین)
# اجرا:  python preview.py          → پنجره اصلی با داده قلابی
#        python preview.py --dark   → تم تیره
#        python preview.py --warn   → پنجره هشدار
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jdatetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import storage
import theme
from main_window import MainWindow
from util import jalali_plus, jalali_today

args = sys.argv[1:]
theme_name = "dark" if "--dark" in args else "light"

app = QApplication(sys.argv)
app.setLayoutDirection(Qt.RightToLeft)
app.setStyle("Fusion")
theme.load_fonts()
theme.set_current(theme_name)
theme.apply(app)
app.setFont(theme.app_font(10))

settings = storage.load()
w = MainWindow(settings)
w.update_identity()
w.set_connection("متصل (مسیر پیش‌فرض)", True)

today = jdatetime.date.today()
fake_occurred = {"outage_date": today.strftime("%Y/%m/%d"), "outage_start_time": "08:30",
                 "outage_stop_time": "09:15", "outage_address": "خیابان آزادی، نبش کوچه مهر"}
fake_planned_today = {"outage_date": today.strftime("%Y/%m/%d"), "outage_start_time": "18:00",
                      "outage_stop_time": "19:30", "outage_address": "بلوار امام، فاز ۲ صنعتی"}
future = (today + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")
fake_planned = {"outage_date": future, "outage_start_time": "10:30",
                "outage_stop_time": "12:00", "outage_address": "شهرک صنعتی، خیابان ۱۶ متری دوم"}

w.update_snapshot({
    "occurred": [fake_occurred],
    "planned": [fake_planned_today, fake_planned],
    "checked_at": "12:34:56",
    "from": jalali_today(),
    "to": jalali_plus(5),
})
w.show()

if "--warn" in args:
    from datetime import datetime, timedelta
    from warn_dialog import WarnDialog
    # زمان آینده + dry_run: پیش‌نمایش هیچ‌وقت عملیات واقعی اجرا نمی‌کند
    start = datetime.now() + timedelta(minutes=6, seconds=40)
    stop = start + timedelta(hours=2)
    fake_warn = {
        "outage_date": (jdatetime.date.today() + jdatetime.timedelta(days=0)).strftime("%Y/%m/%d"),
        "outage_start_time": start.strftime("%H:%M"),
        "outage_stop_time": stop.strftime("%H:%M"),
        "outage_address": "خیابان ولیعصر، بالاتر از پارک ساعی",
    }
    wd = WarnDialog(fake_warn, "shutdown", dry_run=True)
    wd.show()

sys.exit(app.exec())
