# login_dialog.py — ورود به برق‌من: موبایل → کد تایید → انتخاب قبض
# -------------------------------------------------------------------
# v4:
#   • تمام متن‌ها از i18n می‌آیند (فارسی/انگلیسی + RTL/LTR خودکار)
#   • قبض انتخابی با storage.set_bills ذخیره می‌شود (پایه‌ی پایش چند-قبضی؛
#     قبض‌های بعدی از تنظیمات اضافه می‌شوند)
#   • حسابِ بدون قبض: به‌جای خطای بن‌بست، راهنمای چهارمرحله‌ای «ثبت قبض
#     در برق‌من» با دکمه‌ی بررسیِ دوباره نمایش داده می‌شود
# عملیات شبکه در QThread جداگانه اجرا می‌شود تا رابط کاربری هرگز فریز نشود.
import re

from PySide6.QtCore import QRegularExpression, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)
import i18n
import storage
import theme
from api import ApiError, VpnBlocked
from util import num, to_latin_digits
from widgets import BackdropCanvas, IconChip, JellyButton, LogoChip

MOBILE_RE = re.compile(r"^09\d{9}$")
CODE_RE = re.compile(r"^\d{6}$")

STEPS = 3


def hline() -> QFrame:
    f = QFrame()
    f.setObjectName("hline")
    f.setFrameShape(QFrame.HLine)
    return f


def _field_align() -> Qt.AlignmentFlag:
    """تراز متنِ فیلدها با جهت زبان — AlignAbsolute ضروری است چون
    AlignLeft/AlignRight ساده در چیدمان RTL آینه می‌شوند و متن/placeholder
    فیلد به لبه‌ی چپ می‌چسبید (ظاهر «فونت و چیدمان خراب» در صفحه‌ی ورود)"""
    if i18n.is_rtl():
        return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
    return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute


def digits_only(editor: QLineEdit, max_len: int):
    editor.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9]*")))
    editor.setMaxLength(max_len)


class _Task(QThread):
    """اجرای یک تابع در رشته‌ی جداگانه؛ نتیجه یا خطا با سیگنال برمی‌گردد"""

    done = Signal(object, object)  # (result, exception)

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args

    def run(self):
        try:
            self.done.emit(self._fn(*self._args), None)
        except Exception as e:  # noqa: BLE001
            self.done.emit(None, e)


