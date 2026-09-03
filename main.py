# main.py — نقطه‌ی ورود «ناجی» v4
# تری سیستم + پولر چند-قبضی پس‌زمینه + منطق هشدار + اجرای عملیات قدرت
# + تک‌نمونه بودن برنامه (کلیک دوباره روی exe فقط پنجره‌ی موجود را می‌آورد)
# + هماهنگی زنده با رنگ و تم ویندوز
import os
import sys
import threading
from datetime import datetime

from PySide6.QtCore import QObject, QPoint, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap, QPolygon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication, QMenu, QMessageBox, QSystemTrayIcon,
)

import api
import crash
import i18n
import onboarding
import overlay as overlay_mod
import power
import sounds
import storage
import theme
import updater
import wininfo
from login_dialog import LoginDialog
from main_window import MainWindow, _FetchTask
from util import (debug_note, jalali_plus, jalali_today, num,
                  outage_datetime, outage_key, outage_summary)
from warn_dialog import ACTION_KEY_NAMES, WarnDialog

APP_TITLE = "ناجی"

# ---------- تک‌نمونه ----------

_SINGLE_KEY = "Naji-SingleInstance-7f3c2b91"


class SingleInstance:
    """قفل تک‌نمونه با QLocalServer:
    • نمونه‌ی اول: سرور را بالا می‌آورد و سیگنال «show» می‌شنود
    • نمونه‌های بعدی: پیام show را می‌فرستند و بلافاصله خارج می‌شوند —
      یعنی دوبار کلیک روی exe دیگر ناجیِ تازه نمی‌سازد"""

    def __init__(self):
        self.server = None
        self._socket = None

    def try_become_primary(self, on_show) -> bool:
        # باگ v4.0: اول removeServer صدا زده می‌شد و سوکتِ نمونه‌ی زنده را
        # می‌پاک کرد → probe شکست می‌خورد و نمونه‌ی دوم هم primary می‌شد!
        # ترتیب درست: اول probe؛ فقط اگر هیچ نمونه‌ی زنده‌ای نبود، پاکسازی+گوش.
        probe = QLocalSocket()
        probe.connectToServer(_SINGLE_KEY)
        if probe.waitForConnected(300):
            probe.write(b"show\n")
            probe.flush()
            probe.waitForBytesWritten(300)
            probe.disconnectFromServer()
            return False
        probe.abort()
        # بقایای ناجیِ کرش‌کرده پاک شود (سوکت یتیم بدون سرور زنده)
        try:
            QLocalServer.removeServer(_SINGLE_KEY)
        except Exception:
            pass
        self.server = QLocalServer()
        self.server.listen(_SINGLE_KEY)
        self.server.newConnection.connect(self._on_conn)
        self._on_show = on_show
        return True

    def _on_conn(self):
        while self.server.hasPendingConnections():
            sock = self.server.nextPendingConnection()
            if sock:
                sock.readyRead.connect(self._on_read)
                self._socket = sock  # نگه‌داشتن مرجع

    def _on_read(self):
        data = bytes(self._socket.readAll()) if self._socket else b""
        if b"show" in data:
            try:
                self._on_show()
            except Exception:
                pass


def make_icon() -> QIcon:
    """آیکون برنامه — از فایل باندل‌شده؛ در نبود آن رسم برق‌گیری"""
    ico_path = os.path.join(theme.asset_dir(), "icon.ico")
    if os.path.exists(ico_path):
        return QIcon(ico_path)
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#0f172a"))
    p.drawEllipse(1, 1, 62, 62)  # v4.4.7: قرص گرد — هماهنگ با کاشی‌های درون برنامه
    p.setBrush(QColor("#f59e0b"))
    p.drawPolygon(QPolygon([
        QPoint(37, 8), QPoint(17, 36), QPoint(30, 36),
        QPoint(25, 57), QPoint(47, 27), QPoint(34, 27),
    ]))
    p.end()
    return QIcon(pm)


