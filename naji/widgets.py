# widgets.py — کامپوننت‌های سفارشی «ناجی / Aura Glass» (نسخه‌ی ۴)
# ----------------------------------------------------------------
# زبان بصری: «ماتِ آرام» — بومِ ساکنِ مات و کنترل‌های زنده.
#   BackdropCanvas بوم پایه‌ی ساکن (گرادیان+نور تک‌فام+وینیت+گرِین، بدون تایمر)
#   GlassCard     کارتِ اِلیویت با لبه‌ی هِیرلاین و درخشِ بالایی
#   NavRail       نوار کنار برنامه — چهار صفحه با آیکون SVG
#   IconChip      چیپ شیشه‌ای با آیکون SVG دودوتونه (icons.py)
#   HeroCard      کارت هیرو با مدار تزئینی و جاروی نور (شیمر)
#   Segmented     سگمنت شیشه‌ای با قرص سرخورنده
#   Switch        کلید شیشه‌ای با هاله
# بدون هیچ ایموجی — همه‌ی گلیف‌ها SVG وکتوری‌اند.
import math

from PySide6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRect, QRectF, QSize, Qt,
    QTimer, QVariantAnimation, Signal,
)
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter,
    QPainterPath, QPen, QRadialGradient,
)
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QListWidget, QPushButton, QSizePolicy,
    QStyle, QStyleOptionButton, QStyleOptionComboBox, QVBoxLayout, QWidget,
)

import i18n
import icons
import theme


def _rtl() -> bool:
    return i18n.is_rtl()


def _body_font() -> str:
    return theme.FONT_BODY if _rtl() else theme.FONT_LATIN


def _soft_font() -> str:
    return theme.FONT_SOFT if _rtl() else theme.FONT_LATIN


def _start_align() -> Qt.AlignmentFlag:
    """شروعِ بصری — AlignAbsolute تا در چیدمان RTL آینه نشود؛ بدون آن
    شمارش معکوسِ درشت هیرو به لبه‌ی چپ می‌چسبید و از ردیف‌های
    راست‌چینِ زیر خودش جدا می‌افتاد"""
    return (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute) if _rtl() \
        else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)


def _phys_align() -> Qt.AlignmentFlag:
    """ترازِ فیزیکیِ سمتِ شروع — برای متن‌های داده‌ای (عنوان قبض، آدرس) که
    ممکن است با زبانِ رابط یکی نباشند؛ Qt با AlignLeftِ ساده، متنِ فارسی را
    حتی در چیدمان LTR به راست می‌چسباند — AlignAbsolute این را قفل می‌کند"""
    return (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute) if _rtl() \
        else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute)


# ---------- ابزار رنگ و سایه ----------

def qcolor(css: str) -> QColor:
    """تبدیل رشته‌ی رنگی '#hex' یا 'rgba(r,g,b,a)' به QColor
    آلفا هم می‌تواند صحیح ۰..۲۵۵ باشد و هم اعشاری ۰..۱ (سبک CSS)"""
    s = (css or "").strip()
    if s.startswith("rgba"):
        try:
            inner = s[s.index("(") + 1:s.rindex(")")]
            parts = [v.strip() for v in inner.split(",")]
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = float(parts[3])
            if a <= 1.0:
                a = int(round(a * 255))
            else:
                a = int(a)
            return QColor(r, g, b, max(0, min(255, a)))
        except Exception:
            return QColor("#000000")
    c = QColor()
    c.setNamedColor(s)
    return c


def add_shadow(w: QWidget, blur: int = 30, alpha: int = 26, dy: int = 10,
               rgb: str = None):
    """سایه‌ی محو زیر کارت‌ها — رنگ بر اساس تم فعال"""
    p = theme.current_palette()
    eff = QGraphicsDropShadowEffect(w)
    rgb = rgb or p.get("shadow", "27,32,90")
    parts = rgb.split(",")
    c = QColor(int(parts[0]), int(parts[1]), int(parts[2]), alpha)
    eff.setColor(c)
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    w.setGraphicsEffect(eff)


def add_glow(w: QWidget, rgb: str = None, blur: int = 30, alpha: int = 90,
             dy: int = 6):
    """هاله‌ی رنگی زیر دکمه‌ی اصلی — امضای شیشه‌های نئونی"""
    add_shadow(w, blur=blur, alpha=alpha, dy=dy, rgb=rgb or theme.current_palette().get("glow", "91,95,232"))


# ---------- بافت دانه‌ی فیلم (گرِین) ----------

_grain_tile = None


def _grain() -> QImage:
    """کاشی نویز ۹۶×۹۶ با آلفای خیلی کم — بافت فراستِ شیشه"""
    global _grain_tile
    if _grain_tile is None:
        import random
        rnd = random.Random(1404)
        _grain_tile = QImage(96, 96, QImage.Format.Format_ARGB32)
        _grain_tile.fill(Qt.GlobalColor.transparent)
        for _ in range(1350):
            x, y = rnd.randrange(96), rnd.randrange(96)
            a = rnd.randint(4, 14)
            v = rnd.random()
            c = QColor(255, 255, 255, a) if v > 0.5 else QColor(30, 34, 70, a)
            _grain_tile.setPixelColor(x, y, c)
    return _grain_tile


def os_env_anim() -> bool:
    """انیمیشن‌ها فعال‌اند مگر NAJI_NO_ANIM=1 (برای تست/اسکرین‌شات)"""
    import os as _os
    return _os.environ.get("NAJI_NO_ANIM", "") != "1"


# ---------- موتور موشن «دوبینسِ راستین» — پورت وفادار transitions.dev ----------
# مرجع: «Toggle — Thumb slides with a double bounce»
#   --toggle-dur: 350ms · منحنی cubic-bezier(0.34, 1.35, 0.64, 1) · keyframes:
#   0% شروع → 55% (مسیر + ov1) → 80% (مسیر − ov2) → 100% نشست
#   --toggle-travel: 14.66px · ov1: 1px (≈ 6.8% مسیر) · ov2: 0px
# v5.1 — عذرخواهی از نسخه‌ی قبل: در پاسِ «ظرافت» منحنیِ مرجع صاف شده بود
#   (y ≤ 1) و اورشوت تا ۳٫۵٪ کاسته شده بود؛ نتیجه، یک سرسره‌ی ساده بود —
#   یعنی همان چیزی که کاربر با «انیمیشن پیاده نشده» دید. حالا:
#   • بیزیرِ واقعیِ مرجع (y1=1.35) با حل‌گرِ عددی — اورشوتِ ذاتیِ منحنی برگشت
#   • keyframes دقیق ۰/۵۵/۸۰/۱۰۰ و ov1 = ۶٫۸٪ مسیر، ov2 = 0 (عین مرجع)
#   • برای سفرهای بلند (قرص ناوبری/تب‌ها) pop ملایم‌تر (1.22) تا قرص زیر
#     دکمه‌ی همسایه نرود — همان شخصیتِ دوبینس، مقیاس‌شده با مسیر

JELLY_DUR = 360  # ms — نزدیک به مرجع (۳۵۰ms)

_BEZIER_X1, _BEZIER_Y1, _BEZIER_X2, _BEZIER_Y2 = 0.34, 1.35, 0.64, 1.0


def _bezier_y(x: float, y1: float = _BEZIER_Y1) -> float:
    """حل‌گر cubic-bezier سبک CSS: x ورودیِ پیشرفت است، خروجی مقدارِ ease.
    x1/x2 ثابتِ مرجع‌اند (0.34/0.64)؛ y1 = 1.35 اورشوتِ ذاتیِ منحنی است.
    نیوتن + بایسکشن — بدون وابستگی به QEasingCurve (که y>1 را از دست می‌داد)."""
    x1, x2, y2 = _BEZIER_X1, _BEZIER_X2, _BEZIER_Y2
    cx = 3.0 * x1
    bx = 3.0 * (x2 - x1) - cx
    ax = 1.0 - cx - bx
    cy = 3.0 * y1
    by = 3.0 * (y2 - y1) - cy
    ay = 1.0 - cy - by

    def sx(t: float) -> float:
        return ((ax * t + bx) * t + cx) * t

    def sy(t: float) -> float:
        return ((ay * t + by) * t + cy) * t

    def dsx(t: float) -> float:
        return (3.0 * ax * t + 2.0 * bx) * t + cx

    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    t = x
    for _ in range(10):
        e = sx(t) - x
        if abs(e) < 1e-6:
            return sy(t)
        d = dsx(t)
        if abs(d) < 1e-7:
            break
        t -= e / d
    if t < 0.0 or t > 1.0 or abs(sx(t) - x) > 1e-4:
        lo, hi = 0.0, 1.0
        t = x
        for _ in range(48):
            if sx(t) < x:
                lo = t
            else:
                hi = t
            t = 0.5 * (lo + hi)
    return sy(t)


# مقیاسِ اورشوتِ کلیدیِ مرجع: 1px روی 14.66px مسیر
OV_REF = 1.0 / 14.66


def jelly_ease() -> QEasingCurve:
    """سازگاری با فراخوانی‌های قدیمی (فشار دکمه) — منحنیِ نرمِ بدون اورشوت"""
    ec = QEasingCurve(QEasingCurve.Type.BezierSpline)
    ec.addCubicBezierSegment(QPointF(0.34, 1.0), QPointF(0.64, 1.0),
                             QPointF(1.0, 1.0))
    return ec


def jelly_pos(t: float, a: float, b: float, ov_scale: float = OV_REF,
              pop: float = 1.35) -> float:
    """پورت وفادار keyframes مرجع — easingِ CSS بین هر جفت فریم کلیدی:
      0.00 → a            شروع
      0.55 → b + ov1      اورشوت (ov1 = ov_scale×مسیر — مرجع: ۶٫۸٪)
      0.80 → b − ov2      برگشت (مرجع: ov2 = 0)
      1.00 → b            نشستِ نهایی
    pop = y1 منحنی؛ 1.35 عین مرجع (سوییچ)، 1.22 برای سفرهای بلند
    (قرص ناوبری/تب‌ها) تا اوجِ اورشوت زیر دکمه‌ی همسایه نرود.
    حرکتِ حاصل: شتابِ تند + اورشوت + میکرو-فرورفتگی + نشست = دوبینس."""
    travel = b - a
    if abs(travel) < 1e-9:
        return b
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b
    ov1 = travel * ov_scale
    ov2 = 0.0
    key = ((0.0, a), (0.55, b + ov1), (0.80, b - ov2), (1.0, b))
    for i in range(3):
        t0, v0 = key[i]
        t1, v1 = key[i + 1]
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            eased = _bezier_y(u, pop)
            return v0 + (v1 - v0) * eased
    return b


def jelly_pulse(t: float) -> float:
    """نبض ژله‌ای ابعاد — ضریب مقیاس ۱٫۰۰ → ۱٫۰۴ → ۰٫۹۸ → ۱٫۰۰
    کش‌آمدنِ ملایم هنگام حرکت و فرونشستن هنگام لنگیدن"""
    if t <= 0.0:
        return 1.0
    if t >= 1.0:
        return 1.0
    if t < 0.38:
        return 1.0 + 0.04 * (t / 0.38)
    if t < 0.74:
        return 1.04 - 0.06 * ((t - 0.38) / 0.36)
    return 0.98 + 0.02 * ((t - 0.74) / 0.26)


class JellyMotion(QVariantAnimation):
    """انیمیشن پیشرونده‌ی ۰→۱ — ویجتِ مصرف‌کننده در on_tick با jelly_pos و
    jelly_pulse موقعیت و ابعاد را حساب می‌کند (بدون جادوی پراپرتی)"""

    def __init__(self, on_tick, dur: int = JELLY_DUR, parent=None):
        super().__init__(parent)
        self.setStartValue(0.0)
        self.setEndValue(1.0)
        self.setDuration(int(dur))
        self.valueChanged.connect(lambda v: on_tick(float(v)))


def kill_anim(an) -> None:
    """توقف + آزادسازیِ واقعیِ انیمیشن — رفعِ نشتِ آبجکت:
    قبلاً هر تعامل (کلیک ناوبری/تاگل/تب) یک QVariantAnimation نو می‌ساخت و
    قدیمی فقط stop می‌شد ولی به‌عنوان فرزندِ ویجت زنده می‌ماند؛ در نشست‌های
    طولانی صدها آبجکتِ مرده روی هم تلنبار می‌شد."""
    if an is None:
        return
    try:
        an.stop()
        an.deleteLater()
    except RuntimeError:
        pass  # آبجکت ++C قبلاً نابود شده


# زمان‌سنجِ موشنِ کم‌مصرف — جایگزین درایور ۶۰fpsِ QVariantAnimation برای
# حلقه‌های بی‌پایانِ تزئینی (شیمر هیرو، تپش پییل): ۲۴fps کافی است و
# پردازنده/باتری لپ‌تاپ را نمی‌سوزاند (شکایت «برنامه سنگین/گرم می‌کند»)
class FpsDriver(QTimer):
    def __init__(self, fps: int, on_tick, parent=None):
        super().__init__(parent)
        self.setInterval(max(16, int(1000 / fps)))
        self.timeout.connect(on_tick)
        self._phase = 0.0
        self._step = self.interval() / 1000.0

    def advance(self, amount: float) -> float:
        self._phase = (self._phase + amount) % (2.0 * math.pi)
        return self._phase

    def dt(self) -> float:
        return self._step


def _jelly_transform(pnt: QPainter, w: QWidget, scale: float):
    """مقیاس حول مرکز ویجت — فشار ژله‌ایِ دکمه‌های رسم‌دستی"""
    s = max(0.5, min(1.2, scale))
    cx, cy = w.width() / 2.0, w.height() / 2.0
    pnt.translate(cx, cy)
    pnt.scale(s, s)
    pnt.translate(-cx, -cy)


