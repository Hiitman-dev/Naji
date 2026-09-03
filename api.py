# api.py — کلاینت سامانه برق‌من (uiapi.saapa.ir)
#
# نکته‌ی مهم: سرور برق‌من درخواست‌های IP خارج از ایران را بلاک می‌کند.
# اگر کاربر فیلترشکن/VPN (مثل Happ) روشن داشته باشد، ترافیک پیش‌فرض از IP خارجی
# خارج می‌شود و صفحه‌ی "Access Denied" برمی‌گردد.
#
# راه‌حل این ماژول: مسیریابی هوشمند — اول مسیر پیش‌فرض امتحان می‌شود
# (برای وقتی که VPN قانون bypass ایران دارد)، بعد bind شدن به تک‌تک
# کارت‌های شبکه‌ی محلی؛ اولین مسیری که پاسخ واقعی API بدهد برنده است.
# در صورت خرابی مسیر وسط کار، یک‌بار دوباره مسیر یابی می‌شود.

import socket

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from util import jalali_plus, jalali_today

BASE_URI = "https://uiapi.saapa.ir"
BLOCK_SIGNATURE = "blocked from your IP"  # امضای صفحه‌ی 403 بلاک برق‌من
TIMEOUT = 20

BLOCK_MSG = (
    "اتصال مستقیم به سرور برق‌من ممکن نشد!\n\n"
    "احتمالاً فیلترشکن/VPN شما روشن است و IP خروجی خارج از ایران دارد.\n"
    "راه‌حل یکی از این دو:\n"
    "  ۱) در فیلترشکن، قانون «عبور مستقیم (Direct)» برای دامنه‌های "
    "saapa.ir و bargheman.com اضافه کنید.\n"
    "  ۲) VPN را موقتاً خاموش کنید."
)

COMMON_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://ios.bargheman.com",
    "referer": "https://ios.bargheman.com/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
}


class ApiError(Exception):
    """خطای عمومی API (پیام فارسی داخل exception است)
    v6.0 — هر خطا «نوع» دارد تا رابط کاربری بداند مقصر کیست:
      net     → اتصال ما به سرور برقرار نشد (اینترنت/فیلترشکن)
      timeout → سرور آن‌قدر کند بود که زمان‌سنج پرید
      saapa   → سرور برق‌من خودش پاسخ نامعتبر/خطای ۵xx داد
      vpn     → همه‌ی مسیرها بلاک (صفحه‌ی 403 برق‌من)
      auth    → نشست منقضی"""

    def __init__(self, msg: str, kind: str = "net"):
        super().__init__(msg)
        self.kind = kind


class AuthExpired(ApiError):
    """توکن ورود منقضی شده؛ باید دوباره OTP گرفت"""

    def __init__(self, msg: str = "نشست شما منقضی شده است؛ دوباره وارد شوید."):
        super().__init__(msg, kind="auth")


class VpnBlocked(ApiError):
    """هیچ مسیر مستقیمی به برق‌من پیدا نشد (معمولاً VPN)"""

    def __init__(self, msg: str = None):
        super().__init__(msg or BLOCK_MSG, kind="vpn")


class _SourceAddressAdapter(HTTPAdapter):
    """اتصال با IP مبدأ مشخص (bind به کارت شبکه‌ی فیزیکی برای دور زدن TUN VPN)"""

    def __init__(self, source_address=None, **kwargs):
        self._source_address = source_address
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        if self._source_address:
            pool_kwargs["source_address"] = self._source_address
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs
        )


_session = requests.Session()
_session.trust_env = False  # هیچ‌وقت از پروکسی سیستمی/محیطی عبور نکن
_route_state = {"checked": False}


def local_ipv4_candidates() -> list:
    """تمام IPهای محلی کارت‌های شبکه (فیزیکی + TUN)"""
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip != "127.0.0.1" and ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return ips


def _mount(source_ip):
    addr = (source_ip, 0) if source_ip else None
    adapter = _SourceAddressAdapter(addr)
    _session.mount("https://", adapter)
    _session.mount("http://", adapter)


def active_source() -> tuple:
    """("default", None) یا ("nic", ip) — برای نمایش در UI.
    باگ v4.2: این تابع رشته برمی‌گرداند و main.py آن را دو متغیره unpack
    می‌کرد → ValueError در اسلاتِ _on_snapshot → چیپ وضعیت برای همیشه
    روی «در حال بررسی…» قفل می‌شد (حتی با داده‌ی سالم)."""
    src = _route_state.get("source")
    if src is None:
        return ("default", None)
    return ("nic", src)


def _probe(source_ip) -> bool:
    """آیا با این IP مبدأ، پاسخ واقعی API می‌گیریم (نه صفحه‌ی بلاک)؟"""
    _mount(source_ip)
    try:
        r = _session.get(f"{BASE_URI}/api/ebills/GetBills", headers=COMMON_HEADERS, timeout=8)
        # 401 یعنی API زنده است و فقط توکن نمی‌داریم — عالی
        ok = BLOCK_SIGNATURE not in r.text
        if ok:
            # فقط پس از موفقیت ثبت شود وگرنه active_source() کارتِ شکست‌خورده را نشان می‌داد
            _route_state["source"] = source_ip
        return ok
    except requests.RequestException:
        return False