class Poller(QThread):
    """بررسی دوره‌ای خاموشی‌ها در پس‌زمینه (خارج از رشته‌ی رابط کاربری).
    v4: همه‌ی قبض‌های تحت پایش در هر چرخه خوانده می‌شوند و خروجی،
    لیست تلفیقی خاموشی‌ها با برچسب قبض است.
    نکته‌ی لگ: stop() دیگر در رشته‌ی گرافیکی wait نمی‌کند؛ تا آخرین
    درخواستِ در جریان، ناجی زنده می‌ماند و UI هرگز فریز نمی‌شود.
    v6.0: failed حالا «نوع» خطا هم می‌فرستد (net/timeout/saapa/vpn/auth)
    تا رابط کاربری بداند مقصر کیست — برق‌من یا اتصال خودمان."""

    got_snapshot = Signal(object)
    failed = Signal(object)
    blocked = Signal()
    auth_expired = Signal()

    def __init__(self, token: str, bills: list, interval_min: int):
        super().__init__()
        self.token = token
        self.bills = [b for b in (bills or []) if b.get("bill_id")]
        self.interval_min = max(1, int(interval_min))
        self._stop = threading.Event()
        self._wake = threading.Event()

    def run(self):
        while not self._stop.is_set():
            self._poll()
            self._wake.wait(self.interval_min * 60)  # بیدارباش زودهنگام با wake()
            self._wake.clear()

    def _poll(self):
        if not self.bills:
            return
        multi = len(self.bills) > 1
        planned_all, occurred_all, per_bill = [], [], {}
        for b in self.bills:
            try:
                snap = api.get_blackouts(self.token, b["bill_id"])
            except api.AuthExpired:
                self.auth_expired.emit()
                return
            except api.VpnBlocked:
                self.blocked.emit()
                return
            except api.ApiError as e:
                # v6.0 — خطای نوع‌دار: net/timeout/saapa برای بنر وضعیت سرویس
                self.failed.emit({"kind": getattr(e, "kind", "net"),
                                  "msg": str(e)})
                return
            except Exception as e:
                self.failed.emit({"kind": "net", "msg": str(e)})
                return
            title = b.get("bill_title", "")
            per_bill[b["bill_id"]] = {
                "title": title,
                "planned": len(snap.get("planned") or []),
                "occurred": len(snap.get("occurred") or []),
            }
            for o in snap.get("planned") or []:
                o = dict(o)
                o["_bill"] = b["bill_id"]
                o["_bill_title"] = title
                planned_all.append(o)
            for o in snap.get("occurred") or []:
                o = dict(o)
                o["_bill"] = b["bill_id"]
                o["_bill_title"] = title
                occurred_all.append(o)
        snap = {
            "occurred": occurred_all,
            "planned": planned_all,
            "per_bill": per_bill,
            "multi_bills": multi,
        }
        snap["checked_at"] = datetime.now().strftime("%H:%M:%S")
        snap["from"] = jalali_today()
        snap["to"] = jalali_plus(5)
        self.got_snapshot.emit(snap)

    def wake(self):
        self._wake.set()

    def stop(self, wait_ms: int = 0):
        """درخواست توقف؛ بدون بلاک‌کردن رشته‌ی فراخوان (رفع لگ)"""
        self._stop.set()
        self._wake.set()
        if wait_ms > 0:
            self.wait(wait_ms)