class LoginDialog(QDialog):
    """ورود سه‌مرحله‌ای: موبایل ← کد تایید ← انتخاب قبض (+ راهنمای قبضِ ثبت‌نشده).
    لیبل خطا ثابت در پایین است تا چیدمان نپرد."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("login.title"))
        self.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
        self.setFixedWidth(540)

        self.token = ""
        self.mobile = ""
        self.bill_id = ""
        self.bill_title = ""
        self._bill_hint = ""
        self._bills = []
        self._busy_widgets = []
        self._task = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # بوم شفق — بستر کل دیالوگ
        canvas = BackdropCanvas(self)
        canvas.setObjectName("central")
        root.addWidget(canvas)
        inner = QVBoxLayout(canvas)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ---------- سربرگ برند ----------
        brand = QVBoxLayout()
        brand.setContentsMargins(26, 24, 26, 6)
        brand.setSpacing(8)
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(LogoChip(48))   # v4.7 — ۴۸px (بود ۵۶)
        logo_row.addStretch()
        brand.addLayout(logo_row)
        eyebrow = QLabel(i18n.t("login.eyebrow"))
        eyebrow.setObjectName("eyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        brand.addWidget(eyebrow)
        app_name = QLabel(i18n.t("app.name"))
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet(
            f"font-family: \"{theme.display_family(900)}\"; font-size: 23px; font-weight: 900;")
        brand.addWidget(app_name)
        app_sub = QLabel(i18n.t("login.sub"))
        app_sub.setAlignment(Qt.AlignCenter)
        app_sub.setObjectName("muted")
        brand.addWidget(app_sub)
        inner.addLayout(brand)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_mobile())
        self.stack.addWidget(self._page_code())
        self.stack.addWidget(self._page_bill())
        self.stack.addWidget(self._page_guide())   # شاخه‌ی «حسابِ بدون قبض»
        inner.addWidget(self.stack, 1)

        self.err = QLabel("")
        self.err.setObjectName("formError")
        self.err.setWordWrap(True)
        self.err.setAlignment(Qt.AlignCenter)
        self.err.setMinimumHeight(48)
        inner.addWidget(self.err)
        self._restyle_err()

    def _restyle_err(self):
        p = theme.current_palette()
        self.err.setStyleSheet(
            f"color: {p['danger']}; padding: 6px 18px 14px 18px; font-size: 13px;"
        )

    def repaint_theme(self):
        self._restyle_err()

    # ---------- اجرای غیرهمزمان ----------

    def _run(self, fn, on_done, *args):
        """fn را با args در پس‌زمینه اجرا می‌کند؛ تا پایان دکمه‌ها غیرفعال ولی
        UI زنده است.
        باگ v4.2: امضای قبلی (fn, *args, on_done) بود و on_done عملاً
        فقط‌کیوردی می‌شد، ولی هر سه فراخوانی آن را موقعیتی می‌دادند →
        TypeError وسط اسلات → در exe پنجره‌ای (بدون کنسول) دکمه «مرده»
        به نظر می‌رسید. حالا callback دومین پارامتر موقعیتی است.
        علاوه بر آن، اگر شبکه کند باشد کاربر بعد از ۶ ثانیه یک راهنمای
        «هنوز در حال اتصال…» می‌بیند تا کلیکِ ثبت‌شده مرئی باشد."""
        self._task = _Task(fn, *args, parent=self)
        self._task.done.connect(on_done)
        self._busy(True)
        self._set_err("")
        QTimer.singleShot(
            6000, lambda: self._set_hint(i18n.t("login.wait_hint"))
            if (self._task is not None and self._task.isRunning()) else None
        )
        self._task.start()

    def _guard(self, action):
        """هر خطای پایتون داخل اسلات‌ها را به پیام قابل‌دیدن تبدیل می‌کند؛
        بدون این، در exe پنجره‌ای هر استثنا یعنی دکمه‌ای که هیچ عکس‌العملی
        ندارد و کاربر فکر می‌کند برنامه خراب است."""
        try:
            action()
        except Exception as e:  # noqa: BLE001
            self._task_done()
            self._busy(False)
            self._set_err(f"{i18n.t('login.internal_err')}: {e}")

    def _set_hint(self, text: str):
        """پیام خنثی (نه خطا) در نوار پیام پایین — با رنگ متن دوم تم"""
        p = theme.current_palette()
        self.err.setText(f"<span style='color:{p['text2']};'>{text}</span>")

    def _task_done(self):
        """پاکسازی مرتب task پس از اتمام (قبل از رها کردن مرجع)"""
        t, self._task = self._task, None
        if t is not None:
            t.wait(2000)

    def reject(self):
        # تا وقتی درخواست در جریان است، بستن دیالوگ ممکن نیست
        if self._task is not None and self._task.isRunning():
            return
        super().reject()

    # ---------- سربرگ مشترک ----------

    def _header(self, step: int, title: str, subtitle: str) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setSpacing(6)

        steps = QHBoxLayout()
        steps.setSpacing(6)
        for i in range(1, STEPS + 1):
            chip = QLabel(num(i))
            chip.setObjectName("stepChip")
            state = "active" if i == step else ("done" if i < step else "todo")
            chip.setProperty("state", state)
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedSize(28, 28)
            steps.addWidget(chip)
            if i < STEPS:
                line = QFrame()
                line.setObjectName("stepLine")
                line.setFixedHeight(2)
                steps.addWidget(line, 1)
        steps.addStretch()
        s = QLabel(i18n.t("login.step", n=num(step), total=num(STEPS)))
        s.setStyleSheet(
            f"color: {theme.current_palette()['accent']};"
            "font-weight: 800; font-size: 12.5px;"
        )
        steps.addWidget(s)
        lay.addLayout(steps)

        t = QLabel(title)
        t.setStyleSheet(
            f"font-family: \"{theme.display_family(800)}\"; font-size: 18.5px; font-weight: 800;")
        sub = QLabel(subtitle)
        sub.setWordWrap(True)
        sub.setObjectName("muted")
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addSpacing(4)
        return lay

    def _page(self) -> tuple:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(26, 14, 26, 14)
        lay.setSpacing(12)
        return w, lay

    # ---------- صفحه ۱: موبایل ----------

    def _page_mobile(self) -> QWidget:
        w, lay = self._page()
        lay.addLayout(self._header(
            1, i18n.t("login.s1_title"), i18n.t("login.s1_sub")))

        lbl_m = QLabel(i18n.t("login.mobile"))
        lbl_m.setObjectName("fieldLabel")
        lay.addWidget(lbl_m)
        self.in_mobile = QLineEdit()
        self.in_mobile.setPlaceholderText(i18n.t("login.mobile_ph"))
        digits_only(self.in_mobile, 11)
        self.in_mobile.setAlignment(_field_align())
        self.in_mobile.textChanged.connect(lambda: self._set_err(""))
        self.in_mobile.returnPressed.connect(lambda: self._guard(self._send_code))
        lay.addWidget(self.in_mobile)

        lbl_b = QLabel(i18n.t("login.bill_hint"))
        lbl_b.setObjectName("fieldLabel")
        lay.addWidget(lbl_b)
        self.in_bill = QLineEdit()
        self.in_bill.setPlaceholderText(i18n.t("login.bill_hint_ph"))
        self.in_bill.setAlignment(_field_align())
        self.in_bill.returnPressed.connect(self._send_code)
        lay.addWidget(self.in_bill)

        lay.addStretch()
        btn = JellyButton(i18n.t("login.send_code"))
        btn.setObjectName("primary")
        btn.setMinimumHeight(48)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._guard(self._send_code))
        lay.addWidget(btn)
        self._busy_widgets.append(btn)
        return w

    def _send_code(self):
        if self._task is not None:
            return  # درخواست دیگری در جریان است
        mobile = to_latin_digits(self.in_mobile.text())
        if not MOBILE_RE.fullmatch(mobile):
            self._set_err(i18n.t("login.bad_mobile"))
            return
        self._pending_mobile = mobile
        self._pending_hint = re.sub(r"[\s\-]", "", to_latin_digits(self.in_bill.text()))
        self._run(api.send_otp, self._on_send_done, mobile)

    def _on_send_done(self, _result, err):
        self._task_done()
        self._busy(False)
        if err is not None:
            self._set_err(self._fmt_err(i18n.t("login.code_err"), err))
            return
        self.mobile = self._pending_mobile
        self._bill_hint = self._pending_hint
        self._set_err("")
        self.lbl_code_for.setText(
            i18n.t("login.code_for", mobile=num(self.mobile)))
        self.in_code.clear()
        self.stack.setCurrentIndex(1)
        self.in_code.setFocus()

    @staticmethod
    def _fmt_err(prefix: str, err: Exception) -> str:
        if isinstance(err, VpnBlocked):
            return str(err)
        if isinstance(err, ApiError):
            return f"{prefix}: {err}"
        return f"{prefix}: {err}"

    # ---------- صفحه ۲: کد تایید ----------

    def _page_code(self) -> QWidget:
        w, lay = self._page()
        lay.addLayout(self._header(
            2, i18n.t("login.s2_title"), i18n.t("login.s2_sub")))

        self.lbl_code_for = QLabel(i18n.t("login.s2_sub"))
        lay.addWidget(self.lbl_code_for)
        self.in_code = QLineEdit()
        self.in_code.setPlaceholderText(i18n.t("login.code_ph"))
        digits_only(self.in_code, 6)
        self.in_code.setAlignment(_field_align())
        self.in_code.textChanged.connect(lambda: self._set_err(""))
        self.in_code.returnPressed.connect(lambda: self._guard(self._verify))
        lay.addWidget(self.in_code)

        lay.addStretch()
        row = QHBoxLayout()
        row.setSpacing(8)
        btn_back = JellyButton(i18n.t("login.fix_number"))
        btn_back.setMinimumHeight(46)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_ok = JellyButton(i18n.t("login.verify"))
        btn_ok.setObjectName("primary")
        btn_ok.setMinimumHeight(46)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(lambda: self._guard(self._verify))
        row.addWidget(btn_back)
        row.addWidget(btn_ok)
        lay.addLayout(row)
        self._busy_widgets.append(btn_ok)
        return w

    def _verify(self):
        if self._task is not None:
            return
        code = to_latin_digits(self.in_code.text())
        if not CODE_RE.fullmatch(code):
            self._set_err(i18n.t("login.bad_code"))
            return
        self._pending_code = code
        self._run(self._verify_and_fetch, self._on_verify_done, self._pending_code)

    def _verify_and_fetch(self, code: str):
        """در رشته‌ی پس‌زمینه: تایید کد + گرفتن لیست قبض‌ها"""
        token = api.verify_otp(self.mobile, code)
        bills = api.get_bills(token)
        return token, bills

    def _on_verify_done(self, result, err):
        self._task_done()
        self._busy(False)
        if err is not None:
            self._set_err(self._fmt_err(i18n.t("login.verify_err"), err))
            return
        self.token, self._bills = result

        # ---------- حسابِ بدون قبض → راهنما، نه بن‌بست ----------
        if not self._bills:
            self._set_err("")
            self.stack.setCurrentIndex(3)   # صفحه‌ی راهنمای ثبت قبض
            return
        self._set_err("")

        # اگر کاربر شناسه قبض داده و با یکی منطبق بود، خودکار انتخاب می‌شود
        if self._bill_hint:
            for b in self._bills:
                ident = re.sub(r"[\s\-]", "",
                               to_latin_digits(str(b.get("bill_identifier", ""))))
                if ident and (ident == self._bill_hint or self._bill_hint in ident):
                    self._finish(b)
                    return
            # شناسه پیدا نشد — کاربر خودش از لیست انتخاب می‌کند
            self._set_err(i18n.t("login.hint_miss"))

        self.list_bills.clear()
        for b in self._bills:
            title = b.get("bill_title") or i18n.t("bills.title")
            self.list_bills.addItem(
                f"{title} — {to_latin_digits(str(b.get('bill_identifier', '')))}")
        self.list_bills.setCurrentRow(0)
        self.stack.setCurrentIndex(2)
        self.list_bills.setFocus()

    # ---------- صفحه ۳: انتخاب قبض ----------

    def _page_bill(self) -> QWidget:
        w, lay = self._page()
        lay.addLayout(self._header(
            3, i18n.t("login.s3_title"), i18n.t("login.s3_sub")))

        self.list_bills = QListWidget()
        self.list_bills.itemDoubleClicked.connect(lambda _: self._confirm_bill())
        lay.addWidget(self.list_bills, 1)

        btn = JellyButton(i18n.t("login.confirm"))
        btn.setObjectName("primary")
        btn.setMinimumHeight(48)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._confirm_bill)
        lay.addWidget(btn)
        self._busy_widgets.append(btn)
        return w

    def _confirm_bill(self):
        row = self.list_bills.currentRow()
        if row < 0 or row >= len(self._bills):
            self._set_err(i18n.t("login.pick_one"))
            return
        self._finish(self._bills[row])

    # ---------- صفحه ۴: راهنمای «قبض به برق‌من وصل نیست» ----------

    def _page_guide(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(26, 14, 26, 14)
        lay.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(12)
        head.addWidget(IconChip("amber", "bill", 38))   # v4.7 — ۳۸px (بود ۴۶)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(i18n.t("guide.title"))
        t.setStyleSheet(
            f"font-family: \"{theme.display_family(800)}\"; font-size: 18.5px; font-weight: 800;")
        col.addWidget(t)
        sub = QLabel(i18n.t("guide.sub"))
        sub.setObjectName("muted")
        sub.setWordWrap(True)
        col.addWidget(sub)
        head.addLayout(col, 1)
        head.setAlignment(col, Qt.AlignmentFlag.AlignVCenter)  # v4.4.10 — تراز چیپ با متن
        lay.addLayout(head)

        for i in (1, 2, 3, 4):
            step_row = QHBoxLayout()
            step_row.setSpacing(10)
            chip = QLabel(num(i))
            chip.setObjectName("stepChip")
            chip.setProperty("state", "done")
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedSize(28, 28)
            step_row.addWidget(chip, 0, Qt.AlignmentFlag.AlignTop)
            txt = QLabel(i18n.t(f"guide.s{i}"))
            txt.setObjectName("body")
            txt.setWordWrap(True)
            step_row.addWidget(txt, 1)
            lay.addLayout(step_row)

        note = QLabel(i18n.t("login.empty_bills"))
        note.setObjectName("hint")
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addStretch()

        row = QHBoxLayout()
        row.setSpacing(8)
        btn_back = JellyButton(i18n.t("guide.back"))
        btn_back.setMinimumHeight(46)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_retry = JellyButton(i18n.t("guide.retry"))
        btn_retry.setObjectName("primary")
        btn_retry.setMinimumHeight(46)
        btn_retry.setCursor(Qt.PointingHandCursor)
        btn_retry.clicked.connect(lambda: self._guard(self._recheck_bills))
        row.addWidget(btn_back)
        row.addWidget(btn_retry)
        lay.addLayout(row)
        self._busy_widgets.append(btn_retry)
        return w

    def _recheck_bills(self):
        """کاربر گفته قبض را در برق‌من ثبت کرده — دوباره لیست را بگیر"""
        if self._task is not None or not self.token:
            return
        # باگ دوم همان تابع: callback موقعیتی پاس می‌شد و به‌جای token
        # داخل متد می‌نشست (متد هم بدون آرگومان صدا زده می‌شد)
        self._run(self._refetch_bills, self._on_refetch_done, self.token)

    @staticmethod
    def _refetch_bills(token):
        return api.get_bills(token)

    def _on_refetch_done(self, result, err):
        self._task_done()
        self._busy(False)
        if err is not None:
            self._set_err(self._fmt_err(i18n.t("login.net_err"), err))
            return
        self._bills = result or []
        if not self._bills:
            self._set_err(i18n.t("login.empty_bills"))
            return
        self._set_err("")
        self.list_bills.clear()
        for b in self._bills:
            title = b.get("bill_title") or i18n.t("bills.title")
            self.list_bills.addItem(
                f"{title} — {to_latin_digits(str(b.get('bill_identifier', '')))}")
        self.list_bills.setCurrentRow(0)
        self.stack.setCurrentIndex(2)
        self.list_bills.setFocus()

    # ---------- پایان ----------

    def _finish(self, bill: dict):
        self.bill_id = to_latin_digits(str(bill.get("bill_identifier", "")))
        self.bill_title = str(bill.get("bill_title", ""))
        st = storage.load()
        st["mobile"] = self.mobile
        st["warned"] = []
        st["known_keys"] = []
        storage.set_token(self.token)
        # v4: لیست قبض‌ها — پایه‌ی پایش چند-قبضی؛ قبض‌های بعدی از تنظیمات
        storage.set_bills([{"bill_id": self.bill_id, "bill_title": self.bill_title}],
                          self.bill_id)
        st.update(storage.load())
        storage.save()
        self.accept()

    # ---------- ابزار ----------

    def _set_err(self, text: str):
        self.err.setText(text)

    def _busy(self, on: bool):
        for w in self._busy_widgets:
            w.setEnabled(not on)
        if on:
            self.setCursor(Qt.WaitCursor)
        else:
            self.unsetCursor()
