# main_window.py — پنجره‌ی اصلی ناجی v4: نوار کناری + چهار صفحه
#   خانه (داشبورد) | تنظیمات | راهنما | درباره
# زبان بصری Aura Glass: بوم شفق، کارت‌های شیشه‌ای، تایپوگرافی چهارصدایی.
# نکته‌ی کارایی: تغییر کنترل‌های تنظیمات با تأخیر ۴۵۰ms «دپ‌بان» می‌شود؛
# قبلاً هر کلیکِ فلش اسپین، ذخیره‌ی دیسک + ری‌استارت تردِ پایش را بلافاصله
# اجرا می‌کرد و همین بود که «انتخاب بازه‌ی بررسی» را لگ‌دار کرده بود.
from PySide6.QtCore import QPoint, QPropertyAnimation, Qt, QEasingCurve, QThread, QTimer, Signal
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QListWidget, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QTextBrowser, QVBoxLayout, QWidget,
)

import api
import i18n
import sounds
import storage
import theme
import updater
from util import num, outage_datetime, to_latin_digits
from widgets import (
    AboutUsLogo, BackdropCanvas, BillSwitcher, EmptyState, GlassCard,
    GlassCombo, GlassStepper, HistoryChart, HeroCard, IconChip,
    JellyButton, LocationChip, LogoChip, NavRail, Segmented, ServiceBanner,
    StatTile, StatusPill, Switch, add_glow, add_shadow, fill_outage_list,
    os_env_anim,
)

VERSION = "6.1.0"

MODES = [
    ("notify", "set.mode_notify"),
    ("notify_action", "set.mode_notify_action"),
    ("action", "set.mode_action"),
]

MODE_DESC = {
    "notify": "set.mode_desc_notify",
    "notify_action": "set.mode_desc_notify_action",
    "action": "set.mode_desc_action",
}

ACTION_KEYS = ("shutdown", "sleep", "hibernate")

ACTION_NAMES = {
    "shutdown": "set.act_shutdown",
    "sleep": "set.act_sleep",
    "hibernate": "set.act_hibernate",
}

ACTION_HINTS = {
    "shutdown": "set.act_hint_shutdown",
    "sleep": "set.act_hint_sleep",
    "hibernate": "set.act_hint_hibernate",
}

THEME_MODES = [
    ("system", "look.theme_system"),
    ("light", "look.theme_light"),
    ("dark", "look.theme_dark"),
]

LANGS = [
    ("fa", "look.lang_fa"),
    ("en", "look.lang_en"),
]


def card(radius: int = 20) -> tuple:
    """یک کارت شیشه‌ای + لایه‌ی داخلی (v5.0: حاشیه‌ی نفس‌کِش‌تر)"""
    frame = GlassCard(radius=radius)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 15, 18, 15)
    lay.setSpacing(8)
    return frame, lay


def eyebrow(text: str, tone: str = None) -> QLabel:
    """میکرولیبل لاتین با فاصله‌ی حرفی — امضای تایپوگرافیک طراحی
    v4.7: با tone، رنگِ بخشِ مربوط (نقطه‌ی هویتی هر بخش از برنامه)"""
    lbl = QLabel(text)
    lbl.setObjectName("eyebrow")
    if tone:
        chips = theme.chips()
        c = chips.get(tone) or chips["indigo"]
        lbl.setStyleSheet(f"color: {c['fg']}; background: transparent;")
    return lbl


def tone_dot(tone: str) -> QFrame:
    """نقطه‌ی ۸px هویتِ رنگیِ بخش — تمایزِ زیبا و منسجم بین بخش‌های برنامه"""
    d = QFrame()
    d.setFixedSize(8, 8)
    d.setObjectName("legendDot")
    d.setProperty("tone", tone)
    return d


def caption_block(eyebrow_text: str, title: str, side: QLabel = None,
                  tone: str = None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(7)
    if tone:
        row.addWidget(tone_dot(tone), 0, Qt.AlignmentFlag.AlignBottom)
    col = QVBoxLayout()
    col.setSpacing(1)
    col.addWidget(eyebrow(eyebrow_text, tone))
    t = QLabel(title)
    t.setObjectName("h2")
    col.addWidget(t)
    row.addLayout(col)
    row.addStretch()
    if side:
        side.setObjectName("hint")
        row.addWidget(side, 0, Qt.AlignmentFlag.AlignBottom)
    return row


class _FetchTask(QThread):
    """اجرای یک تابع شبکه‌ای در رشته‌ی جداگانه"""
    done = Signal(object, object)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.done.emit(self._fn(), None)
        except Exception as e:  # noqa: BLE001
            self.done.emit(None, e)


class BillPickerDialog(QDialog):
    """پنجره‌ی «افزودن قبض» — قبض‌های حسابت که هنوز زیر پایش نیستند"""

    def __init__(self, existing_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("bills.picker_title"))
        self.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
        self.setFixedWidth(500)
        self.selected = None
        self._task = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        canvas = BackdropCanvas(self)
        canvas.setObjectName("central")
        root.addWidget(canvas)
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(24, 20, 24, 18)
        lay.setSpacing(10)

        logo_row = QHBoxLayout()
        # v4.7 — ۳۸px (بود ۴۶)
        logo_row.addWidget(IconChip("indigo", "bill", 38))
        logo_row.addStretch()
        lay.addLayout(logo_row)

        t = QLabel(i18n.t("bills.picker_title"))
        t.setObjectName("h1")
        sub = QLabel(i18n.t("bills.picker_sub"))
        sub.setObjectName("muted")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)

        self.list_bills = QListWidget()
        lay.addWidget(self.list_bills, 1)

        self.empty_lbl = QLabel(i18n.t("bills.picker_empty"))
        self.empty_lbl.setObjectName("muted")
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setVisible(False)
        lay.addWidget(self.empty_lbl)

        row = QHBoxLayout()
        self.btn_cancel = JellyButton(i18n.t("dash.cancel"))
        self.btn_cancel.setObjectName("ghost")
        self.btn_cancel.setMinimumHeight(44)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_add = JellyButton(i18n.t("bills.picker_add"))
        self.btn_add.setObjectName("primary")
        self.btn_add.setMinimumHeight(46)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self._confirm)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_add, 1)
        lay.addLayout(row)

        self._load(existing_ids)

    def _load(self, existing_ids):
        token = storage.get_token()
        if not token:
            self.empty_lbl.setText(i18n.t("conn.expired"))
            self.empty_lbl.setVisible(True)
            return

        def fetch():
            return api.get_bills(token)

        self._task = _FetchTask(fetch, self)
        self._task.done.connect(lambda r, e: self._loaded(r, e, existing_ids))
        self.btn_add.setEnabled(False)
        self.setCursor(Qt.WaitCursor)
        self._task.start()

    def _loaded(self, result, err, existing_ids):
        if self._task:
            self._task.wait(1500)
            self._task = None
        self.unsetCursor()
        bills = result if isinstance(result, list) else []
        fresh = []
        for b in bills:
            bid = to_latin_digits(str(b.get("bill_identifier", "")))
            if bid and bid not in existing_ids:
                fresh.append(b)
        self._fresh = fresh
        self.list_bills.clear()
        for b in fresh:
            self.list_bills.addItem(
                f"{b.get('bill_title') or '—'} — {b.get('bill_identifier', '')}"
            )
        if fresh:
            self.list_bills.setCurrentRow(0)
            self.btn_add.setEnabled(True)
        else:
            self.empty_lbl.setVisible(True)

    def _confirm(self):
        row = self.list_bills.currentRow()
        if 0 <= row < len(getattr(self, "_fresh", [])):
            b = self._fresh[row]
            self.selected = {
                "bill_id": to_latin_digits(str(b.get("bill_identifier", ""))),
                "bill_title": str(b.get("bill_title", "")),
            }
        self.accept()


