# i18n.py — دوزبانه‌سازی «ناجی» (فارسی / انگلیسی)
# ----------------------------------------------------
# همه‌ی متن‌های برنامه از اینجا می‌آیند؛ هیچ رشته‌ی نمایشی‌ای
# مستقیم در کد نوشته نمی‌شود. لحن متن‌ها دوستانه و خودمانی است.
# v4.4.4 — خلوص زبان (درخواست کاربر): در فارسی فقط فارسی، در انگلیسی فقط
# انگلیسی. میکرولیبل‌های ابرو (ابرو) دیگر در حالت فارسی لاتین نیستند؛
# خط‌های لایسنس/فونت‌های صفحه‌ی «درباره» هم تک‌زبانه شدند تا متن راست‌به‌چپ
# با توکن‌های لاتین قاطی نشود و تراز به‌هم نریزد. (نشانی سایت‌ها مثل
# bargheman.com جزء داده‌اند و در متن‌های راهنما سرِ جای خود می‌مانند.)
#   t("key")            متن زبان فعلی
#   num("15:00")        رقم‌سازی مطابق زبان (فارسی → ارقام فارسی)
#   is_rtl()            چیدمان راست‌به‌چپ؟

_LANG = "fa"

# (فارسی، انگلیسی) — کلیدها گروه‌بندی‌شده بر اساس بخش برنامه
_STRINGS = {
    # ---------- هسته ----------
    "app.name": ("ناجی", "Naji"),
    "app.tagline": ("نگهبان خاموشی برق", "Power-outage guardian"),
    "app.window_title": ("ناجی — پایش خاموشی برق", "Naji — Power-outage monitor"),
    "app.eyebrow": ("ناجی · نگهبان برق", "NAJI · POWER GUARD"),
    "app.version": ("نسخه", "Version"),

    # ---------- درباره — ویژگی‌ها ----------
    "about.feats_eyebrow": ("ویژگی‌های ناجی", "HIGHLIGHTS"),
    "about.feats_title": ("ناجی چه‌کار می‌کند؟", "What Naji does for you"),
    "about.f1t": ("همه‌ی قبض‌ها، یک‌جا", "Every bill, one list"),
    "about.f1s": ("خونه، مغازه، شرکت — همه زیر یک پایش", "Home, shop, office — all in one watch"),
    "about.f2t": ("هشدار سر وقت", "Right-on-time alerts"),
    "about.f2s": ("قبل از هر قطعی سر وقت خبرت می‌کنه", "Heads-up before every single cut"),
    "about.f3t": ("فارسی و انگلیسی", "Persian & English"),
    "about.f3s": ("با چیدمان راست‌چین و چپ‌چینِ خودکار", "With automatic RTL and LTR layout"),
    # v4.4.8 — about.f4t/f4s («هم‌رنگ ویندوز») از UI و i18n حذف شد (به درخواست کاربر)

    # ---------- نوار کناری ----------
    "nav.dashboard": ("خانه", "Home"),
    "nav.settings": ("تنظیمات", "Settings"),
    "nav.help": ("راهنما", "Help"),
    "nav.about": ("درباره", "About"),

    # ---------- وضعیت اتصال ----------
    "conn.preparing": ("در حال آماده‌سازی…", "Getting ready…"),
    "conn.checking": ("در حال بررسی…", "Checking…"),
    "conn.connected": ("وصلیم ({src})", "Connected ({src})"),
    "conn.default_route": ("مسیر پیش‌فرض", "default route"),
    "conn.nic_route": ("آی‌پی {nic}", "IP {nic}"),
    "conn.error": ("خطا در بررسی: {msg}", "Check failed: {msg}"),
    "conn.check_timeout": ("بررسی طول کشید — اینترنت رو چک کن و دوباره تلاش کن", "The check took too long — check your connection and retry"),
    "conn.blocked": ("به برق‌من نمی‌رسیم (احتمالاً فیلترشکن)", "Can't reach Bargheman (VPN?)"),
    "conn.expired": ("ورود منقضی شده — دوباره وارد شو", "Session expired — sign in again"),
    "conn.logged_out": ("خارج از حساب", "Signed out"),
    "conn.last_check": ("آخرین بررسی: {t}", "Last check: {t}"),
    # v6.0 — پیام‌های کوتاه چیپ وضعیت برای خطاهای نوع‌دار
    "conn.err_saapa": ("سرور برق‌من جواب نمی‌ده — مشکل از اون‌جاست، نه ناجی", "Bargheman's server isn't responding — their side, not Naji"),
    "conn.err_timeout": ("برق‌من کند جواب داد — بعداً خودکار دوباره چک می‌کنیم", "Bargheman responded slowly — we'll retry automatically"),
    "conn.err_net": ("به برق‌من وصل نشدیم — اینترنت رو چک کن", "Couldn't reach Bargheman — check your connection"),

    # ---------- تری ----------
    "tray.show": ("نمایش پنجره", "Show window"),
    "tray.check_now": ("بررسی همین حالا", "Check now"),
    "tray.cancel_shutdown": ("لغو خاموش‌شدن در جریان", "Cancel pending shutdown"),
    "tray.logout": ("ورود / خروج از حساب", "Sign in / out"),
    "tray.quit": ("خروج از ناجی", "Quit Naji"),
    "tray.cancel_ok_title": ("لغو شد", "Cancelled"),
    "tray.cancel_ok_body": ("دستور خاموش‌کردن لغو شد. خیالت راحت!", "Shutdown command cancelled. All good!"),
    "tray.cancel_none": ("شات‌دانی در جریان نبود", "No shutdown was pending"),
    "tray.new_outage": ("خاموشی جدید ثبت شد", "New outage added"),
    "tray.more": ("و {n} مورد دیگر…", "and {n} more…"),
    "tray.warn_title": ("برق می‌رود!", "Power's going off!"),
    "tray.warn_body": ("حدود {mins} دیگر برق قطع می‌شود.\n{summary}", "Power cuts in about {mins}.\n{summary}"),
    # v4.4.6 — خاموشی‌ای که تازه شروع شده و پیش‌آگاهش دیده نشده
    "tray.late_title": ("قطعی شروع شد!", "The outage has started!"),
    "tray.late_body": ("خاموشی این قبض همین الان شروع شده:\n{summary}", "The outage for this bill has just started:\n{summary}"),
    "tray.action_done_title": ("خودم انجامش دادم", "Done automatically"),
    "tray.action_done_body": ("برق تا {mins} دیگر قطع می‌شود؛ «{action}» اجرا شد.", "Power cuts in {mins}; ran \"{action}\"."),
    "tray.action_fail_title": ("این یکی دستِ من نبود!", "Couldn't do it"),
    "tray.action_fail_body": ("اجرای «{action}» نشد؛ برق تا {mins} دیگر قطع می‌شود — خودت اقدام کن.", "Couldn't run \"{action}\"; power cuts in {mins} — act manually."),
    "tray.expired_title": ("ورود منقضی شد", "Session expired"),
    "tray.expired_body": ("برای اینکه از خاموشی‌ها باخبر بمونی، دوباره وارد برق‌من شو.", "Sign in to Bargheman again to keep updates flowing."),
    "tray.blocked_title": ("به برق‌من وصل نشدیم", "Couldn't reach Bargheman"),
    "tray.logged_out_conn": ("خارج از حساب", "Signed out"),

    # ---------- هدر ----------
    # نکته‌ی دوجهته: عنوان قبض (داده‌ی فارسی کاربر) با جداکننده‌ی ایزوله (LRI…PDI)
    # محصور می‌شود تا در متن انگلیسی، ترتیب کلمات به‌هم نریزد
    "hdr.bill_line": ("پایش خاموشی  •  {title} ({id})  •  {mobile}",
                      "Monitoring  •  \u2066{title}\u2069 ({id})  •  {mobile}"),
    "hdr.bills_line": ("پایش {n} قبض  •  فعال: {title}",
                       "Watching {n} bills  •  active: \u2066{title}\u2069"),

    # ---------- داشبورد ----------
    "dash.next_outage": ("قطعی بعدی", "Next outage"),
    "dash.no_outage_sub": ("بر اساس آخرین داده‌ها، خاموشی نزدیکی سر راهت نیست", "Nothing scheduled nearby based on latest data"),
    "dash.ongoing": ("در حال قطع…", "Cutting now…"),
    "dash.days_hours": ("{d} روز و {h} ساعت", "{d}d {h}h"),
    "dash.stat_planned": ("قطعی پیش‌رو", "Upcoming"),
    "dash.stat_occurred": ("رخ‌داده‌ی امروز", "Happened today"),
    "dash.stat_lead": ("هشدار پیش از قطع", "Heads-up"),
    "dash.stat_poll": ("فاصله‌ی پایش", "Check every"),
    "dash.count_unit": ("مورد", "items"),
    "dash.minutes": ("دقیقه", "min"),
    "dash.seconds": ("ثانیه", "sec"),
    "dash.outages_title": ("خاموشی‌های ثبت‌شده", "Recorded outages"),
    "dash.outages_eyebrow": ("دفتر خاموشی‌ها", "OUTAGE LOG"),
    "dash.check_now": ("به‌روزرسانی فوری", "Refresh now"),
    "dash.logout": ("خروج از حساب", "Sign out"),
    "dash.logout_confirm": ("با خروج، توکن و قبض‌ها پاک می‌شن و خبردار شدن از خاموشی می‌ایسته.\nمطمئنی؟", "Signing out wipes the token and bill list, and outage alerts stop.\nSure?"),
    "dash.logout_yes": ("آره، خارج شو", "Yes, sign out"),
    "dash.cancel": ("انصراف", "Cancel"),
    "dash.unknown_addr": ("بدون آدرس ثبت‌شده", "No address on file"),
    "dash.no_addr": ("بدون آدرس", "No address"),
    "dash.bill_chip": ("برای {bill}", "for {bill}"),
    "dash.footer_up": ("{p} مورد در راهه", "{p} upcoming"),
    "dash.footer_today": ("{o} مورد امروز", "{o} today"),
    "dash.footer_none": ("فعلاً چیزی روی رادار نیست", "Nothing on the radar right now"),
    "hdr.bills_n": ("پایش {n} قبض", "watching {n} bills"),
    # v5.0 — تولتیپِ چیپ موقعیت سربرگ
    "hdr.location": ("موقعیت", "Location"),

    # ---------- کارت خاموشی ----------
    "day.today": ("امروز", "Today"),
    "day.tomorrow": ("فردا", "Tomorrow"),
    "day.after": ("پس‌فردا", "In 2 days"),
    "day.in_n": ("{n} روز دیگر", "In {n} days"),
    "day.past": ("گذشته", "Past"),
    "day.no_date": ("بدون تاریخ", "No date"),
    "time.range": ("{s} تا {e}", "{s} – {e}"),

    # ---------- حالت خالی ----------
    "empty.title": ("برای ۵ روز پیش‌رو، هیچ خاموشی‌ای ثبت نشده", "No outages scheduled for the next 5 days"),
    "empty.sub": ("خیالت راحت؛ به‌محض ثبت خاموشی در برق‌من، همین‌جا خبرت می‌کنیم", "Relax — the moment Bargheman schedules one, we'll flag it here"),

    # ---------- تنظیمات ----------
    "set.title": ("تنظیمات", "Settings"),
    "set.eyebrow": ("ترجیحات", "PREFERENCES"),
    "set.question": ("وقتی برق می‌خواد بره، چیکار کنیم؟", "When power's about to go, what should happen?"),
    "set.mode_notify": ("فقط خبر بده", "Just notify"),
    "set.mode_notify_action": ("خبر بده + اقدام", "Notify + act"),
    "set.mode_action": ("مستقیم اقدام کن", "Act directly"),
    "set.mode_desc_notify": ("فقط یه اعلان ویندوز می‌بینی؛ هیچ اتفاقی برای سیستم نمی‌افته.", "You just get a Windows notification; nothing happens to the system."),
    "set.mode_desc_notify_action": ("یه پنجره‌ی هشدار با زمان‌سنجِ واکنش باز می‌شه؛ اگه تا آخرِ زمان‌سنج انتخاب نکنی، اقدام پیش‌فرض خودکار اجرا می‌شه.", "An alert window with a reaction timer pops up; if you don't pick before the timer ends, the default action runs by itself."),
    "set.mode_desc_action": ("هیچ پنجره‌ای نمیاد؛ سر وقتِ هشدار، اقدام پیش‌فرض بی‌درنگ اجرا می‌شه.", "No window pops up; at alert time the default action runs right away."),
    "set.lead": ("چند دقیقه قبل از قطعی خبر بدهیم؟", "Heads-up how many minutes before the cut?"),
    "set.lead_tip": ("هر ۲۰ ثانیه زمان خاموشی‌ها با ساعت سیستم سنجیده می‌شه؛ سرِ وقتِ همین عدد، اعلان می‌رسه.", "Outage times are checked against the clock every 20 seconds; the alert lands exactly this many minutes ahead."),
    # v4.4.4 — تایمر اعلان دستِ کاربر: پایانِ این ثانیه‌ها بدون واکنش = اجرای اقدام پیش‌فرض
    "set.notify_secs": ("اعلان چند ثانیه رو صفحه بمونه؟", "Keep the alert on screen for how long?"),
    "set.notify_secs_tip": ("پنجره‌ی هشدار همین‌قدر فرصتِ تصمیم‌گیری می‌ده؛ اگر تا پایان این ثانیه‌ها هیچ دکمه‌ای نزنی، «اقدام پیش‌فرض» خودکار اجرا می‌شه. در حالت «فقط خبر بده» هم اعلان ویندوز همین‌قدر روی صفحه می‌مونه.", "The alert window gives you this many seconds to decide; if no button is pressed in time, the default action runs by itself. In \"Just notify\" mode, the Windows toast also stays up for this long."),
    "set.poll": ("فاصله‌ی پایش برق‌من", "Bargh-man check interval"),
    "set.poll_tip": ("هر چند دقیقه یک‌بار لیست خاموشی‌ها از برق‌من تازه می‌شه — هر چی کمتر، خاموشی‌های جدیدتر زودتر پیدا می‌شن. زمان‌سنجِ هشدار مستقل از این عدد هر ۲۰ ثانیه کار می‌کنه.", "How often the outage list refreshes from Bargh-man — lower means brand-new outages are found sooner. The alert timer runs on its own every 20 seconds."),
    "set.default_action": ("اقدام پیش‌فرض", "Default action"),
    "set.act_shutdown": ("خاموش کردن سیستم", "Shut down"),
    "set.act_sleep": ("حالت خواب", "Sleep"),
    "set.act_hibernate": ("خواب زمستانی", "Hibernate"),
    "set.act_hint_shutdown": ("ویندوز کامل خاموش می‌شه؛ برنامه‌های باز بسته می‌شن.", "Windows shuts down fully; open apps close."),
    "set.act_hint_sleep": ("یه چرت سبک! با تکان دادن ماوس فوراً برمی‌گرده.", "A light nap! Move the mouse and it's instantly back."),
    "set.act_hint_hibernate": ("حافظه روی دیسک ذخیره می‌شه؛ روشن‌شدن بعدی از همون‌جا ادامه پیدا می‌کنه.", "Memory is saved to disk; next boot resumes exactly where you left off."),
    "set.autostart": ("با ویندوز بالا بیا", "Start with Windows"),
    "set.autostart_hint": ("هیچ خاموشی‌ای از قلم نمی‌افته؛ لازم نیست ناجی رو هر بار خودت باز کنی", "So no outage slips by, you never need to open Naji manually"),
    "set.autostart_fail": ("اجرای خودکار ثبت نشد:\n{err}", "Couldn't register autostart:\n{err}"),
    "set.ok": ("باشه", "OK"),
    "set.save": ("ثبت تنظیمات هشدار", "Save alert settings"),
    "set.saved": ("ثبت شد", "Saved"),
    "set.saved_confirm": ("ثبت شد — هشدار قطعی فعاله", "Saved — the outage alert is armed"),
    "set.armed_hint": ("یادآور فعاله: حدود {lead} دقیقه قبل از شروع هر خاموشی خبرت می‌کنیم؛ پنجره‌ی هشدار {secs} ثانیه روی صفحه می‌مونه", "Armed: you'll get a heads-up about {lead} minutes before each cut starts; the alert window stays up for {secs} seconds"),
    "set.last_warn": ("آخرین هشدار: ساعت {t} برای خاموشی {summary}", "Last alert fired at {t} for outage {summary}"),
    "set.last_warn_none": ("هنوز هشداری شلیک نشده؛ با نزدیک شدن اولین خاموشی، ردپایش همین‌جا می‌شینه", "No alert fired yet; once one does, its trace shows up here"),

    # ---------- ظاهر و زبان ----------
    "look.title": ("ظاهر و زبان", "Look & language"),
    "look.eyebrow": ("سلیقه‌ی شما", "LOOK & FEEL"),
    "look.theme": ("تم برنامه", "App theme"),
    "look.theme_system": ("هماهنگ با ویندوز", "Match Windows"),
    "look.theme_light": ("روشن", "Light"),
    "look.theme_dark": ("تیره", "Dark"),
    "look.sync_accent": ("هم‌رنگ شدن با رنگ ویندوز", "Follow the Windows accent"),
    "look.sync_accent_hint": ("رنگ اصلی برنامه از تنظیمات شخصی‌سازی ویندوز خونده می‌شه", "The app's accent color follows your Windows personalization"),
    "look.language": ("زبان برنامه", "App language"),
    "look.lang_fa": ("فارسی", "فارسی"),
    "look.lang_en": ("English", "English"),
    "look.restart_note": ("با عوض کردن زبان، صفحه‌ها تازه‌سازی می‌شن", "Pages refresh when you switch the language"),

    # ---------- قبض‌ها ----------
    "bills.title": ("قبض‌های تحت پایش", "Bills being watched"),
    "bills.eyebrow": ("قبض‌های من", "MY BILLS"),
    "bills.hint": ("می‌تونی چند قبض (خونه، مغازه، شرکت…) رو هم‌زمان دنبال کنی؛ خاموشی همه‌شون توی یک لیست میاد", "Watch several bills (home, shop, office…) at once; all outages land in one list"),
    "bills.active": ("فعال", "Active"),
    "bills.set_active": ("فعال کن", "Set active"),
    "bills.remove": ("حذف", "Remove"),
    "bills.add": ("افزودن قبض", "Add bill"),
    "bills.remove_confirm": ("«{title}» از پایش حذف بشه؟", "Remove \"{title}\" from monitoring?"),
    "bills.remove_yes": ("آره، حذفش کن", "Yes, remove it"),
    "bills.last_one": ("حداقل یه قبض باید بمونه! اگه می‌خوای کلاً خارج بشی، از «خروج از حساب» استفاده کن", "At least one bill must stay! To leave entirely, use Sign out"),
    "bills.added": ("«{title}» اضافه شد به لیست پایش", "\"{title}\" joined the watchlist"),
    "bills.switched": ("پایش روی «{title}» رفت", "Now watching \"{title}\""),
    "bills.picker_title": ("انتخاب قبض جدید", "Pick a bill"),
    "bills.picker_sub": ("قبضی که توی حسابت هست ولی هنوز دنبالش نمی‌کنیم", "A bill in your account that we're not watching yet"),
    "bills.picker_empty": ("همه‌ی قبض‌های حسابت همین الآن زیر پایشن. آفرین!", "You're already watching every bill in your account. Nice!"),
    "bills.picker_add": ("اضافه‌ش کن", "Add it"),
    "bills.hero_badge": ("برای {bill}", "for {bill}"),

    # ---------- راهنما ----------
    "help.title": ("راهنما", "Help"),
    "help.eyebrow": ("خوب بدانید", "GOOD TO KNOW"),
    "help.sub": ("سوال‌هایی که بیشتر از همه پرسیده می‌شن", "The questions we hear the most"),
    "help.q1": ("شناسه قبضم توی برق‌من ثبت نیست؛ حالا چه کنم؟", "My bill ID isn't registered in Bargheman — now what?"),
    "help.a1": ("ناجی فقط خاموشی‌های حسابتِ برق‌من رو می‌بینه؛ پس اول قبض رو اونجا ثبت کن:\n"
                "۱) اپ «برق‌من» یا سایت bargheman.com رو باز کن\n"
                "۲) با همون شماره موبایلی که اینجا زدی وارد شو\n"
                "۳) توی بخش «قبض‌ها» شناسه قبض برقت رو اضافه کن (روی قبض برق یا پنل توزیع هست)\n"
                "۴) بیا توی ناجی و «به‌روزرسانی فوری» رو بزن — همین!",
                "Naji only sees bills registered in Bargheman, so add the bill there first:\n"
                "1) Open the Bargheman app or bargheman.com\n"
                "2) Sign in with the same mobile number you used here\n"
                "3) In \"Bills\", add your bill ID (it's on the paper bill or the utility portal)\n"
                "4) Back in Naji, hit \"Refresh now\" — done!"),
    "help.q2": ("می‌خوام خاموشی دو تا قبض رو هم‌زمان ببینم", "I want to watch two bills at once"),
    "help.a2": ("بخش تنظیمات ← «قبض‌های تحت پایش» ← «افزودن قبض». از اون به بعد خاموشی همه‌ی قبض‌ها توی یک لیست میان و برای هر کدوم هم برچسب می‌ذاریم که بدونی مال کدومه.",
                "Settings → \"Bills being watched\" → \"Add bill\". From then on, outages for all bills arrive in one list, each tagged so you know whose is whose."),
    "help.q3": ("وصل نمی‌شه و می‌گه فیلترشکن روشنه", "It says it can't connect — probably my VPN"),
    "help.a3": ("سرور برق‌من درخواست‌های IP خارج از ایران رو نمی‌پذیره. یکی از این دوتا:\n"
                "• توی فیلترشکن برای saapa.ir و bargheman.com قانون «Direct» بذار\n"
                "• یا موقتاً فیلترشکن رو خاموش کن",
                "Bargheman's server rejects non-Iranian IPs. Do one of these:\n"
                "• Add a \"Direct\" rule for saapa.ir and bargheman.com in your VPN\n"
                "• Or turn the VPN off for a moment"),
    "help.q4": ("هشدار قطعی رو نمی‌بینم", "I never see the outage alert"),
    "help.a4": ("چک کن حالت هشدار روی «خبر بده + اقدام» یا «فقط خبر بده» باشه. بعد از تغییر، دکمه‌ی «ثبت تنظیمات هشدار» رو بزن تا «ثبت شد» ببینی. ناجی هر ۲۰ ثانیه زمان خاموشی‌ها رو با ساعت سیستم می‌سنجه و همون‌طور که در تنظیمات گفتی چند دقیقه قبل از شروع هر خاموشی خبر می‌ده. پنجره‌ی هشدار هم فقط به اندازه‌ای که در تنظیمات گفتی (پیش‌فرض ۱۵ ثانیه) باز می‌مونه؛ اگه تا آخرش واکنش ندی، اقدام پیش‌فرض اجرا می‌شه. پایین همون بخش هشدار هم ردپای آخرین هشدار شلیک‌شده رو می‌بینی — یعنی اگه ویندوز توست رو نشون نداده باشه، این‌جا معلومه که هشدار واقعاً رفته.",
                "Make sure the alert mode is \"Notify + act\" or \"Just notify\". After changing it, hit \"Save alert settings\" until you see \"Saved\". Naji measures outage times against the clock every 20 seconds and alerts you as many minutes ahead as you configured. The alert window only stays open for the seconds you set (default 15); if you don't react in time, the default action runs. The same alert section also shows the trace of the last fired alert — so even if Windows swallows the toast, you'll know the alert went out."),
    "help.q5": ("بستن پنجره، ناجی رو نمی‌بنده؟", "Closing the window doesn't quit Naji?"),
    "help.a5": ("نه عمداً! ناجی می‌ره توی تری (کنار ساعت) تا خاموشی‌ها رو دنبال کنه؛ خروج کامل هم از منوی همون تری انجام می‌شه.",
                "On purpose! Naji hides to the tray (near the clock) to keep watching. Quit fully from the tray menu."),
    "help.q6": ("دوبار کلیک روی آیکون، دو تا برنامه باز می‌کنه؟", "Does double-launching open two copies?"),
    "help.a6": ("نه دیگه! اگه ناجی باز باشه، کلیک دوباره فقط همون پنجره‌ی قبلی رو جلوی چشت میاره.",
                "Nope! If Naji is already running, launching again just brings the existing window to the front."),

    # ---------- درباره ----------
    "about.title": ("درباره ناجی", "About Naji"),
    "about.eyebrow": ("قصه‌ی ناجی", "THE STORY"),
    "about.wordmark": ("درباره ما", "ABOUT US"),
    "about.story": ("ناجی یه ابزار کوچیک و خودمونیه که مواظبِ خاموشی‌های برقت باشه؛ "
                    "از برق‌من می‌خونه، سرِ وقت خبرت می‌کنه و اگه خودت نبودی، همون‌طور که گفتی سیستم رو می‌ذاره خواب.",
                    "Naji is a small, home-grown tool that keeps an eye on your power cuts: "
                    "it reads Bargheman, nudges you in time, and if you're away it tucks the system in exactly as you told it to."),
    "about.disclaimer": ("ناجی یه برنامه‌ی غیررسمیه و به شرکت توزیع برق ربطی نداره؛ همه‌ی داده‌ها از سرویس برق‌من میاد.",
                         "Naji is an unofficial tool, unaffiliated with the utility company; all data comes from the Bargheman service."),
    # v4.4.6 — خط‌های «طراحی/فونت‌ها/منبع داده» (بخش لایسنس) کلاً از برنامه حذف
    # شد؛ اطلاعات لایسنس فقط در انتهای README گیت‌هاب می‌ماند (درخواست کاربر)
    "about.made": ("با عشق، برای برق ایران", "Made with love for Iran's power grid"),

    # ---------- ورود ----------
    "login.title": ("ورود به برق‌من", "Sign in to Bargheman"),
    "login.eyebrow": ("نشست امن", "SECURE SESSION"),
    "login.sub": ("وارد شو تا ناجی خاموشی‌هات رو ببینه", "Sign in so Naji can see your outages"),
    "login.step": ("گام {n} از {total}", "Step {n} of {total}"),
    "login.s1_title": ("شماره‌ی موبایلت", "Your mobile number"),
    "login.s1_sub": ("همون شماره‌ای که توی برق‌من زدی؛ کد تأیید همون‌جا پیامک می‌شه",
                     "The same one you use in Bargheman; the code is texted to it"),
    "login.mobile": ("شماره موبایل", "Mobile number"),
    "login.mobile_ph": ("مثلاً: ۰۹۱۲۳۴۵۶۷۸۹", "e.g. 09123456789"),
    "login.bill_hint": ("شناسه قبض (اختیاری)", "Bill ID (optional)"),
    "login.bill_hint_ph": ("اگه بدی، همون قبض خودکار انتخاب می‌شه", "If you know it, that bill gets picked for you"),
    "login.send_code": ("کد رو بفرست", "Send the code"),
    "login.bad_mobile": ("شماره موبایل باید ۱۱ رقم باشه و با ۰۹ شروع بشه.", "The number must be 11 digits and start with 09."),
    "login.wait_hint": ("هنوز داریم به برق‌من وصل می‌شیم؛ چند لحظه صبر کن…",
                        "Still connecting to Bargheman; hang on a moment…"),
    "login.internal_err": ("خطای داخلی ناجی", "Naji internal error"),
    "login.code_err": ("مشکل در ارسال کد", "Couldn't send the code"),
    "login.s2_title": ("کد تأیید", "The code"),
    "login.s2_sub": ("کد ۶ رقمی پیامک‌شده رو وارد کن", "Type the 6-digit code we texted"),
    "login.code_for": ("کد ۶ رقمی که به {mobile} پیامک شد رو وارد کن:", "Enter the 6-digit code texted to {mobile}:"),
    "login.code_ph": ("مثلاً: ۱۲۳۴۵۶", "e.g. 123456"),
    "login.fix_number": ("شماره رو تصحیح کن", "Fix the number"),
    "login.verify": ("تأیید و انتخاب قبض", "Verify & pick a bill"),
    "login.bad_code": ("کد تأیید باید ۶ رقم باشه.", "The code must be 6 digits."),
    "login.verify_err": ("تأیید نشد؛ کد رو دوباره چک کن", "Verification failed — check the code"),
    "login.s3_title": ("انتخاب قبض", "Pick a bill"),
    "login.s3_sub": ("کدوم قبض رو دنبال کنیم؟ (بعداً می‌تونی از تنظیمات اضافه‌اش کنی)", "Which bill should we watch? (you can add more in Settings)"),
    "login.pick_one": ("یه قبض از لیست انتخاب کن.", "Pick a bill from the list."),
    "login.confirm": ("همینه!", "That's the one!"),
    "login.empty_bills": ("وارد شدی، ولی حسابت هنوز هیچ قبضی نداره. راهنمای پایین رو ببین.",
                          "You're in, but your account has no bills yet. See the guide below."),
    "login.hint_miss": ("شناسه‌ای که زدی توی حسابت پیدا نشد؛ خودت از لیست انتخابش کن.",
                        "The ID you typed isn't in your account; pick it from the list yourself."),
    "login.net_err": ("ارتباط با سرور برق‌من برقرار نشد؛ اتصال اینترنت رو چک کن.", "Couldn't reach Bargheman; check your connection."),
    "login.bad_response": ("پاسخ نامعتبر از سرور برق‌من", "Invalid response from Bargheman"),
    "login.unknown_resp": ("پاسخ نامشخص از سرور برق‌من", "Unclear response from Bargheman"),
    "login.expired_msg": ("نشست شما منقضی شده؛ دوباره وارد شوید.", "Your session expired; sign in again."),

    # ---------- راهنمای ثبت قبض ----------
    "guide.title": ("قبض به برق‌من وصل نیست؟", "Bill not linked to Bargheman?"),
    "guide.sub": ("چهار قدم ساده تا فعال شدن پایش:", "Four easy steps to get monitoring:"),
    "guide.s1": ("اپ «برق‌من» یا سایت bargheman.com رو باز کن", "Open the Bargheman app or bargheman.com"),
    "guide.s2": ("با همون شماره موبایل اینجا وارد شو", "Sign in with the same mobile number as here"),
    "guide.s3": ("از بخش «قبض‌ها» شناسه قبض برقت رو اضافه کن — روی قبض یا پنل توزیع هست",
                 "Under \"Bills\", add your bill ID — it's on the paper bill or utility portal"),
    "guide.s4": ("برگرد توی ناجی و «به‌روزرسانی فوری» رو بزن", "Come back to Naji and hit \"Refresh now\""),
    "guide.retry": ("بررسی دوباره", "Check again"),
    "guide.back": ("برگرد به شماره", "Back to number"),

    # ---------- هشدار قطع برق ----------
    "warn.title": ("هشدار قطع برق", "Power-cut alert"),
    "warn.banner": ("برق داره می‌ره!", "Power's about to go!"),
    "warn.banner_sub": ("برای اینکه چیزی از دستت نره، یکی رو انتخاب کن", "Pick one so nothing gets lost"),
    "warn.until_cut": ("تا لحظه‌ی قطع", "until the cut"),
    "warn.until_auto": ("تا اجرای خودکار", "until auto-run"),
    "warn.no_time": ("زمان قطعی نامشخصه", "Cut time is unknown"),
    "warn.past": ("گذشته", "Past"),
    "warn.past_hint": ("زمان این خاموشی گذشته", "This outage's time has passed"),
    "warn.default": ("اقدام پیش‌فرض: {a}", "Default action: {a}"),
    "warn.note": ("اگه تا {s} ثانیه انتخابی نکنی، خودم سیستم رو روی «{a}» می‌ذارم.",
                  "If you don't choose within {s} seconds, I'll put the system on \"{a}\" myself."),
    "warn.do_shutdown": ("خاموشش کن", "Shut down"),
    "warn.do_sleep": ("بذار بخوابه", "Let it sleep"),
    "warn.do_hibernate": ("خواب زمستانی", "Hibernate"),
    "warn.ignore": ("بی‌خیال", "Ignore"),

    # ---------- تک‌صداها ----------
    "single.msg": ("ناجی همین‌حالا بازه؛ پنجره‌ش رو برات آوردم جلو.", "Naji is already running; I brought its window forward."),
    "misc.ellipsis": ("…", "…"),
    "misc.dash": ("—", "—"),

    # ================================================================
    # ---------- v6.0 — وضعیت سرویس برق‌من ----------
    "svc.down_title": ("سرور برق‌من در دسترس نیست", "Bargheman's server is down"),
    "svc.down_body": ("داده‌ی خاموشی‌ها از سرویس برق‌من میاد و فعلاً سرورش جواب نمی‌ده. مشکل از ناجی نیست — تا سرور پایدار شد، داده‌ها خودکار تازه می‌شن.", "Outage data comes from Bargheman and its server isn't responding right now. It's not Naji's fault — data refreshes automatically once the server recovers."),
    "svc.slow_title": ("برق‌من خیلی کُند جواب می‌ده", "Bargheman is responding very slowly"),
    "svc.slow_body": ("سرور برق‌من دیر جواب می‌ده و بررسی این بار ناتمام موند. مشکل از سمت برق‌منه، نه ناجی — چند لحظه بعد دوباره امتحان کن.", "Bargheman's server is slow and this check didn't finish. The issue is on Bargheman's side, not Naji — try again in a moment."),
    "svc.net_title": ("اتصال به برق‌من برقرار نشد", "Couldn't reach Bargheman"),
    "svc.net_body": ("اینترنت یا مسیر اتصال به برق‌من در دسترس نیست. اگه فیلترشکن داری، برای saapa.ir و bargheman.com قانون Direct بذار.", "Your internet or the route to Bargheman is unreachable. If you use a VPN, add a Direct rule for saapa.ir and bargheman.com."),
    "svc.retry": ("تلاش دوباره", "Retry"),
    "svc.dismiss": ("بستن", "Dismiss"),

    # ---------- v6.0 — تاریخچه‌ی قطعی‌ها ----------
    "hist.title": ("تاریخچه‌ی قطعی‌ها", "Outage history"),
    "hist.eyebrow": ("دفترچه‌ی آمار", "HISTORY"),
    "hist.seg7": ("۷ روز اخیر", "Last 7 days"),
    "hist.seg30": ("۳۰ روز اخیر", "Last 30 days"),
    "hist.span7": ("هفته‌ی اخیر", "this week"),
    "hist.span30": ("ماه اخیر", "this month"),
    "hist.sum": ("{span}: {c} قطعی • {m} دقیقه بدون برق", "{span}: {c} cuts • {m} minutes without power"),
    "hist.empty": ("هنوز داده‌ای ثبت نشده؛ با ادامه‌ی کار ناجی، آمار این‌جا جمع می‌شه", "No data recorded yet; keep Naji running and stats will build up here"),

    # ---------- v6.0 — سوییچر قبض‌ها ----------
    "bills.switcher_eyebrow": ("پایش چندقبضی", "MULTI-BILL"),

    # ---------- v6.0 — ویجت شناور ----------
    "overlay.title": ("قطعی بعدی", "Next outage"),
    "overlay.none": ("قطعی نزدیکی نیست", "Nothing nearby"),
    "overlay.sub_none": ("همه‌چیز وصل است", "All good"),
    "tray.widget_show": ("نمایش ویجت شناور", "Show floating widget"),
    "tray.widget_hide": ("بستن ویجت شناور", "Hide floating widget"),
    "look.widget": ("ویجت شناور روی دسکتاپ", "Floating desktop widget"),
    "look.widget_hint": ("شمارش معکوس همیشه جلوی چشت — بدون باز کردن پنجره‌ی اصلی", "Keep the countdown in sight without opening the main window"),

    # ---------- v6.0 — صدا و هشدار ----------
    "sound.title": ("صدا و هشدار", "Sound & alerts"),
    "sound.eyebrow": ("حس شنیداری", "SOUND"),
    "sound.scheme": ("طرح صدای هشدار", "Alert sound scheme"),
    "sound.scheme_system": ("سیستم (همون صدای ویندوز)", "System (Windows default)"),
    "sound.scheme_gentle": ("آرام — دو بوق ملایم", "Gentle — two soft beeps"),
    "sound.scheme_urgent": ("فوری — بوق‌های پیاپی", "Urgent — rapid beeps"),
    "sound.scheme_silent": ("بی‌صدا", "Silent"),
    "sound.test": ("آزمایش صدا", "Test sound"),
    "sound.mute": ("بی‌صدایی موقت (۱ ساعت)", "Temporary mute (1 hour)"),
    "sound.mute_hint": ("هشدارها تا یک ساعت بی‌صدا می‌شن؛ بعدش خودکار برمی‌گردن", "Alerts stay silent for an hour, then come back automatically"),
    "sound.muted_until": ("تا ساعت {t} بی‌صداست", "Muted until {t}"),

    # ---------- v6.0 — به‌روزرسانی ----------
    "upd.title": ("به‌روزرسانی ناجی", "Updates"),
    "upd.eyebrow": ("همیشه تازه", "UPDATES"),
    "upd.check_switch": ("خودکار چک کن نسخه‌ی جدید اومده؟", "Check for new versions automatically"),
    "upd.check_now": ("بررسی الآن", "Check now"),
    "upd.current": ("نسخه‌ی فعلی: {v}", "Current version: {v}"),
    "upd.latest": ("آخرین نسخه رو داری ({v})", "You're on the latest version ({v})"),
    "upd.found": ("نسخه‌ی {v} اومده!", "Version {v} is out!"),
    "upd.fail": ("بررسی نشد — اینترنت یا فیلترشکن رو چک کن", "Couldn't check — verify your internet/VPN"),
    "upd.notes": ("تغییرات این نسخه", "What's new in this version"),
    "upd.download": ("دانلود از گیت‌هاب", "Download from GitHub"),
    "upd.dialog_title": ("نسخه‌ی جدید ناجی", "New version of Naji"),
    "upd.checking": ("در حال بررسی…", "Checking…"),
    "upd.notes_empty": ("فهرست تغییرات برای این نسخه ثبت نشده.", "No changelog was published for this release."),

    # ---------- v6.0 — آنبوردینگ ----------
    "onboard.title": ("به ناجی خوش اومدی", "Welcome to Naji"),
    "onboard.t1": ("خوش اومدی به ناجی!", "Welcome to Naji!"),
    "onboard.s1": ("ناجی خاموشی‌های برقِ محلت رو از برق‌من می‌خونه، قبل از هر قطعی سر وقت خبرت می‌کنه و اگه خودت نباشی، همون‌طور که تنظیم می‌کنی سیستم رو می‌ذاره خواب یا خاموش می‌کنه.", "Naji reads power outages for your area from Bargheman, gives you a right-on-time heads-up before every cut, and — if you're away — puts the system to sleep or shuts it down just the way you set it."),
    "onboard.f1t": ("هشدار سر وقت", "Right-on-time alerts"),
    "onboard.f1s": ("چند دقیقه قبل از هر قطعی، با اعلان و صدا خبرت می‌کنه", "Notifies you with a toast and sound minutes before every cut"),
    "onboard.f2t": ("اقدام خودکار", "Automatic action"),
    "onboard.f2s": ("خاموش، خواب یا خواب زمستانی — سر وقت، بدون تو", "Shut down, sleep, or hibernate — on time, without you"),
    "onboard.f3t": ("آمار و تاریخچه", "Stats & history"),
    "onboard.f3s": ("قطعی‌های اخیر رو نموداری ببین و الگوشون رو بشناس", "See recent outages as a chart and learn their pattern"),
    "onboard.t2": ("چرا شماره موبایل می‌خواد؟", "Why does it need my mobile number?"),
    "onboard.s2": ("ناجی داده‌هاش رو از سرویس رسمی «برق‌من» می‌خونه و اون‌جا حساب‌ها با شماره موبایل شناخته می‌شن. شماره‌ات فقط برای ورود به همون برق‌من استفاده می‌شه؛ نه جایی دیگه می‌ره، نه سرور ابری جدا داریم.", "Naji reads data from the official Bargheman service, and accounts there are identified by mobile number. Your number is only used to sign in to Bargheman itself; it never goes anywhere else and we run no extra cloud."),
    "onboard.how": ("هشدار چطور کار می‌کنه؟", "How does the alert work?"),
    "onboard.s2b": ("ناجی هر ۲۰ ثانیه زمان خاموشی‌ها رو با ساعتِ سیستمت می‌سنجه و همون‌قدر که تنظیم کنی زودتر خبر می‌ده — حتی اگه پنجره‌ی برنامه بسته باشه و ناجی توی تری باشه.", "Naji measures outage times against your system clock every 20 seconds and alerts you as early as you configure — even when the window is closed and Naji lives in the tray."),
    "onboard.t3": ("یه تنظیم کوچیک", "One last little setup"),
    "onboard.s3": ("برای شروع: وقتی برق می‌خواد بره، ناجی چیکار کنه؟", "To start: when the power is about to go, what should Naji do?"),
    "onboard.note": ("همه‌ی این‌ها بعداً توی «تنظیمات» هم قابل تغییره.", "You can change all of this later in Settings."),
    "onboard.next": ("بعدی", "Next"),
    "onboard.back": ("قبلی", "Back"),
    "onboard.finish": ("بریم بابت!", "Let's go!"),
    "onboard.skip": ("ردش کن", "Skip"),

    # ---------- v6.0 — گزارش کرش ----------
    "crash.title": ("ناجی یه خطای غیرمنتظره دید", "Naji hit an unexpected error"),
    "crash.body": ("گزارش خطا توی کامپیوتر خودت ذخیره شد (پوشه‌ی Naji). اگه دوست داری کمک کنی بهتر بشیم، دکمه‌ی «کپی گزارش» رو بزن و برای ما بفرست — چیزی به‌صورت خودکار جایی ارسال نمی‌شه.", "The report was saved locally in your Naji folder. If you'd like to help us improve, copy the report and send it to us — nothing is ever sent automatically."),
    "crash.copy": ("کپی گزارش خطا", "Copy crash report"),
    "crash.open": ("باز کردن پوشه‌ی گزارش", "Open report folder"),
    "crash.close": ("بستن", "Close"),
}


def set_lang(lang: str):
    """تنظیم زبان فعال — 'fa' | 'en'"""
    global _LANG
    _LANG = "en" if str(lang).lower().startswith("en") else "fa"


def lang() -> str:
    return _LANG


def is_rtl() -> bool:
    return _LANG == "fa"


def t(key: str, **kw) -> str:
    """ترجمه‌ی کلید با قالب‌بندی اختیاری {placeholder}"""
    pair = _STRINGS.get(key)
    if pair is None:
        return key
    txt = pair[1] if _LANG == "en" else pair[0]
    if kw:
        try:
            txt = txt.format(**kw)
        except Exception:
            pass
    return txt


# ---------- رقم‌سازی ----------

_LATIN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def num(s) -> str:
    """ارقام مطابق زبان فعال: فارسی → ارقام فارسی، انگلیسی → لاتین"""
    s = str(s if s is not None else "")
    return s.translate(_LATIN_TO_FA) if _LANG == "fa" else s


def pct(a: float) -> int:
    """آلفای ۰..۱ به ۰..۲۵۵"""
    return max(0, min(255, int(round(a * 255))))


def all_keys() -> tuple:
    return tuple(_STRINGS.keys())
