# power.py — عملیات برق سیستم: خاموش کردن / اسلیپ / هیبرنیت
import ctypes
import subprocess

# پنجره‌ی فرصت برای لغو شات‌دان (از تری: «لغو خاموش کردن در جریان»)
SHUTDOWN_GRACE_SECONDS = 30


def shutdown(delay_seconds: int = SHUTDOWN_GRACE_SECONDS) -> bool:
    """خاموش کردن ویندوز با تاخیر (قابل لغو با cancel_shutdown)"""
    try:
        r = subprocess.run(
            ["shutdown", "/s", "/t", str(max(1, delay_seconds))],
            check=False, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # returncode بررسی شود وگرنه شکست دستور (مثلاً XP/عدم دسترسی) هم «موفق» گزارش می‌شد
        return r.returncode == 0
    except OSError:
        return False


def cancel_shutdown() -> bool:
    """لغو شات‌دان در جریان (shutdown /a)"""
    try:
        r = subprocess.run(
            ["shutdown", "/a"],
            check=False, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return r.returncode == 0
    except OSError:
        return False


def sleep_now() -> bool:
    """اسلیپ واقعی — فراخوانی مستقیم SetSuspendState با پارامتر بولی درست؛
    (برخلاف ترفند rundll32 که اگر هیبرنیت فعال باشد سیستم را هیبرنیت می‌کند)"""
    try:
        return bool(ctypes.windll.powrprof.SetSuspendState(False, False, False))
    except OSError:
        return False


def hibernate_now() -> bool:
    """هیبرنیت؛ اگر هیبرنیت در ویندوز غیرفعال باشد، سیستم اسلیپ می‌شود.
    برای فعال‌سازی: powercfg /h on"""
    try:
        if bool(ctypes.windll.powrprof.SetSuspendState(True, False, False)):
            return True
    except OSError:
        pass
    try:
        r = subprocess.run(
            ["shutdown", "/h"],
            check=False, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return r.returncode == 0
    except OSError:
        return False


def perform(action: str, shutdown_delay: int = SHUTDOWN_GRACE_SECONDS) -> bool:
    """action: shutdown | sleep | hibernate"""
    if action == "shutdown":
        return shutdown(shutdown_delay)
    if action == "sleep":
        return sleep_now()
    if action == "hibernate":
        return hibernate_now()
    return False
