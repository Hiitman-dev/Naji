# storage.py — ذخیره‌ی تنظیمات با رمزنگاری DPAPI ویندوز (توکن برق‌من + تنظیمات کاربر)
import base64
import ctypes
import json
import os
import re
import sys
import winreg
from ctypes import wintypes
from datetime import date, datetime, timedelta
from pathlib import Path

APP_NAME = "Naji"

DEFAULTS = {
    "mobile": "",
    "token_enc": "",          # توکن برق‌من — فقط به‌صورت رمز‌شده با DPAPI
    "bill_id": "",
    "bill_title": "",
    "bills": [],                   # همه‌ی قبض‌های تحت پایش [{bill_id, bill_title}]
    "active_bill": "",             # قبض فعال در داشبورد/پایش
    "mode": "notify_action",       # notify | notify_action | action
    "default_action": "shutdown",  # shutdown | sleep | hibernate
    "lead_minutes": 10,            # چند دقیقه قبل از قطعی هشدار بدهیم (تنظیم کاربر، ۱ تا ۱۲۰)
    "notify_seconds": 15,          # پنجره/توست هشدار چند ثانیه باز بماند؛ بدون واکنش، اقدام پیش‌فرض (تنظیم کاربر، ۵ تا ۱۲۰)
    "poll_minutes": 5,             # فاصله‌ی پایش برق‌من — تنظیم کاربر (۱ تا ۶۰)
    "autostart": True,
    "theme_mode": "dark",          # system | light | dark — v4.6: پیش‌فرض مشکیِ مات
    "lang": "fa",                  # fa | en
    "sync_windows": True,          # رنگ‌آمیزی با رنگ اکسنت ویندوز
    "theme": "dark",              # (سازگاری نسخه‌های قبل) آخرین تم دستی
    "matte_done": False,           # v4.6 — مهاجرت یک‌باره‌ی مشکیِ مات انجام شد؟
    "warned": [],                  # هشدارهای قبلاً داده‌شده (dedupe فقط در همین اجرا)
    "known_keys": [],              # خاموشی‌هایی که کاربر دیده است
    "last_warn": {},               # ردپای آخرین هشدار شلیک‌شده {at, summary}
    # ---------- v6.0 ----------
    "sound_scheme": "system",      # system | gentle | urgent | silent — طرح صدای هشدار
    "mute_until": 0,               # epoch ثانیه — بی‌صدایی موقت هشدارها
    "overlay_enabled": False,      # ویجت شناور شمارش معکوس روی دسکتاپ
    "overlay_pos": "",             # موقعیت ویجت شناور "x,y"
    "update_check": True,          # چک خودکار نسخه‌ی جدید از گیت‌هاب
    "onboarded": False,            # آنبوردینگ چند مرحله‌ای دیده شد؟
}

# ---------- DPAPI ----------


class _BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def dpapi_protect(data: bytes) -> str:
    """رمزنگاری با DPAPI ویندوز (بازشدنی فقط توسط همین کاربر ویندوز)"""
    buf = ctypes.create_string_buffer(data, len(data))
    pin = _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    pout = _BLOB()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(pin), "BarghGuard", None, None, None, 0, ctypes.byref(pout)
    )
    if not ok:
        raise OSError("CryptProtectData failed")
    try:
        return base64.b64encode(ctypes.string_at(pout.pbData, pout.cbData)).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(pout.pbData)


def dpapi_unprotect(b64: str) -> bytes:
    raw = base64.b64decode(b64)
    buf = ctypes.create_string_buffer(raw, len(raw))
    pin = _BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    pout = _BLOB()
    descr = wintypes.LPWSTR()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(pin), ctypes.byref(descr), None, None, None, 0, ctypes.byref(pout)
    )
    if not ok:
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(pout.pbData, pout.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(pout.pbData)


# ---------- تنظیمات ----------


def settings_path() -> str:
    base = os.environ.get("APPDATA") or str(Path.home())
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "settings.json")


_state = None