def ensure_route(force: bool = False):
    """انتخاب مسیر سالم؛ در صورت بلاک بودن همه‌ی مسیرها VpnBlocked می‌دهد"""
    if _route_state["checked"] and not force:
        return
    candidates = [None] + local_ipv4_candidates()  # اول مسیر پیش‌فرض، بعد bind به هر کارت
    for c in candidates:
        if _probe(c):
            _route_state["checked"] = True
            return
    raise VpnBlocked(BLOCK_MSG)


def _request(method: str, path: str, token: str = None, payload=None, timeout: int = TIMEOUT):
    ensure_route()
    headers = dict(COMMON_HEADERS)
    if token:
        headers["authorization"] = f"Bearer {token}"

    r = None
    for attempt in (1, 2):
        try:
            r = _session.request(
                method, BASE_URI + path, headers=headers,
                json=payload if method != "GET" else None, timeout=timeout,
            )
        except requests.Timeout as e:
            if attempt == 1:
                ensure_route(force=True)  # شاید مسیر عوض شده (تغییر VPN/وای‌فای)
                continue
            # v6.0 — سرور کند/بی‌پاسخ: مقصر سمت برق‌من است، نه ناجی
            raise ApiError(
                "سرور برق‌من این‌قدر کند بود که پاسخ نرسید؛ کمی بعد دوباره امتحان کنید.",
                kind="timeout",
            ) from e
        except requests.RequestException as e:
            if attempt == 1:
                ensure_route(force=True)  # شاید مسیر عوض شده (تغییر VPN/وای‌فای)
                continue
            raise ApiError(
                "ارتباط با سرور برق‌من برقرار نشد؛ اتصال اینترنت را بررسی کنید.",
                kind="net",
            ) from e

        if BLOCK_SIGNATURE in r.text:
            if attempt == 1:
                ensure_route(force=True)
                continue
            raise VpnBlocked(BLOCK_MSG)
        if token and r.status_code in (401, 403):
            raise AuthExpired()
        if r.status_code >= 500:
            # v6.0 — خطای ۵xx = مشکل سرور برق‌من
            raise ApiError(
                f"سرور برق‌من موقتاً در دسترس نیست (کد {r.status_code}) — مشکل از سمت برق‌منه، نه ناجی.",
                kind="saapa",
            )
        return r

    raise ApiError("پاسخ نامشخص از سرور برق‌من", kind="saapa")


def _json(r):
    try:
        return r.json()
    except ValueError as e:
        raise ApiError("پاسخ نامعتبر از سرور برق‌من", kind="saapa") from e


def _extract(data_json, default):
    status = data_json.get("status")
    if status in (401, 403):
        raise AuthExpired(str(data_json.get("message") or "نشست شما منقضی شده است؛ دوباره وارد شوید."))
    if status is not None and status != 200:
        raise ApiError(
            str(data_json.get("message") or f"خطای سرویس برق‌من (کد {status})"),
            kind="saapa",
        )
    data = data_json.get("data")
    return default if data is None else data


# ---------- عملیات ----------

def send_otp(mobile: str):
    r = _request("POST", "/api/otp/sendCode", payload={"mobile": mobile})
    return _extract(_json(r), {})


def verify_otp(mobile: str, code: str) -> str:
    """توکن برق‌من را برمی‌گرداند"""
    r = _request(
        "POST", "/api/otp/verifyCode",
        payload={"mobile": mobile, "code": code, "request_source": 5, "device_token": ""},
    )
    data_json = _json(r)
    data = _extract(data_json, {})
    token = (data or {}).get("Token")
    if not token:
        raise ApiError(str(data_json.get("message") or "کد تایید نامعتبر است."))
    return token


def get_bills(token: str) -> list:
    r = _request("GET", "/api/ebills/GetBills", token=token)
    data = _extract(_json(r), {})
    # سرور بسته به نسخه، یا {"data": {"bill_data": [...]}} می‌دهد یا خودِ data لیست است؛
    # هر دو شکل پشتیبانی می‌شود وگرنه پاسخ لیستی با AttributeError کرش می‌کرد.
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("bill_data") or []
    return []


def get_blackouts(token: str, bill_id: str) -> dict:
    """خاموشی‌های رخ‌داده‌ی امروز + برنامه‌ریزی‌شده‌ی ۵ روز آینده"""
    r1 = _request(
        "POST", "/api/ebills/BlackoutsReport", token=token,
        payload={"bill_id": bill_id, "date": jalali_today()},
    )
    r2 = _request(
        "POST", "/api/ebills/PlannedBlackoutsReport", token=token,
        payload={"bill_id": bill_id, "from_date": jalali_today(), "to_date": jalali_plus(5)},
    )
    occurred = _extract(_json(r1), [])
    planned = _extract(_json(r2), [])
    if not isinstance(occurred, list):
        occurred = []
    if not isinstance(planned, list):
        planned = []
    return {"occurred": occurred, "planned": planned}
