# onboarding.py — آنبوردینگ چند مرحله‌ایِ کاربر تازه (v6.0)
# --------------------------------------------------------------------
# اولویت ۳ بریف: چرا شماره موبایل می‌خواهد، هشدار چطور کار می‌کند، و
# تنظیمِ اولیه‌ی خاموش/خواب — یک دیالوگ کوتاهِ سه‌مرحله‌ای اولِ اجرا.
# زبان بصری: هم‌خانواده‌ی Aura Glass (بوم + کارت شیشه‌ای + آیکون دودوتون).
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

import i18n
import theme
from widgets import (
    BackdropCanvas, GlassCard, GlassStepper, IconChip, JellyButton,
    Segmented, add_shadow,
)

MODES = [
    ("notify", "set.mode_notify"),
    ("notify_action", "set.mode_notify_action"),
    ("action", "set.mode_action"),
]

ACTION_KEYS = ("shutdown", "sleep", "hibernate")
ACTION_NAMES = {
    "shutdown": "set.act_shutdown",
    "sleep": "set.act_sleep",
    "hibernate": "set.act_hibernate",
}


def _rtl() -> bool:
    return i18n.is_rtl()


class OnboardingDialog(QDialog):
    """سه گامِ خوش‌آمد: ناجی چیست → چرا شماره موبایل → تنظیم هشدار"""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(i18n.t("onboard.title"))
        self.setLayoutDirection(Qt.RightToLeft if _rtl() else Qt.LeftToRight)
        self.setFixedSize(560, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        canvas = BackdropCanvas(self)
        canvas.setObjectName("central")
        root.addWidget(canvas)
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(26, 22, 26, 18)
        lay.setSpacing(12)

        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.stack.addWidget(self._page_welcome())
        self.stack.addWidget(self._page_phone())
        self.stack.addWidget(self._page_setup())

        # ---------- ردیف دکمه‌ها ----------
        foot = QHBoxLayout()
        foot.setSpacing(8)
        self.btn_skip = JellyButton(i18n.t("onboard.skip"))
        self.btn_skip.setObjectName("ghost")
        self.btn_skip.setCursor(Qt.PointingHandCursor)
        self.btn_skip.clicked.connect(self.accept)
        foot.addWidget(self.btn_skip)
        foot.addStretch()
        self.btn_back = JellyButton(i18n.t("onboard.back"))
        self.btn_back.setObjectName("ghost")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self._go_back)
        foot.addWidget(self.btn_back)
        self.btn_next = JellyButton(i18n.t("onboard.next"))
        self.btn_next.setObjectName("primary")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setMinimumWidth(150)
        self.btn_next.clicked.connect(self._go_next)
        foot.addWidget(self.btn_next)
        lay.addLayout(foot)

        self._page = 0
        self._sync_buttons()

    # ---------- گام ۱: ناجی چیست ----------

    def _page_welcome(self) -> QWidget:
        body, lay = self._shell()
        title = QLabel(i18n.t("onboard.t1"))
        title.setObjectName("h1")
        sub = QLabel(i18n.t("onboard.s1"))
        sub.setObjectName("body")
        sub.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(6)
        card, cl = self._card(lay)
        for kind, glyph, tk, sk in (
            ("amber", "bell", "onboard.f1t", "onboard.f1s"),
            ("teal", "power", "onboard.f2t", "onboard.f2s"),
            ("violet", "chart", "onboard.f3t", "onboard.f3s"),
        ):
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(IconChip(kind, glyph, 38))
            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(i18n.t(tk))
            t.setObjectName("muted")
            f = t.font()
            f.setWeight(f.Weight.DemiBold)
            t.setFont(f)
            s = QLabel(i18n.t(sk))
            s.setObjectName("hint")
            s.setWordWrap(True)
            col.addWidget(t)
            col.addWidget(s)
            row.addLayout(col, 1)
            cl.addLayout(row)
        body.setLayout(lay)
        return body

    # ---------- گام ۲: چرا شماره موبایل ----------

    def _page_phone(self) -> QWidget:
        body, lay = self._shell()
        title = QLabel(i18n.t("onboard.t2"))
        title.setObjectName("h1")
        lay.addWidget(title)
        card, cl = self._card(lay)
        chip_row = QHBoxLayout()
        chip_row.addWidget(IconChip("indigo", "shield", 40))
        t = QLabel(i18n.t("onboard.s2"))
        t.setObjectName("body")
        t.setWordWrap(True)
        chip_row.addWidget(t, 1)
        cl.addLayout(chip_row)
        card2, c2 = self._card(lay)
        h = QLabel(i18n.t("onboard.how"))
        h.setObjectName("h2")
        b = QLabel(i18n.t("onboard.s2b"))
        b.setObjectName("body")
        b.setWordWrap(True)
        c2.addWidget(h)
        c2.addWidget(b)
        lay.addStretch()
        return body

    # ---------- گام ۳: تنظیم هشدار ----------

    def _page_setup(self) -> QWidget:
        body, lay = self._shell()
        title = QLabel(i18n.t("onboard.t3"))
        title.setObjectName("h1")
        sub = QLabel(i18n.t("onboard.s3"))
        sub.setObjectName("body")
        sub.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(sub)

        card, cl = self._card(lay)
        s = self.settings

        lbl_m = QLabel(i18n.t("set.question"))
        lbl_m.setObjectName("fieldLabel")
        cl.addWidget(lbl_m)
        self.segment_mode = Segmented(
            [(v, i18n.t(k)) for v, k in MODES],
            s.get("mode", "notify_action"))
        self.segment_mode.changed.connect(self._on_mode)
        cl.addWidget(self.segment_mode)

        lbl_a = QLabel(i18n.t("set.default_action"))
        lbl_a.setObjectName("fieldLabel")
        cl.addWidget(lbl_a)
        self.combo_action = QComboBox()
        for key in ACTION_KEYS:
            self.combo_action.addItem(i18n.t(ACTION_NAMES[key]), key)
        saved = s.get("default_action", "shutdown")
        self.combo_action.setCurrentIndex(
            ACTION_KEYS.index(saved) if saved in ACTION_KEYS else 0)
        self.combo_action.currentIndexChanged.connect(self._on_action)
        cl.addWidget(self.combo_action)

        lbl_l = QLabel(i18n.t("set.lead"))
        lbl_l.setObjectName("fieldLabel")
        cl.addWidget(lbl_l)
        self.spin_lead = GlassStepper(minimum=1, maximum=120,
                                      value=int(s.get("lead_minutes", 10)))
        self.spin_lead.setSuffix(" " + i18n.t("dash.minutes"))
        self.spin_lead.valueChanged.connect(self._on_lead)
        cl.addWidget(self.spin_lead)

        note = QLabel(i18n.t("onboard.note"))
        note.setObjectName("hint")
        note.setWordWrap(True)
        cl.addWidget(note)
        lay.addStretch()
        return body

    # ---------- کمکی‌ها ----------

    def _shell(self) -> tuple:
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(8)
        return body, lay

    def _card(self, parent_lay) -> tuple:
        frame = GlassCard(radius=18)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(16, 13, 16, 13)
        fl.setSpacing(8)
        add_shadow(frame, blur=30, alpha=26, dy=9)
        parent_lay.addWidget(frame)
        return frame, fl

    def _sync_buttons(self):
        self.btn_back.setVisible(self._page > 0)
        self.btn_next.setText(
            i18n.t("onboard.finish") if self._page == 2 else i18n.t("onboard.next"))
        self.stack.setCurrentIndex(self._page)

    def _go_next(self):
        if self._page < 2:
            self._page += 1
            self._sync_buttons()
        else:
            self._collect()
            self.accept()

    def _go_back(self):
        if self._page > 0:
            self._page -= 1
            self._sync_buttons()

    def _on_mode(self, mode: str):
        self.settings["mode"] = mode

    def _on_action(self, idx: int):
        key = self.combo_action.itemData(idx)
        if key:
            self.settings["default_action"] = str(key)

    def _on_lead(self, v: int):
        self.settings["lead_minutes"] = int(v)

    def _collect(self):
        self.settings["mode"] = self.segment_mode.value()
        self.settings["default_action"] = str(self.combo_action.currentData())
        self.settings["lead_minutes"] = int(self.spin_lead.value())