class _JellyPress:
    """میکسینِ فشار دوبینسی برای دکمه‌ها (درخواست: «همین انیمیشن برای دکمه‌ها»):
    فشردن → جمع‌شدن نرم به ۰٫۹۶۵؛ رهاشدن → همان keyframesِ مرجعِ transitions.dev
    (اورشوت → میکرو-فرورفتگی → نشست) روی مقیاس، با بیزیرِ واقعیِ 1.35.
    paintEvent با self._jelly_scale() حول مرکز می‌کشد."""

    PRESS_SCALE = 0.965

    def _jelly_init(self):
        self._s = 1.0
        self._janim = None
        self.pressed.connect(self._jelly_press)
        self.released.connect(self._jelly_release)

    def _jelly_scale(self) -> float:
        return getattr(self, "_s", 1.0)

    def _jelly_run(self, b: float, ov_scale: float, dur: int, pop: float = 1.35,
                   eased: bool = False):
        a = float(getattr(self, "_s", 1.0))
        kill_anim(getattr(self, "_janim", None))

        def _tick(t: float):
            self._s = jelly_pos(t, a, b, ov_scale=ov_scale, pop=pop)
            self.update()

        self._janim = JellyMotion(_tick, dur=dur, parent=self)
        self._janim.start()

    def _jelly_press(self):
        if not os_env_anim():
            return
        # فشردن: نرم و کوتاه — بدون اورشوت
        a = float(getattr(self, "_s", 1.0))
        kill_anim(getattr(self, "_janim", None))

        def _tick(t: float):
            u = _bezier_y(t, 1.0)   # فقط حمله‌ی نرم، بدون اورشوت
            self._s = a + (self.PRESS_SCALE - a) * u
            self.update()

        self._janim = JellyMotion(_tick, dur=110, parent=self)
        self._janim.start()

    def _jelly_release(self):
        if not os_env_anim():
            self._s = 1.0
            self.update()
            return
        # رهاشدن: دوبینسِ راستین — از مقیاسِ فشرده تا ۱٫۰ با اورشوتِ مرجع.
        # v5.1 — کلیکِ خیلی سریع (فشار و رها در یک چرخه‌ی event loop) هم
        # باید ژله بگیرد: اگر فشرده‌شدن فرصت اجرا نیافته بود، از مقیاسِ
        # فشرده شروع می‌کنیم — بازگشتِ دوبینس همیشه دیده می‌شود
        a = float(getattr(self, "_s", 1.0))
        if a > self.PRESS_SCALE + 0.02:
            a = self.PRESS_SCALE
        kill_anim(getattr(self, "_janim", None))

        def _tick(t: float):
            self._s = jelly_pos(t, a, 1.0, ov_scale=0.55, pop=1.35)
            self.update()

        self._janim = JellyMotion(_tick, dur=JELLY_DUR, parent=self)
        self._janim.start()


class JellyButton(QPushButton, _JellyPress):
    """دکمه‌ی استایل‌شده با QSS و فیدبک ژله‌ای ظریف (v4.6):
    فشردن → جمع‌شدن ۰٫۹۶؛ رهاشدن → برگشتِ دوبینسِ ریز با اورشوت ۱٫۰۱۲.
    نقاشی از مسیر استایل (CE_PushButton) با ترانسفورم مقیاس حول مرکز —
    چیدمان و ناحیه‌ی کلیک دست‌نخورده می‌ماند."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._jelly_init()

    def paintEvent(self, event):
        pnt = QPainter(self)
        if abs(self._jelly_scale() - 1.0) > 0.001:
            _jelly_transform(pnt, self, self._jelly_scale())
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, pnt, self)
        pnt.end()


# ---------- بوم پس‌زمینه (ماتِ آرام — v4.8) ----------

class BackdropCanvas(QWidget):
    """لایه‌ی پایه‌ی برنامه — ساکن و آرام به سبک مایکا (Fluent 2):
    گرادیان مات + یک نورِ تک‌فامِ ساکن در بالای بوم + وینیتِ نرم +
    دانه‌ی فیلم. همه در یک لایه‌ی کش‌شده‌ی واحدند؛ paintEvent فقط یک
    بلیت است و هیچ تایمر و هیچ لکه‌ی متحرکی وجود ندارد — پس‌زمینه‌ی
    زنده «RGB/چیپ» حس می‌داد و کلاً حذف شد؛ حرکت فقط در کنترل‌هاست
    (قرص ناوبری، سوییچ، دکمه‌ها)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base = None    # لایه‌ی پایه‌ی کش‌شده (گرادیان+نور+وینیت+گرِین)

    def repaint_theme(self):
        self._base = None
        self.update()

    def _build_base(self):
        """لایه‌ی ثابت پس‌زمینه — فقط با تغییر اندازه/تم ساخته می‌شود"""
        p = theme.current_palette()
        w, h = max(1, self.width()), max(1, self.height())
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        pnt = QPainter(img)
        pnt.setPen(Qt.NoPen)
        # ۱) گرادیان ماتِ بوم
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(p["bg_top"]))
        grad.setColorAt(1, QColor(p["bg_bottom"]))
        pnt.setBrush(grad)
        pnt.drawRect(0, 0, w, h)
        span = max(w, h)
        # ۲) نورِ تک‌فامِ ساکن در بالای بوم (تینتِ مایکا — هرگز چندفام، هرگز متحرک)
        for rgb, alpha, size, gx, gy in theme.aurora_spec():
            d = size * span
            cx, cy = gx * w, gy * h
            g = QRadialGradient(cx, cy, d / 2)
            parts = [int(v) for v in rgb.split(",")]
            g.setColorAt(0.0, QColor(*parts, alpha))
            g.setColorAt(0.55, QColor(*parts, int(alpha * 0.40)))
            g.setColorAt(1.0, QColor(0, 0, 0, 0))
            pnt.setBrush(g)
            pnt.drawEllipse(QRectF(cx - d / 2, cy - d / 2, d, d))
        # ۳) وینیتِ نرمِ گوشه‌ها — عمقِ بدون جلا
        v = QRadialGradient(w * 0.5, h * 0.42, math.hypot(w * 0.5, h * 0.58))
        vrgb = [int(x) for x in p.get("vignette", "0,0,0").split(",")]
        v.setColorAt(0.0, QColor(vrgb[0], vrgb[1], vrgb[2], 0))
        v.setColorAt(0.62, QColor(vrgb[0], vrgb[1], vrgb[2], 0))
        v.setColorAt(1.0, QColor(vrgb[0], vrgb[1], vrgb[2],
                                 60 if theme.current_name() == "light" else 88))
        pnt.setBrush(v)
        pnt.drawRect(0, 0, w, h)
        # ۴) دانه‌ی فیلم — بافت ارگانیک؛ ضدِ «پلاستیکی» شدن گرادیان
        pnt.setOpacity(0.5)
        gr = _grain()
        for tx in range(0, w, 96):
            for ty in range(0, h, 96):
                pnt.drawImage(tx, ty, gr)
        pnt.end()
        from PySide6.QtGui import QPixmap as _PM
        self._base = _PM.fromImage(img)

    def freeze(self, phase: float = 0.37):
        """سازگاری با رندرهای آفسکرین — دیگر حرکتی برای منجمدکردن نیست"""
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if self._base is None or self._base.width() != w or self._base.height() != h:
            self._build_base()
        pnt = QPainter(self)
        pnt.drawPixmap(0, 0, self._base)
        pnt.end()


# نام قدیمی برای سازگاریِ importها (کلاس از v4.8 کاملاً ساکن است)
AuroraCanvas = BackdropCanvas


# ---------- کارت شیشه‌ای ----------

class GlassCard(QFrame):
    """قاب فراستی اِلیویت — v5.0 حس 2.5D:
    پرشِ گرادیانی (بالای کارت روشن‌تر از کف) + خط اسپکولار بالا +
    لبه‌ی ضخامت در کف (سایه‌ی داخلی ظریف — کارت مثل اسلبِ سرِپا)
    + لبه‌ی هِیرلاین. هر محتوایی می‌تواند داخلش باشد؛ بومِ اکریلیک
    از پشتِ شیشه کمی می‌گذرد."""

    def __init__(self, parent=None, radius: int = 20):
        super().__init__(parent)
        self.setObjectName("glass")
        self._radius = radius

    def paintEvent(self, event):
        p = theme.current_palette()
        light = theme.current_name() == "light"
        w, h = self.width(), self.height()
        r = self._radius
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)
        # پرش شیشه — گرادیان اِلیویشن: بالای کارت روشن‌تر، کف کمی تیره‌تر
        # (همان قاعده‌ی «سطحِ بالاتر = روشن‌تر» متریال — عمقِ بدون رنگِ اشباع)
        top = qcolor(p["glass"])
        bot = QColor(top)
        if light:
            top = top.lighter(104)
            bot.setAlpha(max(0, bot.alpha() - 10))
        else:
            top = top.lighter(112)
            bot.setAlpha(max(0, bot.alpha() - 8))
        elev = QLinearGradient(0, 0, 0, h)
        elev.setColorAt(0, top)
        elev.setColorAt(1, bot)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(elev)
        pnt.drawPath(path)
        pnt.setClipPath(path)
        # درخش سربخش (شیشه‌ی واقعی نورِ بالا را بازتاب می‌دهد)
        sheen = QLinearGradient(0, 0, 0, h * 0.55)
        sheen.setColorAt(0, qcolor(p["sheen"]))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        pnt.setBrush(sheen)
        pnt.drawRect(0, 0, w, h * 0.55)
        # لبه‌ی ضخامت — سایه‌ی داخلیِ ظریف در کف کارت (حس 2.5D)
        thick = QLinearGradient(0, h - 16, 0, h)
        thick.setColorAt(0, QColor(0, 0, 0, 0))
        thick.setColorAt(1, QColor(0, 0, 0, 30 if not light else 12))
        pnt.setBrush(thick)
        pnt.drawRect(0, h - 16, w, 16)
        pnt.setClipping(False)
        # لبه‌ی اسپکولار — از سفیدِ بالا به تیره‌ی پایین
        edge = QLinearGradient(0, 0, 0, h)
        edge.setColorAt(0, qcolor(p["glass_border"]))
        dark = not light
        edge.setColorAt(0.35, QColor(255, 255, 255, 14 if dark else 22))
        edge.setColorAt(1, qcolor(p["glass_edge"]))
        pen = QPen(edge, 1.2)
        pnt.setPen(pen)
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        pnt.end()


# ---------- چیپ آیکونی شیشه‌ای ----------

class IconChip(QWidget):
    """قرص گردِ شیشه‌ای با آیکون SVG دودوتونه — واحد بصری تکرارشونده.
    v4.4.7: کاشی مربعی‌گوشه حذف شد — همه‌ی کاشی‌های آیکونی دایره‌اند"""

    def __init__(self, kind: str = "indigo", glyph: str = "bolt",
                 size: int = 38, parent=None):
        super().__init__(parent)
        self._kind = kind
        self._glyph = glyph
        self.setFixedSize(size, size)

    def set_icon(self, kind: str = None, glyph: str = None):
        if kind:
            self._kind = kind
        if glyph:
            self._glyph = glyph
        self.update()

    def paintEvent(self, event):
        chips = theme.chips()
        c = chips.get(self._kind, chips["indigo"])
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        s = self.width()
        # قرص گرد — تینت رنگی ملایم (نیم‌پیکسل تورفتگی برای لبه‌ی تمیز AA)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(qcolor(c["bg"]))
        disc = QRectF(0.5, 0.5, s - 1, s - 1)
        pnt.drawEllipse(disc)
        # اسپکولار بالا — داخل همان دایره کلیپ می‌شود تا بیرون نزند
        # (v4.7: صدفِ مات — براقِ کف‌کرده؛ چیپِ براق حس «ارزان» می‌دهد)
        pnt.save()
        clip = QPainterPath()
        clip.addEllipse(disc)
        pnt.setClipPath(clip)
        sheen = QLinearGradient(0, 0, 0, s * 0.7)
        sheen.setColorAt(0, QColor(255, 255, 255, 28 if theme.current_name() == "light" else 16))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        pnt.setBrush(sheen)
        pnt.drawRect(0, 0, s, s * 0.7)
        pnt.restore()
        # آیکون SVG دودوتونه: خطوط اصلی محکم + پرش نرمِ هم‌رنگِ محو
        inset = s * 0.21
        d = int(s - 2 * inset) or 1
        h = c["fg"].lstrip("#")
        try:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            soft = f"rgba({r},{g},{b},0.45)"
        except Exception:
            soft = c["fg"]
        pm = icons.icon_pixmap(self._glyph, d, c["fg"], soft)
        pnt.drawImage(int(inset), int(inset), pm)
        pnt.end()


# ---------- لوگوی برنامه ----------

