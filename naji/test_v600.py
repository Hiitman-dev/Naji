# test_v600.py — تست دودِ نسخه‌ی ۶٫۰٫۰ (خارج از ویندوز هم اجرا می‌شود)
# --------------------------------------------------------------------
# پوشش: آیکون‌های دودوتون، قاب نمایش شمارش هیرو، تاریخچه‌ی قطعی‌ها،
# خطاهای نوع‌دار API، بنر وضعیت سرویس، سوییچر قبض‌ها، آنبوردینگ،
# ویجت شناور، صداها، آپدیتر و گزارشگر کرش — در هر دو زبان fa/en.
import os
import sys
import tempfile
import traceback

# محیط ایزوله + بدون انیمیشن
os.environ["NAJI_NO_ANIM"] = "1"
_TMP = tempfile.mkdtemp(prefix="naji_test_")
os.environ["APPDATA"] = _TMP

# استابِ winreg برای اجرای تست روی سیستم‌های غیرویندوزی (تزریق قبل از import)
if "winreg" not in sys.modules:
    try:
        import winreg  # noqa: F401
    except ImportError:
        import types
        _wr = types.ModuleType("winreg")
        _wr.HKEY_CURRENT_USER = 0x80000001
        _wr.KEY_SET_VALUE = 0x0002
        _wr.REG_SZ = 1
        _wr.OpenKey = lambda *a, **k: (_ for _ in ()).throw(OSError("test"))
        _wr.SetValueEx = lambda *a, **k: None
        _wr.DeleteValue = lambda *a, **k: None

        class _Ctx:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        _wr.OpenKey = lambda *a, **k: _Ctx()
        sys.modules["winreg"] = _wr

PASS, FAIL = 0, []


def check(name: str, cond: bool):
    global PASS
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL.append(name)
        print(f"  ✗ {name}")


