# warn_dialog.py — پنجره‌ی هشدار «T ثانیه فرصت واکنش» با حلقه‌ی شمارش معکوس
# ---------------------------------------------------------------------------
# v4.4.4 — تایمر اعلان دستِ خود کاربر است (نه زمان خاموشی): پنجره فقط
# «react_secs» ثانیه باز می‌ماند؛ اگر تا پایانش هیچ دکمه‌ای نره،
# اقدام پیش‌فرض خودکار اجرا می‌شود.
# v4: همه‌ی متن‌ها از i18n (فارسی/انگلیسی + RTL/LTR خودکار)؛ ارقام مطابق زبان.
# ظاهر Aura Glass: بوم شفق با ته‌مایه‌ی سرخ، حلقه‌ی گرادیانی هاله‌دار،
# دکمه‌های آیکون‌دار SVG — بدون هیچ ایموجی.
import math
import time

from PySide6.QtCore import Qt, QRectF, QTimer, Signal
from PySide6.QtGui import (
    QConicalGradient, QColor, QFont, QFontMetrics, QPainter, QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
    QWidget,
)

import i18n
import icons
import power
import theme
from util import outage_addr, outage_datetime, outage_summary
from widgets import BackdropCanvas, GlassCard, IconChip, JellyButton, qcolor

# نام کنش‌ها — مقدار، کلید i18n است (برای توست تری هم استفاده می‌شود)
ACTION_KEY_NAMES = {
    "shutdown": "set.act_shutdown",
    "sleep": "set.act_sleep",
    "hibernate": "set.act_hibernate",
}

# آیکون SVG هر دکمه‌ی کنش
ACTION_ICONS = {
    "shutdown": "power",
    "sleep": "moon",
    "hibernate": "snow",
}


class IconedButton(QPushButton):
    """دکمه با آیکون SVG تم‌آگاه در سمت راستِ متن (RTL)"""

    def __init__(self, text: str, glyph: str, kind: str = "indigo", parent=None):
        super().__init__(text, parent)
        self._glyph = glyph
        self._kind = kind
        self.setMinimumHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self._sync_icon()

    def repaint_theme(self):
        self._sync_icon()

    def _sync_icon(self):
        chips = theme.chips()
        c = chips.get(self._kind, chips["indigo"])
        self.setIcon(icons.icon_qicon(self._glyph, 18, c["fg"], c["fg"]))