class LogoChip(QWidget):
    """لوگوی گرادیانی ناجی — گلیف SVG سفید + هاله؛
    گلیف پیش‌فرض صاعقه است و برای «درباره ما» با users صدا زده می‌شود"""

    def __init__(self, size: int = 46, parent=None, glyph: str = "bolt"):
        super().__init__(parent)
        self._glyph = glyph
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = theme.current_palette()
        s = self.width()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        # هاله‌ی بسیار ملایم پشت کاشی — عمق Fluent بدون برش گوشه‌ها
        halo = QRadialGradient(s / 2, s / 2, s * 0.72)
        halo.setColorAt(0.42, qcolor(theme.current_palette()["accent_tint"]))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(halo)
        pnt.drawEllipse(QRectF(0, 0, s, s))
        # کاشی گردِ ویندوز ۱۱ — گرادیان مورب برند (v7: دایره → کاشیِ Fluent)
        rad = s * 0.26
        tile = QRectF(1.0, 1.0, s - 2.0, s - 2.0)
        grad = QLinearGradient(0, 0, s, s)
        grad.setColorAt(0.0, QColor(p["grad1"]))
        grad.setColorAt(0.55, QColor(p["grad2"]))
        grad.setColorAt(1.0, QColor(p["grad3"]))
        tpath = QPainterPath()
        tpath.addRoundedRect(tile, rad, rad)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(grad)
        pnt.drawPath(tpath)
        pnt.setClipPath(tpath)
        # شین مات بالای کاشی — صدفِ آرام (نه براقیت ارزان)
        sheen = QLinearGradient(0, 0, 0, s * 0.62)
        sheen.setColorAt(0, QColor(255, 255, 255, 46 if theme.current_name() == "light" else 38))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        pnt.setBrush(sheen)
        pnt.drawRect(0, 0, s, s * 0.62)
        # نورِ عمودی سمت چپِ گرادیان — عمق لایه‌ای آیکون‌های ویندوز ۱۱
        side = QLinearGradient(0, 0, s * 0.5, 0)
        side.setColorAt(0, QColor(255, 255, 255, 22))
        side.setColorAt(1, QColor(255, 255, 255, 0))
        pnt.setBrush(side)
        pnt.drawRect(0, 0, s * 0.5, s)
        pnt.setClipping(False)
        # لبه‌ی داخلی شیشه‌ای — ۱px نیمه‌شفاف (امضای آیکون‌های Win11)
        pnt.setPen(QPen(QColor(255, 255, 255, 54), 1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawRoundedRect(tile.adjusted(0.5, 0.5, -0.5, -0.5),
                            rad - 0.5, rad - 0.5)
        # گلیف SVG سفید (صاعقه یا نشان دیگر) — مجموعه Fluent v7
        inset = s * 0.25
        pm = icons.icon_pixmap(self._glyph, int(s - 2 * inset), "#ffffff",
                               "rgba(255,255,255,0.4)")
        pnt.drawImage(int(inset), int(inset), pm)
        pnt.end()


# ---------- لوگوی صفحه‌ی «درباره ما» ----------

class AboutUsLogo(QWidget):
    """نشان «درباره ما» — قرص گرادیانی با گلیف دو چهره + واژه‌نگار زیرش.
    الگوی بصری از تصویر مرجع کاربر: آیکون افراد بالای کلمه‌ی ABOUT US؛
    همین‌جا با هویت Aura Glass (هاله، گرادیان، فونت نمایشی) اجرا شده."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        # v4.7 — ۷۰px برای یک نشانِ برندِ درون‌صفحه‌ای درشت است؛ ۵۶px همان
        # وقار را با ظرافتِ بیشتر می‌دهد (پرهیز از آیکون‌های بزرگ‌نما)
        self.chip = LogoChip(56, glyph="users")
        lay.addWidget(self.chip, 0, Qt.AlignmentFlag.AlignHCenter)
        self.word = QLabel(i18n.t("about.wordmark"))
        lay.addWidget(self.word, 0, Qt.AlignmentFlag.AlignHCenter)
        self._restyle()

    def _restyle(self):
        p = theme.current_palette()
        disp = theme.display_family(800) if _rtl() else theme.FONT_LATIN
        # نکته: letter-spacing اتصال حروف فارسی را می‌شکند — فقط برای LTR
        ls = "" if _rtl() else "letter-spacing: 3px;"
        self.word.setStyleSheet(
            f"font-family: \"{disp}\"; color: {p['text2']};"
            "font-size: 14.5px; font-weight: 800; background: transparent;"
            f"{ls}"
        )

    def repaint_theme(self):
        self._restyle()
        self.update()


# ---------- دکمه‌ی تم (خورشید/ماه SVG) ----------

class ThemeButton(QPushButton, _JellyPress):
    """دکمه‌ی تعویض تم — گلیف SVG در قرص شیشه‌ای گرد (v4.4.7)
    v4.6: فشار ژله‌ای ظریف — جمع‌شدن و برگشتِ دوبینسِ ریز"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # v4.7 — ۳۶px؛ قرص‌های کنترلیِ ۴۰px+ در کنار گلیف‌های ۱۷–۱۸px
        # سنگین دیده می‌شدند (جست‌وجوی منابع: Material/Fluent — گلیف ۱۶–۲۰px)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self._jelly_init()

    def _paint_disc(self, pnt, glyph: str, gsize: int):
        p = theme.current_palette()
        if self.isDown():
            bg = QColor(255, 255, 255, 60 if theme.current_name() == "light" else 26)
        elif self.underMouse():
            bg = qcolor(p["glass_strong"])
        else:
            bg = qcolor(p["glass_soft"])
        pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
        pnt.setBrush(bg)
        pnt.drawEllipse(QRectF(0.5, 0.5, self.width() - 1,
                               self.height() - 1))
        fg, soft = p["text2"], p["text3"]
        pm = icons.icon_pixmap(glyph, gsize, fg, soft)
        pnt.drawImage((self.width() - gsize) // 2,
                      (self.height() - gsize) // 2, pm)

    def paintEvent(self, event):
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        if abs(self._jelly_scale() - 1.0) > 0.001:
            _jelly_transform(pnt, self, self._jelly_scale())
        glyph = "moon" if theme.current_name() == "light" else "sun"
        self._paint_disc(pnt, glyph, 17)
        pnt.end()


class LangButton(QPushButton, _JellyPress):
    """دکمه‌ی تغییر زبان — قرص شیشه‌ای با گلیف FA/EN؛
    زیر دکمه‌ی لایت/دارک در نوار کنار می‌نشیند (v4.4.9: درخواست کاربر)
    v4.6: فشار ژله‌ای ظریف"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(i18n.t("look.language"))
        self._jelly_init()

    def paintEvent(self, event):
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        if abs(self._jelly_scale() - 1.0) > 0.001:
            _jelly_transform(pnt, self, self._jelly_scale())
        self._paint_disc_shared(pnt)
        pnt.end()

    def _paint_disc_shared(self, pnt):
        p = theme.current_palette()
        if self.isDown():
            bg = QColor(255, 255, 255, 60 if theme.current_name() == "light" else 26)
        elif self.underMouse():
            bg = qcolor(p["glass_strong"])
        else:
            bg = qcolor(p["glass_soft"])
        pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
        pnt.setBrush(bg)
        pnt.drawEllipse(QRectF(0.5, 0.5, self.width() - 1,
                               self.height() - 1))
        pm = icons.icon_pixmap("faen", 18, p["text2"], p["text3"])
        pnt.drawImage((self.width() - 18) // 2, (self.height() - 18) // 2, pm)


# ---------- سوییچ شیشه‌ای ----------

class Switch(QCheckBox):
    """کلید روشن/خاموش — پورت کامل و وفادارِ انیمیشن Toggle از transitions.dev
    (v5.1 — دوبینسِ راستین): دستگیره با منحنیِ واقعیِ cubic-bezier(0.34, 1.35,
    0.64, 1) و keyframes ۰/۵۵/۸۰/۱۰۰ سفر می‌کند (اورشوتِ مرجع ≈ ۶٫۸٪ مسیر →
    میکرو-فرورفتگی → نشست) و رنگِ ریل روی ساعتِ مستقل خودش کراس‌فید می‌شود.
    ناحیه‌ی کلیک کل ریل است."""

    X_OFF, X_ON = 4.0, 24.0      # x چپِ دستگیره — مسیر ۲۰px (مرجع: ۱۴٫۶۶px)
    OV_SCALE = OV_REF            # عین مرجع: 1px روی 14.66px ≈ ۶٫۸٪ مسیر

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setChecked(checked)
        self.setFixedSize(50, 30)
        self.setCursor(Qt.PointingHandCursor)
        # وضعیت انیمیشن — گاردِ معادل .is-init: در لود اول هیچ keyframe‌ای
        # پخش نمی‌شود؛ دستگیره و ریل مستقیم روی مقدار نهایی می‌نشینند
        self._thumb_x = self.X_ON if checked else self.X_OFF
        self._track_t = 1.0 if checked else 0.0   # کراس‌فید رنگ ریل
        self._pulse = 1.0                          # نبض ژله‌ای ابعاد
        self._anim = None
        self._tanim = None
        self.toggled.connect(self._start_jelly)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def _start_jelly(self, on: bool):
        """سفرِ دوبینس دستگیره + کراس‌فید مستقل رنگ ریل (پورت مرجع)"""
        if not os_env_anim():
            self._thumb_x = self.X_ON if on else self.X_OFF
            self._track_t = 1.0 if on else 0.0
            self._pulse = 1.0
            self.update()
            return
        a = self.X_OFF if on else self.X_ON
        b = self.X_ON if on else self.X_OFF
        kill_anim(self._anim)
        kill_anim(self._tanim)
        self._anim = JellyMotion(self._on_jelly, dur=JELLY_DUR, parent=self)
        self._anim._a, self._anim._b, self._anim._on = a, b, on
        self._anim.start()
        # ریل روی ساعتِ خودش — منحنی نرمِ جدا از سفرِ دستگیره (مطابق مرجع)
        self._tanim = QVariantAnimation(self)
        self._tanim._on = on
        self._tanim.setStartValue(0.0)
        self._tanim.setEndValue(1.0)
        self._tanim.setDuration(JELLY_DUR + 60)
        self._tanim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._tanim.valueChanged.connect(self._on_track)
        self._tanim.finished.connect(self._tanim.deleteLater)
        self._tanim.start()

    def _on_jelly(self, t: float):
        an = self._anim
        if an is None:
            return
        self._thumb_x = jelly_pos(t, an._a, an._b, ov_scale=self.OV_SCALE,
                                  pop=1.35)   # عین مرجع
        self._pulse = jelly_pulse(t)
        self.update()

    def _on_track(self, v: float):
        if self._tanim is None:
            return
        t = float(v)
        on = self._tanim._on
        self._track_t = t if on else 1.0 - t
        self.update()

    def _lerp_color(self, c1: QColor, c2: QColor, t: float) -> QColor:
        return QColor(
            int(round(c1.red() + (c2.red() - c1.red()) * t)),
            int(round(c1.green() + (c2.green() - c1.green()) * t)),
            int(round(c1.blue() + (c2.blue() - c1.blue()) * t)),
            int(round(c1.alpha() + (c2.alpha() - c1.alpha()) * t)),
        )

    def paintEvent(self, event):
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        pnt.setPen(Qt.NoPen)
        # ریل — کراس‌فید شیشه ← اکسنت روی ساعتِ مستقل (v4.6)
        track = self._lerp_color(qcolor(p["glass_edge"]), QColor(p["accent"]),
                                 self._track_t)
        if not self.isEnabled():
            track.setAlpha(min(track.alpha(), 90))
        pnt.setBrush(track)
        pnt.drawRoundedRect(QRectF(1, 3, 48, 24), 12, 12)
        # درخش داخلی ریل — صدفِ مات (v4.7)
        sheen_a = 26 if theme.current_name() == "light" else 20
        sheen = QLinearGradient(0, 3, 0, 27)
        sheen.setColorAt(0, QColor(255, 255, 255, sheen_a))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        pnt.setBrush(sheen)
        pnt.drawRoundedRect(QRectF(1, 3, 48, 24), 12, 12)
        # مرکز دستگیره + نبض ژله‌ای (کش‌آمدن در راستای سفر، فرونشستن در لنگش)
        cx = self._thumb_x + 10.0
        pw = 20.0 * self._pulse
        ph = 20.0 * (2.0 - self._pulse)
        # هاله‌ی دستگیره — با پیشرفت کراس‌فیدِ ریل
        if self.isEnabled() and self._track_t > 0.02:
            glow = QRadialGradient(cx, 15, 17)
            gt = qcolor(p["accent_tint"])
            gt.setAlpha(int(gt.alpha() * self._track_t))
            glow.setColorAt(0.4, gt)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            pnt.setBrush(glow)
            pnt.drawEllipse(QRectF(cx - 17, -2, 34, 34))
        # دستگیره
        pnt.setBrush(QColor("#ffffff"))
        pnt.drawEllipse(QRectF(cx - pw / 2, 15 - ph / 2, pw, ph))
        pnt.setBrush(QColor(0, 0, 0, 26))
        pnt.drawEllipse(QRectF(cx - ph / 2 + 3, 15 + ph / 2 - 3, pw * 0.7, 5))
        pnt.end()


# ---------- نوار کنار برنامه (ناوبری صفحات) ----------

class NavButton(QPushButton, _JellyPress):
    """دکمه‌ی ناوبری: آیکون بالای برچسب متنی (v4.4.2: متن زیر آیکون برگشت)؛
    v4.6 — نشانه‌ی انتخاب فقط رنگِ آیکون/متن است؛ پس‌زمینه‌ی انتخاب را
    قرصِ سرخورنده‌ی ریل (NavRail) با انیمیشن دوبینس فراهم می‌کند."""

    def __init__(self, key: str, text: str, glyph: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._text = text
        self._glyph = glyph
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(76, 62)
        self.setObjectName("navItem")
        self.setToolTip(text)
        self._jelly_init()

    def retranslate(self, text: str):
        self._text = text
        self.setToolTip(text)
        self.update()

    def paintEvent(self, event):
        p = theme.current_palette()
        checked = self.isChecked()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        if abs(self._jelly_scale() - 1.0) > 0.001:
            _jelly_transform(pnt, self, self._jelly_scale())
        w, h = self.width(), self.height()
        # v4.6 — فقط هاور پس‌زمینه دارد؛ پس‌زمینه‌ی انتخاب = قرصِ متحرک ریل
        if not checked and self.underMouse():
            path = QPainterPath()
            path.addRoundedRect(QRectF(2, 2, w - 4, h - 4), 14, 14)
            pnt.setPen(Qt.NoPen)
            pnt.setBrush(qcolor(p["glass_soft"]))
            pnt.drawPath(path)
        # آیکون بالا — در حالت انتخاب با رنگ اکسنت (v4.7: گلیف ۲۰px —
        # سایزِ مرجعِ ناوبریِ سایدبار در Material/Fluent؛ ۲۲px سنگین بود)
        gsz = 20
        if checked:
            fg = p["accent"]
            h2 = fg.lstrip("#")
            soft = f"rgba({int(h2[0:2], 16)},{int(h2[2:4], 16)},{int(h2[4:6], 16)},0.4)"
        else:
            fg, soft = p["text2"], p["text3"]
        pm = icons.icon_pixmap(self._glyph, gsz, fg, soft)
        pnt.drawImage(int((w - gsz) / 2), 10, pm)
        # برچسب متنی زیر آیکون
        pnt.setPen(QColor(fg if checked else p["text2"]))
        f = QFont(_body_font())
        f.setPointSizeF(9.0)
        f.setWeight(QFont.Weight.DemiBold)
        pnt.setFont(f)
        pnt.drawText(QRectF(2, 32, w - 4, 26),
                     int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                     self._text)
        pnt.end()


class NavRail(QWidget):
    """ستون ناوبری راست/چپ برنامه — کپسول شیشه‌ای با چهار صفحه"""

    page_selected = Signal(str)
    theme_toggled = Signal()   # دکمه‌ی تم پایین نوار — چرخه‌ی system→light→dark
    lang_toggled = Signal()    # v4.4.9 — دکمه‌ی زبان، زیر دکمه‌ی تم

    PAGES = (
        ("dashboard", "nav.dashboard", "home"),
        ("settings", "nav.settings", "gear"),
        # v4.4.6 — ممیزی آیکون‌ها: «راهنما» علامت سؤال است، نه سپر (سپر = امنیت)
        ("help", "nav.help", "help"),
        ("about", "nav.about", "users"),
    )

    def __init__(self, current: str = "dashboard", parent=None):
        super().__init__(parent)
        self.setObjectName("navRail")
        self.setFixedWidth(92)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 10, 6, 10)
        lay.setSpacing(4)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        for key, i18n_key, glyph in self.PAGES:
            b = NavButton(key, i18n.t(i18n_key), glyph)
            b.setChecked(key == current)
            b.clicked.connect(lambda _=False, k=key: self.page_selected.emit(k))
            # v4.6 — قرص با کلیک کاربر با دوبینس به سمت دکمه‌ی هدف سفر می‌کند
            b.clicked.connect(lambda _=False, btn=b: self._sync_thumb(animate=True, target=btn))
            self._group.addButton(b)
            self._buttons[key] = b
            lay.addWidget(b)
        lay.addStretch()
        # دکمه‌ی تم پایین نوار — به سیگنال وصل می‌شود (عملگر مرده نباشد)
        self.btn_theme = ThemeButton()
        self.btn_theme.clicked.connect(self.theme_toggled.emit)
        lay.addWidget(self.btn_theme, 0, Qt.AlignmentFlag.AlignHCenter)
        # v4.4.9 — دکمه‌ی زبان درست زیر دکمه‌ی لایت/دارک (درخواست کاربر)
        lay.addSpacing(6)
        self.btn_lang = LangButton()
        self.btn_lang.clicked.connect(self.lang_toggled.emit)
        lay.addWidget(self.btn_lang, 0, Qt.AlignmentFlag.AlignHCenter)
        self._paint_cache = None
        # v4.6 — قرصِ سرخورنده‌ی ناوبری: پورت انیمیشن «Toggle — Thumb slides
        # with a double bounce» از transitions.dev (نسخه‌ی ژله‌ی ظریف).
        # گاردِ معادل .is-init: تا اولین تعاملِ واقعی هیچ سفری پخش نمی‌شود
        # (در لود اول، قرص مستقیم روی دکمه‌ی فعال می‌نشیند)
        self._thumb_y = None       # y بالای قرص در مختصات ریل (float)
        self._thumb_w = 0.0
        self._thumb_h = 0.0
        self._pulse = 1.0          # نبض ژله‌ای ابعاد
        self._tint = 1.0           # کراس‌فید لبه‌ی اکسنت — ساعتِ مستقل
        self._anim = None
        self._tanim = None
        self._sync_thumb(animate=False)

    # --- قرصِ سرخورنده (v4.6) ---

    def _thumb_rect(self, btn) -> QRectF:
        g = btn.geometry()
        return QRectF(g.x() + 2, g.y() + 2, g.width() - 4, g.height() - 4)

    def _stop_thumb_anims(self):
        kill_anim(getattr(self, "_anim", None))
        kill_anim(getattr(self, "_tanim", None))
        self._anim = None
        self._tanim = None

    def _sync_thumb(self, animate: bool, target=None):
        """قرص روی دکمه‌ی فعال می‌نشیند؛ با animate=True با دوبینسِ ظریف
        سفر می‌کند (اورشوت ۳٫۵٪ مسیر → برگشت ۱٪ → نشست)"""
        btn = target or self._buttons.get(self.current())
        if btn is None:
            return
        r = self._thumb_rect(btn)
        self._thumb_w, self._thumb_h = r.width(), r.height()
        # گارد .is-init — نبودِ موقعیت قبلی یعنی لود اول؛ فقط نشستن بدون انیمیشن
        snap = ((not animate) or (not os_env_anim()) or (not self.isVisible())
                or (self._thumb_y is None)
                or abs(r.y() - self._thumb_y) < 0.5)
        self._stop_thumb_anims()
        if snap:
            self._thumb_y = r.y()
            self._pulse = 1.0
            self._tint = 1.0
            self.update()
            return
        self._from_y, self._to_y = self._thumb_y, r.y()
        # v5.1 — دوبینسِ راستین: pop=1.22 برای سفرِ بلند (اورشوتِ کاملِ 1.35
        # قرص را زیر دکمه‌ی همسایه می‌برد) — همان شخصیتِ مرجع، مقیاس‌شده
        self._anim = JellyMotion(self._on_thumb, dur=JELLY_DUR + 40, parent=self)
        self._anim.start()
        # کراس‌فید رنگ قرص روی ساعتِ مستقل و آرام‌تر (مطابق مرجع)
        self._tanim = QVariantAnimation(self)
        self._tanim.setStartValue(0.35)
        self._tanim.setEndValue(1.0)
        self._tanim.setDuration(JELLY_DUR + 120)
        self._tanim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._tanim.valueChanged.connect(self._on_tint)
        self._tanim.finished.connect(self._tanim.deleteLater)
        self._tanim.start()

    def _on_thumb(self, t: float):
        self._thumb_y = jelly_pos(t, self._from_y, self._to_y,
                                  ov_scale=0.028, pop=1.22)
        self._pulse = jelly_pulse(t)
        self.update()

    def _on_tint(self, v):
        self._tint = float(v)
        self.update()

    def _paint_thumb(self, pnt: QPainter):
        """قرصِ فعال — v5.0 با هاله‌ی نرم بنفش زیرِ آن (بریف: active state
        with soft glow)؛ همان چهره‌ی شیشه‌ای قبلی، این‌بار با عمقِ نور"""
        if self._thumb_y is None or self._thumb_w <= 0 or self._thumb_h <= 0:
            return
        p = theme.current_palette()
        # نبض ژله‌ای — در راستای سفر (عمودی) کش می‌آید، عرض جبران می‌شود
        ph = self._thumb_h * self._pulse
        pw = self._thumb_w * (2.0 - self._pulse)
        cx = self._thumb_w / 2.0 + 2.0 + 6.0  # وسط دکمه‌ها (حاشیه‌ی ریل + تورفتگی)
        cy = self._thumb_y + self._thumb_h / 2.0
        path = QPainterPath()
        path.addRoundedRect(QRectF(cx - pw / 2, cy - ph / 2, pw, ph), 14, 14)
        # هاله‌ی نرمِ فعال — نورِ اکسنتِ محو زیر قرص (شعاع داخل ریل محو می‌شود)
        h2 = p["accent"].lstrip("#")
        gc = QColor(int(h2[0:2], 16), int(h2[2:4], 16), int(h2[4:6], 16),
                    int(64 * self._tint))
        gr = max(pw, ph) * 0.78
        glow = QRadialGradient(cx, cy, gr)
        glow.setColorAt(0.35, gc)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(glow)
        pnt.drawEllipse(QRectF(cx - gr, cy - gr, gr * 2, gr * 2))
        pnt.setBrush(qcolor(p["glass_strong"]))
        pnt.drawPath(path)
        if self._tint > 0.01:
            border = QColor(int(h2[0:2], 16), int(h2[2:4], 16),
                            int(h2[4:6], 16), int(150 * self._tint))
            pnt.setPen(QPen(border, 1))
            pnt.setBrush(Qt.NoBrush)
            pnt.drawPath(path)

    def paintEvent(self, event):
        super().paintEvent(event)
        # v4.7 — پرده‌ی ظریف ریل: نوار کنار از بدنه‌ی محتوا جدا می‌شود
        # (در تیره کمی روشن‌تر از بوم، در صدف کمی گرم‌تر) — تمایزِ بخش‌ها
        # بدون سنگینیِ قاب
        p0 = theme.current_palette()
        veil = QColor(255, 255, 255, 20) if theme.current_name() != "light" \
            else QColor(124, 110, 92, 26)
        pnt = QPainter(self)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(veil)
        pnt.drawRect(0, 0, self.width(), self.height())
        # v4.6 — قرصِ سرخورنده زیرِ دکمه‌ها (رنگ‌آمیزیِ والد قبل از فرزندان است)
        pnt.setRenderHint(QPainter.Antialiasing)
        self._paint_thumb(pnt)
        pnt.end()
        # خط مرزی ظریف بین نوار و محتوا — ساختار فضایی بدون سنگینی
        p = theme.current_palette()
        pnt = QPainter(self)
        edge = qcolor(p["glass_edge"])
        edge.setAlpha(edge.alpha() + 14)
        pnt.setPen(QPen(edge, 1))
        x = 0.5 if _rtl() else self.width() - 0.5  # سمتِ محتوا
        pnt.drawLine(QPointF(x, 14), QPointF(x, self.height() - 14))
        pnt.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # هندسه‌ی دکمه‌ها بعد از چیدمان معتبر می‌شود — قرص دوباره بنشیند
        self._sync_thumb(animate=False)

    def retranslate(self):
        for key, i18n_key, _g in self.PAGES:
            self._buttons[key].retranslate(i18n.t(i18n_key))

    def set_current(self, key: str, animate: bool = True):
        b = self._buttons.get(key)
        if b:
            b.setChecked(True)
            self._sync_thumb(animate=animate, target=b)

    def current(self) -> str:
        for k, b in self._buttons.items():
            if b.isChecked():
                return k
        return "dashboard"

    def repaint_theme(self):
        self.update()


# ---------- کنترل سگمنتی شیشه‌ای ----------

class Segmented(QWidget):
    """چند دکمه‌ی انحصاری در کپسول شیشه‌ای با قرصِ سرخورنده — انیمیشن ۲۶۰ms"""

    changed = Signal(str)

    def __init__(self, options: list, current: str = None, parent=None):
        """options: list of (value, label)"""
        super().__init__(parent)
        self.setObjectName("segment")
        self.setFixedHeight(44)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(5, 5, 5, 5)
        lay.setSpacing(4)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        self._anim = None
        for value, label in options:
            b = JellyButton(label)  # v4.6 — فشار ژله‌ای ظریف
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setChecked(value == current)
            b.setProperty("active", value == current)
            b.clicked.connect(lambda _=False, v=value, btn=b: self._select(v, btn))
            self._group.addButton(b)
            self._buttons[value] = b
            lay.addWidget(b)
        # قرص شیشه‌ای زیر دکمه‌ی فعال
        self._ind = QFrame(self)
        self._ind.setObjectName("segInd")
        self._ind.setAttribute(Qt.WA_TransparentForMouseEvents)
        for b in self._buttons.values():
            b.raise_()
        self._sync_indicator(animate=False)

    def retranslate(self, options: list):
        """options با همان مقادیر ولی برچسب‌های تازه"""
        for value, label in options:
            b = self._buttons.get(value)
            if b:
                b.setText(label)
        self._sync_indicator(animate=False)

    def set_current(self, value: str):
        """انتخاب برنامه‌ای — بدون emit مجدد سیگنال changed"""
        b = self._buttons.get(value)
        if not b or b.isChecked():
            return
        b.setChecked(True)
        for v, btn in self._buttons.items():
            btn.setProperty("active", v == value)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._sync_indicator(animate=True, target=b)

    def _select(self, value, btn):
        self._sync_indicator(animate=True, target=btn)
        for v, b in self._buttons.items():
            b.setProperty("active", v == value)
            b.style().unpolish(b)
            b.style().polish(b)
        self.changed.emit(value)

    def _sync_indicator(self, animate: bool, target=None):
        btn = target or self._buttons.get(self.value())
        if btn is None:
            return
        g = btn.geometry()
        # v4.7 — ریشه‌ی باگ «سلکشن بین تب‌ها»: انیمیشن قبلی هیچ‌وقت متوقف
        # نمی‌شد؛ توقفِ صریح + نشستنِ فوری (اکنون با آزادسازیِ کامل آبجکت)
        kill_anim(getattr(self, "_anim", None))
        self._anim = None
        if not animate or (not os_env_anim()) or g == self._ind.geometry():
            self._ind.setGeometry(g)
            self.update()
            return
        # v5.1 — قرصِ تب‌ها هم با همان دوبینسِ مرجع سفر می‌کند (سفر افقیِ
        # بلند → pop=1.2)؛ عرض با نرمِ ساده هم‌گام می‌شود
        g0 = self._ind.geometry()
        self._from_g, self._to_g = QRectF(g0), QRectF(g)

        def _tick(t: float):
            f, to = self._from_g, self._to_g
            x = jelly_pos(t, f.x(), to.x(), ov_scale=0.018, pop=1.2)
            u = _bezier_y(min(1.0, t), 1.0)
            w = f.width() + (to.width() - f.width()) * u
            self._ind.setGeometry(QRect(round(x), round(f.y() +
                                  (to.y() - f.y()) * u),
                                  round(w), round(f.height() +
                                  (to.height() - f.height()) * u)))
            self.update()

        self._anim = JellyMotion(_tick, dur=JELLY_DUR, parent=self)
        self._anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_indicator(animate=False)

    def paintEvent(self, event):
        # کپسول شیشه‌ای + قرصِ دکمه‌ی فعال — همه در یک پاس
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 15, 15)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(qcolor(p["glass_soft"]))
        pnt.drawPath(path)
        pnt.setPen(QPen(qcolor(p["glass_edge"]), 1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        # قرص فعال — سفیدِ فراستی
        g = self._ind.geometry()
        if g.width() > 0 and g.height() > 0:
            ind = QPainterPath()
            ind.addRoundedRect(QRectF(g.x(), g.y(), g.width(), g.height()), 11, 11)
            pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
            pnt.setBrush(qcolor(p["glass_strong"]))
            pnt.drawPath(ind)
        pnt.end()

    def value(self) -> str:
        for v, b in self._buttons.items():
            if b.isChecked():
                return v
        return next(iter(self._buttons), "")


# ---------- کامبوباکس و اسپین‌باکس شیشه‌ای ----------

class GlassCombo(QComboBox):
    """کامبو با شِورانِ رسم‌شده به‌جای PNG موقت (سازگار با نام‌کاربری فارسی/فاصله‌دار).
    v4.4.9: چرخِ ماوس عمداً بی‌اثر است — انتخابِ «خاموش/خواب/خواب زمستانی» فقط
    با کلیک و باز کردن فهرست انجام می‌شود؛ اسکرولِ صفحه دیگر انتخاب را
    جابه‌جا نمی‌کند و رویداد به اسکرول‌اریا پاس می‌شود."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def wheelEvent(self, event):
        event.ignore()  # اسکرول صفحه — نه تغییر انتخاب (v4.4.9)

    def repaint_theme(self):
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        # شِوران تم‌آگاه در ناحیه‌ی فلش کامبو (با RTL خودکار چپ می‌افتد)
        try:
            opt = QStyleOptionComboBox()
            self.initStyleOption(opt)
            r = self.style().subControlRect(QStyle.CC_ComboBox, opt,
                                            QStyle.SC_ComboBoxArrow, self)
            if r.width() <= 0 or r.height() <= 0:
                return
            p = theme.current_palette()
            pnt = QPainter(self)
            pnt.setRenderHint(QPainter.Antialiasing)
            cx, cy = r.center().x(), r.center().y()
            path = QPainterPath()
            path.moveTo(cx - 4.5, cy - 2.2)
            path.lineTo(cx, cy + 2.6)
            path.lineTo(cx + 4.5, cy - 2.2)
            pnt.setPen(QPen(QColor(p["text2"]), 1.8, Qt.SolidLine,
                            Qt.RoundCap, Qt.RoundJoin))
            pnt.setBrush(Qt.NoBrush)
            pnt.drawPath(path)
            pnt.end()
        except Exception:
            pass


class _StepButton(QPushButton, _JellyPress):
    """دکمه‌ی استپر: گام فوری با فشردن + تکرار خودکار با نگه‌داشتن.
    گلیف خطی رسم‌شده (منفی/پلاس) — بدون ایموجی، وکتوری و تم‌آگاه.
    v4.6: فشار ژله‌ای ظریف."""

    stepped = Signal()

    def __init__(self, kind: str = "minus", parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setFixedSize(34, 34)
        self.setCursor(Qt.PointingHandCursor)
        self._jelly_init()
        self._delay = QTimer(self)
        self._delay.setSingleShot(True)
        self._delay.setInterval(430)
        self._rep = QTimer(self)
        self._rep.setInterval(85)
        self._delay.timeout.connect(self._go)
        self._rep.timeout.connect(self._go)
        self.pressed.connect(self._on_press)
        self.released.connect(self._on_release)

    def _on_press(self):
        self.stepped.emit()          # گام فوری — clicked روی رهاسازی است، دوبار نمی‌زند
        self._delay.start()

    def _on_release(self):
        self._delay.stop()
        self._rep.stop()

    def _go(self):
        self._delay.stop()
        self._rep.start()
        self.stepped.emit()

    def paintEvent(self, event):
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        if abs(self._jelly_scale() - 1.0) > 0.001:
            _jelly_transform(pnt, self, self._jelly_scale())
        if self.isDown():
            bg = QColor(255, 255, 255, 60 if theme.current_name() == "light" else 26)
        elif self.underMouse() and self.isEnabled():
            bg = qcolor(p["glass_strong"])
        else:
            bg = qcolor(p["glass_soft"])
        pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
        pnt.setBrush(bg)
        pnt.drawEllipse(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1))
        fg = QColor(p["text3"]) if not self.isEnabled() else QColor(p["text2"])
        pnt.setPen(QPen(fg, 2.0, Qt.SolidLine, Qt.RoundCap))
        pnt.setBrush(Qt.NoBrush)
        cy = self.height() / 2
        pnt.drawLine(QPointF(10, cy), QPointF(24, cy))     # خط منفی
        if self._kind == "plus":
            cx = self.width() / 2
            pnt.drawLine(QPointF(cx, 10), QPointF(cx, 24))  # خط عمودی پلاس
        pnt.end()


class GlassStepper(QWidget):
    """استپر شیشه‌ای حرفه‌ای — v4.4.9 جایگزین اسپین‌باکس بومی (درخواست کاربر):
    * دو دکمه‌ی گرد کم/زیاد با تکرار خودکارِ نگه‌داشتن
    * چرخِ ماوس عمداً هیچ اثری ندارد — اسکرولِ صفحه دیگر عدد را جابه‌جا نمی‌کند
    * بدون سقف عملیِ عدد (سقف فقط سینتکسی/حافظه‌ای است)
    * عدد وسط، درون کپسول شیشه‌ایِ صاف (گوشه‌ی شکسته ندارد) و با ارقام زبان فعلی"""

    valueChanged = Signal(int)

    def __init__(self, minimum: int = 1, maximum: int = 99999, value: int = None,
                 suffix: str = "", parent=None):
        super().__init__(parent)
        self._min = int(minimum)
        self._max = int(maximum)
        self._suffix = suffix
        self._val = int(value) if value is not None else self._min
        self.setFixedHeight(46)
        self.setMinimumWidth(190)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.btn_dec = _StepButton("minus")
        self.btn_inc = _StepButton("plus")
        self.btn_dec.stepped.connect(lambda: self._step(-1))
        self.btn_inc.stepped.connect(lambda: self._step(+1))
        self.val_lbl = QLabel()
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(self.btn_dec, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.val_lbl, 1)
        lay.addWidget(self.btn_inc, 0, Qt.AlignmentFlag.AlignVCenter)
        self._refresh()

    # ---------- نمایش ----------
    def _text(self) -> str:
        return i18n.num(str(self._val)) + self._suffix

    def _refresh(self):
        self.val_lbl.setText(self._text())
        self.btn_dec.setEnabled(self._val > self._min)
        self.btn_inc.setEnabled(self._val < self._max)

    def _restyle_label(self):
        f = QFont(_body_font())
        f.setPointSizeF(11.5)
        f.setWeight(QFont.Weight.DemiBold)
        self.val_lbl.setFont(f)
        self.val_lbl.setStyleSheet(
            f"color: {theme.current_palette()['text']}; background: transparent;")

    def repaint_theme(self):
        self._restyle_label()
        self.update()

    def paintEvent(self, event):
        """کپسول شیشه‌ای زیر عدد — گوشه‌ی کاملاً صاف (عرض نصف ارتفاع)،
        دیگر هیچ گوشه‌ی شکسته‌ای از قاب بومی اسپین‌باکس باقی نمی‌ماند"""
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        h = self.height()
        x1 = self.btn_dec.geometry().right() + 7
        x2 = self.btn_inc.geometry().left() - 7
        if x2 - x1 > 8:
            pill = QRectF(x1, 5, x2 - x1, h - 10)
            pnt.setPen(Qt.NoPen)
            pnt.setBrush(qcolor(p["glass_soft"]))
            pnt.drawRoundedRect(pill, (h - 10) / 2, (h - 10) / 2)
            pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
            pnt.setBrush(Qt.NoBrush)
            pnt.drawRoundedRect(pill, (h - 10) / 2, (h - 10) / 2)
        pnt.end()

    # ---------- منطق ----------
    def _step(self, d: int):
        nv = max(self._min, min(self._max, self._val + d))
        if nv == self._val:
            return
        self._val = nv
        self._refresh()
        self.valueChanged.emit(self._val)

    # ---------- سازگاری با API اسپین قبلی ----------
    def setRange(self, a: int, b: int):
        self._min, self._max = int(a), int(b)
        self._val = max(self._min, min(self._max, self._val))
        self._refresh()

    def minimum(self) -> int:
        return self._min

    def maximum(self) -> int:
        return self._max

    def setValue(self, v: int):
        v = max(self._min, min(self._max, int(v)))
        changed = v != self._val
        self._val = v
        self._refresh()
        if changed:
            self.valueChanged.emit(self._val)

    def value(self) -> int:
        return self._val

    def setSuffix(self, s: str):
        self._suffix = s or ""
        self._refresh()

    def setAlignment(self, *_):
        """سازگاری — عدد همیشه وسطِ کپسول است"""


# ---------- کاشی آمار ----------

class StatTile(GlassCard):
    """کاشی آمار شیشه‌ای: چیپ دودوتونه + کپشن + عدد درشت استعدادی"""

    def __init__(self, kind: str, glyph: str, caption: str, value: str = "—",
                 parent=None):
        super().__init__(parent, radius=18)
        self.setObjectName("stat")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(13, 11, 13, 11)
        lay.setSpacing(10)
        self.chip = IconChip(kind, glyph, 34)
        # v4.4.10 — جبران اپتیکالِ تراز چیپ و متن (اندازه‌گیری پیکسلی):
        # در LTR ارقام/واژه‌های لاتین حرف نزولی ندارند و جوهرِ بلوک متن
        # بالا می‌نشیند (en: +۳٫۰px؛ fa: +۰٫۵px) — ۶px حاشیه‌ی زیرینِ چیپ
        # فقط برای LTR، هر دو زبان را روی محورِ بصری مشترک می‌نشاند
        pad_bottom = 0 if _rtl() else 6
        chip_wrap = QWidget()
        cw = QVBoxLayout(chip_wrap)
        cw.setContentsMargins(0, 0, 0, pad_bottom)
        cw.addWidget(self.chip)
        lay.addWidget(chip_wrap, 0, Qt.AlignmentFlag.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.cap = QLabel(caption)
        self.cap.setObjectName("statCaption")
        self.cap.setWordWrap(False)
        col.addWidget(self.cap)
        self.val = QLabel(value)
        self.val.setObjectName("statValue")
        col.addWidget(self.val)
        lay.addLayout(col, 1)
        # v4.4.10 — ستون متن وسطِ عمودی شود، وگرنه فضای اضافی تهِ کارت
        # می‌ماند و چیپ با متن تراز دیده نمی‌شود (شکایت تراز کل برنامه)
        lay.setAlignment(col, Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch(0)

    def set_value(self, text: str):
        self.val.setText(text)

    def set_caption(self, text: str):
        self.cap.setText(text)

    def set_glyph(self, glyph: str, kind: str = None):
        self.chip.set_icon(kind, glyph)


# ---------- کارت هیرو (قطعی بعدی) ----------

class _CountdownDisplay(QWidget):
    """قابِ نمایشِ شمارش معکوس — v6.0 (بریف: کادرِ دقیقه‌ها باید پس‌زمینه‌ی
    متمایزِ خودش را داشته باشد، حس شود و فید نکند):
    • پنلِ فرورفته با پرشِ تیره‌ی نیمه‌اوپک — کاملاً جدا از گرادیانِ هیرو
    • سایه‌ی داخلی در سقف + نورِ داخلی در کف = حس «جای‌داده‌شده در کارت»
    • لبه‌ی هِیرلاین + گلیف کرنومترِ سفید در سمتِ شروع
    شمارش معکوس داخل همین پنل می‌نشیند و در هر تمی کنتراستِ کامل دارد."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(64)
        lay = QHBoxLayout(self)
        m = 14
        # حاشیه‌ها فیزیکی‌اند و در RTL آینه نمی‌شوند — سمتِ گلیف دستی عوض می‌شود
        # تا متنِ شمارش هرگز زیر گلیف کرنومتر نرود
        if _rtl():
            lay.setContentsMargins(m, 9, m + 26, 9)
        else:
            lay.setContentsMargins(m + 26, 9, m, 9)
        lay.setSpacing(0)
        self.count = QLabel("—")
        self.count.setObjectName("heroCount")
        self.count.setAlignment(_start_align())
        lay.addWidget(self.count, 1)

    def paintEvent(self, event):
        p = theme.current_palette()
        w, h = self.width(), self.height()
        rtl = _rtl()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 16, 16)
        # بدنه — تیره‌ی نیمه‌اوپک؛ روی گرادیانِ هیرو «می‌نشیند»، نه فید
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(qcolor(p["hero_disp"]))
        pnt.drawPath(path)
        pnt.setClipPath(path)
        # سایه‌ی داخلیِ سقف — عمقِ فرورفتگی
        shade = QLinearGradient(0, 0, 0, 13)
        shade.setColorAt(0, QColor(0, 0, 0, 95))
        shade.setColorAt(1, QColor(0, 0, 0, 0))
        pnt.setBrush(shade)
        pnt.drawRect(0, 0, w, 13)
        # نورِ داخلیِ کف — شیشه‌ی واقعی نورِ پایین را هم برمی‌گرداند
        lite = QLinearGradient(0, h - 9, 0, h)
        lite.setColorAt(0, QColor(255, 255, 255, 0))
        lite.setColorAt(1, QColor(255, 255, 255, 26))
        pnt.setBrush(lite)
        pnt.drawRect(0, h - 9, w, 9)
        pnt.setClipping(False)
        # لبه‌ی هِیرلاین — روشن و قابل‌لمس
        pnt.setPen(QPen(qcolor(p["hero_disp_edge"]), 1.1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        # گلیف کرنومتر — سمتِ شروع، سفیدِ ثابت (بستر پنل تیره است)
        gs = 20
        gx = (w - gs - 12) if rtl else 12
        pm = icons.icon_pixmap("timer", gs, "#ffffff", "rgba(255,255,255,0.55)")
        pnt.drawImage(gx, int((h - gs) / 2), pm)
        pnt.end()


class HeroCard(GlassCard):
    """کارت قهرمان صفحه: گرادیان اکسنتِ عمیق و جاروی نور — بدون هیچ حلقه‌ی
    تزئینی (به درخواست کاربر، دایره‌های پس‌زمینه حذف شدند).
    اصول چیدمان v4.2:
      • شمارش معکوس «خودتنظیم» است — اندازه‌ی قلم بر اساس عرض واقعی متن و
        عرض آزاد کارت انتخاب می‌شود؛ متن فارسیِ بلند («۱ روز و ۱۴ ساعت»)
        هرگز از لبه بیرون نمی‌زند
      • با حذف مدار، تمام عرض کارت در اختیار شمارش است — قلم بزرگ‌تر جا می‌شود
      • خط آدرس با ارتفاع رزروشده و بیرون‌زدگی از لبه ندارند"""

    def __init__(self, parent=None):
        super().__init__(parent, radius=22)
        # v5.0 — کارتِ بلندتر برای شمارشِ درشت‌تر (بریف: very large countdown)
        self.setMinimumHeight(208)
        self.setMaximumHeight(244)
        self._next = None
        self._next_dt = None
        self._addr_full = ""
        self._shimmer_x = -0.35
        self._last_count = None    # متن قبلی شمارش — برای نخوردنِ QSS در هر ثانیه
        self._last_font_px = 44

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(6)

        # ردیف ۱: چیپ عنوان + نشان قبض (چند-قبضی)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.chip_lbl = QLabel(i18n.t("dash.next_outage"))
        self.chip_lbl.setObjectName("heroChip")
        top.addWidget(self.chip_lbl)
        self.bill_lbl = QLabel("")
        self.bill_lbl.setVisible(False)
        top.addWidget(self.bill_lbl)
        top.addStretch()
        lay.addLayout(top)
        lay.addSpacing(4)

        # ردیف ۲: قابِ نمایشِ شمارش معکوس (v6.0 — پنلِ فرورفته با پس‌زمینه‌ی
        # متمایز؛ شمارش دیگر روی گرادیان شناور نیست و فید نمی‌شود)
        self.display = _CountdownDisplay()
        self.countdown = self.display.count
        lay.addWidget(self.display)

        # ردیف ۳: روز و بازه‌ی ساعت
        self.sub = QLabel(i18n.t("dash.no_outage_sub"))
        self.sub.setObjectName("heroSub")
        self.sub.setWordWrap(True)
        self.sub.setAlignment(_phys_align())
        lay.addWidget(self.sub)
        lay.addSpacing(2)

        # ردیف ۴: آدرس (ارتفاع ثابت — بیرون نمی‌زند)
        self.addr = QLabel("")
        self.addr.setObjectName("heroAddr")
        self.addr.setFixedHeight(18)
        self.addr.setAlignment(_phys_align())
        lay.addWidget(self.addr)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        # شیمر — جاروی نور روی شیشه؛ v5.1: درایور ۲۴fps (بود ۶۰fps) +
        # توقفِ کامل وقتی صفحه/پنجره پنهان است — هیچ رفرشِ بی‌مصرفی
        # در پس‌زمینه کار نمی‌کند (سنگینی/گرمای گزارش‌شده رفع شد)
        self._shimmer_x = -0.35
        self._shimmer = FpsDriver(24, self._shimmer_step, self)
        if os_env_anim():
            self._shimmer.start()
        self._restyle()

    def _shimmer_step(self):
        # سیکل ۵٫۶ ثانیه‌ای از -۰٫۳۵ تا ۱٫۳۵ (همان مسیر قبلی شیمر)
        x = getattr(self, "_shim_phase", 0.0) + self._shimmer.dt() / 5.6
        self._shim_phase = x % 1.7
        self._shimmer_x = self._shim_phase - 0.35
        self.update()

    def showEvent(self, e):
        super().showEvent(e)
        if os_env_anim():
            self._shimmer.start()

    def hideEvent(self, e):
        super().hideEvent(e)
        self._shimmer.stop()

    def _on_shimmer(self, v):
        self._shimmer_x = float(v)
        self.update()

    # --- استایل درون‌خطی تم‌آگاه ---
    def _restyle(self):
        p = theme.current_palette()
        disp = theme.display_family(800) if _rtl() else theme.FONT_LATIN
        soft = _soft_font()
        self.chip_lbl.setStyleSheet(
            f"background: rgba(255,255,255,0.16); color: {p['hero_text']};"
            "border: 1px solid rgba(255,255,255,0.22);"
            "border-radius: 12px; padding: 4px 12px; font-size: 13px; font-weight: 700;"
        )
        self.bill_lbl.setStyleSheet(
            f"background: rgba(255,255,255,0.10); color: {p['hero_sub']};"
            "border: 1px solid rgba(255,255,255,0.14);"
            "border-radius: 12px; padding: 4px 10px; font-size: 12px; font-weight: 600;"
        )
        self._apply_count_font(self._last_font_px)
        self.sub.setStyleSheet(
            f"font-family: \"{soft}\"; color: {p['hero_sub']};"
            "font-size: 14.5px; font-weight: 600; background: transparent;"
        )
        self.addr.setStyleSheet(
            f"font-family: \"{soft}\"; color: {p['hero_sub']};"
            "font-size: 13px; background: transparent;"
        )

    def _apply_count_font(self, px: int):
        """قلم شمارش معکوس با اندازه‌ی مشخص — فقط وقتی اندازه عوض شود QSS نو می‌شود"""
        if px == self._last_font_px and hasattr(self, "_count_styled"):
            return
        self._last_font_px = px
        disp = theme.display_family(900) if _rtl() else theme.FONT_LATIN
        self.countdown.setStyleSheet(
            f"font-family: \"{disp}\"; color: {theme.current_palette()['hero_text']};"
            f"font-size: {px}px; font-weight: 900; background: transparent;"
        )
        self._count_styled = True

    def repaint_theme(self):
        self._restyle()
        self.update()

    # --- داده ---
    def set_next(self, outage: dict | None):
        self._next = outage
        self._next_dt = None
        if outage:
            from util import outage_addr, outage_datetime
            self._next_dt = outage_datetime(outage)
            s = i18n.num(str(outage.get("outage_start_time", "؟")))
            e = i18n.num(str(outage.get("outage_stop_time", "؟")))
            day = _day_label(outage.get("outage_date"))
            self.sub.setText(f"{day}  •  {i18n.t('time.range', s=s, e=e)}")
            self._addr_full = outage_addr(outage) or i18n.t("dash.unknown_addr")
            # نشان قبض — فقط وقتی بیش از یک قبض پایش می‌شود
            title = str(outage.get("_bill_title") or "")
            if outage.get("_multi") and title:
                self.bill_lbl.setText(title)
                self.bill_lbl.setVisible(True)
            else:
                self.bill_lbl.setVisible(False)
        else:
            self.sub.setText(i18n.t("dash.no_outage_sub"))
            self._addr_full = ""
            self.bill_lbl.setVisible(False)
        self._elide()
        self._tick()

    def _elide(self):
        if self._addr_full and self.addr.width() < 40:
            # هنوز در چیدمان قرار نگرفته — بعد از اولین چیدمان دوباره
            QTimer.singleShot(0, self._elide)
            return
        fm = QFontMetrics(self.addr.font())
        self.addr.setText(
            fm.elidedText(self._addr_full, Qt.ElideRight, self.addr.width() - 4)
            if self._addr_full else ""
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()

    def _tick(self):
        from datetime import datetime
        if not self._next_dt:
            self._set_count("—")
            return
        rem = (self._next_dt - datetime.now()).total_seconds()
        if rem <= 0:
            self._set_count(i18n.t("dash.ongoing"))
            return
        if rem >= 86400:
            d = int(rem // 86400)
            h = int((rem % 86400) // 3600)
            self._set_count(
                i18n.t("dash.days_hours", d=i18n.num(d), h=i18n.num(h))
            )
        else:
            h, m2 = divmod(int(rem), 3600)
            m, s = divmod(m2, 60)
            self._set_count(i18n.num(f"{h:02d}:{m:02d}:{s:02d}"))

    def _set_count(self, text: str):
        """متن شمارش + خودتنظیمی اندازه‌ی قلم تا متن هرگز از قاب بیرون نزند
        (عرضِ آزاد = عرضِ پنل − گلیف و حاشیه‌ها)"""
        if text == self._last_count and hasattr(self, "_fit_done"):
            return
        self._last_count = text
        self.countdown.setText(text)
        # فضای مجاز متن: عرض پنل − حاشیه‌ها و گلیف کرنومتر
        avail = max(90, self.display.width() - 86)
        self._apply_count_font(self._fit_px(text, 44, 21, avail))
        self._fit_done = True

    @staticmethod
    def _fit_px(text: str, max_px: int, min_px: int, avail: int) -> int:
        """بزرگ‌ترین اندازه‌ی پیکسلی که متن در عرضِ avail جا شود —
        اندازه‌گیری واقعی با setPixelSize (نه مقیاس‌ خطی از اندازه‌ی پیش‌فرض)"""
        px = max_px
        while px > min_px:
            f = QFont(theme.display_family(900) if _rtl() else theme.FONT_LATIN)
            f.setPixelSize(px)
            f.setWeight(QFont.Weight.Black)
            f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            if QFontMetrics(f).horizontalAdvance(text) <= avail:
                break
            px -= 1
        return px

    # --- نقاشی ---
    def paintEvent(self, event):
        p = theme.current_palette()
        w, h = self.width(), self.height()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 22, 22)
        # گرادیان عمیق
        grad = QLinearGradient(w, 0, w * 0.25, h)
        grad.setColorAt(0, QColor(p["grad1"]))
        grad.setColorAt(0.55, QColor(p["grad2"]))
        grad.setColorAt(1, QColor(p["grad3"]))
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(grad)
        pnt.drawPath(path)
        pnt.setClipPath(path)
        # شفق داخلی — دو لکه‌ی نرم رنگی (v5.0: لکه‌ی دوم بنفشِ روشنِ هم‌خانواده)
        dark = theme.current_name() != "light"
        blob1 = QRadialGradient(w * 0.82, h * 0.12, w * 0.5)
        blob1.setColorAt(0, QColor(255, 255, 255, 26 if dark else 34))
        blob1.setColorAt(1, QColor(0, 0, 0, 0))
        pnt.setBrush(blob1)
        pnt.drawEllipse(QRectF(w * 0.32, -h * 0.55, w * 1.0, h * 1.4))
        blob2 = QRadialGradient(w * 0.08, h * 0.05, w * 0.35)
        blob2.setColorAt(0, QColor(198, 140, 255, 38 if dark else 42))
        blob2.setColorAt(1, QColor(0, 0, 0, 0))
        pnt.setBrush(blob2)
        pnt.drawEllipse(QRectF(-w * 0.22, -h * 0.3, w * 0.62, h * 0.9))
        # شیمر — نوار نور مورب که عبور می‌کند (v4.7: خیلی محو — مات)
        sx = self._shimmer_x * w
        shim = QLinearGradient(sx - w * 0.18, 0, sx + w * 0.18, h)
        shim.setColorAt(0.42, QColor(255, 255, 255, 0))
        shim.setColorAt(0.5, QColor(255, 255, 255, 16 if dark else 18))
        shim.setColorAt(0.58, QColor(255, 255, 255, 0))
        pnt.setBrush(shim)
        pnt.drawRect(0, 0, w, h)
        pnt.setClipping(False)
        # لبه‌ی اسپکولار (v4.7: لبه‌ی بالاییِ کف‌کرده در روشن)
        edge = QLinearGradient(0, 0, 0, h)
        edge.setColorAt(0, QColor(255, 255, 255, 70 if dark else 84))
        edge.setColorAt(0.4, QColor(255, 255, 255, 16 if dark else 20))
        edge.setColorAt(1, QColor(20, 16, 70, 80))
        pnt.setPen(QPen(edge, 1.2))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        pnt.end()


def _day_label(raw) -> str:
    from util import jalali_day_label
    return jalali_day_label(raw)[0]


# ---------- کارت خاموشی ----------

class OutageCard(QWidget):
    """یک ردیف خاموشی: چیپ دودوتونه + چیپ روز + ساعت درشت + آدرس (+نشان قبض)"""

    HEIGHT = 80

    def __init__(self, item: dict, kind: str, day_label: str, day_key: str = "later",
                 parent=None):
        """kind: occurred | planned — day_key: today|tomorrow|after|in_n|past|done"""
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(self.HEIGHT)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        if kind == "occurred":
            chip_kind, glyph = "teal", "check"
            day_kind = "done"
        else:
            chip_kind, glyph = "indigo", "clock"
            day_kind = {"today": "today", "tomorrow": "soon"}.get(day_key, "later")

        # v4.7 — چیپ ۳۶px با گلیف ~۲۰px (مرجع Material/Fluent)؛ ۴۲px حس «ارزان» می‌داد
        self.icon = IconChip(chip_kind, glyph, 36)
        row.addWidget(self.icon)

        mid = QVBoxLayout()
        mid.setSpacing(3)
        top = QHBoxLayout()
        top.setSpacing(8)
        chip = QLabel(day_label)
        chip.setObjectName("chip")
        chip.setProperty("kind", day_kind)
        top.addWidget(chip)

        s = i18n.num(str(item.get("outage_start_time", "؟")))
        e = i18n.num(str(item.get("outage_stop_time", "؟")))
        time_lbl = QLabel(i18n.t("time.range", s=s, e=e))
        time_lbl.setObjectName("timeRange")
        top.addWidget(time_lbl)

        # نشان قبض — فقط در پایش چند-قبضی
        bill_title = str(item.get("_bill_title") or "")
        if item.get("_multi") and bill_title:
            bchip = QLabel(bill_title)
            bchip.setObjectName("chip")
            bchip.setProperty("kind", "bill")
            top.addWidget(bchip)
        top.addStretch()
        mid.addLayout(top)

        addr = ""
        try:
            from util import outage_addr
            addr = outage_addr(item)
        except Exception:
            addr = str(item.get("outage_address") or "").strip()
        addr = addr or i18n.t("dash.unknown_addr")
        addr_lbl = QLabel(addr)
        addr_lbl.setObjectName("muted")
        addr_lbl.setAlignment(_phys_align())   # آدرس داده‌ی فارسی است؛ در UI انگلیسی هم سرِ ستون بماند
        addr_lbl.setStyleSheet(
            f"font-family: \"{_soft_font()}\"; font-size: 13.5px;")
        mid.addWidget(addr_lbl)
        row.addLayout(mid, 1)
        # v4.4.10 — بلوک متن وسطِ ردیف؛ چیپ ۴۲px وسط است و متن هم باید
        # روی همان محور بنشیند (وگرنه متن بالا-لنگر و چیپ پایین‌تر دیده می‌شد)
        row.setAlignment(mid, Qt.AlignmentFlag.AlignVCenter)
        # رفع هم‌ریختگی: کارت ارتفاع ثابت ۸۰px دارد؛ آدرس بلند باید بریده شود
        # وگرنه از ردیف بیرون می‌زند و روی ردیف بعدی می‌افتد
        self._addr_full = addr
        self.addr_lbl = addr_lbl

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.addr_lbl.width()
        if w > 40:
            fm = QFontMetrics(self.addr_lbl.font())
            self.addr_lbl.setText(
                fm.elidedText(self._addr_full, Qt.ElideRight, w - 2))

    def repaint_theme(self):
        self.update()


# ---------- پییل وضعیت اتصال ----------

class StatusPill(QWidget):
    """کپسول شیشه‌ای وضعیت با نقطه‌ی تپنده — جایگزین متنیِ «●»"""

    LEVEL = {"ok": "#2bbd8a", "bad": "#f4596c", "unknown": None}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = i18n.t("conn.preparing")
        self._level = "unknown"
        self._pulse = 0.0
        self.setFixedHeight(32)
        self.setMinimumWidth(120)
        self.setMaximumWidth(340)   # متن‌های خطای بلند سربرگ را نباید بترکانند
        # v5.1 — تپشِ نقطه روی درایور ۲۴fps (بود ۶۰fps) + توقف وقتی پنهان است
        self._pulse_drv = FpsDriver(24, self._pulse_step, self)

    def _pulse_step(self):
        self._pulse = self._pulse_drv.advance(self._pulse_drv.dt())
        self.update()

    def _on_pulse(self, v):
        self._pulse = float(v)
        self.update()

    def showEvent(self, e):
        super().showEvent(e)
        if os_env_anim() and self.LEVEL.get(self._level):
            self._pulse_drv.start()

    def hideEvent(self, e):
        super().hideEvent(e)
        self._pulse_drv.stop()

    def set_state(self, text: str, level: str):
        self._text = text
        self._level = level if level in self.LEVEL else "unknown"
        # نقطه‌ی بی‌رنگ (نامشخص) نبض ندارد — درایور همین‌جا مدیریت می‌شود
        if self.LEVEL.get(self._level) and os_env_anim():
            if self.isVisible() and not self._pulse_drv.isActive():
                self._pulse_drv.start()
        else:
            self._pulse_drv.stop()
            self._pulse = 0.0
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self._text) + 58
        return QSize(max(120, min(340, w)), 32)

    def repaint_theme(self):
        self.update()

    def paintEvent(self, event):
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 15, 15)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(qcolor(p["glass_strong"]))
        pnt.drawPath(path)
        pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        rtl = _rtl()
        # نقطه‌ی وضعیت — سمتِ شروع (راست در فارسی، چپ در انگلیسی)
        cx = (w - 17) if rtl else 17
        cy = h / 2
        color = self.LEVEL.get(self._level)
        if color:
            c = qcolor(color)
            beat = 0.5 + 0.5 * math.sin(self._pulse)
            halo = QRadialGradient(cx, cy, 11)
            hc = QColor(c)
            hc.setAlpha(int(60 + 50 * beat))
            halo.setColorAt(0.3, hc)
            halo.setColorAt(1.0, QColor(0, 0, 0, 0))
            pnt.setPen(Qt.NoPen)
            pnt.setBrush(halo)
            pnt.drawEllipse(QRectF(cx - 11, cy - 11, 22, 22))
            pnt.setBrush(c)
            pnt.drawEllipse(QRectF(cx - 3.4, cy - 3.4, 6.8, 6.8))
        else:
            pnt.setPen(Qt.NoPen)
            pnt.setBrush(qcolor(p["text3"]))
            pnt.drawEllipse(QRectF(cx - 3.2, cy - 3.2, 6.4, 6.4))
        # متن — سمت مقابل نقطه؛ با بریدگیِ میان‌نقطه تا هرگز روی چیزی نریزد
        pnt.setPen(QColor(p["text"]))
        f = QFont(_body_font())
        f.setPointSizeF(9.4)
        f.setWeight(QFont.Weight.DemiBold)
        pnt.setFont(f)
        if rtl:
            rect = QRectF(8, 0, w - 36, h)
            align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        else:
            rect = QRectF(36, 0, w - 36 - 8, h)
            align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        max_txt = max(48, int(rect.width()))
        shown = QFontMetrics(f).elidedText(self._text, Qt.ElideMiddle, max_txt)
        pnt.drawText(rect, int(align), shown)
        pnt.end()


# ---------- چیپ موقعیت سربرگ (v5.0) ----------

class LocationChip(QWidget):
    """چیپ موقعیت سربرگ — پینِ نقشه + آدرسِ بریده‌شده؛ کاملاً داده‌محور:
    فقط وقتی آدرسِ واقعی از آخرین اسنپ‌شات هست دیده می‌شود (بدون داده‌ی قلابی).
    چهره‌ی شیشه‌ای هم‌خانواده‌ی پییلِ وضعیت."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._addr = ""
        self.setFixedHeight(32)
        self.setMaximumWidth(260)   # v5.1 — سقف عرض: سربرگ در پنجره‌ی باریک نمی‌شکند
        self.setVisible(False)

    def set_address(self, text: str):
        self._addr = (text or "").strip()
        self.setVisible(bool(self._addr))
        if self._addr:
            self.setToolTip(i18n.t("hdr.location") + ": " + self._addr)
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self._text) + 46 if self._text else 80
        return QSize(max(80, min(320, w)), 32)

    def repaint_theme(self):
        self.update()

    def paintEvent(self, event):
        if not self._addr:
            return
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 15, 15)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(qcolor(p["glass_strong"]))
        pnt.drawPath(path)
        pnt.setPen(QPen(qcolor(p["glass_border"]), 1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        rtl = _rtl()
        # پین — سمتِ شروع (راست در فارسی)
        gsz = 15
        gx = (w - gsz - 12) if rtl else 12
        h2 = p["accent"].lstrip("#")
        fg = p["accent"]
        soft = f"rgba({int(h2[0:2], 16)},{int(h2[2:4], 16)},{int(h2[4:6], 16)},0.45)"
        pnt.drawImage(gx, int((h - gsz) / 2), icons.icon_pixmap("mappin", gsz, fg, soft))
        # متن آدرس — بریده با «…» تا هرگز روی چیپ کناری نریزد
        f = QFont(_body_font())
        f.setPointSizeF(9.2)
        f.setWeight(QFont.Weight.DemiBold)
        pnt.setFont(f)
        if rtl:
            rect = QRectF(8, 0, w - 38, h)
            align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        else:
            rect = QRectF(38, 0, w - 44, h)
            align = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        max_txt = max(40, int(rect.width()))
        self._text = QFontMetrics(f).elidedText(self._addr, Qt.ElideMiddle, max_txt)
        pnt.setPen(QColor(p["text2"]))
        pnt.drawText(rect, int(align), self._text)
        pnt.end()


# ---------- حالت خالی تزئینی ----------

class EmptyState(QWidget):
    """وقتی هیچ خاموشی‌ای نیست: صاعقه‌ی ناجی + جرقه‌ها + پیام آرام
    (به درخواست کاربر: نشانِ دایره‌ایِ مدار با صاعقه عوض شد)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 16, 0, 16)
        lay.setSpacing(10)
        art = QLabel()
        art.setAlignment(Qt.AlignCenter)
        self._art = art
        lay.addWidget(art)
        self.t1 = QLabel(i18n.t("empty.title"))
        self.t1.setObjectName("muted")
        self.t1.setAlignment(Qt.AlignCenter)
        self.t1.setWordWrap(True)
        lay.addWidget(self.t1)
        self.t2 = QLabel(i18n.t("empty.sub"))
        self.t2.setObjectName("hint")
        self.t2.setAlignment(Qt.AlignCenter)
        self.t2.setWordWrap(True)
        lay.addWidget(self.t2)
        self.repaint_theme()

    def retranslate(self):
        self.t1.setText(i18n.t("empty.title"))
        self.t2.setText(i18n.t("empty.sub"))

    def repaint_theme(self):
        p = theme.current_palette()
        chips = theme.chips()
        c = chips["indigo"]
        # v4.7 — هنرِ حالت خالی کوچک‌تر: صاعقه‌ی ۶۰px وسطِ بوم ۹۲×۶۴
        # (۸۴px قبلی بزرگ‌نمای بی‌دلیل بود)
        art = QImage(92, 64, QImage.Format.Format_ARGB32)
        art.fill(Qt.GlobalColor.transparent)
        pnt = QPainter(art)
        pnt.setRenderHint(QPainter.Antialiasing)
        bolt = icons.icon_pixmap("bolt", 60, c["fg"], c["fg"])
        pnt.setOpacity(0.9)
        pnt.drawImage(14, 0, bolt)
        sp = icons.icon_pixmap("spark", 20, c["fg"], c["fg"])
        pnt.setOpacity(0.9)
        pnt.drawImage(66, 4, sp)
        pnt.setOpacity(0.55)
        pnt.drawImage(6, 32, icons.icon_pixmap("spark", 13, p["text3"], p["text3"]))
        pnt.end()
        self._art.setPixmap(QPixmap_from_image(art))


def QPixmap_from_image(img):
    from PySide6.QtGui import QPixmap
    return QPixmap.fromImage(img)


# ---------- نمونه‌سازی کارت‌ها در لیست ----------

def fill_outage_list(list_widget: QListWidget, occurred: list, planned: list,
                     multi: bool = False):
    """کارت خاموشی‌ها را در QListWidget می‌چیند؛ True اگر موردی بود"""
    from PySide6.QtCore import QSize as _QSize
    from PySide6.QtWidgets import QListWidgetItem
    from util import day_label_key

    list_widget.clear()
    has_any = False

    def _add(item: dict, kind: str, day: str, day_key: str):
        nonlocal has_any
        has_any = True
        it = QListWidgetItem()
        it.setSizeHint(_QSize(0, OutageCard.HEIGHT))
        list_widget.addItem(it)
        list_widget.setItemWidget(it, OutageCard(item, kind, day, day_key))

    for o in occurred or []:
        o = dict(o)
        o["_multi"] = multi
        _add(o, "occurred", i18n.t("day.today"), "today")
    for o in planned or []:
        o = dict(o)
        o["_multi"] = multi
        key, _param, _diff = day_label_key(o.get("outage_date"))
        label = _day_label(o.get("outage_date"))
        _add(o, "planned", label, key)
    return has_any


# ---------- بنر وضعیت سرویس برق‌من (v6.0) ----------

class _HealthDots(QWidget):
    """نوار سلامتِ کوچک — وضعیت ۸ بررسیِ اخیر برق‌من (صفحه‌ی وضعیتِ مینی):
    سبز = سالم، قرمز = خطا، خاکستری = بی‌داده"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._health = []          # bool | None — از جدید به قدیم
        self.setFixedHeight(26)

    def set_health(self, health: list):
        self._health = list(health or [])[:8]
        self.update()

    def paintEvent(self, event):
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        n = max(1, len(self._health))
        gap = 7
        d = 8
        total = n * d + (n - 1) * gap
        x0 = (w - total) / 2 if w > total else 4
        # ترتیب: جدیدترین در سمتِ شروع
        pnt.setPen(Qt.NoPen)
        for i, ok in enumerate(self._health):
            cx = x0 + i * (d + gap) + d / 2
            if ok is True:
                c = QColor("#2bbd8a")
            elif ok is False:
                c = QColor("#f4596c")
            else:
                p = theme.current_palette()
                c = qcolor(p["text3"])
                c.setAlpha(110)
            pnt.setBrush(c)
            pnt.drawEllipse(QRectF(cx - d / 2, h / 2 - d / 2, d, d))
        if not self._health:
            p = theme.current_palette()
            pnt.setBrush(qcolor(p["text3"]))
            pnt.setOpacity(0.5)
            pnt.drawEllipse(QRectF(w / 2 - d / 2, h / 2 - d / 2, d, d))
        pnt.end()


class _BannerCloseButton(QPushButton, _JellyPress):
    """دکمه‌ی کوچکِ بستنِ بنر — گلیف ضربدرِ رسم‌شده در paintEvent خودش
    (نقاشیِ فرزند داخل paintEvent والد ممنوع است — هشدار Qt می‌دهد)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self._jelly_init()

    def paintEvent(self, event):
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        p = theme.current_palette()
        if self.isDown():
            bg = QColor(255, 255, 255, 26)
        elif self.underMouse():
            bg = qcolor(p["danger_tint"])
        else:
            bg = QColor(0, 0, 0, 0)
        if bg.alpha() > 0:
            pnt.setPen(Qt.NoPen)
            pnt.setBrush(bg)
            pnt.drawEllipse(QRectF(0.5, 0.5, self.width() - 1,
                                   self.height() - 1))
        col = QColor(p["danger"]) if self.underMouse() else QColor(p["text3"])
        pnt.setPen(QPen(col, 2.2, Qt.SolidLine, Qt.RoundCap))
        s = self.width()
        k = 7
        c = s / 2
        pnt.drawLine(QPointF(c - k / 2, c - k / 2),
                     QPointF(c + k / 2, c + k / 2))
        pnt.drawLine(QPointF(c + k / 2, c - k / 2),
                     QPointF(c - k / 2, c + k / 2))
        pnt.end()


class ServiceBanner(GlassCard):
    """بنر «وضعیت سرویس برق‌من» — v6.0 (اولویت ۱ بریف: وقتی سرور برق‌من
    قطع/کند است، به‌جای خطای خام، پیامِ واضح که «مشکل از برق‌منه، نه ناجی»):
    چیپ هشدار + عنوان و توضیح + نوار سلامتِ ۸ بررسیِ اخیر + تلاش دوباره/بستن"""

    retry_clicked = Signal()
    dismissed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, radius=18)
        self.setObjectName("svcBanner")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)

        self.chip = IconChip("amber", "alert", 40)
        lay.addWidget(self.chip, 0, Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(2)
        self.title = QLabel("")
        self.title.setObjectName("svcTitle")
        self.body = QLabel("")
        self.body.setObjectName("svcBody")
        self.body.setWordWrap(True)
        col.addWidget(self.title)
        col.addWidget(self.body)
        lay.addLayout(col, 1)

        side = QVBoxLayout()
        side.setSpacing(4)
        self.dots = _HealthDots()
        self.dots.setFixedWidth(120)
        side.addWidget(self.dots, 0, Qt.AlignmentFlag.AlignHCenter)
        self.btn_retry = JellyButton(i18n.t("svc.retry"))
        self.btn_retry.setObjectName("ghost")
        self.btn_retry.setCursor(Qt.PointingHandCursor)
        self.btn_retry.setFixedHeight(34)
        self.btn_retry.clicked.connect(self.retry_clicked.emit)
        side.addWidget(self.btn_retry)
        lay.addLayout(side, 0)

        self.btn_close = _BannerCloseButton(self)
        self.btn_close.clicked.connect(self._dismiss)
        lay.addWidget(self.btn_close, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setVisible(False)

    def set_state(self, kind: str, health: list = None):
        """kind: saapa (سرور کند/قطع) | net (اتصال ما) — پیام متفاوت"""
        chips = theme.chips()
        c = chips.get("amber")
        self.chip.set_icon("amber", "alert")
        if kind == "net":
            self.chip.set_icon("rose", "signal")
            self.title.setText(i18n.t("svc.net_title"))
            self.body.setText(i18n.t("svc.net_body"))
        elif kind == "timeout":
            self.chip.set_icon("amber", "timer")
            self.title.setText(i18n.t("svc.slow_title"))
            self.body.setText(i18n.t("svc.slow_body"))
        else:
            self.chip.set_icon("amber", "alert")
            self.title.setText(i18n.t("svc.down_title"))
            self.body.setText(i18n.t("svc.down_body"))
        self.btn_retry.setText(i18n.t("svc.retry"))
        self.btn_close.setToolTip(i18n.t("svc.dismiss"))
        if health is not None:
            self.dots.set_health(health)
        self.setVisible(True)

    def set_health(self, health: list):
        self.dots.set_health(health)

    def _dismiss(self):
        self.setVisible(False)
        self.dismissed.emit()

    def repaint_theme(self):
        self.update()


# ---------- نمودار تاریخچه‌ی قطعی‌ها (v6.0) ----------

class _BarArea(QWidget):
    """ناحیه‌ی نمودار میله‌ای — رسمِ سفارشی با گرادیانِ اکسنت:
    • هر میله = یک روز (تعداد قطعی)؛ میله‌ی امروز با فامِ دوم سبز می‌درخشد
    • عددِ تعداد روی میله، برچسبِ روز زیر میله
    • کفِ راهنما و خطوطِ راهنمای افقیِ محو"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._days = []            # [{label, count, minutes, today}]
        self.setMinimumHeight(148)

    def set_data(self, days: list):
        self._days = list(days or [])
        self.update()

    def paintEvent(self, event):
        if not self._days:
            return
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pad_top, pad_bot, pad_side = 22, 22, 2
        chart_h = h - pad_top - pad_bot
        n = len(self._days)
        slot = w / n
        body_font = QFont(_body_font())
        body_font.setPointSizeF(8.2)
        cap_font = QFont(_soft_font())
        cap_font.setPointSizeF(8.4)
        mx = max(1, max(d.get("count", 0) for d in self._days))
        # خطوط راهنمای افقی محو (سه پله)
        pnt.setPen(QPen(qcolor(p["glass_edge"]), 1))
        for k in (1, 2, 3):
            y = pad_top + chart_h - chart_h * k / 3.0
            pnt.drawLine(QPointF(pad_side, y), QPointF(w - pad_side, y))
        for i, d in enumerate(self._days):
            count = max(0, int(d.get("count", 0)))
            bw = min(26.0, slot * 0.56)
            x = i * slot + (slot - bw) / 2
            bh = 0.0 if count == 0 else max(6.0, chart_h * (count / mx))
            y = pad_top + chart_h - bh
            bar = QPainterPath()
            bar.addRoundedRect(QRectF(x, y, bw, bh), 4, 4)
            pnt.setPen(Qt.NoPen)
            if d.get("today"):
                grad = QLinearGradient(x, y, x, y + bh)
                grad.setColorAt(0, QColor(p["accent2"]))
                grad.setColorAt(1, QColor(p["accent2"]))
                pnt.setBrush(grad)
            else:
                grad = QLinearGradient(x, y, x, y + bh)
                grad.setColorAt(0, QColor(p["grad1"]))
                grad.setColorAt(1, QColor(p["grad3"]))
                pnt.setBrush(grad)
            if count == 0:
                # روزِ بی‌قطعی — نشانگرِ کوتاهِ محو
                pnt.setBrush(qcolor(p["glass_edge"]))
                pnt.drawRoundedRect(QRectF(x, pad_top + chart_h - 3, bw, 3), 2, 2)
            else:
                pnt.drawPath(bar)
                # عدد روی میله
                pnt.setPen(QColor(p["text2"]))
                pnt.setFont(body_font)
                pnt.drawText(QRectF(x - slot * 0.22, y - 17, bw + slot * 0.44, 15),
                             int(Qt.AlignmentFlag.AlignHCenter |
                                 Qt.AlignmentFlag.AlignVCenter),
                             i18n.num(count))
            # برچسب روز — فقط هر چند تا (در ۳۰ روزه شلوغ نشود)
            lab = str(d.get("label", ""))
            if n <= 8 or i % max(1, n // 7) == 0 or i == n - 1:
                pnt.setPen(QColor(p["text3"]))
                pnt.setFont(cap_font)
                pnt.drawText(QRectF(i * slot, h - pad_bot + 4, slot, 16),
                             int(Qt.AlignmentFlag.AlignHCenter |
                                 Qt.AlignmentFlag.AlignVCenter), lab)
        pnt.end()


class HistoryChart(GlassCard):
    """کارت تاریخچه‌ی قطعی‌ها — v6.0 (اولویت ۲ بریف: چند وقته قطعی داشتیم،
    چقدر طول کشیده، آمار هفتگی/ماهانه): سگمنت ۷/۳۰ روز + نمودار + خطِ خلاصه.
    داده‌ها همان‌هایی که همین حالا از API می‌آیند و در storage ثبت می‌شوند."""

    range_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, radius=20)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 15, 18, 13)
        lay.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(8)
        self.chip = IconChip("violet", "chart", 34)
        head.addWidget(self.chip)
        col = QVBoxLayout()
        col.setSpacing(0)
        self.eyebrow_lbl = QLabel(i18n.t("hist.eyebrow"))
        self.eyebrow_lbl.setObjectName("eyebrow")
        self.title_lbl = QLabel(i18n.t("hist.title"))
        self.title_lbl.setObjectName("h2")
        col.addWidget(self.eyebrow_lbl)
        col.addWidget(self.title_lbl)
        head.addLayout(col)
        head.addStretch()
        self.segment = Segmented(
            [("7", i18n.t("hist.seg7")), ("30", i18n.t("hist.seg30"))], "7")
        self.segment.setMinimumWidth(190)
        self.segment.changed.connect(self._on_range)
        head.addWidget(self.segment, 0, Qt.AlignmentFlag.AlignBottom)
        lay.addLayout(head)

        self.bars = _BarArea()
        lay.addWidget(self.bars, 1)

        self.summary = QLabel("")
        self.summary.setObjectName("hint")
        self.summary.setAlignment(_phys_align())
        lay.addWidget(self.summary)
        self.empty_hint = QLabel(i18n.t("hist.empty"))
        self.empty_hint.setObjectName("hint")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.empty_hint.setWordWrap(True)
        lay.addWidget(self.empty_hint)
        self._has_data = False

    def _on_range(self, v: str):
        self.range_changed.emit(v)

    def range_value(self) -> str:
        return self.segment.value()

    def set_range(self, v: str):
        self.segment.set_current(v)

    def set_data(self, days: list):
        """days: [{label, count, minutes, today}] — قدیمی به جدید"""
        self.bars.set_data(days)
        total_c = sum(int(d.get("count", 0)) for d in days)
        total_m = sum(int(d.get("minutes", 0)) for d in days)
        self._has_data = total_c > 0
        self.bars.setVisible(True)
        self.empty_hint.setVisible(not self._has_data)
        rng = self.segment.value()
        span = i18n.t("hist.span7") if rng == "7" else i18n.t("hist.span30")
        if self._has_data:
            self.summary.setText(i18n.t(
                "hist.sum", span=span, c=i18n.num(total_c), m=i18n.num(total_m)))
        else:
            self.summary.setText("")
        self.update()

    def repaint_theme(self):
        self.update()


# ---------- سوییچر قبض‌ها (v6.0) ----------

class BillSwitcher(QWidget):
    """سوییچر شیشه‌ای چند-قبضی — v6.0 (بریف: تب‌بندی یا سوییچرِ واضح‌تر):
    کپسول شیشه‌ای با یک «تبِ قرصی» برای هر قبض + دکمه‌ی + برای افزودن.
    تب فعال با گرادیان اکسنت روشن می‌شود."""

    bill_selected = Signal(str)
    add_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("billSwitch")
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(6, 6, 6, 6)
        self._lay.setSpacing(6)
        self._buttons = {}
        self._active = ""
        self.setVisible(False)

    def rebuild(self, bills: list, active_id: str = ""):
        while self._lay.count():
            it = self._lay.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        self._buttons.clear()
        self._active = active_id or ""
        for b in bills or []:
            bid = b.get("bill_id", "")
            title = b.get("bill_title") or bid
            is_on = bid == self._active
            btn = JellyButton(title)
            btn.setObjectName("billTabOn" if is_on else "billTab")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(title)
            btn.clicked.connect(lambda _=False, k=bid: self.bill_selected.emit(k))
            self._lay.addWidget(btn)
            self._buttons[bid] = btn
        add = JellyButton("+")
        add.setObjectName("billAdd")
        add.setCursor(Qt.PointingHandCursor)
        add.setFixedWidth(44)
        add.setToolTip(i18n.t("bills.add"))
        add.clicked.connect(self.add_requested.emit)
        self._lay.addWidget(add)
        self._lay.addStretch(1)
        self.setVisible(len(self._buttons) > 1)

    def set_active(self, active_id: str):
        if active_id == self._active:
            return
        self._active = active_id
        for bid, btn in self._buttons.items():
            btn.setObjectName("billTabOn" if bid == active_id else "billTab")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.update()

    def paintEvent(self, event):
        # کپسول شیشه‌ای میزبانِ تب‌ها — هم‌خانواده‌ی سگمنت
        p = theme.current_palette()
        pnt = QPainter(self)
        pnt.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 20, 20)
        pnt.setPen(Qt.NoPen)
        pnt.setBrush(qcolor(p["glass_soft"]))
        pnt.drawPath(path)
        pnt.setPen(QPen(qcolor(p["glass_edge"]), 1))
        pnt.setBrush(Qt.NoBrush)
        pnt.drawPath(path)
        pnt.end()

    def repaint_theme(self):
        self.update()