def _sanitize(state: dict) -> dict:
    """تنظیمات خوانده‌شده از دیسک را اعتبارسنجی و نرمال می‌کند.
    بدون این، مقدار خراب (مثلاً poll_minutes برابر null یا «abc») در اولین
    int() باعث کرش برنامه در شروع می‌شد."""
    def _int(key, default, lo, hi):
        try:
            v = int(state.get(key, default))
        except (TypeError, ValueError):
            v = default
        state[key] = max(lo, min(hi, v))

    _int("lead_minutes", 10, 1, 120)
    _int("notify_seconds", 15, 5, 120)
    _int("poll_minutes", 5, 1, 240)

    if state.get("mode") not in ("notify", "notify_action", "action"):
        state["mode"] = "notify_action"
    if state.get("default_action") not in ("shutdown", "sleep", "hibernate"):
        state["default_action"] = "shutdown"
    if state.get("theme") not in ("light", "dark"):
        state["theme"] = "dark"
    if state.get("theme_mode") not in ("system", "light", "dark"):
        state["theme_mode"] = "dark"
    if str(state.get("lang", "")).lower().startswith("en"):
        state["lang"] = "en"
    else:
        state["lang"] = "fa"
    state["autostart"] = bool(state.get("autostart", True))
    state["sync_windows"] = bool(state.get("sync_windows", True))
    # v6.0 — کلیدهای تازه
    if state.get("sound_scheme") not in ("system", "gentle", "urgent", "silent"):
        state["sound_scheme"] = "system"
    try:
        state["mute_until"] = max(0, int(float(state.get("mute_until", 0) or 0)))
    except (TypeError, ValueError):
        state["mute_until"] = 0
    state["overlay_enabled"] = bool(state.get("overlay_enabled", False))
    state["update_check"] = bool(state.get("update_check", True))
    state["onboarded"] = bool(state.get("onboarded", False))
    op = state.get("overlay_pos")
    state["overlay_pos"] = str(op) if isinstance(op, str) else ""
    for lst in ("warned", "known_keys"):
        if not isinstance(state.get(lst), list):
            state[lst] = []
    if not isinstance(state.get("last_warn"), dict):
        state["last_warn"] = {}
    for k in ("mobile", "token_enc", "bill_id", "bill_title", "active_bill"):
        if not isinstance(state.get(k), str):
            state[k] = ""

    # v4.6 — مهاجرت یک‌باره‌ی «مشکیِ مات»: برنامه برای همه‌ی کاربرانِ فعلی
    # یک‌بار روی تمِ تیره‌ی مات می‌نشیند (درخواست صریح کاربر)؛ انتخابِ بعدیِ
    # خودِ کاربر با نشانِ matte_done محترم شمرده می‌شود و دیگر دست نمی‌خورد
    if not state.get("matte_done"):
        state["theme"] = "dark"
        state["theme_mode"] = "dark"
        state["matte_done"] = True

    # لیست قبض‌ها — فقط جفت‌های رشته‌ای معتبر؛ خالی بودن → از قبض قدیمی ساخته می‌شود
    bills = state.get("bills")
    if not isinstance(bills, list):
        bills = []
    clean = []
    seen = set()
    for b in bills:
        if not isinstance(b, dict):
            continue
        bid = str(b.get("bill_id", "") or "").strip()
        bti = str(b.get("bill_title", "") or "").strip()
        if bid and bid not in seen:
            seen.add(bid)
            clean.append({"bill_id": bid, "bill_title": bti})
    if not clean and state.get("bill_id"):
        clean = [{"bill_id": state["bill_id"], "bill_title": state.get("bill_title", "")}]
    state["bills"] = clean
    if state.get("active_bill") not in seen:
        state["active_bill"] = clean[0]["bill_id"] if clean else ""
    # سازگاری: bill_id همیشه همان قبض فعال است تا منطق‌های قدیمی نشکنند
    if state["active_bill"]:
        state["bill_id"] = state["active_bill"]
        for b in clean:
            if b["bill_id"] == state["active_bill"]:
                state["bill_title"] = b["bill_title"]
                break
    return state


def load() -> dict:
    global _state
    if _state is None:
        data = {}
        try:
            with open(settings_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        # v5.1 — فایلِ «null» (نوشته‌ی ناقصِ دیسک/خروجِ ناگهانی) هرگز
        # نباید اپ را در استارتاپ با AttributeError بیندازد
        if not isinstance(data, dict):
            data = {}
        _state = _sanitize({**DEFAULTS, **{k: v for k, v in data.items() if k in DEFAULTS}})
    return _state


def _ensure():
    """v6.0 — دسترسی‌های عمومی هرگز روی _state=None نمی‌میرند؛
    هر getter خودش load() را تضمین می‌کند (تست‌ها/اسکریپت‌ها هم امن شوند)"""
    if _state is None:
        load()


def save():
    global _state
    # v5.1 — هرگز «null» روی دیسک ننویس: اگر load هنوز صدا نشده، اول لود
    if _state is None:
        load()
    tmp = settings_path() + ".tmp"
    try:
        # نوشتنِ اتمیک: اول کنارِ فایل، بعد جایگزینی — قطعِ برق وسطِ نوشتن
        # دیگر settings.json را خراب نمی‌کند
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, settings_path())
    except OSError:
        # فول‌بک: مسیر tmp (سقط حافظه‌ی موقت) نشد؟ مستقیم بنویس
        try:
            with open(settings_path(), "w", encoding="utf-8") as f:
                json.dump(_state, f, ensure_ascii=False, indent=2)
        except OSError:
            pass


