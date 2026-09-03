# screenshot.py — اسکرین‌شات از هر سه پنجره، در هر دو تم
# خروجی: light_main.png, dark_main.png, light_warn.png, dark_warn.png, light_login.png
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jdatetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

import storage
import theme
from login_dialog import LoginDialog
from main_window import MainWindow
from util import jalali_plus, jalali_today
from warn_dialog import WarnDialog


def shot(widget, path: str):
    pm = widget.grab()
    ok = pm.save(path, "PNG")
    print(f"  saved: {path} ({pm.width()}x{pm.height()}) — ok={ok}")


def make_window():
    s = storage.load()
    w = MainWindow(s)
    w.update_identity()
    w.set_connection("متصل (مسیر پیش‌فرض)", True)
    today = jdatetime.date.today()
    occurred = {"outage_date": today.strftime("%Y/%m/%d"), "outage_start_time": "08:30",
                "outage_stop_time": "09:15", "outage_address": "خیابان آزادی، نبش کوچه مهر"}
    pl_today = {"outage_date": today.strftime("%Y/%m/%d"), "outage_start_time": "18:00",
                "outage_stop_time": "19:30", "outage_address": "بلوار امام، فاز ۲ صنعتی"}
    future = (today + jdatetime.timedelta(days=2)).strftime("%Y/%m/%d")
    pl_future = {"outage_date": future, "outage_start_time": "10:30",
                 "outage_stop_time": "12:00", "outage_address": "شهرک صنعتی، خیابان ۱۶ متری دوم"}
    w.update_snapshot({
        "occurred": [occurred],
        "planned": [pl_today, pl_future],
        "checked_at": "12:34:56",
        "from": jalali_today(),
        "to": jalali_plus(5),
    })
    w.resize(720, 800)
    w.show()
    return w, pl_today


def make_warn(outage):
    # dry_run=True: در پیش‌نمایش/اسکرین‌شات هرگز عملیات واقعی قدرت اجرا نمی‌شود
    wd = WarnDialog(outage, "shutdown", dry_run=True)
    wd.resize(540, 480)
    wd.show()
    return wd


def make_login():
    ld = LoginDialog()
    ld.resize(500, 480)
    ld.show()
    return ld


def run(name: str, build):
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")
    theme.load_fonts()
    theme.set_current(name)
    theme.apply(app)
    app.setFont(theme.app_font(10))
    w = build()
    app.processEvents()
    QTimer.singleShot(200, lambda: (shot(w, f"{name}_{tag}.png"), app.quit()))
    return app.exec()


if __name__ == "__main__":
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else "main"
    name = sys.argv[2] if len(sys.argv) > 2 else "light"

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")
    theme.load_fonts()
    theme.set_current(name)
    theme.apply(app)
    app.setFont(theme.app_font(10))

    s = storage.load()
    if tag == "main":
        w, pl_today = make_window()
    elif tag == "warn":
        from datetime import datetime, timedelta
        # زمان آینده (همیشه امن) — هرگز زمان گذشته برای پنجره‌ی هشدار
        start = datetime.now() + timedelta(minutes=6, seconds=40)
        stop = start + timedelta(hours=2)
        w = make_warn({"outage_date": jdatetime.date.today().strftime("%Y/%m/%d"),
                       "outage_start_time": start.strftime("%H:%M"),
                       "outage_stop_time": stop.strftime("%H:%M"),
                       "outage_address": "خیابان ولیعصر، بالاتر از پارک ساعی"})
    elif tag == "login":
        w = make_login()
    else:
        print("tag: main|warn|login"); sys.exit(1)

    QTimer.singleShot(200, lambda: (shot(w, f"{name}_{tag}.png"), app.quit()))
    sys.exit(app.exec())
