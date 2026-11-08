# `MEMORY.md` — حافظهٔ بلندمدت و اپیزودیک چهاربخشی (فصل ۱۰ و ۱۴ دورهٔ کوئرا)

این فایل به عنوان حافظهٔ پایدار بین‌نشستی (`LangGraph Store` & Episodic File Memory) عمل می‌کند و در پایان هر عملیات توسط `JITFileRetriever.update_episodic_memory_file` به‌روزرسانی می‌شود.

## 1. User Preferences (ترجیحات کاربر و سیاست بودجه هکاتون)
- زبان تعامل: فارسی روان، بدون اصطلاحات پیچیدهٔ زیرساختی، مبتنی بر رابط کاربری دوگانه **Chat Plus (۳۵٪ پنل چت راست / ۶۵٪ بوم زنده زیرساخت چپ)**.
- بودجه اولیه هکاتون لیارا: **۲,۰۰۰,۰۰۰ تومان (`2,000,000 Tomans`)**؛ اولویت با پیشنهاد پلن‌های اقتصادی (`ir-mini` و `ir-standard-1g`) جهت آنلاین ماندن سرویس تا پایان داوری.
- سیاست تأیید انسانی (**Anti-Fatigue HITL**): عدم نمایش پاپ‌آپ برای عملیات اکتشافی/خواندنی؛ توقف `interrupt()` فقط در گلوگاه مالی و تغییرات پروداکشن.

## 2. Project Topology (توپولوژی پروژه‌های فعال در لیارا)
- **پروژه نمونه ۱ (`shop-api-prod`):**
  - پلتفرم: `python` (FastAPI + Uvicorn)
  - پورت اجرایی: `8000`
  - پلن فعلی: ارتقایافته از `ir-mini` (512MB) به `ir-standard-2g` (2048MB) پس از رخداد OOM.
  - قابلیت `Zero-Downtime`: فعال (`true`)
  - دامنه متصل: `shop.example.ir` (پشت کلودفلر / ثبت‌شده در ایرنیک `nic.ir` با گواهی Let's Encrypt SSL).

## 3. Build & Incident Learnings (آموخته‌های رخدادهای SRE و خطاهای بیلد قبلی)
- **یادگیری رخداد #1 (حلقه خودکار Build-Fix بدون کپی-پیست):** در پروژه `shop-api-prod`، خطای بیلد اولیه ناشی از عدم تطابق پورت `3000` در `liara.json` با پورت `8000` سرور و پکیج اشتباه در `requirements.txt` بود که توسط پل `BuildAutoHealerBridge` و ساب‌ایجنت `code-remediator` در تلاش اول به صورت خودکار اصلاح و منتشر گردید.
- **یادگیری رخداد #2 (تشخیص خطای HTTP 500 و OOMKilled 137):** خطای `HTTP 500` در مسیر `/api/v1/checkout` به دلیل اشباع ۹۹.۲٪ حافظه RAM (`508MB / 512MB`) و کد خروج کانتینر `137 (OOMKilled)` به همراه نشت کانکشن در `src/db.py` رخ داد. با ارتقای پلن و کاهش `pool_size` به ۱۰ برطرف شد.
- **یادگیری امنیتی #3 (دفاع در برابر لاگ سمی):** تلاش برای Indirect Prompt Injection در هدر `HTTP_USER_AGENT` لاگ‌ها توسط `LogSanitizer` و تگ `<untrusted_log_data>` خنثی گردید.

## 4. Reference IDs (شناسه‌های کلیدی مرجع برای حفظ در Context Compaction)
- `active_project_name`: `shop-api-prod`
- `last_healthy_source_id`: `src-001`
- `last_healthy_release_id`: `rel-v101-healthy`
- `virtual_agent_identity`: `liara-sre-virtual-agent`