class MainWindow(QMainWindow):
    check_now = Signal()
    logout_requested = Signal()
    settings_changed = Signal()
    theme_mode_changed = Signal(str)      # system | light | dark
    lang_changed = Signal(str)            # fa | en
    sync_windows_changed = Signal(bool)
    bills_changed = Signal(list)          # لیست تازه‌ی قبض‌ها
    active_bill_changed = Signal(str)
    check_updates_requested = Signal()    # v6.0 — دکمه‌ی «بررسی الآن» آپدیتر
    overlay_toggled = Signal(bool)        # v6.0 — سوییچ ویجت شناور

    def __init__(self, settings: dict):
        super().__init__()
        self.setWindowTitle(i18n.t("app.window_title"))
        self.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
        self.setMinimumSize(720, 600)
        try:
            avail_h = self.screen().availableGeometry().height()
        except Exception:
            avail_h = 900
        # v5.0 — پنجره‌ی پهن‌تر برای چیدمانِ پریمیوم دسکتاپی
        self.resize(980, min(980, max(620, avail_h - 36)))
        self.settings = settings
        self._identity_applied = False
        self._last_snapshot = {}
        self._current_page = "dashboard"
        self._page_anim = None

        # دپ‌بان تنظیمات: کنترل‌ها فقط «صف» می‌کنند؛ ۴۵۰ms بعد از آخرین
        # تغییر، یک‌بار ذخیره و انتشار انجام می‌شود
        self._settings_timer = QTimer(self)
        self._settings_timer.setSingleShot(True)
        self._settings_timer.setInterval(450)
        self._settings_timer.timeout.connect(self._commit_settings)

        # بوم شفق — پس‌زمینه‌ی زنده‌ی برنامه؛ ستون نوار + صفحات روی آن
        central = BackdropCanvas()
        central.setObjectName("central")
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.nav = NavRail("dashboard")
        self.nav.page_selected.connect(self._on_nav)
        self.nav.theme_toggled.connect(self._cycle_theme)
        self.nav.lang_toggled.connect(self._toggle_lang)  # v4.4.9
        outer.addWidget(self.nav)

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        # ---------- سربرگ مشترک ----------
        head_widget = QWidget()
        head = QHBoxLayout(head_widget)
        head.setContentsMargins(18, 12, 18, 4)
        head.setSpacing(12)
        self.logo = LogoChip(40)   # v4.7 — ۴۰px (بود ۴۸)
        head.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignVCenter)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(eyebrow(i18n.t("app.eyebrow")))
        title = QLabel(i18n.t("app.name"))
        title.setObjectName("h1")
        titles.addWidget(title)
        self.lbl_bill = QLabel("—")
        self.lbl_bill.setObjectName("hint")
        titles.addWidget(self.lbl_bill)
        head.addLayout(titles)
        # v5.0 — چیپ موقعیت سربرگ (بریف: Location)؛ داده‌محور — فقط با
        # آدرسِ واقعیِ آخرین اسنپ‌شات دیده می‌شود، وگرنه کاملاً پنهان است
        self.loc = LocationChip()
        head.addWidget(self.loc, 0, Qt.AlignmentFlag.AlignVCenter)

        head.addStretch()
        self.pill = StatusPill()
        head.addWidget(self.pill, 0, Qt.AlignmentFlag.AlignVCenter)
        # v4.7 — «خروج از حساب» به گوشه‌ی بالای سربرگ رفت (درخواست کاربر:
        # جای دور از مسیرِ دست، تا کلیکِ اشتباه نشود). ابزارِ کوچکِ کم‌رنگ؛
        # فقط هاور رنگِ خطر می‌گیرد
        self.btn_logout = JellyButton(i18n.t("dash.logout"))
        self.btn_logout.setObjectName("signout")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setToolTip(i18n.t("dash.logout"))
        self.btn_logout.clicked.connect(self._confirm_logout)
        head.addWidget(self.btn_logout, 0, Qt.AlignmentFlag.AlignVCenter)
        content_lay.addWidget(head_widget)

        # ---------- صفحات ----------
        self.stack = QStackedWidget()
        self.pages = {}
        for key, builder in (
            ("dashboard", self._page_dashboard),
            ("settings", self._page_settings),
            ("help", self._page_help),
            ("about", self._page_about),
        ):
            page = builder()
            self.pages[key] = page
            self.stack.addWidget(page)
        content_lay.addWidget(self.stack, 1)
        outer.addWidget(content, 1)

        self.setCentralWidget(central)
        self._identity_applied = True

    # ---------- کمکی‌های صفحه ----------

    def _scroll_wrap(self, inner: QWidget) -> QScrollArea:
        """هر صفحه در اسکرول‌AREA شیشه‌ای با اسکرول‌بارِ نمایان"""
        scroll = QScrollArea()
        scroll.setObjectName("contentScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(inner)
        return scroll

    def _page_shell(self) -> tuple:
        body = QWidget()
        root = QVBoxLayout(body)
        root.setContentsMargins(16, 6, 16, 14)
        root.setSpacing(10)
        return body, root

    # ---------- صفحه‌ی خانه ----------

    def _page_dashboard(self) -> QScrollArea:
        body, root = self._page_shell()

        # v6.0 — سوییچر قبض‌ها (فقط در پایش چند-قبضی دیده می‌شود)
        self.bill_switch = BillSwitcher()
        self.bill_switch.bill_selected.connect(self._on_switch_bill)
        self.bill_switch.add_requested.connect(self._add_bill)
        root.addWidget(self.bill_switch)

        # v6.0 — بنر وضعیت سرویس برق‌من (وقتی سرور قطع/کند است)
        self.svc_banner = ServiceBanner()
        self.svc_banner.retry_clicked.connect(self.check_now.emit)
        root.addWidget(self.svc_banner)

        # ردیف هیرو: کارت قطعی بعدی + کاشی‌های آمار
        # (۵/۴ → ۴/۵: کاشی‌ها نفس می‌کِشند و کپشن‌ها یک‌خطی می‌مانند؛
        #   شمارش معکوس هیرو خودتنظیم است و فضای کمتر را جبران می‌کند)
        hero_row = QHBoxLayout()
        hero_row.setSpacing(14)

        self.hero = HeroCard()
        add_shadow(self.hero, blur=48, alpha=80, dy=18)
        hero_row.addWidget(self.hero, 4)

        stats_box = QWidget()
        stats_lay = QGridLayout(stats_box)
        stats_lay.setContentsMargins(0, 0, 0, 0)
        stats_lay.setSpacing(12)
        self.stat_planned = StatTile("violet", "bolt", i18n.t("dash.stat_planned"), "—")
        self.stat_occurred = StatTile("teal", "check", i18n.t("dash.stat_occurred"), "—")
        # v4.4.6 — ممیزی آیکون‌ها: «چند دقیقه قبل» = زنگ هشدار (نه گیج)؛
        # «فاصله‌ی پایش» = کرنومتر (نه دایره‌ی ناقصِ شبیه ماهِ شکسته)
        self.stat_lead = StatTile("amber", "bell", i18n.t("dash.stat_lead"), "—")
        self.stat_poll = StatTile("sky", "timer", i18n.t("dash.stat_poll"), "—")
        for i, st in enumerate((self.stat_planned, self.stat_occurred,
                                self.stat_lead, self.stat_poll)):
            add_shadow(st, blur=32, alpha=32, dy=10)
            stats_lay.addWidget(st, i // 2, i % 2)
        stats_lay.setRowStretch(0, 1)
        stats_lay.setRowStretch(1, 1)
        stats_lay.setColumnStretch(0, 1)
        stats_lay.setColumnStretch(1, 1)
        hero_row.addWidget(stats_box, 5)
        root.addLayout(hero_row)
        self._refresh_stats()

        # کارت خاموشی‌ها
        cf, cl = card()
        add_shadow(cf, blur=40, alpha=38, dy=12)
        self.lbl_last = QLabel(i18n.t("conn.last_check", t="—"))
        cl.addLayout(caption_block(
            i18n.t("dash.outages_eyebrow"), i18n.t("dash.outages_title"), self.lbl_last,
            tone="violet"))

        self.outage_list = QListWidget()
        self.outage_list.setSelectionMode(QListWidget.NoSelection)
        self.outage_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.outage_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.outage_list.setMinimumHeight(80)
        cl.addWidget(self.outage_list, 1)

        # حالت خالی تزئینی
        self.empty_state = EmptyState()
        self.empty_state.setVisible(False)
        cl.addWidget(self.empty_state, 1)
        root.addWidget(cf, 1)

        # v6.0 — کارت تاریخچه‌ی قطعی‌ها (نمودار هفتگی/ماهانه از داده‌های ثبت‌شده)
        self.hist_card = HistoryChart()
        add_shadow(self.hist_card, blur=36, alpha=30, dy=10)
        self.hist_card.range_changed.connect(self._on_hist_range)
        root.addWidget(self.hist_card)
        self._refresh_history()

        # نوار پایین — بریف v5.0: خلاصه در سمتِ شروع + دکمه‌ی اصلیِ درشتِ
        # «به‌روزرسانی فوری» با هاله‌ی بنفش در انتهای ردیف
        # (خلاصه از کف کارتِ خاموشی‌ها به این‌جا منتقل شد — بدون تکرار)
        bar = QWidget()
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(6, 2, 6, 2)
        bar_lay.setSpacing(8)
        self.dot_upcoming = QFrame()
        self.dot_upcoming.setFixedSize(8, 8)
        self.dot_upcoming.setObjectName("legendDot")
        self.dot_upcoming.setProperty("tone", "violet")
        self.lbl_upcoming = QLabel("—")
        self.lbl_upcoming.setObjectName("hint")
        self.dot_today = QFrame()
        self.dot_today.setFixedSize(8, 8)
        self.dot_today.setObjectName("legendDot")
        self.dot_today.setProperty("tone", "teal")
        self.lbl_today = QLabel("—")
        self.lbl_today.setObjectName("hint")
        self.lbl_footer_bill = QLabel("")
        self.lbl_footer_bill.setObjectName("hint")
        bar_lay.addWidget(self.dot_upcoming, 0, Qt.AlignmentFlag.AlignVCenter)
        bar_lay.addWidget(self.lbl_upcoming)
        bar_lay.addSpacing(6)
        bar_lay.addWidget(self.dot_today, 0, Qt.AlignmentFlag.AlignVCenter)
        bar_lay.addWidget(self.lbl_today)
        bar_lay.addSpacing(6)
        bar_lay.addWidget(self.lbl_footer_bill)
        bar_lay.addStretch()
        btn_check = JellyButton(i18n.t("dash.check_now"))
        btn_check.setObjectName("primary")
        btn_check.setCursor(Qt.PointingHandCursor)
        btn_check.setMinimumHeight(52)
        btn_check.setMinimumWidth(240)
        btn_check.clicked.connect(self.check_now.emit)
        # هاله‌ی بنفشِ محو زیر دکمه (بریف: soft purple glow)
        add_glow(btn_check, blur=36, alpha=110, dy=8)
        bar_lay.addWidget(btn_check)
        self.btn_check = btn_check
        root.addWidget(bar)

        return self._scroll_wrap(body)

    # ---------- صفحه‌ی تنظیمات ----------

    def _page_settings(self) -> QScrollArea:
        body, root = self._page_shell()
        s = self.settings

        # ---------- کارت هشدار ----------
        ca, cl = card()
        add_shadow(ca, blur=34, alpha=30, dy=10)
        q = QLabel(i18n.t("set.question"))
        q.setObjectName("muted")
        cl.addLayout(caption_block(i18n.t("set.eyebrow"), i18n.t("set.title"), q,
                                   tone="teal"))

        self.segment = Segmented(
            [(v, i18n.t(k)) for v, k in MODES], s.get("mode", "notify_action"))
        self.segment.changed.connect(self._queue_settings)
        cl.addWidget(self.segment)

        self.mode_desc = QLabel(
            i18n.t(MODE_DESC.get(s.get("mode", "notify_action"), "")))
        self.mode_desc.setObjectName("hint")
        self.mode_desc.setWordWrap(True)
        cl.addWidget(self.mode_desc)

        # v4.4.1: زمانِ هشدار دست خود کاربر است — چند دقیقه قبل از شروع
        # هر خاموشی خبر بدهیم؛ چرخ پایش (هر ۲۰ ثانیه) داخلی می‌ماند و
        # نیازی به تنظیم ندارد.
        lbl_l = QLabel(i18n.t("set.lead"))
        lbl_l.setObjectName("fieldLabel")
        cl.addWidget(lbl_l)
        self.spin_lead = GlassStepper()
        # v4.4.9 — سقف عددی برداشته شد (سقف فقط سینتکسی است)
        self.spin_lead.setRange(1, 99999)
        self.spin_lead.setValue(int(s.get("lead_minutes", 10)))
        self.spin_lead.setSuffix(" " + i18n.t("dash.minutes"))
        self.spin_lead.setMinimumHeight(46)
        self.spin_lead.setMaximumWidth(220)
        self.spin_lead.setAlignment(
            Qt.AlignmentFlag.AlignHCenter if i18n.is_rtl()
            else Qt.AlignmentFlag.AlignLeft)
        self.spin_lead.valueChanged.connect(self._queue_settings)
        cl.addWidget(self.spin_lead)
        self.lbl_lead_hint = QLabel(i18n.t("set.lead_tip"))
        self.lbl_lead_hint.setObjectName("hint")
        self.lbl_lead_hint.setWordWrap(True)
        cl.addWidget(self.lbl_lead_hint)

        # v4.4.4 — تایمر اعلان هم دستِ کاربر است: پنجره‌ی هشدار فقط همین‌قدر
        # ثانیه باز می‌ماند؛ بدون واکنش، اقدام پیش‌فرض خودکار اجرا می‌شود
        lbl_n = QLabel(i18n.t("set.notify_secs"))
        lbl_n.setObjectName("fieldLabel")
        cl.addWidget(lbl_n)
        self.spin_notify = GlassStepper()
        self.spin_notify.setRange(1, 99999)  # v4.4.9 — بدون سقف
        self.spin_notify.setValue(int(s.get("notify_seconds", 15)))
        self.spin_notify.setSuffix(" " + i18n.t("dash.seconds"))
        self.spin_notify.setMinimumHeight(46)
        self.spin_notify.setMaximumWidth(220)
        self.spin_notify.setAlignment(
            Qt.AlignmentFlag.AlignHCenter if i18n.is_rtl()
            else Qt.AlignmentFlag.AlignLeft)
        self.spin_notify.valueChanged.connect(self._queue_settings)
        cl.addWidget(self.spin_notify)
        self.lbl_notify_hint = QLabel(i18n.t("set.notify_secs_tip"))
        self.lbl_notify_hint.setObjectName("hint")
        self.lbl_notify_hint.setWordWrap(True)
        cl.addWidget(self.lbl_notify_hint)

        # v4.4.3: «فاصله‌ی پایش برق‌من» هم دوباره دستِ کاربر است — این عدد
        # سرعتِ پیدا شدن خاموشی‌های تازه‌لیست‌شده را تعیین می‌کند؛ زمان‌سنجِ
        # هشدار مستقل از آن هر ۲۰ ثانیه کار می‌کند.
        lbl_p = QLabel(i18n.t("set.poll"))
        lbl_p.setObjectName("fieldLabel")
        cl.addWidget(lbl_p)
        self.spin_poll = GlassStepper()
        self.spin_poll.setRange(1, 99999)  # v4.4.9 — بدون سقف
        self.spin_poll.setValue(int(s.get("poll_minutes", 5)))
        self.spin_poll.setSuffix(" " + i18n.t("dash.minutes"))
        self.spin_poll.setMinimumHeight(46)
        self.spin_poll.setMaximumWidth(220)
        self.spin_poll.setAlignment(
            Qt.AlignmentFlag.AlignHCenter if i18n.is_rtl()
            else Qt.AlignmentFlag.AlignLeft)
        self.spin_poll.valueChanged.connect(self._queue_settings)
        cl.addWidget(self.spin_poll)
        self.lbl_poll_hint = QLabel(i18n.t("set.poll_tip"))
        self.lbl_poll_hint.setObjectName("hint")
        self.lbl_poll_hint.setWordWrap(True)
        cl.addWidget(self.lbl_poll_hint)

        lbl_a = QLabel(i18n.t("set.default_action"))
        lbl_a.setObjectName("fieldLabel")
        cl.addWidget(lbl_a)
        self.combo_action = GlassCombo()
        for key in ACTION_KEYS:
            self.combo_action.addItem(i18n.t(ACTION_NAMES[key]), key)
        saved_action = s.get("default_action", "shutdown")
        self.combo_action.setCurrentIndex(
            ACTION_KEYS.index(saved_action) if saved_action in ACTION_KEYS else 0)
        self.combo_action.currentIndexChanged.connect(self._queue_settings)
        cl.addWidget(self.combo_action)
        self.lbl_action_hint = QLabel(
            i18n.t(ACTION_HINTS.get(saved_action, "")))
        self.lbl_action_hint.setObjectName("hint")
        self.lbl_action_hint.setWordWrap(True)
        cl.addWidget(self.lbl_action_hint)

        # وضعیت مسلح یادآور — همیشه مرئی تا کاربر در هر لحظه ببیند
        # هشدار خودکار فعاله (پاسخ به «یقین پیدا کنم ست شده»)
        self.lbl_armed = QLabel()
        self.lbl_armed.setObjectName("hint")
        self.lbl_armed.setWordWrap(True)
        cl.addWidget(self.lbl_armed)
        self._refresh_armed_hint()

        # ردپای آخرین هشدار شلیک‌شده — حتی اگر توست ویندوز دیده نشود،
        # این‌جا معلوم است که هشدار واقعاً شلیک کرده یا نه
        self.lbl_last_warn = QLabel()
        self.lbl_last_warn.setObjectName("hint")
        self.lbl_last_warn.setWordWrap(True)
        cl.addWidget(self.lbl_last_warn)
        self.update_last_warn()

        # دکمه‌ی ثبت — ذخیره‌ی فوری + تأییدِ دیدنی؛ دیگر ذخیره‌ی بی‌صدا نیست
        # (دکمه سمتِ شروع ردیف می‌نشیند؛ متن تأیید در ادامه‌ی همان ردیف)
        save_row = QHBoxLayout()
        save_row.setSpacing(10)
        self.lbl_saved = QLabel("")
        self.lbl_saved.setObjectName("hint")
        self.lbl_saved.setWordWrap(True)
        self.btn_commit = JellyButton(i18n.t("set.save"))
        self.btn_commit.setObjectName("primary")
        self.btn_commit.setCursor(Qt.PointingHandCursor)
        self.btn_commit.setMinimumHeight(46)
        self.btn_commit.setMaximumWidth(320)
        self.btn_commit.clicked.connect(self._commit_clicked)
        add_glow(self.btn_commit)
        save_row.addWidget(self.btn_commit)
        save_row.addWidget(self.lbl_saved, 1)
        cl.addLayout(save_row)
        self._saved_timer = QTimer(self)
        self._saved_timer.setSingleShot(True)
        self._saved_timer.setInterval(4000)
        self._saved_timer.timeout.connect(self._clear_saved_feedback)

        # سوییچ اتواستارت
        auto_row = QHBoxLayout()
        auto_row.setSpacing(10)
        self.switch_auto = Switch(bool(s.get("autostart", True)))
        self.switch_auto.toggled.connect(self._apply_autostart)
        auto_row.addWidget(self.switch_auto)
        auto_col = QVBoxLayout()
        auto_col.setSpacing(0)
        auto_lbl = QLabel(i18n.t("set.autostart"))
        auto_lbl.setObjectName("muted")
        auto_col.addWidget(auto_lbl)
        auto_hint = QLabel(i18n.t("set.autostart_hint"))
        auto_hint.setObjectName("hint")
        auto_col.addWidget(auto_hint)
        auto_row.addLayout(auto_col)
        auto_row.setAlignment(auto_col, Qt.AlignmentFlag.AlignVCenter)  # v4.4.10
        auto_row.addStretch()
        cl.addLayout(auto_row)
        root.addWidget(ca)

        # ---------- کارت صدا و هشدار (v6.0) ----------
        cs_, cs_l = card()
        add_shadow(cs_, blur=34, alpha=30, dy=10)
        cs_l.addLayout(caption_block(
            i18n.t("sound.eyebrow"), i18n.t("sound.title"), tone="amber"))

        lbl_snd = QLabel(i18n.t("sound.scheme"))
        lbl_snd.setObjectName("fieldLabel")
        cs_l.addWidget(lbl_snd)
        snd_row = QHBoxLayout()
        snd_row.setSpacing(10)
        self.combo_sound = GlassCombo()
        for key, i18n_key in sounds.schemes_for_combo():
            self.combo_sound.addItem(i18n.t(i18n_key), key)
        saved_snd = s.get("sound_scheme", "system")
        idx = self.combo_sound.findData(saved_snd)
        self.combo_sound.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_sound.currentIndexChanged.connect(self._on_sound_scheme)
        snd_row.addWidget(self.combo_sound, 1)
        self.btn_sound_test = JellyButton(i18n.t("sound.test"))
        self.btn_sound_test.setObjectName("ghost")
        self.btn_sound_test.setCursor(Qt.PointingHandCursor)
        self.btn_sound_test.setFixedHeight(44)
        self.btn_sound_test.clicked.connect(self._test_sound)
        snd_row.addWidget(self.btn_sound_test)
        cs_l.addLayout(snd_row)

        mute_row = QHBoxLayout()
        mute_row.setSpacing(10)
        self.switch_mute = Switch(False)
        self.switch_mute.toggled.connect(self._on_temp_mute)
        mute_row.addWidget(self.switch_mute)
        mute_col = QVBoxLayout()
        mute_col.setSpacing(0)
        mute_lbl = QLabel(i18n.t("sound.mute"))
        mute_lbl.setObjectName("muted")
        mute_col.addWidget(mute_lbl)
        self.lbl_mute_hint = QLabel(i18n.t("sound.mute_hint"))
        self.lbl_mute_hint.setObjectName("hint")
        self.lbl_mute_hint.setWordWrap(True)
        mute_col.addWidget(self.lbl_mute_hint)
        mute_row.addLayout(mute_col)
        mute_row.setAlignment(mute_col, Qt.AlignmentFlag.AlignVCenter)
        mute_row.addStretch()
        cs_l.addLayout(mute_row)
        self._sync_mute_switch()
        root.addWidget(cs_)

        # ---------- کارت قبض‌ها ----------
        cb, cbl = card()
        add_shadow(cb, blur=34, alpha=30, dy=10)
        bills_hint = QLabel(i18n.t("bills.hint"))
        bills_hint.setObjectName("hint")
        bills_hint.setWordWrap(True)
        cbl.addLayout(caption_block(
            i18n.t("bills.eyebrow"), i18n.t("bills.title"), bills_hint, tone="teal"))

        self.bills_box = QVBoxLayout()
        self.bills_box.setSpacing(6)
        cbl.addLayout(self.bills_box)
        self._rebuild_bill_rows()

        btn_add_bill = JellyButton(i18n.t("bills.add"))
        btn_add_bill.setObjectName("ghost")
        btn_add_bill.setCursor(Qt.PointingHandCursor)
        btn_add_bill.setMinimumHeight(42)
        btn_add_bill.clicked.connect(self._add_bill)
        cbl.addWidget(btn_add_bill, 0, Qt.AlignmentFlag.AlignLeft)
        root.addWidget(cb)

        # ---------- کارت ظاهر و زبان ----------
        cv, cvl = card()
        add_shadow(cv, blur=34, alpha=30, dy=10)
        cvl.addLayout(caption_block(
            i18n.t("look.eyebrow"), i18n.t("look.title"), tone="teal"))

        look_grid = QGridLayout()
        look_grid.setHorizontalSpacing(12)
        look_grid.setVerticalSpacing(10)

        lbl_theme = QLabel(i18n.t("look.theme"))
        lbl_theme.setObjectName("fieldLabel")
        self.segment_theme = Segmented(
            [(v, i18n.t(k)) for v, k in THEME_MODES],
            s.get("theme_mode", "system"))
        self.segment_theme.changed.connect(self._on_theme_mode)
        look_grid.addWidget(lbl_theme, 0, 0)
        look_grid.addWidget(self.segment_theme, 0, 1)

        sync_row = QHBoxLayout()
        sync_row.setSpacing(10)
        self.switch_sync = Switch(bool(s.get("sync_windows", True)))
        self.switch_sync.toggled.connect(self._on_sync_windows)
        sync_row.addWidget(self.switch_sync)
        sync_col = QVBoxLayout()
        sync_col.setSpacing(0)
        sync_lbl = QLabel(i18n.t("look.sync_accent"))
        sync_lbl.setObjectName("muted")
        sync_col.addWidget(sync_lbl)
        sync_hint = QLabel(i18n.t("look.sync_accent_hint"))
        sync_hint.setObjectName("hint")
        sync_col.addWidget(sync_hint)
        sync_row.addLayout(sync_col)
        sync_row.setAlignment(sync_col, Qt.AlignmentFlag.AlignVCenter)  # v4.4.10
        sync_row.addStretch()
        look_grid.addWidget(self._wrap_row(sync_row), 1, 1)

        lbl_lang = QLabel(i18n.t("look.language"))
        lbl_lang.setObjectName("fieldLabel")
        self.segment_lang = Segmented(
            [(v, i18n.t(k)) for v, k in LANGS], s.get("lang", "fa"))
        self.segment_lang.changed.connect(self._on_lang)
        look_grid.addWidget(lbl_lang, 2, 0)
        look_grid.addWidget(self.segment_lang, 2, 1)
        look_grid.setColumnStretch(1, 1)
        cvl.addLayout(look_grid)

        # v6.0 — سوییچ ویجت شناور دسکتاپ
        ov_row = QHBoxLayout()
        ov_row.setSpacing(10)
        self.switch_overlay = Switch(bool(s.get("overlay_enabled", False)))
        self.switch_overlay.toggled.connect(self._on_overlay_toggle)
        ov_row.addWidget(self.switch_overlay)
        ov_col = QVBoxLayout()
        ov_col.setSpacing(0)
        ov_lbl = QLabel(i18n.t("look.widget"))
        ov_lbl.setObjectName("muted")
        ov_col.addWidget(ov_lbl)
        ov_hint = QLabel(i18n.t("look.widget_hint"))
        ov_hint.setObjectName("hint")
        ov_hint.setWordWrap(True)
        ov_col.addWidget(ov_hint)
        ov_row.addLayout(ov_col)
        ov_row.setAlignment(ov_col, Qt.AlignmentFlag.AlignVCenter)
        ov_row.addStretch()
        cvl.addLayout(ov_row)
        root.addWidget(cv)

        # ---------- کارت به‌روزرسانی (v6.0) ----------
        cu, cul = card()
        add_shadow(cu, blur=34, alpha=30, dy=10)
        cul.addLayout(caption_block(
            i18n.t("upd.eyebrow"), i18n.t("upd.title"), tone="sky"))
        upd_switch_row = QHBoxLayout()
        upd_switch_row.setSpacing(10)
        self.switch_update = Switch(bool(s.get("update_check", True)))
        self.switch_update.toggled.connect(self._on_update_check)
        upd_switch_row.addWidget(self.switch_update)
        upd_col = QVBoxLayout()
        upd_col.setSpacing(0)
        upd_lbl = QLabel(i18n.t("upd.check_switch"))
        upd_lbl.setObjectName("muted")
        upd_col.addWidget(upd_lbl)
        upd_switch_row.addLayout(upd_col)
        upd_switch_row.setAlignment(upd_col, Qt.AlignmentFlag.AlignVCenter)
        upd_switch_row.addStretch()
        cul.addLayout(upd_switch_row)
        upd_row = QHBoxLayout()
        upd_row.setSpacing(10)
        self.lbl_upd_ver = QLabel(i18n.t("upd.current", v=num(VERSION)))
        self.lbl_upd_ver.setObjectName("hint")
        upd_row.addWidget(self.lbl_upd_ver, 1)
        self.btn_check_upd = JellyButton(i18n.t("upd.check_now"))
        self.btn_check_upd.setObjectName("ghost")
        self.btn_check_upd.setCursor(Qt.PointingHandCursor)
        self.btn_check_upd.setFixedHeight(42)
        self.btn_check_upd.clicked.connect(self.check_updates_requested.emit)
        upd_row.addWidget(self.btn_check_upd)
        cul.addLayout(upd_row)
        self.lbl_upd_status = QLabel("")
        self.lbl_upd_status.setObjectName("hint")
        self.lbl_upd_status.setWordWrap(True)
        cul.addWidget(self.lbl_upd_status)
        root.addWidget(cu)
        root.addStretch()

        return self._scroll_wrap(body)

    def _wrap_row(self, row: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(row)
        return w

    # ---------- صفحه‌ی راهنما ----------

    def _page_help(self) -> QScrollArea:
        body, root = self._page_shell()
        sub = QLabel(i18n.t("help.sub"))
        sub.setObjectName("muted")
        root.addLayout(caption_block(i18n.t("help.eyebrow"), i18n.t("help.title"), sub,
                                     tone="amber"))

        # v4.3: سوال «دوبار کلیک» حذف شد — به درخواست کاربر؛ پنج سوالِ
        # پرکاربرد کافی است و صفحه سبک‌تر می‌ماند
        # v4.4.7: آیکون سرِ پرسش‌ها کلاً حذف شد — به درخواست کاربر؛
        # سوال و پاسخ خالص، بدون کاشی
        for i in range(1, 6):
            cf, cl = card()
            add_shadow(cf, blur=26, alpha=22, dy=8)
            q = QLabel(i18n.t(f"help.q{i}"))
            q.setObjectName("h2")
            q.setWordWrap(True)
            cl.addWidget(q)
            a = QLabel(i18n.t(f"help.a{i}"))
            a.setObjectName("body")
            a.setWordWrap(True)
            cl.addWidget(a)
            root.addWidget(cf)
        root.addStretch()
        return self._scroll_wrap(body)

    # ---------- صفحه‌ی درباره ----------

    def _page_about(self) -> QScrollArea:
        body, root = self._page_shell()
        root.addLayout(caption_block(i18n.t("about.eyebrow"), i18n.t("about.title"),
                                     tone="rose"))

        brand = GlassCard(radius=20)
        add_shadow(brand, blur=34, alpha=30, dy=10)
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(20, 20, 20, 18)
        bl.setSpacing(8)
        # نشان «درباره ما» — دو چهره + واژه‌نگار (مثل تصویر مرجع کاربر)
        bl.addWidget(AboutUsLogo(), 0, Qt.AlignmentFlag.AlignHCenter)
        name = QLabel(i18n.t("app.name"))
        name.setObjectName("h1")
        name.setAlignment(Qt.AlignCenter)
        bl.addWidget(name)
        ver = QLabel(f"{i18n.t('app.version')} {num(VERSION)}  •  {i18n.t('app.tagline')}")
        ver.setObjectName("hint")
        ver.setAlignment(Qt.AlignCenter)
        bl.addWidget(ver)
        story = QLabel(i18n.t("about.story"))
        story.setObjectName("body")
        story.setWordWrap(True)
        bl.addSpacing(4)
        bl.addWidget(story)
        root.addWidget(brand)

        # سه ویژگی کلیدی — v4.4.8: خانه‌ی «هم‌رنگ ویندوز» حذف شد (به درخواست کاربر)؛
        # گرید از ۲×۲ به سه خانه رسید
        feats_card, fcl = card()
        add_shadow(feats_card, blur=26, alpha=22, dy=8)
        fcl.addLayout(caption_block(i18n.t("about.feats_eyebrow"), i18n.t("about.feats_title"),
                                    tone="rose"))
        fgrid = QGridLayout()
        fgrid.setHorizontalSpacing(18)
        fgrid.setVerticalSpacing(12)
        for i, (kind, glyph, tk, sk) in enumerate((
            ("indigo", "bill", "about.f1t", "about.f1s"),
            ("rose", "bell", "about.f2t", "about.f2s"),
            ("sky", "faen", "about.f3t", "about.f3s"),
        )):
            cell = QHBoxLayout()
            cell.setSpacing(10)
            cell.addWidget(IconChip(kind, glyph, 34))
            c2 = QVBoxLayout()
            c2.setSpacing(1)
            ft = QLabel(i18n.t(tk))
            ft.setObjectName("muted")
            f2 = QFont()
            f2.setWeight(QFont.Weight.DemiBold)
            ft.setFont(f2)
            fs = QLabel(i18n.t(sk))
            fs.setObjectName("hint")
            fs.setWordWrap(True)
            c2.addWidget(ft)
            c2.addWidget(fs)
            cell.addLayout(c2, 1)
            cell.setAlignment(c2, Qt.AlignmentFlag.AlignVCenter)  # v4.4.10
            wrap = QWidget()
            wrap.setLayout(cell)
            fgrid.addWidget(wrap, i // 2, i % 2)
        fgrid.setColumnStretch(0, 1)
        fgrid.setColumnStretch(1, 1)
        fcl.addLayout(fgrid)
        root.addWidget(feats_card)

        # v4.4.6 — خط‌های «طراحی/فونت‌ها/منبع داده» (بخش لایسنس) کلاً از برنامه
        # حذف شد؛ اطلاعات لایسنس فقط در انتهای README گیت‌هاب می‌ماند

        foot = QLabel(f"{i18n.t('about.disclaimer')}\n\n{i18n.t('about.made')}")
        foot.setObjectName("hint")
        foot.setAlignment(Qt.AlignCenter)
        foot.setWordWrap(True)
        root.addWidget(foot)
        root.addStretch()
        return self._scroll_wrap(body)

    # ---------- رفتار ناوبری ----------

    def _on_nav(self, key: str):
        self._switch_page(key)

    def show_page(self, key: str):
        self.nav.set_current(key)
        self._switch_page(key)

    def _switch_page(self, key: str):
        """جابه‌جایی صفحه‌ها (v6.0 — بریف: انیمیشن نرم بین صفحات):
        لغزشِ افقیِ سبکِ صفحه‌ی جدید با QPropertyAnimation روی پراپرتی pos —
        برخلاف fadeِ قدیمی (QGraphicsOpacityEffect)، هیچ افکت گرافیکیِ
        باک‌انده در GPU ویندوز در کار نیست؛ فقط جابه‌جاییِ واقعیِ ویجت است
        و روی هر سخت‌افزاری صاف اجرا می‌شود. جهتِ لغزش با ترتیب صفحات و
        RTL هماهنگ است (پیشرو = از سمتِ جلو وارد می‌شود)."""
        page = self.pages.get(key)
        if page is None:
            return
        old_key = getattr(self, "_current_page", key)
        if self.stack.currentWidget() is page:
            self._current_page = key
            return
        self.stack.setCurrentWidget(page)
        self._current_page = key
        if not os_env_anim():
            page.move(0, 0)
            return
        order = list(self.pages.keys())   # dashboard, settings, help, about
        try:
            forward = order.index(key) >= order.index(old_key)
        except ValueError:
            forward = True
        rtl = i18n.is_rtl()
        dx = (1 if forward else -1) * (1 if rtl else -1) * 40
        # قتلِ انیمیشن قبلی — سفرهای پشت‌سرهم هیچ‌وقت قاطی نمی‌شوند
        if self._page_anim is not None:
            try:
                self._page_anim.stop()
                self._page_anim.deleteLater()
            except RuntimeError:
                pass
            self._page_anim = None
        end = QPoint(0, 0)
        page.move(end)
        anim = QPropertyAnimation(page, b"pos", self)
        anim.setStartValue(QPoint(dx, 0))
        anim.setEndValue(end)
        anim.setDuration(270)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda p=page: p.move(QPoint(0, 0)))
        self._page_anim = anim
        anim.start()

    # ---------- v6.0 — صدا و هشدار ----------

    def _on_sound_scheme(self, idx: int):
        key = self.combo_sound.itemData(idx)
        if key:
            self.settings["sound_scheme"] = str(key)
            self._settings_timer.start()

    def _test_sound(self):
        sounds.play(self.combo_sound.currentData(), None, force=True)

    def _sync_mute_switch(self):
        import time as _time
        muted = int(self.settings.get("mute_until", 0) or 0) > _time.time()
        self.switch_mute.blockSignals(True)
        self.switch_mute.setChecked(muted)
        self.switch_mute.blockSignals(False)
        if muted:
            from datetime import datetime as _dt
            t = _dt.fromtimestamp(int(self.settings.get("mute_until", 0)))
            self.lbl_mute_hint.setText(
                i18n.t("sound.muted_until", t=num(t.strftime("%H:%M"))))
        else:
            self.lbl_mute_hint.setText(i18n.t("sound.mute_hint"))

    def _on_temp_mute(self, on: bool):
        import time as _time
        if on:
            self.settings["mute_until"] = int(_time.time()) + 3600
        else:
            self.settings["mute_until"] = 0
        self._sync_mute_switch()
        self._settings_timer.start()

    def _on_overlay_toggle(self, on: bool):
        if not self._identity_applied:
            return
        self.settings["overlay_enabled"] = bool(on)
        storage.save()
        self.overlay_toggled.emit(bool(on))

    def _on_update_check(self, on: bool):
        if not self._identity_applied:
            return
        self.settings["update_check"] = bool(on)
        storage.save()

    # ---------- v6.0 — سوییچر قبض‌ها و تاریخچه ----------

    def _on_switch_bill(self, bill_id: str):
        """تبِ قبض فعال عوض شد — ذخیره + انتشار برای ری‌استارت پولر"""
        if not bill_id:
            return
        bills = storage.bills()
        if bill_id != (storage.active_bill() or {}).get("bill_id", ""):
            storage.set_bills(bills, bill_id)
            self.settings.update(storage.load())
            self.bill_switch.set_active(bill_id)
            self.update_identity()
            self.active_bill_changed.emit(bill_id)

    def _on_hist_range(self, rng: str):
        self._refresh_history()

    def _refresh_history(self):
        """نمودار تاریخچه از داده‌های ثبت‌شده در storage (v6.0)"""
        rng = 7 if getattr(self, "hist_card", None) and \
            self.hist_card.range_value() == "7" else 30
        days = storage.history_days(rng)
        self.hist_card.set_data(days)

    def refresh_dynamic_controls(self):
        """سوییچ‌هایی که وضعیتشان بیرون از پنجره عوض می‌شود (ویجت/بی‌صدا)"""
        if hasattr(self, "switch_overlay"):
            self.switch_overlay.blockSignals(True)
            self.switch_overlay.setChecked(
                bool(self.settings.get("overlay_enabled", False)))
            self.switch_overlay.blockSignals(False)
        if hasattr(self, "switch_mute"):
            self._sync_mute_switch()

    # ---------- v6.0 — بنر وضعیت سرویس ----------

    def show_service_banner(self, kind: str, health: list = None):
        if hasattr(self, "svc_banner"):
            self.svc_banner.set_state(kind, health)

    def hide_service_banner(self):
        if hasattr(self, "svc_banner"):
            self.svc_banner.setVisible(False)

    def set_service_health(self, health: list):
        if hasattr(self, "svc_banner") and self.svc_banner.isVisible():
            self.svc_banner.set_health(health)

    # ---------- v6.0 — به‌روزرسانی ----------

    def set_update_status(self, text: str):
        if hasattr(self, "lbl_upd_status"):
            self.lbl_upd_status.setText(text)

    def show_update_dialog(self, info: dict):
        dlg = UpdateDialog(info, self)
        dlg.exec()

    # ---------- تنظیمات (دپ‌بان) ----------

    def _queue_settings(self, *_):
        """کنترل‌ها فقط تغییر را صف می‌کنند — اعمال واقعی با تاخیر"""
        if not self._identity_applied:
            return
        mode = self.segment.value()
        self.settings["mode"] = mode
        self.settings["default_action"] = self.combo_action.currentData()
        self.settings["lead_minutes"] = int(self.spin_lead.value())
        self.settings["notify_seconds"] = int(self.spin_notify.value())
        self.settings["poll_minutes"] = int(self.spin_poll.value())
        self.mode_desc.setText(i18n.t(MODE_DESC.get(mode, "")))
        self._sync_action_hint()
        self._refresh_armed_hint()
        self._refresh_stats()
        # انتشار بلافاصله نیست؛ ۴۵۰ms بعد از آخرین تغییر
        self._settings_timer.start()

    def _refresh_armed_hint(self):
        """متن وضعیت مسلح یادآور — پیش‌آگاهیِ دقیقه‌شمار + طول پنجره‌ی واکنش"""
        if hasattr(self, "lbl_armed"):
            self.lbl_armed.setText(i18n.t(
                "set.armed_hint",
                lead=num(int(self.settings.get("lead_minutes", 10))),
                secs=num(int(self.settings.get("notify_seconds", 15)))))

    def update_last_warn(self):
        """ردپای آخرین هشدار شلیک‌شده را از storage می‌خواند؛
        کنترل‌کننده بعد از هر شلیک هم این را صدا می‌زند"""
        if not hasattr(self, "lbl_last_warn"):
            return
        lw = storage.last_warn()
        if lw.get("at") and lw.get("summary"):
            self.lbl_last_warn.setText(i18n.t(
                "set.last_warn", t=num(lw["at"]), summary=lw["summary"]))
        else:
            self.lbl_last_warn.setText(i18n.t("set.last_warn_none"))

    def _commit_clicked(self):
        """دکمه‌ی ثبت: ذخیره‌ی فوری + تأییدِ دیدنیِ «ست شده»
        (درخواست کاربر: من یقین پیدا کنم ست شده)"""
        if not self._identity_applied:
            return
        self._settings_timer.stop()
        self._commit_settings()
        self.btn_commit.setText(i18n.t("set.saved"))
        self.lbl_saved.setText(i18n.t("set.saved_confirm"))
        self._refresh_armed_hint()
        self._saved_timer.start()

    def _clear_saved_feedback(self):
        """بازگشت دکمه به حالت عادی بعد از چند ثانیه"""
        self.btn_commit.setText(i18n.t("set.save"))
        self.lbl_saved.setText("")

    def _commit_settings(self):
        storage.save()
        self.settings_changed.emit()

    def _sync_action_hint(self):
        key = self.combo_action.currentData()
        self.lbl_action_hint.setText(i18n.t(ACTION_HINTS.get(key, "")))

    def _refresh_stats(self):
        """مقادیر کاشی‌های آمار را از تنظیمات و آخرین اسنپ‌شات تازه می‌کند"""
        p = self._last_snapshot
        self.stat_planned.set_value(f"{num(len(p.get('planned') or []))} {i18n.t('dash.count_unit')}")
        self.stat_occurred.set_value(f"{num(len(p.get('occurred') or []))} {i18n.t('dash.count_unit')}")
        self.stat_lead.set_value(f"{num(self.settings.get('lead_minutes', 10))} {i18n.t('dash.minutes')}")
        self.stat_poll.set_value(f"{num(self.settings.get('poll_minutes', 5))} {i18n.t('dash.minutes')}")

    def _apply_autostart(self, checked: bool):
        if not self._identity_applied:
            return
        self.settings["autostart"] = checked
        err = storage.set_autostart(checked)
        storage.save()
        if err:
            box = QMessageBox(self)
            box.setWindowTitle(i18n.t("app.name"))
            box.setIcon(QMessageBox.Warning)
            box.setText(i18n.t("set.autostart_fail", err=err))
            box.addButton(i18n.t("set.ok"), QMessageBox.AcceptRole)
            box.exec()

    # ---------- قبض‌ها ----------

    def _rebuild_bill_rows(self):
        while self.bills_box.count():
            item = self.bills_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        bills = storage.bills()
        active = (storage.active_bill() or {}).get("bill_id", "")
        for b in bills:
            row_card = GlassCard(radius=14)
            row_lay = QHBoxLayout(row_card)
            row_lay.setContentsMargins(10, 8, 10, 8)
            row_lay.setSpacing(10)
            row_lay.addWidget(IconChip("indigo", "bill", 34))
            col = QVBoxLayout()
            col.setSpacing(0)
            # تراز فیزیکی: عنوان قبض داده‌ی فارسی است و در UI انگلیسی هم
            # باید سرِ ستونِ شروع بنشیند (رفع چیدمان شکسته‌ی ردیف قبض‌ها)
            from widgets import _phys_align
            start = _phys_align()
            t = QLabel(b.get("bill_title") or "—")
            t.setObjectName("muted")
            t.setAlignment(start)
            i_lbl = QLabel(f"{num(b.get('bill_id'))}")
            i_lbl.setObjectName("hint")
            i_lbl.setAlignment(start)
            col.addWidget(t)
            col.addWidget(i_lbl)
            row_lay.addLayout(col, 1)
            row_lay.setAlignment(col, Qt.AlignmentFlag.AlignVCenter)  # v4.4.10
            active_chip = QLabel(i18n.t("bills.active"))
            active_chip.setObjectName("chip")
            active_chip.setProperty("kind", "later")
            active_chip.setVisible(b.get("bill_id") == active)
            row_lay.addWidget(active_chip)
            btn_rm = JellyButton(i18n.t("bills.remove"))
            btn_rm.setObjectName("ghost")
            btn_rm.setCursor(Qt.PointingHandCursor)
            btn_rm.setFixedHeight(34)
            btn_rm.clicked.connect(
                lambda _, bid=b.get("bill_id"), bti=b.get("bill_title"):
                self._remove_bill(bid, bti))
            row_lay.addWidget(btn_rm)
            self.bills_box.addWidget(row_card)

    def _add_bill(self):
        existing = {b.get("bill_id") for b in storage.bills()}
        dlg = BillPickerDialog(existing, self)
        if dlg.exec() and dlg.selected:
            cur = storage.bills()
            cur.append(dlg.selected)
            storage.set_bills(cur, (storage.active_bill() or {}).get("bill_id"))
            self.settings.update(storage.load())
            self._rebuild_bill_rows()
            self.bills_changed.emit(storage.bills())

    def _remove_bill(self, bill_id: str, title: str):
        bills = storage.bills()
        if len(bills) <= 1:
            box = QMessageBox(self)
            box.setWindowTitle(i18n.t("app.name"))
            box.setIcon(QMessageBox.Information)
            box.setText(i18n.t("bills.last_one"))
            box.addButton(i18n.t("set.ok"), QMessageBox.AcceptRole)
            box.exec()
            return
        box = QMessageBox(self)
        box.setWindowTitle(i18n.t("bills.remove"))
        box.setIcon(QMessageBox.Question)
        box.setText(i18n.t("bills.remove_confirm", title=title))
        yes = box.addButton(i18n.t("bills.remove_yes"), QMessageBox.YesRole)
        box.addButton(i18n.t("dash.cancel"), QMessageBox.NoRole)
        box.exec()
        if box.clickedButton() is not yes:
            return
        rest = [b for b in bills if b.get("bill_id") != bill_id]
        active = (storage.active_bill() or {}).get("bill_id", "")
        new_active = active if active != bill_id else rest[0]["bill_id"]
        storage.set_bills(rest, new_active)
        self.settings.update(storage.load())
        self._rebuild_bill_rows()
        self.bills_changed.emit(storage.bills())
        self.active_bill_changed.emit(new_active)

    # ---------- ظاهر و زبان ----------

    def _cycle_theme(self):
        """دکمه‌ی تم نوار کناری: چرخه‌ی system → light → dark → system
        هم‌گام با سگمنت «تم برنامه» در تنظیمات."""
        order = ["system", "light", "dark"]
        cur = self.settings.get("theme_mode", "system")
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "system"
        if hasattr(self, "segment_theme"):
            self.segment_theme.set_current(nxt)
        self._on_theme_mode(nxt)

    def _toggle_lang(self):
        """دکمه‌ی زبان نوار کناری (v4.4.9) — تعویض فوری fa↔en؛
        همان مسیر سگمنت زبان: ذخیره + سیگنال بازسازی"""
        self._on_lang("en" if i18n.lang() == "fa" else "fa")

    def _on_theme_mode(self, mode: str):
        if not self._identity_applied:
            return
        self.settings["theme_mode"] = mode
        storage.save()
        self.theme_mode_changed.emit(mode)

    def _on_sync_windows(self, on: bool):
        if not self._identity_applied:
            return
        self.settings["sync_windows"] = on
        storage.save()
        self.sync_windows_changed.emit(on)

    def _on_lang(self, lang: str):
        if not self._identity_applied:
            return
        self.settings["lang"] = lang
        storage.save()
        self.lang_changed.emit(lang)

    def _confirm_logout(self):
        box = QMessageBox(self)
        box.setWindowTitle(i18n.t("dash.logout"))
        box.setIcon(QMessageBox.Question)
        box.setText(i18n.t("dash.logout_confirm"))
        yes = box.addButton(i18n.t("dash.logout_yes"), QMessageBox.YesRole)
        box.addButton(i18n.t("dash.cancel"), QMessageBox.NoRole)
        box.exec()
        if box.clickedButton() is yes:
            self.logout_requested.emit()

    # ---------- بروزرسانی‌ها ----------

    def update_identity(self):
        bills = storage.bills()
        active = storage.active_bill() or {}
        mobile = self.settings.get("mobile") or "—"
        if len(bills) > 1:
            text = i18n.t(
                "hdr.bills_line", n=num(len(bills)), title=active.get("bill_title", "—"),
                id=num(active.get("bill_id", "—")), mobile=num(mobile))
        else:
            text = i18n.t(
                "hdr.bill_line", title=active.get("bill_title", "—"),
                id=num(active.get("bill_id", "—")), mobile=num(mobile))
        # خط دوم سربرگ بلند است (عنوان + شناسه + موبایل)؛ عرضِ بریده‌شدن
        # داینامیک است (v5.1): متنِ کامل نگه داشته می‌شود و در resizeEvent
        # به عرضِ واقعیِ لیبل بریده می‌شود — دیگر در پنجره‌ی باریک سرریز نمی‌کند
        self._bill_text_full = text
        self._reelide_bill()

    def _reelide_bill(self):
        """بریدنِ متنِ قبض‌ها به عرضِ واقعیِ لیبل (رفعِ سربارگیِ سربرگ)"""
        if not hasattr(self, "_bill_text_full"):
            return
        w = max(120, self.lbl_bill.width() - 2)
        fm = QFontMetrics(self.lbl_bill.font())
        self.lbl_bill.setText(fm.elidedText(self._bill_text_full,
                                            Qt.ElideMiddle, w))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # بعد از چیدمان، عرضِ نهایی لیبل معلوم می‌شود — یک‌بار در صف
        QTimer.singleShot(0, self._reelide_bill)

    def update_snapshot(self, snap: dict):
        self._last_snapshot = snap
        occurred = snap.get("occurred") or []
        planned = snap.get("planned") or []
        multi = bool(snap.get("multi_bills"))
        has_any = fill_outage_list(self.outage_list, occurred, planned, multi)
        self.outage_list.setVisible(has_any)
        self.empty_state.setVisible(not has_any)
        checked = snap.get("checked_at")
        self.lbl_last.setText(
            i18n.t("conn.last_check", t=num(checked)) if checked
            else i18n.t("conn.last_check", t="—")
        )
        # خلاصه‌ی پایین کارت — شمارنده‌ی زنده‌ی خاموشی‌ها با راهنمای رنگی
        n_up, n_today = len(planned), len(occurred)
        has_any_count = bool(n_up or n_today)
        self.dot_upcoming.setVisible(has_any_count)
        self.dot_today.setVisible(has_any_count)
        self.lbl_today.setVisible(has_any_count)
        if has_any_count:
            self.lbl_upcoming.setText(i18n.t("dash.footer_up", p=num(n_up)))
            self.lbl_today.setText(i18n.t("dash.footer_today", o=num(n_today)))
        else:
            self.lbl_upcoming.setText(i18n.t("dash.footer_none"))
        bills = storage.bills()
        self.lbl_footer_bill.setText(
            i18n.t("hdr.bills_n", n=num(len(bills))) if len(bills) > 1 else "")
        # v6.0 — سوییچر قبض‌ها فقط در پایش چند-قبضی ظاهر می‌شود
        if hasattr(self, "bill_switch"):
            active_id = (storage.active_bill() or {}).get("bill_id", "")
            self.bill_switch.rebuild(bills, active_id)
        # v6.0 — نمودار تاریخچه با هر اسنپ‌شات تازه شود
        self._refresh_history()
        # کارت هیرو: نزدیک‌ترین خاموشیِ آینده
        from datetime import datetime as _dt
        from util import outage_addr as _oa
        now = _dt.now()
        nxt = None
        candidates = []
        for o in planned:
            d = outage_datetime(o)
            if d and d > now:
                candidates.append((d, o))
        candidates.sort(key=lambda x: x[0])
        if candidates:
            nxt = dict(candidates[0][1])
            # نشان قبض روی هیرو — همان قانون لیست (فقط در پایش چند-قبضی)
            nxt["_multi"] = multi
        self.hero.set_next(nxt)
        # v5.0 — چیپ موقعیت سربرگ: آدرسِ واقعیِ نزدیک‌ترین خاموشیِ آینده؛
        # بدون داده، چیپ پنهان می‌شود (هیچ‌وقت آدرسِ قلابی نشان نمی‌دهیم)
        self.loc.set_address(_oa(nxt) if nxt else "")
        self._refresh_stats()

    def set_connection(self, text: str, state):
        """state: True متصل | False مشکل | None نامشخص"""
        self.pill.set_state(text, {True: "ok", False: "bad", None: "unknown"}[state])

    def closeEvent(self, event):
        # بستن پنجره = مخفی شدن به تری؛ خروج واقعی فقط از منوی تری
        event.ignore()
        self.hide()


def _vwrap(lbl: QLabel) -> QVBoxLayout:
    v = QVBoxLayout()
    v.setSpacing(0)
    v.addWidget(lbl)
    return v


# ---------- دیالوگ نسخه‌ی جدید + تغییرات درون‌برنامه‌ای (v6.0) ----------

class UpdateDialog(QDialog):
    """«نسخه‌ی جدید اومده» + فهرست تغییرات (changelog) از GitHub Releases؛
    چهره‌ی شیشه‌ای هم‌خانواده — و بدون هیچ نصبِ خودکار: دانلود فقط با
    کلیکِ خودِ کاربر انجام می‌شود."""

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle(i18n.t("upd.dialog_title"))
        self.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
        self.setFixedWidth(520)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        canvas = BackdropCanvas(self)
        canvas.setObjectName("central")
        root.addWidget(canvas)
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(26, 22, 26, 20)
        lay.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(IconChip("sky", "rocket", 42))
        col = QVBoxLayout()
        col.setSpacing(1)
        t = QLabel(i18n.t("upd.found", v=num(info.get("version", "?"))))
        t.setObjectName("h1")
        sub = QLabel(i18n.t("upd.notes"))
        sub.setObjectName("muted")
        col.addWidget(t)
        col.addWidget(sub)
        head.addLayout(col, 1)
        lay.addLayout(head)

        notes = str(info.get("notes") or "").strip() or i18n.t("upd.notes_empty")
        box = QTextBrowser()
        box.setOpenExternalLinks(False)
        box.setPlainText(notes)
        box.setMinimumHeight(180)
        lay.addWidget(box, 1)

        row = QHBoxLayout()
        row.setSpacing(8)
        btn_later = JellyButton(i18n.t("dash.cancel"))
        btn_later.setObjectName("ghost")
        btn_later.setMinimumHeight(44)
        btn_later.clicked.connect(self.reject)
        row.addWidget(btn_later)
        btn_dl = JellyButton(i18n.t("upd.download"))
        btn_dl.setObjectName("primary")
        btn_dl.setMinimumHeight(46)
        btn_dl.clicked.connect(self._download)
        row.addWidget(btn_dl, 1)
        lay.addLayout(row)

    def _download(self):
        import webbrowser
        url = self.info.get("url") or updater.releases_url()
        try:
            webbrowser.open(url)
        except Exception:
            pass
        self.accept()