class Controller(QObject):
    """هماهنگ‌کننده: پنجره، تری، پولر، هشدارها و عملیات قدرت"""

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._quit_requested = False
        self.settings = storage.load()
        self.icon = make_icon()
        self.window = MainWindow(self.settings)
        self._wire_window()
        self.tray = QSystemTrayIcon(self.icon)
        self.poller = None
        self.overlay = None            # ویجت شناور (v6.0)
        self._retired_pollers = []  # پولرهای در حال توقف — تا پایان run() مرجع نگه داشته می‌شود
        self.warn_queue = []
        self.dialog = None
        self._last_blocked_toast = 0.0
        self._last_planned = []  # آخرین لیست خاموشی‌های برنامه‌ریزی‌شده (برای چک زمان‌بندی مستقل از پول)
        self._health = []              # v6.0 — سلامت ۸ بررسیِ اخیر (True/False/None)
        # v4.4.6 — «مسلح‌بودن» با پیش‌آگاهیِ فعلی؛ تغییر این عدد یعنی re-arm
        self._armed_lead = max(1, int(self.settings.get("lead_minutes", 10)))
        self._wake_sig = None  # امضای (lead, poll) آخرین wake پولر

        # چک‌کننده‌ی هشدار: هر ۲۰ ثانیه، صرف‌نظر از بازه‌ی بررسیِ کاربر.
        self.warn_timer = QTimer(self)
        self.warn_timer.setInterval(20_000)
        self.warn_timer.timeout.connect(self._check_warnings)
        self.warn_timer.start()

        # پایش تغییر رنگ/تم ویندوز — هر ۵ ثانیه یک نگاه سبک به رجیستری
        self.win_watch = QTimer(self)
        self.win_watch.setInterval(5_000)
        self.win_watch.timeout.connect(self._on_windows_look_changed)
        self.win_watch.start()

        # v4.4.5 — واکنش فوری: خود کوانت (Qt ۶٫۵+) وقتی تم سیستم عوض شود
        # سیگنال می‌دهد؛ چرخ ۵ ثانیه‌ای هم به‌عنوان پشتوانه می‌ماند
        try:
            self.app.styleHints().colorSchemeChanged.connect(
                self._on_windows_look_changed)
        except Exception:
            pass

        # نگهبان «در حال بررسی» — اگر ۹۰ ثانیه بعد از «بررسی الان» هیچ
        # پاسخی نرسید، چیپ قفل نماند و حالت خطای نرم نشان بدهد
        self._checking_since = None
        self.check_guard = QTimer(self)
        self.check_guard.setSingleShot(True)
        self.check_guard.setInterval(90_000)
        self.check_guard.timeout.connect(self._on_check_timeout)

        self._build_tray()
        self.window.update_identity()

    # ---------- سیم‌کشی پنجره (بازسازی‌پذیر برای تعویض زبان) ----------

    def _wire_window(self):
        self.window.check_now.connect(self._check_now)
        self.window.logout_requested.connect(self._logout)
        self.window.settings_changed.connect(self._on_settings_changed)
        self.window.theme_mode_changed.connect(self._on_theme_mode_changed)
        self.window.lang_changed.connect(self._on_lang_changed)
        self.window.sync_windows_changed.connect(self._on_sync_windows)
        self.window.bills_changed.connect(self._on_bills_changed)
        self.window.active_bill_changed.connect(self._on_active_bill)
        # v6.0 — سوییچ ویجت شناور + دکمه‌ی بررسیِ نسخه‌ی جدید
        self.window.overlay_toggled.connect(self._on_overlay_toggled)
        self.window.check_updates_requested.connect(self._check_updates_manual)

    def _rebuild_window(self):
        """تعویض زبان: کل پنجره با متن‌های تازه ساخته می‌شود —
        تمیزترین راه برای RTL/LTR شدنِ چیدمان بدون ریسکِ باقی‌ماندن متن"""
        geo = self.window.saveGeometry()
        try:
            page = self.window.nav.current()
        except Exception:
            page = "dashboard"
        old = self.window
        old.deleteLater()
        self.window = MainWindow(storage.load())
        self._wire_window()
        self.window.update_identity()
        snap = getattr(self, "_last_snap", None)
        if snap:
            self.window.update_snapshot(snap)
        try:
            self.window.restoreGeometry(geo)
        except Exception:
            pass
        self.window.show()
        self.window.show_page(page)

    # ---------- تری سیستم ----------

    def _build_tray(self):
        menu = QMenu()
        self._tray_menu = menu  # نگه‌داشتن مرجع
        a_show = QAction(i18n.t("tray.show"), menu)
        a_show.triggered.connect(self._show_window)
        a_check = QAction(i18n.t("tray.check_now"), menu)
        a_check.triggered.connect(self._check_now)
        a_cancel = QAction(i18n.t("tray.cancel_shutdown"), menu)
        a_cancel.triggered.connect(self._cancel_shutdown)
        # v6.0 — ویجت شناور از تری هم قابل روشن/خاموش است
        self.a_widget = QAction(self._widget_action_text(), menu)
        self.a_widget.triggered.connect(self._toggle_overlay_from_tray)
        a_login = QAction(i18n.t("tray.logout"), menu)
        a_login.triggered.connect(self._logout)
        a_quit = QAction(i18n.t("tray.quit"), menu)
        a_quit.triggered.connect(self.quit)
        for a in (a_show, a_check, a_cancel):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(self.a_widget)
        menu.addSeparator()
        menu.addAction(a_login)
        menu.addAction(a_quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip(APP_TITLE)
        self.tray.activated.connect(self._on_tray_activated)

    def _widget_action_text(self) -> str:
        on = bool(self.settings.get("overlay_enabled", False))
        return i18n.t("tray.widget_hide") if on else i18n.t("tray.widget_show")

    def _retranslate_tray(self):
        self._build_tray()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_window()

    def _show_window(self):
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def _toast(self, title: str, body: str, icon=None, msecs: int = 12000):
        self.tray.showMessage(title, body, icon or QSystemTrayIcon.Information, msecs)

    def _check_now(self):
        if not self.poller:
            # پولر مرده/خارج‌شده؟ اگر لاگین هستیم دوباره راه بیفتد وگرنه کاری نکن
            if self._logged_in():
                self._start_poller()
            else:
                return
        self.window.set_connection(i18n.t("conn.checking"), None)
        self._checking_since = datetime.now()
        self.check_guard.start()
        self.poller.wake()

    def _on_check_timeout(self):
        """قفل‌شکن چیپ وضعیت — هیچ پاسخی بعد از ۹۰ ثانیه نرسیده"""
        if self._checking_since is None:
            return
        self._checking_since = None
        self.window.set_connection(i18n.t("conn.check_timeout"), None)

    def _mark_check_done(self):
        """پایان هر نتیجه‌ی بررسی (موفق/خطا) — نگهبان را خلع سلاح می‌کند"""
        self._checking_since = None
        try:
            self.check_guard.stop()
        except Exception:
            pass

    def _cancel_shutdown(self):
        ok = power.cancel_shutdown()
        if ok:
            self._toast(i18n.t("tray.cancel_ok_title"), i18n.t("tray.cancel_ok_body"))
        else:
            self._toast(i18n.t("tray.cancel_ok_title"), i18n.t("tray.cancel_none"))

    # ---------- اجرا و ورود ----------

    def run(self):
        # باگ «اعلان نیومد»: قبلاً کلیدهای warn: روی دیسک باقی می‌ماندند و
        # اگر همان خاموشی یک‌بار هشدار خورده بود (اجرای قبلی/پیش‌آگاهی قبلی)،
        # تنظیمِ تازه‌ی «۱۲ دقیقه قبل» بی‌صدا بلعیده می‌شد. dedupe حالا
        # فقط در همین اجرا معتبر است — هشدارِ تکراری بهتر از سکوت است.
        storage.clear_warned()
        if self._logged_in():
            self._start()
        else:
            self.window.show()
            if not self._login():
                self.quit()
                return
        # انتظار برای اتمام برنامه در app.exec()

    def _logged_in(self) -> bool:
        return bool(storage.get_token() and storage.bills())

    def _login(self) -> bool:
        dlg = LoginDialog(self.window)
        if dlg.exec():
            self.window.update_identity()
            self.window.show()
            self._start()
            return True
        return False

    def _start(self):
        self._start_poller()
        self.tray.show()
        # v6.0 — آنبوردینگ سه‌مرحله‌ای فقط یک‌بار در عمر حساب
        if not self.settings.get("onboarded", False):
            self._run_onboarding()
        # v6.0 — ویجت شناور اگر فعال باشد همین حالا بیاید بالا
        self._sync_overlay()
        # v6.0 — چک خودکار نسخه‌ی جدید (با تاخیر، بعد از آرام‌شدن استارت)
        QTimer.singleShot(9000, self._check_updates_silent)

    def _run_onboarding(self):
        try:
            dlg = onboarding.OnboardingDialog(self.settings, self.window)
            dlg.exec()
            self.settings["onboarded"] = True
            storage.save()
            # تنظیمات انتخابی کاربر در ویزارد همان لحظه مسلح شود
            self._armed_lead = max(1, int(self.settings.get("lead_minutes", 10)))
            try:
                self._check_warnings()
            except Exception:
                pass
        except Exception as e:
            debug_note(f"onboarding-skip: {e}")

    def _start_poller(self):
        self._stop_poller()
        self.poller = Poller(
            storage.get_token(),
            storage.bills(),
            int(self.settings.get("poll_minutes", 5)),
        )
        self.poller.got_snapshot.connect(self._on_snapshot)
        self.poller.failed.connect(self._on_failed)
        self.poller.blocked.connect(self._on_blocked)
        self.poller.auth_expired.connect(self._on_auth_expired)
        self.poller.start()
        # اولین چرخه همین لحظه شروع می‌شود — چیپ همین حالا صادق باشد
        if storage.bills():
            self.window.set_connection(i18n.t("conn.checking"), None)
            self._checking_since = datetime.now()
            self.check_guard.start()

    def _stop_poller(self):
        p = self.poller
        self.poller = None
        if not p:
            return
        p.stop()  # بدون wait — UI هرگز برای توقف ترد بلاک نمی‌شود
        if p.isRunning():
            self._retired_pollers.append(p)
            p.finished.connect(self._poller_retired)

    def _poller_retired(self):
        sender = self.sender()
        if sender in self._retired_pollers:
            self._retired_pollers.remove(sender)
        sender.deleteLater()

    # ---------- اسنپ‌شات و منطق هشدار ----------

    def _on_snapshot(self, snap: dict):
        self._last_snap = snap
        self._mark_check_done()
        self._record_health(True)
        self.window.hide_service_banner()
        # اول چیپ اتصال — اگر هر بخش دیگر خطا بدهد، وضعیت «در حال بررسی»
        # هرگز قفل نماند (باگ v4.2: ValueError قبل از set_connection)
        try:
            kind, detail = api.active_source()
            if kind == "default":
                conn_text = i18n.t("conn.connected", src=i18n.t("conn.default_route"))
            else:
                conn_text = i18n.t("conn.connected", src=i18n.t("conn.nic_route", nic=detail))
            self.window.set_connection(conn_text, True)
        except Exception:
            pass
        # v6.0 — ثبت تاریخچه‌ی قطعی‌ها (رخ‌داده‌های امروزِ هر قبض)
        try:
            per_bill = {}
            for o in snap.get("occurred") or []:
                bid = str(o.get("_bill") or "")
                if bid:
                    per_bill.setdefault(bid, []).append(o)
            for bid, items in per_bill.items():
                storage.record_bill_history(bid, items)
        except Exception as e:
            debug_note(f"history-record-fail: {e}")
        try:
            self.window.update_snapshot(snap)
        except Exception as e:
            debug_note(f"snapshot-ui-fail: {e}")
        # v6.0 — ویجت شناور هم همگام بماند
        if self.overlay is not None:
            try:
                self._feed_overlay(snap)
                self.overlay.set_level(True)
            except Exception:
                pass

        planned = snap.get("planned") or []
        keys = [outage_key(o) for o in planned]
        known = set(self.settings.get("known_keys") or [])
        self.settings["known_keys"] = keys[-100:]
        storage.save()

        # اعلان «خاموشی جدید» فقط برای مواردی که تازه اضافه شده‌اند
        if known:
            new_items = [o for o in planned if outage_key(o) not in known]
            if new_items:
                lines = "\n".join(outage_summary(o) for o in new_items[:3])
                more = "\n" + i18n.t("tray.more", n=num(len(new_items) - 3)) \
                    if len(new_items) > 3 else ""
                self._toast(i18n.t("tray.new_outage"), lines + more)

        # چک لحظه‌ی هشدار مستقل و مکرر (هر ۲۰ ثانیه) روی همین لیست انجام می‌شود
        self._last_planned = planned
        try:
            self._check_warnings()
        except Exception:
            pass

    # خاموشی‌ای که تازه شروع شده — این‌قدر دقیقه بعد از شروع هنوز «دیر نیست»
    # و خبرِ فوریِ «قطعی شروع شد» می‌دهد (بدون هیچ اقدام سیستمی)
    LATE_GRACE_MIN = 15.0

    def _check_warnings(self):
        """هشدار خودکار: مستقل از بازه‌ی بررسیِ سرور، هر ۲۰ ثانیه زمان‌های
        خاموشی با ساعت سیستم سنجیده می‌شود و به همان تعداد دقیقه‌ای که
        کاربر در تنظیمات ثبت کرده (lead_minutes)، قبل از شروع هر خاموشی
        یک‌بار خبر داده می‌شود.
        v4.4.6 — سه ترمیم برای «ست کردم ولی واکنش نداد»:
        • پارس بی‌سخت‌گیری تاریخ/ساعت (در util) — دیگر هیچ رکوردی بی‌صدا
          رد نمی‌شود؛ شکست پارس هم در debug.log ثبت می‌شود
        • خاموشی‌ای که به هر دلیل (پول ۶۰ دقیقه‌ایِ کش‌شده، تغییر ساعت
          ویندوز) دیر دیده شود و تازه شروع شده باشد → خبر فوری «شروع شد»
        • هر شلیک/رد شدن قابل ردیابی در debug.log است"""
        now = datetime.now()
        lead = float(max(1, int(self.settings.get("lead_minutes", 10))))
        for o in self._last_planned:
            start = outage_datetime(o)
            if start is None:
                # خود outage_datetime امضای رکورد را در debug.log نوشت
                continue
            mins = (start - now).total_seconds() / 60.0
            key = "warn:" + outage_key(o)
            if -self.LATE_GRACE_MIN <= mins <= 0:
                # تازه شروع شده (یا ساعت سیستم چند ثانیه جلوتر است) —
                # خبرِ فوری، بدون اقدام خودکار (اقدامِ دیر خطرناک است)
                if not storage.is_warned(key) \
                        and not storage.is_warned("late:" + outage_key(o)):
                    storage.add_warned("late:" + outage_key(o))
                    debug_note(f"warn-late mins={mins:.1f} key={outage_key(o)}")
                    self._dispatch_late(o)
                continue
            if mins <= 0 or mins > lead:
                continue
            if storage.is_warned(key):
                continue
            storage.add_warned(key)
            debug_note(f"warn-fire lead={lead:g} mins={mins:.1f} key={outage_key(o)}")
            self._dispatch_warning(o, mins)

    def _dispatch_late(self, outage: dict):
        """خاموشی‌ای که تازه شروع شده و هشدارِ پیش‌آگاهش دیده نشده —
        فقط خبر فوری + ردپا؛ هیچ اقدام سیستمی (خاموش/خواب) اجرا نمی‌شود"""
        try:
            storage.set_last_warn({
                "at": datetime.now().strftime("%H:%M"),
                "summary": outage_summary(outage),
            })
            self.window.update_last_warn()
        except Exception:
            pass
        # v6.0 — طرح صدای انتخابی کاربر (با احترام به بی‌صدایی موقت)
        sounds.play(self.settings.get("sound_scheme", "system"), self.settings)
        self._toast(
            i18n.t("tray.late_title"),
            i18n.t("tray.late_body", summary=outage_summary(outage)),
            QSystemTrayIcon.Warning,
        )
        try:
            QApplication.alert(self.window)
        except Exception:
            pass

    def _dispatch_warning(self, outage: dict, mins: float):
        """مطابق انتخاب کاربر: فقط نوتیف / نوتیف+عمل / فقط عمل"""
        mode = self.settings.get("mode", "notify_action")
        # گرد کردن به‌جای خرد کردن: کاربر ۱۲ تنظیم کرده، توست هم بگوید ۱۲
        when = f"{num(max(1, round(mins)))} {i18n.t('dash.minutes')}"

        # ردپای هشدار در کارت تنظیمات — حتی اگر توست ویندوز دیده نشود،
        # کاربر می‌بیند که هشدار واقعاً شلیک شده (تفکیک «شلیک نشد» از
        # «ویندوز نشان نداد» — فوکوس‌اسست و تنظیمات نوتیفیکیشن)
        try:
            storage.set_last_warn({
                "at": datetime.now().strftime("%H:%M"),
                "summary": outage_summary(outage),
            })
            self.window.update_last_warn()
        except Exception:
            pass

        # v6.0 — طرح صدای انتخابی کاربر (با احترام به بی‌صدایی موقت)
        sounds.play(self.settings.get("sound_scheme", "system"), self.settings)

        if mode == "notify":
            self._toast(
                i18n.t("tray.warn_title"),
                i18n.t("tray.warn_body", mins=when, summary=outage_summary(outage)),
                # v4.4.4 — طول نمایش توست هم دستِ کاربر است (پیش‌فرض ۱۵ ثانیه)
                msecs=max(5, int(self.settings.get("notify_seconds", 15))) * 1000,
            )
            # اگر توست ویندوز لای فوکوس‌اسست گم شد، چشمک تسک‌بار هم هست —
            # کاربر در هر حالت یک نشانه‌ی دیدنی از هشدار می‌گیرد
            try:
                QApplication.alert(self.window)
            except Exception:
                pass
        elif mode == "action":
            action = self.settings.get("default_action", "shutdown")
            if power.perform(action):
                self._toast(
                    i18n.t("tray.action_done_title"),
                    i18n.t("tray.action_done_body",
                           mins=when, action=i18n.t(ACTION_KEY_NAMES.get(action, action))),
                )
            else:
                self._toast(
                    i18n.t("tray.action_fail_title"),
                    i18n.t("tray.action_fail_body",
                           action=i18n.t(ACTION_KEY_NAMES.get(action, action)), mins=when),
                    QSystemTrayIcon.Warning,
                )
        else:  # notify_action: پنجره‌ی هشدار با دکمه‌ها؛ در پایان شمارش، عمل پیش‌فرض
            self.warn_queue.append(outage)
            self._drain()

    def _drain(self):
        if self.dialog is not None or not self.warn_queue:
            return
        outage = self.warn_queue.pop(0)
        # v4.4.4 — طول نمایش اعلان دستِ کاربر: پایانِ این ثانیه‌ها بدون واکنش
        # یعنی اقدام پیش‌فرض خودکار اجرا شود
        self.dialog = WarnDialog(
            outage, self.settings.get("default_action", "shutdown"),
            react_secs=int(self.settings.get("notify_seconds", 15)))
        self.dialog.finished.connect(self._dialog_done)
        self.dialog.action_failed.connect(self._on_action_failed)
        self.dialog.show()
        self.dialog.raise_()
        QApplication.alert(self.dialog)

    def _dialog_done(self, _result=None):
        self.dialog = None
        QTimer.singleShot(150, self._drain)

    def _on_action_failed(self, action: str):
        self._toast(
            i18n.t("tray.action_fail_title"),
            i18n.t("tray.action_fail_body",
                   action=i18n.t(ACTION_KEY_NAMES.get(action, action)),
                   mins=f"1 {i18n.t('dash.minutes')}"),
            QSystemTrayIcon.Warning,
        )

    # ---------- خطاها و تنظیمات ----------

    def _record_health(self, ok: bool):
        """سلامتِ ۸ بررسیِ اخیر — برای نوارِ نقطه‌ایِ بنر وضعیت سرویس"""
        self._health = ([ok] + list(self._health))[:8]
        self.window.set_service_health(self._health)

    def _on_failed(self, info):
        """v6.0 — خطاها نوع‌دار شدند: وقتی سرور برق‌من (uiapi.saapa.ir)
        قطع یا کُند است، به‌جای خطایِ خام، بنرِ واضحِ «مشکل از برق‌منه،
        نه ناجی» با نوارِ سلامت و دکمه‌ی تلاش دوباره نشان داده می‌شود"""
        self._mark_check_done()
        self._record_health(False)
        if isinstance(info, dict):
            kind = str(info.get("kind", "net"))
            msg = str(info.get("msg", ""))
        else:  # سازگاری با پیام‌های رشته‌ای قدیمی
            kind, msg = "net", str(info)
        # متنِ چیپ وضعیت — کوتاه و بلامبجام
        if kind == "saapa":
            pill = i18n.t("conn.err_saapa")
        elif kind == "timeout":
            pill = i18n.t("conn.err_timeout")
        elif kind == "vpn":
            pill = i18n.t("conn.blocked")
        elif kind == "auth":
            pill = i18n.t("conn.expired")
        else:
            pill = i18n.t("conn.err_net")
        state = None if kind in ("saapa", "timeout", "net") else False
        self.window.set_connection(pill, state)
        # بنر وضعیت — فقط برای خطاهای سرویس/اتصال (نه VPN که پیامِ خودش را دارد)
        if kind in ("saapa", "timeout", "net"):
            self.window.show_service_banner(kind, self._health)
        # ویجت شناور هم نقطه‌ی وضعیتش قرمز شود
        if self.overlay is not None:
            try:
                self.overlay.set_level(False)
            except RuntimeError:
                pass

    def _on_blocked(self):
        self._mark_check_done()
        self._record_health(False)
        self.window.set_connection(i18n.t("conn.blocked"), False)
        now = datetime.now().timestamp()
        if now - self._last_blocked_toast > 1800:  # حداکثر هر ۳۰ دقیقه یک‌بار
            self._last_blocked_toast = now
            self._toast(
                i18n.t("tray.blocked_title"),
                api.BLOCK_MSG.replace("\n", " "),
                QSystemTrayIcon.Warning, 20000,
            )

    def _on_auth_expired(self):
        self._stop_poller()
        self._mark_check_done()
        self.window.set_connection(i18n.t("conn.expired"), False)
        self._toast(
            i18n.t("tray.expired_title"),
            i18n.t("tray.expired_body"),
            QSystemTrayIcon.Warning,
        )
        self._login()

    # ---------- v6.0 — ویجت شناور دسکتاپ ----------

    def _toggle_overlay_from_tray(self):
        on = not bool(self.settings.get("overlay_enabled", False))
        self.settings["overlay_enabled"] = on
        storage.save()
        if hasattr(self.window, "refresh_dynamic_controls"):
            self.window.refresh_dynamic_controls()
        self._sync_overlay()

    def _on_overlay_toggled(self, on: bool):
        self.settings["overlay_enabled"] = bool(on)
        storage.save()
        self._sync_overlay()
        # سوییچ تنظیمات هم همگام بماند (وقتی از × روی ویجت بسته می‌شود)
        try:
            self.window.refresh_dynamic_controls()
        except Exception:
            pass

    def _sync_overlay(self):
        """ویجت شناور را با تنظیم فعلی همگام می‌کند (بالا/پایین/بازسازی)"""
        enabled = bool(self.settings.get("overlay_enabled", False)) \
            and self._logged_in()
        if enabled and self.overlay is None:
            try:
                self.overlay = overlay_mod.MiniOverlay()
                self.overlay.open_requested.connect(self._show_window)
                self.overlay.close_requested.connect(
                    lambda: self._on_overlay_toggled(False))
                pos = str(self.settings.get("overlay_pos", "") or "")
                if "," in pos:
                    try:
                        x, y = pos.split(",")
                        self.overlay.move(int(float(x)), int(float(y)))
                    except (ValueError, TypeError):
                        pass
                self._feed_overlay(self._last_snap or None)
                self.overlay.set_level(None)
                self.overlay.show()
            except Exception as e:
                debug_note(f"overlay-open-fail: {e}")
                self.overlay = None
        elif not enabled and self.overlay is not None:
            try:
                ov = self.overlay
                self.overlay = None
                ov.close()
                ov.deleteLater()
            except RuntimeError:
                pass
        # متنِ آیتمِ تری تازه شود
        try:
            self.a_widget.setText(self._widget_action_text())
        except Exception:
            pass

    def _feed_overlay(self, snap):
        """آخرین اسنپ‌شات به ویجت شناور داده شود (نزدیک‌ترین قطعی آینده)"""
        if self.overlay is None:
            return
        nxt, title = None, ""
        if snap:
            from datetime import datetime as _dt
            now = _dt.now()
            cands = []
            for o in snap.get("planned") or []:
                d = outage_datetime(o)
                if d and d > now:
                    cands.append((d, o))
            cands.sort(key=lambda x: x[0])
            if cands:
                nxt = cands[0][1]
                title = str(nxt.get("_bill_title") or "")
        self.overlay.set_next(nxt, title)

    def _on_overlay_level(self, ok: bool):
        if self.overlay is not None:
            self.overlay.set_level(ok)

    # ---------- v6.0 — به‌روزرسانی و چنج‌لاگ ----------

    def _check_updates_silent(self):
        """چکِ خودکارِ بی‌سروصدا (فقط اگر نسخه‌ی جدید باشد خبر می‌دهد)"""
        if not self.settings.get("update_check", True):
            return
        self._fetch_updates(announce_latest=False)

    def _check_updates_manual(self):
        """دکمه‌ی «بررسی الآن» در تنظیمات — نتیجه هرچه بود نشان داده می‌شود"""
        self.window.set_update_status(i18n.t("upd.checking"))
        self._fetch_updates(announce_latest=True)

    def _fetch_updates(self, announce_latest: bool):
        self._upd_task = _FetchTask(updater.fetch_latest, self)

        def _done(result, err):
            try:
                if self._upd_task:
                    self._upd_task.wait(1200)
                self._upd_task = None
            except Exception:
                self._upd_task = None
            if err or not isinstance(result, dict):
                debug_note(f"update-check-fail: {err}")
                if announce_latest:
                    self.window.set_update_status(i18n.t("upd.fail"))
                return
            remote = str(result.get("version", ""))
            if updater.is_newer(remote, updater.VERSION):
                if announce_latest:
                    self.window.set_update_status("")
                self._toast(
                    i18n.t("upd.dialog_title"),
                    i18n.t("upd.found", v=num(remote)),
                )
                self.window.show_update_dialog(result)
            else:
                if announce_latest:
                    self.window.set_update_status(
                        i18n.t("upd.latest", v=num(updater.VERSION)))

        self._upd_task.done.connect(_done)
        self._upd_task.start()

    def _on_settings_changed(self):
        # v4.4.6 — re-arm هشدار: اگر «چند دقیقه قبل» عوض شده باشد، dedupe
        # همین اجرا پاک می‌شود و «همین حالا» سنجش تازه انجام می‌شود؛ دیگر
        # کاربر تا تیکِ ۲۰ ثانیه‌ای (و بدتر: تا شلیکِ قبلیِ مصرف‌شده) منتظر
        # نمی‌ماند — ریشه‌ی «۵۰ دقیقه ست کردم، واکنشی نیست».
        lead = max(1, int(self.settings.get("lead_minutes", 10)))
        if lead != getattr(self, "_armed_lead", None):
            self._armed_lead = lead
            storage.clear_warned()
            try:
                self._check_warnings()
            except Exception:
                pass
        # v4.4.3: بازه‌ی پایش دوباره قابل تنظیم است؛ اگر عوض شده باشد پولر
        # با فاصله‌ی تازه از نو راه می‌افتد؛ وگرنه فقط اگر مرده باشد
        want = max(1, int(self.settings.get("poll_minutes", 5)))
        cur = getattr(self.poller, "interval_min", None)
        if self._logged_in() and (not self.poller or cur != want):
            self._start_poller()
        elif self._logged_in() and self.poller is not None:
            # داده‌ی تازه قبل از باز شدن پنجره‌ی پیش‌آگاهی — مخصوصاً با
            # فاصله‌ی پایش بزرگ (مثلاً ۶۰ دقیقه) که لیست ممکن است کهنه باشد
            sig = (lead, want)
            if sig != getattr(self, "_wake_sig", None):
                self._wake_sig = sig
                try:
                    self.poller.wake()
                except Exception:
                    pass

    def _on_theme_mode_changed(self, mode: str):
        # باگ v4.2: برای حالت «system» همیشه از ویندوز مشتق شود؛
        # قبلاً reset_theme=False می‌شد و تمِ قبلی می‌ماند → «سینک نمی‌شه»
        self._apply_look(reset_theme=True)

    def _on_sync_windows(self, on: bool):
        self._apply_look()

    def _apply_look(self, reset_theme: bool = False):
        """اعمال ظاهر: رنگ اکسنت ویندوز + تم روشن/تیره (دستی یا سیستمی)"""
        if self.settings.get("sync_windows", True):
            theme.apply_accent(wininfo.accent_rgb())
        else:
            theme.apply_accent(None)
        mode = self.settings.get("theme_mode", "dark")
        if reset_theme:
            theme_name = mode if mode in ("light", "dark") else (
                "dark" if wininfo.apps_dark() else "light")
            self.settings["theme"] = theme_name
            storage.save()
        theme.apply(self.app, self.settings.get("theme", "dark"))
        self.window.update()
        # v6.0 — ویجت شناور هم با تم تازه رنگ بگیرد
        if self.overlay is not None:
            self.overlay.refresh_look()

    def _on_windows_look_changed(self, *_):
        """نگاه سبک هر ۵ ثانیه + سیگنال کوانت: رنگ اکسنت یا تم عوض شده؟
        (*_ — سیگنال colorSchemeChanged یک آرگومان می‌فرستد، تایمر هیچ)"""
        if not self.settings.get("sync_windows", True):
            return
        try:
            if not wininfo.changed_since_previous():
                return
        except Exception:
            return
        self._apply_look(reset_theme=self.settings.get("theme_mode", "dark") == "system")

    def _on_lang_changed(self, lang: str):
        i18n.set_lang(lang)
        # v4.4.4 — قواعد قلمِ QSS زبان‌آگاه شدند (ابروی فارسی/لاتین)؛
        # پس قبل از بازسازی پنجره، استایل‌شیت سراسری هم تازه شود
        self._apply_look()
        self._rebuild_window()
        self._retranslate_tray()
        # v6.0 — ویجت شناور با زبان تازه از نو ساخته شود
        if self.overlay is not None:
            try:
                ov = self.overlay
                self.overlay = None
                ov.close()
                ov.deleteLater()
            except RuntimeError:
                pass
            if bool(self.settings.get("overlay_enabled", False)):
                self._sync_overlay()

    def _on_bills_changed(self, bills: list):
        self.window.update_identity()
        self._on_settings_changed()  # اگر پولر مرده، دوباره راه بیفتد

    def _on_active_bill(self, bill_id: str):
        self.window.update_identity()
        # قبض فعال عوض شد؟ چرخه‌ی پایش از نو — ولی بدون بلاک‌کردن UI
        if self._logged_in():
            self._start_poller()

    def _logout(self):
        self._stop_poller()
        storage.reset_session()
        self.window.update_identity()
        self.window.set_connection(i18n.t("tray.logged_out_conn"), None)
        self._login()

    def quit(self):
        self._quit_requested = True
        # v6.0 — موقعیت ویجت شناور برای اجرای بعدی ثبت شود
        if self.overlay is not None:
            try:
                self.settings["overlay_pos"] = f"{self.overlay.x()},{self.overlay.y()}"
            except RuntimeError:
                pass
            try:
                self.overlay.close()
            except RuntimeError:
                pass
        storage.save()
        if self.poller:
            self.poller.stop(wait_ms=1500)  # فقط موقع خروجِ کامل صبر می‌کنیم
        self.tray.hide()
        self.app.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Naji")
    app.setApplicationDisplayName(APP_TITLE)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")

    # v6.0 — گزارشگر کرش: لاگ محلیِ خوانا + دیالوگِ اجازه‌دار (اولویت ۱ بریف)
    crash.install(updater.VERSION)

    settings = storage.load()
    i18n.set_lang(settings.get("lang", "fa"))
    app.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)

    theme.load_fonts()
    # ظاهر اولیه: رنگ اکسنت +یندوز و تم سیستمی/دستی
    if settings.get("sync_windows", True):
        theme.apply_accent(wininfo.accent_rgb())
    mode = settings.get("theme_mode", "dark")
    if mode == "system":
        theme_name = "dark" if wininfo.apps_dark() else "light"
        settings["theme"] = theme_name
        storage.save()
        theme.set_current(theme_name)
    else:
        theme.set_current(settings.get("theme", "dark"))
    theme.apply(app)
    app.setFont(theme.app_font(11))

    app.setWindowIcon(make_icon())

    # ---------- تک‌نمونه ----------
    controller_holder = {}

    def on_second_launch():
        c = controller_holder.get("c")
        if c:
            c._show_window()
            # بازخورد به کاربر: چرا پنجره‌ی جدیدی باز نشد
            try:
                c._toast(i18n.t("app.name"), i18n.t("single.msg"), msecs=6000)
            except Exception:
                pass

    single = SingleInstance()
    if not single.try_become_primary(on_second_launch):
        # نمونه‌ی دوم بود؛ فقط پیام داده و خارج شد
        sys.exit(0)

    controller = Controller(app)
    controller_holder["c"] = controller
    controller.run()
    if controller._quit_requested:
        # باگ تاریخی: quit() پیش از exec() در Qt هیچ اثری ندارد
        sys.exit(0)
    code = app.exec()
    # خروجِ تمیز حتی اگر ترد پولر هنوز منتظر پاسخِ شبکه باشد
    os._exit(code)


if __name__ == "__main__":
    main()