def get_token() -> str:
    _ensure()
    enc = _state.get("token_enc")
    if not enc:
        return ""
    try:
        return dpapi_unprotect(enc).decode("utf-8")
    except Exception:
        return ""


def set_token(token: str):
    _ensure()
    _state["token_enc"] = dpapi_protect(token.encode("utf-8")) if token else ""


def reset_session():
    _ensure()
    """خروج از حساب — قبض‌ها هم پاک می‌شوند؛ زبان/ظاهر سرِ جایش می‌ماند"""
    _state["token_enc"] = ""
    _state["bill_id"] = ""
    _state["bill_title"] = ""
    _state["bills"] = []
    _state["active_bill"] = ""
    _state["warned"] = []
    _state["known_keys"] = []
    save()


def bills() -> list:
    _ensure()
    """لیست قبض‌های تحت پایش (کپی امن)"""
    return [dict(b) for b in (_state.get("bills") or [])]


def active_bill() -> dict:
    _ensure()
    """قبض فعال؛ اگر نبود قبض اول یا دیکشنری خالی"""
    bl = bills()
    if not bl:
        return {}
    act = _state.get("active_bill") or ""
    for b in bl:
        if b["bill_id"] == act:
            return b
    return bl[0]


def set_bills(items: list, active_id: str = None):
    _ensure()
    """جایگزینی لیست قبض‌ها و انتخاب قبض فعال"""
    clean = []
    seen = set()
    for b in items or []:
        bid = str((b or {}).get("bill_id", "") or "").strip()
        bti = str((b or {}).get("bill_title", "") or "").strip()
        if bid and bid not in seen:
            seen.add(bid)
            clean.append({"bill_id": bid, "bill_title": bti})
    _state["bills"] = clean
    act = active_id if active_id in seen else (clean[0]["bill_id"] if clean else "")
    _state["active_bill"] = act
    _state["bill_id"] = act
    for b in clean:
        if b["bill_id"] == act:
            _state["bill_title"] = b["bill_title"]
            break
    save()


def is_warned(key: str) -> bool:
    _ensure()
    return key in (_state.get("warned") or [])


def add_warned(key: str):
    _ensure()
    warned = _state.setdefault("warned", [])
    if key not in warned:
        warned.append(key)
        del warned[:-200]  # سقف ۲۰۰ آیتم
    save()


def clear_warned():
    _ensure()
    """پاک‌کردن هشدارهای مصرف‌شده — باگ «اعلان نیومد»:
    قبلاً کلیدهای warn: روی دیسک می‌ماندند و اگر خاموشیِ پیش‌رو حتی
    یک‌بار (در اجرای قبلی یا با پیش‌آگاهی قبلی) هشدار خورده بود،
    تغییرِ «چند دقیقه قبل» دیگر هرگز هشدار تازه شلیک نمی‌کرد.
    حالا dedupe فقط در همین اجرا معتبر است؛ تکرارِ هشدار همیشه
    بهتر از سکوتِ بی‌صدا است."""
    _state["warned"] = []
    save()


def last_warn() -> dict:
    _ensure()
    """ردپای آخرین هشدار شلیک‌شده — برای نمایش در کارت تنظیمات"""
    lw = _state.get("last_warn")
    return lw if isinstance(lw, dict) else {}


def set_last_warn(info: dict):
    _ensure()
    """ثبت ردپای هشدار: حتی اگر توست ویندوز دیده نشود، کاربر در
    تنظیمات می‌بیند که هشدار واقعاً شلیک شده (تفکیک «شلیک نشد»
    از «ویندوز نشان نداد»)"""
    _state["last_warn"] = {
        "at": str(info.get("at", "")),
        "summary": str(info.get("summary", "")),
    }
    save()


# ---------- اجرای خودکار با ویندوز ----------

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_VALUE = APP_NAME


def autostart_command() -> str:
    if getattr(sys, "frozen", False):  # اجرا از exe ساخته‌شده با PyInstaller
        return f'"{sys.executable}"'
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(pythonw):
            exe = pythonw
    return f'"{exe}" "{os.path.abspath(sys.argv[0])}"'


def set_autostart(enabled: bool):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, _RUN_VALUE, 0, winreg.REG_SZ, autostart_command())
            else:
                try:
                    winreg.DeleteValue(k, _RUN_VALUE)
                except FileNotFoundError:
                    pass
        return None
    except Exception as e:  # noqa: BLE001 — هر خطای رجیستری نباید برنامه را بخواباند
        return str(e)


# ---------- تاریخچه‌ی قطعی‌ها (v6.0) ----------
# داده‌هایی که همین حالا از API برق‌من می‌آیند (رخ‌داده‌های امروز) در فایل
# history.json جمع می‌شوند تا نمودار آمار هفتگی/ماهانه از آن‌ها ساخته شود.
# ساختار: {"<bill_id>": {"<YYYY-MM-DD>": {"count": n, "minutes": m}}}
# سقف نگهداری ۱۲۰ روز — فایل جدا از settings.json تا تنظیمات سبک بماند.