class RingWidget(QWidget):
    """حلقه‌ی پیشرفت شمارش معکوس — گرادیان مخروطی خطر→هشدار با هاله‌ی نرم.
    v4.1: دیسک شیشه‌ای داخل حلقه بسترِ متن می‌شود و اندازه‌ی قلم شمارش
    خودتنظیم است تا عدد هرگز از داخل حلقه بیرون نزند."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(184, 184)
        self._fraction = 1.0
        self._font_px = 30

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.count = QLabel("--:--")
        self.count.setObjectName("warnCount")
        self.count.setAlignment(Qt.AlignCenter)
        self.hint = QLabel(i18n.t("warn.until_auto"))
        self.hint.setObjectName("warnHint")
        self.hint.setAlignment(Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.count)
        lay.addWidget(self.hint)
        lay.addStretch()

    def set_text(self, text: str):
        """متن شمارش با خودتنظیمی قلم — تا در دیسک داخلی جا شود"""
        self.count.setText(text)
        # قطر داخلی مفید: ۱۸۴ − ۲×۱۶ (حاشیه‌ی مسیر) − ۲×۱۲ (ضخامت قلم) − ۲×۱۰ (ایمنی)
        avail = 184 - 32 - 24 - 20
        px = 30
        while px > 16:
            f = QFont(theme.display_family(900))
            f.setPixelSize(px)
            f.setWeight(QFont.Weight.Black)
            f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            if QFontMetrics(f).horizontalAdvance(text) <= avail:
                break
            px -= 1
        if px != self._font_px:
            self._font_px = px
            self.count.setStyleSheet(
                f"font-family: \"{theme.display_family(900)}\"; font-size: {px}px;"
                "font-weight: 900; background: transparent;"
            )

    def set_fraction(self, f: float):
        self._fraction = max(0.0, min(1.0, f))
        self.update()

    def paintEvent(self, event):
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(16, 16, -16, -16)
        # دیسک داخلی شیشه‌ای — بستر متن شمارش؛ حلقه را از متن جدا می‌کند
        disc = QRadialGradient(rect.center().x(), rect.center().y() - 14,
                               rect.width() * 0.62)
        disc.setColorAt(0, qcolor(p["ring_fill"]))
        disc.setColorAt(1, QColor(255, 255, 255, 0))
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(disc)
        pnt.drawEllipse(rect.adjusted(7, 7, -7, -7))
        # مسیر خالی — فراستی
        pen = QPen(QColor(255, 255, 255, 46 if theme.current_name() == "light" else 30),
                   12, Qt.SolidLine, Qt.RoundCap)
        pnt.setPen(pen)
        pnt.drawArc(rect, 0, 360 * 16)
        # پیشرفت (از بالای حلقه، پادساعت‌گرد) با گرادیان مخروطی
        if self._fraction > 0:
            grad = QConicalGradient(rect.center(), 90)
            grad.setColorAt(0.0, QColor(p["danger"]))
            grad.setColorAt(0.55, QColor(p["danger"]))
            grad.setColorAt(1.0, QColor(p["warn"]))
            # هاله‌ی زیر قوس — نورِ شیشه
            glow = QPen(QColor(255, 84, 102, 60), 20, Qt.SolidLine, Qt.RoundCap)
            pnt.setPen(glow)
            pnt.drawArc(rect, 90 * 16, int(-360 * 16 * self._fraction))
            pen = QPen()
            pen.setWidth(12)
            pen.setCapStyle(Qt.RoundCap)
            pen.setBrush(grad)
            pnt.setPen(pen)
            pnt.drawArc(rect, 90 * 16, int(-360 * 16 * self._fraction))
        pnt.end()


class WarnDialog(QDialog):
    """هشدار همیشه‌روشن با «تایمر واکنش» کاربر (v4.4.4):
    پنجره فقط react_secs ثانیه باز می‌ماند؛ کاربر یکی از کنش‌ها را
    انتخاب می‌کند یا انصراف می‌دهد؛ اگر تا پایان تایمرِ اعلان کاری
    نکند، کنش پیش‌فرض خودکار اجرا می‌شود — دیگر ارتباطی به لحظه‌ی
    شروع خاموشی ندارد (درخواست صریح کاربر)."""

    action_failed = Signal(str)  # نام کنشی که اجرایش شکست خورد

    def __init__(self, outage: dict, default_action: str, parent=None,
                 dry_run=False, react_secs: int = 15):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowTitle(i18n.t("warn.title"))
        self.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
        self.setFixedWidth(600)
        self.start_dt = outage_datetime(outage)
        self.default_action = default_action
        # تایمر اعلان — مستقل از زمان خاموشی؛ سقف/کف امن ۵..۶۰۰ ثانیه
        self.react_secs = max(5, min(600, int(react_secs)))
        self.executed = None
        self.dry_run = dry_run  # برای پیش‌نمایش/اسکرین‌شات: هیچ کنشی اجرا نمی‌شود
        self._t0 = time.monotonic()

        # بوم شفق با ته‌مایه‌ی سرخ — بستری که همه‌ی محتوا روی آن می‌نشیند
        canvas = BackdropCanvas(self)
        canvas.setObjectName("central")
        body_lay = QVBoxLayout(canvas)
        body_lay.setContentsMargins(22, 20, 22, 18)
        body_lay.setSpacing(14)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(canvas)

        # ---------- بنر هشدار ----------
        banner = GlassCard(radius=18)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(14, 12, 14, 12)
        banner_lay.setSpacing(12)
        bchip = IconChip("rose", "alert", 36)   # v4.7 — ۳۶px (بود ۴۲)
        banner_lay.addWidget(bchip, 0, Qt.AlignVCenter)
        btxt = QVBoxLayout()
        btxt.setSpacing(1)
        head = QLabel(i18n.t("warn.banner"))
        head.setObjectName("warnBanner")
        btxt.addWidget(head)
        bsub = QLabel(i18n.t("warn.banner_sub"))
        bsub.setObjectName("hint")
        btxt.addWidget(bsub)
        banner_lay.addLayout(btxt, 1)
        banner_lay.setAlignment(btxt, Qt.AlignmentFlag.AlignVCenter)  # v4.4.10 — تراز چیپ با متن
        body_lay.addWidget(banner)

        # ---------- حلقه و اطلاعات ----------
        info_card = GlassCard(radius=18)
        mid = QHBoxLayout(info_card)
        mid.setContentsMargins(16, 14, 16, 14)
        mid.setSpacing(20)
        self.ring = RingWidget()
        mid.addWidget(self.ring, 0, Qt.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(8)
        from widgets import _phys_align
        when = QLabel(outage_summary(outage))
        when.setAlignment(_phys_align())
        when.setStyleSheet(
            f"font-family: \"{theme.display_family(800)}\"; font-size: 15.5px; font-weight: 800;")
        addr = outage_addr(outage) or i18n.t("dash.unknown_addr")
        addr_lbl = QLabel(addr)
        addr_lbl.setWordWrap(True)
        addr_lbl.setAlignment(_phys_align())
        addr_lbl.setObjectName("muted")
        act = QLabel(i18n.t(
            "warn.default", a=i18n.t(ACTION_KEY_NAMES.get(default_action, default_action))))
        act.setObjectName("hint")
        info.addWidget(when)
        info.addWidget(addr_lbl)
        info.addStretch()
        info.addWidget(act)
        mid.addLayout(info, 1)
        body_lay.addWidget(info_card)

        self.note = QLabel(i18n.t(
            "warn.note",
            a=i18n.t(ACTION_KEY_NAMES.get(default_action, default_action)),
            s=i18n.num(self.react_secs)))
        self.note.setWordWrap(True)
        self.note.setObjectName("hint")
        self.note.setAlignment(Qt.AlignCenter)
        body_lay.addWidget(self.note)

        # ---------- کنش‌ها ----------
        row = QHBoxLayout()
        row.setSpacing(8)
        btn_shutdown = JellyButton(i18n.t("warn.do_shutdown"))
        btn_shutdown.setObjectName("danger")
        btn_shutdown.setMinimumHeight(48)
        btn_shutdown.setCursor(Qt.PointingHandCursor)
        btn_sleep = IconedButton(i18n.t("warn.do_sleep"), "moon", "indigo")
        btn_hiber = IconedButton(i18n.t("warn.do_hibernate"), "snow", "sky")
        btn_cancel = JellyButton(i18n.t("warn.ignore"))
        btn_cancel.setObjectName("ghost")
        btn_cancel.setMinimumHeight(48)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        # رگرسیون نسخه‌ی ۳: اتصال دکمه‌ها در بازطراحی جا افتاده بود و هر چهار
        # دکمه کاملاً بی‌عملگر شده بودند — کاربر در پنجره‌ی هشدار گیر می‌کرد.
        for b, key in (
            (btn_shutdown, "shutdown"), (btn_sleep, "sleep"),
            (btn_hiber, "hibernate"), (btn_cancel, "cancel"),
        ):
            b.clicked.connect(lambda _, a=key: self._exec(a))
        for b in (btn_shutdown, btn_sleep, btn_hiber, btn_cancel):
            row.addWidget(b, 1 if b is btn_shutdown else 0)
        body_lay.addLayout(row)

        self.timer = QTimer(self)
        self.timer.setInterval(250)  # نیم‌ثانیه‌ی قدیمی برای ثانیه‌شمار دقیق نرم است
        self.timer.timeout.connect(self._tick)
        self._t0 = time.monotonic()  # تایمر از همین لحظه، نه از ابتدای ساخت ویجت‌ها
        self.timer.start()
        self._tick()

        QApplication.beep()

    def _tick(self):
        """شمارش معکوسِ تایمرِ اعلان (نه زمان خاموشی):
        صفر شد بدون واکنش → کنش پیش‌فرض خودکار اجرا می‌شود."""
        left = self.react_secs - (time.monotonic() - self._t0)
        if left <= 0:
            self.timer.stop()
            self.ring.set_fraction(0.0)
            self.ring.set_text(i18n.num("0"))
            self._exec(self.default_action)
            return
        # اگر زمان خاموشی نامعلوم بود فقط زیرنویس حلقه عوض می‌شود؛
        # تایمر واکنش به هر حال معتبر است (سازوکار اعلام، وابسته به زمان قطع نیست)
        self.ring.hint.setText(
            i18n.t("warn.until_auto") if self.start_dt else i18n.t("warn.no_time"))
        self.ring.set_text(i18n.num(str(max(1, int(math.ceil(left))))))
        self.ring.set_fraction(left / float(self.react_secs))

    def _exec(self, action: str):
        self.timer.stop()
        self.executed = action
        if self.dry_run:
            # حالت پیش‌نمایش: فقط ثبت انتخاب، بدون هیچ دستور سیستمی
            self.accept()
            return
        ok = True
        if action == "shutdown":
            ok = power.shutdown()  # ۳۰ ثانیه فرصت لغو از تری
        elif action == "sleep":
            ok = power.sleep_now()
        elif action == "hibernate":
            ok = power.hibernate_now()
        # cancel → فقط بسته می‌شود
        if action != "cancel" and not ok:
            self.action_failed.emit(action)
        self.accept()
