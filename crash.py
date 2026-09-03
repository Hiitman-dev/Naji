# crash.py — گزارش خطای اختیاری + لاگ محلیِ خوانا (v6.0)
# --------------------------------------------------------------------
# اولویت ۱ بریف: اگر اپ کرش کرد یا خطای غیرمنتظره داد، «با اجازه‌ی کاربر»
# (نه خودکار و بی‌اجازه) گزارشی کوتاه قابل ارسال باشد — یا حداقل لاگ محلی
# خوانا ساخته شود. اینجا هر دو انجام می‌شود:
#   ۱) ردپای کامل کرش همیشه در APPDATA/Naji/crash.log نوشته می‌شود (محلی)
#   ۲) دیالوگ دوستانه به کاربر اجازه‌ی «کپی گزارش» یا «بازکردن پوشه‌ی لاگ»
#      می‌دهد — ارسالِ خودکارِ هیچ‌چیزی در کار نیست.
import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

APP_DIR_NAME = "Naji"
_reporting = False   # قفل ضدِ کرشِ بازگشتی (خطا داخل خودِ گزارشگر)


def log_dir() -> str:
    base = os.environ.get("APPDATA") or str(Path.home())
    d = os.path.join(base, APP_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def log_path() -> str:
    return os.path.join(log_dir(), "crash.log")


def _write_log(exc: BaseException, where: str):
    try:
        p = log_path()
        # سقف ۵۱۲KB — فایل بزرگ؟ از نو شروع کن
        try:
            if os.path.getsize(p) > 524288:
                os.remove(p)
        except OSError:
            pass
        with open(p, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"زمان: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"نسخه: {where}\n")
            f.write(f"پایتون: {platform.python_version()} — "
                    f"{platform.system()} {platform.release()}\n")
            f.write("-" * 60 + "\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
            f.write("\n")
    except Exception:
        pass


def build_report(exc: BaseException, version: str) -> str:
    """گزارشِ کوتاهِ آماده‌ی کپی — بدون هیچ داده‌ی شخصی"""
    import io
    buf = io.StringIO()
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=buf)
    tb = buf.getvalue()[-1800:]
    return (
        f"Naji {version} — crash report\n"
        f"time: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"python: {platform.python_version()} | {platform.system()} "
        f"{platform.release()}\n"
        f"{'-' * 48}\n{tb}"
    )


def _show_dialog(exc: BaseException, version: str):
    """دیالوگ دوستانه — فقط با اجازه‌ی کاربر چیزی کپی/فرستاده می‌شود.
    هر خطایی اینجا بلعیده می‌شود؛ گزارشگر هرگز خودش کرش نمی‌کند."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        import i18n
        app = QApplication.instance()
        if app is None:
            return
        box = QMessageBox()
        box.setWindowTitle(i18n.t("app.name"))
        box.setIcon(QMessageBox.Icon.Critical)
        box.setText(i18n.t("crash.title"))
        box.setInformativeText(i18n.t("crash.body"))
        btn_copy = box.addButton(i18n.t("crash.copy"),
                                 QMessageBox.ButtonRole.ActionRole)
        btn_open = box.addButton(i18n.t("crash.open"),
                                 QMessageBox.ButtonRole.ActionRole)
        box.addButton(i18n.t("crash.close"), QMessageBox.ButtonRole.RejectRole)
        box.exec()

        if box.clickedButton() is btn_copy:
            try:
                app.clipboard().setText(build_report(exc, version))
            except Exception:
                pass
        elif box.clickedButton() is btn_open:
            try:
                if platform.system() == "Windows":
                    os.startfile(log_dir())  # noqa: S606
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", log_dir()])
            except Exception:
                pass
    except Exception:
        pass


def install(version: str):
    """نصب hook سراسری — در شروع برنامه صدا زده می‌شود.
    کرش‌ها: لاگ محلی همیشه + دیالوگِ اجازه‌دار (در حد امکان)."""

    def _hook(tp, val, tb):
        global _reporting
        if _reporting:
            # خودِ گزارشگر خطا خورد — دست نزنیم، خاموش بنویسیم
            try:
                _write_log(val, version + " (nested)")
            except Exception:
                pass
            return
        _reporting = True
        try:
            _write_log(val, version)
        finally:
            try:
                import util
                util.debug_note(f"crash: {tp.__name__}: {val}")
            except Exception:
                pass
            try:
                _show_dialog(val, version)
            except Exception:
                pass
            _reporting = False
        # رفتار پیش‌فرض: خروج با کد خطا — مثل قبل
        sys.__excepthook__(tp, val, tb)

    sys.excepthook = _hook