HISTORY_MAX_DAYS = 120


def history_path() -> str:
    base = os.environ.get("APPDATA") or str(Path.home())
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "history.json")


_history = None


def _hload() -> dict:
    global _history
    if _history is None:
        try:
            with open(history_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        _history = data if isinstance(data, dict) else {}
    return _history


def _hsave():
    try:
        tmp = history_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_history or {}, f, ensure_ascii=False)
        os.replace(tmp, history_path())
    except OSError:
        pass


def _prune_history(h: dict):
    """حذف رکوردهای قدیمی‌تر از سقف ۱۲۰ روز"""
    cutoff = (datetime.now() - timedelta(days=HISTORY_MAX_DAYS)).date()
    for bid in list(h.keys()):
        days = h.get(bid)
        if not isinstance(days, dict):
            del h[bid]
            continue
        for day in list(days.keys()):
            try:
                if date.fromisoformat(str(day)) < cutoff:
                    del days[day]
            except ValueError:
                del days[day]
        if not days:
            del h[bid]


def record_bill_history(bill_id: str, occurred: list):
    """ثبت رخ‌داده‌های امروزِ یک قبض — در هر چرخه‌ی پایش صدا زده می‌شود.
    چون لیست «رخ‌داده‌ی امروز» برق‌من مرجعِ کامل است، رکوردِ امروزِ همان
    قبض بازنویسی می‌شود (بدون رشدِ تکراری) و مدت هر قطعی از فاصله‌ی
    شروع/پایان درمی‌آید (عبور از نیمه‌شب هم هندل می‌شود)."""
    if not bill_id:
        return
    h = _hload()
    today = date.today().isoformat()
    items = [o for o in (occurred or []) if isinstance(o, dict)]
    minutes = 0.0
    for o in items:
        st = _parse_hhmm(o.get("outage_start_time"))
        en = _parse_hhmm(o.get("outage_stop_time"))
        if st is not None and en is not None:
            dur = (en - st) % (24 * 60)   # عبور از نیمه‌شب
            minutes += max(0, dur)
        elif st is not None and en is None:
            minutes += 0                  # بدون پایان مشخص — فقط شمارش
    day_rec = {"count": len(items), "minutes": int(round(minutes))}
    bill_rec = h.setdefault(str(bill_id), {})
    prev = bill_rec.get(today) or {}
    # ادغام: بیشینه‌ی شمارش و دقیقه — چرخه‌های هم‌روز نباید کمتر نویسند
    bill_rec[today] = {
        "count": max(int(day_rec["count"]), int(prev.get("count", 0) or 0)),
        "minutes": max(int(day_rec["minutes"]), int(prev.get("minutes", 0) or 0)),
    }
    _prune_history(h)
    _hsave()


def _parse_hhmm(raw):
    """'10:30' یا '۱۰:۳۰:۰۰' → دقیقه‌ی شبانه‌روز | None — بدون وابستگی به util"""
    try:
        s = str(raw or "").strip().translate(
            str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
        m = re.match(r"^(\d{1,2}):(\d{1,2})", s)
        if not m:
            return None
        hh, mm = int(m.group(1)), int(m.group(2))
        if hh > 23 or mm > 59:
            return None
        return hh * 60 + mm
    except Exception:
        return None


def history_days(n: int = 30) -> list:
    """آمار n روز اخیر (قدیمی → جدید) جمعِ همه‌ی قبض‌ها:
    [{date, label_day, count, minutes}] — label_day = شماره‌ی روز ماه"""
    h = _hload()
    agg = {}
    for bid, days in h.items():
        if not isinstance(days, dict):
            continue
        for day, rec in days.items():
            if not isinstance(rec, dict):
                continue
            a = agg.setdefault(day, {"count": 0, "minutes": 0})
            a["count"] += int(rec.get("count", 0) or 0)
            a["minutes"] += int(rec.get("minutes", 0) or 0)
    out = []
    today = date.today()
    for i in range(int(n) - 1, -1, -1):
        d = today - timedelta(days=i)
        key = d.isoformat()
        rec = agg.get(key, {})
        out.append({
            "date": key,
            "label_day": str(d.day),
            "count": int(rec.get("count", 0)),
            "minutes": int(rec.get("minutes", 0)),
            "today": i == 0,
        })
    return out


def history_total(n: int = 30) -> tuple:
    """(تعداد کل قطعی‌ها، مجموع دقیقه‌های قطع) در n روز اخیر"""
    days = history_days(n)
    return (sum(d["count"] for d in days), sum(d["minutes"] for d in days))


def clear_history():
    global _history
    _history = {}
    _hsave()