def section(title: str):
    print(f"\n— {title} —")


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    import i18n
    i18n.set_lang("fa")

    # ---------- ۱) i18n — کلیدهای تازه در هر دو زبان ----------
    section("i18n")
    need_fa_en = [
        "svc.down_title", "svc.slow_title", "svc.net_title", "svc.retry",
        "hist.title", "hist.seg7", "hist.seg30", "hist.sum", "hist.empty",
        "overlay.title", "overlay.none", "tray.widget_show",
        "sound.title", "sound.scheme", "sound.scheme_system", "sound.test",
        "sound.mute", "upd.title", "upd.check_now", "upd.found", "upd.notes",
        "onboard.t1", "onboard.t2", "onboard.t3", "onboard.finish",
        "crash.title", "crash.copy", "conn.err_saapa", "conn.err_net",
        "conn.err_timeout", "look.widget", "look.widget_hint",
        "bills.switcher_eyebrow",
    ]
    for k in need_fa_en:
        pair = i18n._STRINGS.get(k)
        check(f"کلید {k}", bool(pair) and len(pair) == 2
              and bool(pair[0].strip()) and bool(pair[1].strip()))
    i18n.set_lang("en")
    check("ترجمه‌ی انگلیسی svc.down_title",
          i18n.t("svc.down_title") != "svc.down_title")
    i18n.set_lang("fa")

    # ---------- ۲) آیکون‌های دودوتون ----------
    section("icons v6 — duotone bold")
    import icons
    check("تعداد گلیف‌ها ≥ ۳۵", len(icons.ALL_ICONS) >= 35)
    for g in ("chart", "tabs", "pip", "download", "sound", "mute", "rocket",
              "copy", "folder", "close", "bolt", "bill", "timer", "gear"):
        check(f"گلیف {g} موجود و رندرشونده",
              icons.has_icon(g) and not icons.icon_pixmap(
                  g, 32, "#bfa4ff", "rgba(191,164,255,0.45)").isNull())
    # لایه‌ی SOFT واقعاً در SVG تزریق می‌شود (دودوتون)
    raw = bytes(icons.svg_bytes("bell", "#ffffff", "rgba(255,255,255,0.45)")).decode()
    check("تزریق fill-opacity برای لایه‌ی نرم", "fill-opacity" in raw)

    # ---------- ۳) storage — تنظیمات تازه + تاریخچه ----------
    section("storage v6")
    import storage
    st = storage.load()
    check("sound_scheme پیش‌فرض", st.get("sound_scheme") == "system")
    check("overlay_enabled پیش‌فرض", st.get("overlay_enabled") is False)
    check("update_check پیش‌فرض", st.get("update_check") is True)
    check("onboarded پیش‌فرض", st.get("onboarded") is False)
    # حالت نامعتبر → نرمال
    st["sound_scheme"] = "yallaaaa"
    st2 = storage._sanitize(dict(st))
    check("نرمال‌سازی sound_scheme نامعتبر", st2.get("sound_scheme") == "system")
    # تاریخچه
    rec = {"outage_date": "1404/06/12", "outage_start_time": "10:30",
           "outage_stop_time": "13:00", "_bill": "b1"}
    storage.record_bill_history("b1", [rec, dict(rec)])
    days = storage.history_days(7)
    today = [d for d in days if d["today"]][0]
    check("ثبت ۲ قطعی امروز", today["count"] == 2)
    check("مجموع دقیقه‌ها = ۳۰۰", today["minutes"] == 300)  # 2×(2.5h=150m)
    tot_c, tot_m = storage.history_total(7)
    check("جمع کل ۷ روزه", tot_c == 2 and tot_m == 300)
    # عبور از نیمه‌شب
    storage.record_bill_history("b2", [{"outage_start_time": "23:30",
                                        "outage_stop_time": "01:15"}])
    d2 = [d for d in storage.history_days(7) if d["today"]][0]
    check("عبور از نیمه‌شب (۱۰۵ دقیقه)", d2["minutes"] == 105 + 300)
    # prune رکورد کهنه
    from datetime import date, timedelta
    h = storage._hload()
    old = (date.today() - timedelta(days=200)).isoformat()
    h.setdefault("b1", {})[old] = {"count": 9, "minutes": 999}
    storage._prune_history(h)
    check("هرسِ رکورد ۲۰۰ روزه", old not in h.get("b1", {}))

    # ---------- ۴) API — خطاهای نوع‌دار ----------
    section("api v6 — error kinds")
    import api
    e1 = api.ApiError("x", kind="saapa")
    check("ApiError.kind", e1.kind == "saapa")
    check("AuthExpired.kind = auth", api.AuthExpired().kind == "auth")
    check("VpnBlocked.kind = vpn", api.VpnBlocked().kind == "vpn")

    # ---------- ۵) آپدیتر ----------
    section("updater")
    import updater
    check("۶٫۱۰٫۰ > ۶٫۹٫۳", updater.is_newer("6.10.0", "6.9.3"))
    check("v7.0.0 > 6.99.99", updater.is_newer("v7.0.0", "6.99.99"))
    check("همان نسخه تازه نیست", not updater.is_newer("6.0.0", "6.0.0"))
    check("نسخه‌ی خراب تازه نیست", not updater.is_newer("oops", "6.0.0"))
    check("parse_version", updater.parse_version("v6.2.1-beta") == (6, 2, 1))

    # ---------- ۶) صداها ----------
    section("sounds")
    import sounds
    import time as _t
    check("طرح‌های صدا", sounds.SCHEMES == ("system", "gentle", "urgent", "silent"))
    check("بی‌صدا در طرح silent", sounds.play("silent", {}) is None)
    check("is_muted با آینده", sounds.is_muted({"mute_until": _t.time() + 999}))
    check("is_muted با گذشته", not sounds.is_muted({"mute_until": 0}))

    # ---------- ۷) crash ----------
    section("crash reporter")
    import crash
    try:
        raise ValueError("boom-for-test")
    except ValueError as exc:
        rep = crash.build_report(exc, "6.0.0")
    check("گزارش شامل نوع خطا", "ValueError" in rep and "boom-for-test" in rep)
    check("گزارش شامل نسخه", "6.0.0" in rep)

    # ---------- ۸) ویجت‌های تازه ----------
    section("widgets v6")
    import theme
    theme.load_fonts()
    theme.set_current("dark")
    from widgets import (BillSwitcher, HistoryChart, HeroCard, ServiceBanner,
                         _CountdownDisplay)
    hero = HeroCard()
    check("قاب نمایش شمارش هیرو", isinstance(hero.display, _CountdownDisplay)
          and hero.display.minimumHeight() >= 60)
    check("شمارش داخل قاب نشسته", hero.countdown.parent() is hero.display)

    banner = ServiceBanner()
    banner.set_state("saapa", [True, False, True])
    check("بنر سرویس با kind=saapa", banner.isVisible() and
          "برق‌من" in banner.title.text())
    banner.set_state("net", None)
    check("بنر سرویس با kind=net", "اتصال" in banner.title.text())

    hist = HistoryChart()
    days = [{"label": str(i % 30 + 1), "count": i % 3, "minutes": i * 5,
             "today": i == 6} for i in range(7)]
    hist.set_data(days)
    check("نمودار ۷ روزه + خلاصه", "قطعی" in hist.summary.text())

    sw = BillSwitcher()
    sw.rebuild([{"bill_id": "1", "bill_title": "خانه"},
                {"bill_id": "2", "bill_title": "مغازه"}], "1")
    check("سوییچر چند-قبضی نمایان", sw.isVisible() and len(sw._buttons) == 2)
    sw.rebuild([{"bill_id": "1", "bill_title": "خانه"}], "1")
    check("تک‌قبض → سوییچر پنهان", not sw.isVisible())

    # ---------- ۹) پنجره‌ی اصلی + صفحات ----------
    section("main window")
    from main_window import MainWindow, VERSION
    check("نسخه ۶٫۱٫۰", VERSION == "6.1.0")
    s = dict(storage.DEFAULTS)
    s["onboarded"] = True
    win = MainWindow(s)
    check("داشبورد: بنر سرویس", hasattr(win, "svc_banner"))
    check("داشبورد: سوییچر قبض", hasattr(win, "bill_switch"))
    check("داشبورد: نمودار تاریخچه", hasattr(win, "hist_card"))
    check("تنظیمات: طرح صدا", hasattr(win, "combo_sound"))
    check("تنظیمات: ویجت شناور", hasattr(win, "switch_overlay"))
    check("تنظیمات: به‌روزرسانی", hasattr(win, "switch_update"))
    # جابه‌جایی صفحه با انیمیشن (QPropertyAnimation)
    # توجه: در محیط تست NAJI_NO_ANIM=1 است — انیمیشن را موقتاً فعال می‌کنیم
    import main_window as _mw
    _real_anim_flag = _mw.os_env_anim
    _mw.os_env_anim = lambda: True
    win.resize(980, 700)
    win.show()
    win._switch_page("settings")
    check("جابه‌جایی انیمیشنی صفحه", win._page_anim is not None
          and win._current_page == "settings")
    _mw.os_env_anim = _real_anim_flag
    app.processEvents()
    win._switch_page("dashboard")
    app.processEvents()
    check("بازگشت به داشبورد", win._current_page == "dashboard")

    # ---------- ۱۰) آنبوردینگ و ویجت شناور ----------
    section("onboarding + overlay")
    from onboarding import OnboardingDialog
    dlg = OnboardingDialog(s)
    check("آنبوردینگ ۳ گامی", dlg.stack.count() == 3)
    dlg._go_next()
    check("گام ۲ بعد از بعدی", dlg.stack.currentIndex() == 1)
    dlg._go_next()
    dlg._collect()
    check("جمع‌آوری تنظیمات ویزارد", "mode" in s and "default_action" in s)

    from overlay import MiniOverlay
    ov = MiniOverlay()
    ov.set_next({"outage_date": "1404/06/12", "outage_start_time": "23:59",
                 "outage_stop_time": "00:00"}, "خانه")
    check("ویجت شناور ساخته شد", ov is not None and ov._next_txt)
    ov.close()

    # ---------- ۱۱) رندر خروجی برای بازبینی چشمی ----------
    section("offscreen snapshots")
    try:
        win.update_snapshot({"occurred": [], "planned": [], "per_bill": {},
                             "multi_bills": False, "checked_at": "12:00"})
        win.grab().save(os.path.join(_TMP, "win_dark.png"))
        hist.grab().save(os.path.join(_TMP, "hist_dark.png"))
        hero.grab().save(os.path.join(_TMP, "hero_dark.png"))
        banner.grab().save(os.path.join(_TMP, "banner_dark.png"))
        sw2 = BillSwitcher()
        sw2.rebuild([{"bill_id": "1", "bill_title": "خانه"},
                     {"bill_id": "2", "bill_title": "مغازه"}], "2")
        sw2.resize(420, 52)
        sw2.grab().save(os.path.join(_TMP, "switcher_dark.png"))
        print(f"  ✓ اسنپ‌شات‌ها در {_TMP}")
    except Exception as e:
        print(f"  ! رندر اسنپ‌شات شکست: {e}")
        traceback.print_exc()

    # ---------- ۱۲) زبان انگلیسی — ساخت دوباره پنجره ----------
    section("english rebuild")
    i18n.set_lang("en")
    try:
        win2 = MainWindow(s)
        win2._switch_page("about")
        app.processEvents()
        check("پنجره در LTR انگلیسی", not win2.isRightToLeft())
        win2.close()
    except Exception as e:
        print(f"  ✗ پنجره‌ی انگلیسی: {e}")
        FAIL.append("english window")
    i18n.set_lang("fa")

    # ---------- جمع‌بندی ----------
    print(f"\n{'=' * 48}\nPASS: {PASS}   FAIL: {len(FAIL)}")
    if FAIL:
        for f in FAIL:
            print(f"  ✗ {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
