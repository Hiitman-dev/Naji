# overlay.py — ویجت شناور دسکتاپ (v6.0)
# --------------------------------------------------------------------
# اولویت ۲ بریف: دیدن شمارش معکوس بدون باز کردن کل پنجره‌ی اپ.
# پنجره‌ی کوچکِ همیشه-رو، بدون قاب، شیشه‌ای (هم‌خانواده‌ی Aura Glass):
#   • شمارش معکوس زنده + عنوان قبض + نقطه‌ی وضعیت اتصال
#   • درگ با ماوس؛ موقعیت در storage ذخیره می‌شود
#   • دابل‌کلیک = باز شدن پنجره‌ی اصلی | دکمه‌ی × = بستن ویجت
from PySide6.QtCore import QPoint, QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

import i18n
import icons
import theme
from util import outage_datetime

from widgets import qcolor


def _body_font() -> str:
    return theme.FONT_BODY if i18n.is_rtl() else theme.FONT_LATIN


def _disp_font() -> str:
    return theme.display_family(800) if i18n.is_rtl() else theme.FONT_LATIN


class MiniOverlay(QWidget):
    """کارتِ کوچکِ همیشه-رو — شمارش معکوسِ همیشه جلوی چشم"""

    open_requested = Signal()     # دابل‌کلیک → پنجره‌ی اصلی
    close_requested = Signal()    # × → خاموش شدن ویجت

    W, H = 232, 132

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(self.W, self.H)
        self.setWindowTitle(i18n.t("app.name"))

        self._next_dt = None
        self._next_txt = "—"
        self._sub = ""
        self._bill = ""
        self._level = None          # True وصل | False مشکل | None نامشخص
        self._press_pos = None
        self._drag_moved = False
        self._count_font_px = 34

        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start()

    # ---------- داده ----------

    def set_next(self, outage: dict | None, bill_title: str = ""):
        self._next_dt = outage_datetime(outage) if outage else None
        self._bill = bill_title or ""
        if outage:
            from util import outage_addr
            s = i18n.num(str(outage.get("outage_start_time", "؟")))
            e = i18n.num(str(outage.get("outage_stop_time", "؟")))
            self._sub = f"{s} تا {e}" if i18n.is_rtl() else f"{s} – {e}"
            addr = outage_addr(outage)
            if addr:
                fm = QFontMetrics(QFont(_body_font(), 9))
                self._sub = fm.elidedText(
                    addr, Qt.TextElideMode.ElideMiddle, self.W - 56)
        else:
            self._sub = ""
        self._on_tick()

    def set_level(self, level):
        self._level = level
        self.update()

    def _on_tick(self):
        from datetime import datetime
        if not self._next_dt:
            txt = i18n.t("overlay.none")
        else:
            rem = (self._next_dt - datetime.now()).total_seconds()
            if rem <= 0:
                txt = i18n.t("dash.ongoing")
            elif rem >= 86400:
                d = int(rem // 86400)
                h = int((rem % 86400) // 3600)
                txt = i18n.t("dash.days_hours", d=i18n.num(d), h=i18n.num(h))
            else:
                h, m2 = divmod(int(rem), 3600)
                m, s = divmod(m2, 60)
                txt = i18n.num(f"{h:02d}:{m:02d}:{s:02d}")
        if txt != self._next_txt:
            self._next_txt = txt
            self._fit_font()
        self.update()

    def _fit_font(self):
        """قلمِ شمارش — بزرگ‌ترین سایزی که در عرض ویجت جا شود"""
        px = 34
        f = QFont(_disp_font())
        f.setWeight(QFont.Weight.Black)
        while px > 16:
            f.setPixelSize(px)
            if QFontMetrics(f).horizontalAdvance(self._next_txt) <= self.W - 40:
                break
            px -= 1
        self._count_font_px = px

    # ---------- درگ و کلیک ----------

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._drag_moved = False
            self._press_local = e.position().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._press_pos is not None and (e.buttons() & Qt.MouseButton.LeftButton):
            gp = e.globalPosition().toPoint()
            if (gp - (self.frameGeometry().topLeft() + self._press_pos)).manhattanLength() > 6:
                self._drag_moved = True
            self.move(gp - self._press_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        # کلیکِ ساده (بدون درگ) روی ناحیه‌ی گلیف × = بستن؛ بقیه = بازکردن
        if self._press_pos is not None and not self._drag_moved:
            pos = e.position().toPoint()
            if self._close_rect().contains(QPoint(pos.x(), pos.y())):
                self.close_requested.emit()
            else:
                self.open_requested.emit()
        self._press_pos = None
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.open_requested.emit()

    def moveEvent(self, e):
        super().moveEvent(e)
        # موقعیت برای اجرای بعدی ذخیره شود (فقط حافظه؛ دیسک هنگام خروج/بستن)
        try:
            import storage
            st = storage.load()
            st["overlay_pos"] = f"{self.x()},{self.y()}"
        except Exception:
            pass

    # ---------- نقاشی ----------

    def _close_rect(self) -> QRectF:
        w, h = self.width(), self.height()
        return QRectF(w - 30, 8, 22, 22)

    def refresh_look(self):
        self._fit_font()
        self.update()

    def paintEvent(self, event):
        p = theme.current_palette()
        w, h = self.width(), self.height()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        pnt.setRenderHint(QPainter.TextAntialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(4, 4, w - 8, h - 8), 20, 20)

        # سایه‌ی زیر کارت (به‌جای QGraphicsDropShadow — سبک‌تر برای پنجره‌ی Tool)
        pnt.setPen(Qt.NoPen)
        sh = QColor(0, 0, 0, 90)
        pnt.setBrush(sh)
        pnt.drawRoundedRect(QRectF(8, 10, w - 8, h - 8), 20, 20)

        # بدنه‌ی شیشه‌ای — گرادیان اِلیویت + هِیرلاین
        top = qcolor(p["glass_strong"])
        bot = QColor(top)
        bot.setAlpha(max(0, bot.alpha() - 10))
        grad = QLinearGradient(0, 4, 0, h - 4)
        grad.setColorAt(0, top)
        grad.setColorAt(1, bot)
        pnt.setBrush(grad)
        pnt.drawPath(path)

        # نوارِ اکسنتِ لبه — امضای برند در ابعاد کوچک
        acc = QLinearGradient(0, 4, w, 4)
        acc.setColorAt(0, QColor(p["grad1"]))
        acc.setColorAt(0.55, QColor(p["grad2"]))
        acc.setColorAt(1, QColor(p["grad3"]))
        pnt.setBrush(acc)
        pnt.drawRoundedRect(QRectF(4, 4, w - 8, 5), 2.5, 2.5)

        # گلیف صاعقه + عنوان
        rtl = i18n.is_rtl()
        pm = icons.icon_pixmap("bolt", 20, p["accent"], p["accent"])
        gx = (w - 32 - 20) if rtl else 20
        pnt.drawImage(gx, 20, pm)
        f_title = QFont(_body_font())
        f_title.setPointSizeF(8.8)
        f_title.setWeight(QFont.Weight.DemiBold)
        pnt.setFont(f_title)
        pnt.setPen(QColor(p["text3"]))
        if rtl:
            title_rect = QRectF(48, 18, w - 96, 22)
            align_t = int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        else:
            title_rect = QRectF(48, 18, w - 96, 22)
            align_t = int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        pnt.drawText(title_rect, align_t, i18n.t("overlay.title"))

        # شمارش معکوس — درشت، وسط
        f_cnt = QFont(_disp_font())
        f_cnt.setPixelSize(self._count_font_px)
        f_cnt.setWeight(QFont.Weight.Black)
        pnt.setFont(f_cnt)
        pnt.setPen(QColor(p["text"]))
        pnt.drawText(QRectF(12, 40, w - 24, 46),
                     int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                     self._next_txt)

        # ردیف پایین: نقطه‌ی وضعیت + قبض/بازه
        dot_x = (w - 26) if rtl else 22
        cy = h - 22
        lv = self._level
        if lv is True:
            c = QColor("#2bbd8a")
        elif lv is False:
            c = QColor("#f4596c")
        else:
            c = qcolor(p["text3"])
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(c)
        pnt.drawEllipse(QRectF(dot_x - 3.2, cy - 3.2, 6.4, 6.4))
        f_sub = QFont(_body_font())
        f_sub.setPointSizeF(8.6)
        pnt.setFont(f_sub)
        pnt.setPen(QColor(p["text2"]))
        sub = self._bill or self._sub or i18n.t("overlay.sub_none")
        fm = QFontMetrics(f_sub)
        sub = fm.elidedText(sub, Qt.TextElideMode.ElideMiddle, w - 64)
        if rtl:
            pnt.drawText(QRectF(14, cy - 11, w - 46, 22),
                         int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight), sub)
        else:
            pnt.drawText(QRectF(40, cy - 11, w - 62, 22),
                         int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), sub)

        # دکمه‌ی × — گلیفِ خطی ظریف
        cr = self._close_rect()
        pnt.setPen(QPen(QColor(p["text3"]), 1.8, Qt.SolidLine, Qt.RoundCap))
        ccx, ccy = cr.center().x(), cr.center().y()
        pnt.drawLine(QPointF(ccx - 4, ccy - 4), QPointF(ccx + 4, ccy + 4))
        pnt.drawLine(QPointF(ccx + 4, ccy - 4), QPointF(ccx - 4, ccy + 4))

        # لبه
        pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        pnt.end()
