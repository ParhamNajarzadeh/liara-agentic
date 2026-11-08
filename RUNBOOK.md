# `RUNBOOK.md` — دستورالعمل اجرایی عملیات، مدیریت رخداد و بازیابی از خطا (فصل ۱۲ و ۱۶ کوئرا)

این سند راهنمای عملیاتی تیم داوری و مهندسان قابلیت اطمینان سایت (SRE) برای راه‌اندازی، پایش، عیب‌یابی و بازنشستگی اضطراری (Kill-Switch) دستیار هوشمند زیرساخت لیارا است.

## ۱. راه‌اندازی سریع و بدون وابستگی بیرونی (Zero-Dependency Startup)
تمامی ماژول‌های هسته (`src/core/`), سرور MCP (`src/mcp_server/`) و گراف ارکستراسیون (`src/orchestrator/`) ۱۰۰٪ خودبسنده طراحی شده‌اند:

```bash
# ۱. کپی الگوی متغیرهای محیطی (بدون هیچ کلید هاردکدشده در کد)
cp .env.example .env

# ۲. اجرای ممیزی امنیتی داوران (تأیید صفر کلید هاردکدشده و سلامت ساختار)
python3 scripts/pre_publish_judge_audit.py

# ۳. اجرای تست دود سرتاسری هر ۴ سناریوی کلیدی
python3 scripts/smoke_test.py

# ۴. اجرای ارزیابی خودکار ۲۰ نمونه (Golden, Edge, Adversarial)
python3 eval/run_eval.py
```

## ۲. پیکربندی اتصال مستقیم ایجنت‌های کدنویسی به متیس و سرور MCP لیارا
برای اینکه ایجنت کدنویسی (`Claude Code` یا `DeepSeek Harness / dsh`) مستقیماً به مدل مقرون‌به‌صرفهٔ `deepseek-v4.1-flash` روی متیس و سرور `liara-mcp-server` متصل شود:

```bash
export METIS_API_KEY="your_metis_key_from_env"

# اتصال Claude Code به DeepSeek روی متیس:
export ANTHROPIC_BASE_URL=https://api.metisai.ir/deepseek/anthropic
export ANTHROPIC_AUTH_TOKEN=${METIS_API_KEY}
export ANTHROPIC_MODEL=deepseek-v4.1-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4.1-flash

# اتصال DeepSeek Harness (dsh) به متیس:
export DEEPSEEK_BASE_URL=https://api.metisai.ir/deepseek/v1
export DEEPSEEK_API_KEY=${METIS_API_KEY}
```

## ۳. پلی‌بوک واکنش به رخدادهای عملیاتی (Incident Response Playbook)

| کد رخداد | نشانه در تلمتری و لاگ لیارا | اقدام خودکار دستیار (Autonomous) | اقدام نیازمند تأیید (HITL Gate) |
| :--- | :--- | :--- | :--- |
| **شکست بیلد در زمان دیپلوی (`BUILD_FAILED`)** | خطای `pip`/`npm`، خطای سینتکس یا عدم تطابق پورت در `GET /v1/projects/{name}/events` | صدور قرارداد کار چهاربخشی (`WorkOrderContract`) به ساب‌ایجنت `code-remediator`، اصلاح کد/پورت، بسته‌بندی مجدد `.tar.gz` و انتشار مجدد (تا ۲ تلاش) | نیازی به تأیید انسانی یا کپی-پیست دستی ندارد (Anti-Fatigue HITL) |
| **خطای `HTTP 500` با کد خروج `137 (OOMKilled)`** | اشباع حافظه RAM در `/metrics` (نزدیک به ۱۰۰٪ ظرفیت پلن) و ثبت رویداد `OOMKilled` | اجرای موازی ۳ کارگر SRE (Fan-Out)، پاکسازی لاگ در `<untrusted_log_data>` و تولید گزارش RCA همراه با پچ استخر اتصالات دیتابیس | تأیید ارتقای پلن (`scale_plan` به `ir-standard-2g`) با نمایش اثر مالی روی شارژ ۲ میلیون تومانی |
| **خطای `HTTP 500` بلافاصله پس از ریلیز جدید (`Crash 1`)** | سلامت نرمال CPU/RAM اما کرش اپلیکیشن در `rel-v102-broken` | شناسایی آخرین ریلیز سالم (`rel-v101-healthy`) از اندپوینت `GET /v1/projects/{name}/releases` | تأیید اجرای `rollback_release` و بازگردانی وضعیت با Time Travel |
| **مشاهده تلاش تزریق پرامپت در لاگ‌ها (`Prompt Injection`)** | وجود عبارات `Ignore previous instructions` یا `DELETE /v1/projects` در لاگ HTTP | خنثی‌سازی با Regex در `LogSanitizer`، محصورسازی در `<untrusted_log_data>` و مسدودسازی سخت `DELETE` در `GovernanceEngine` | در صورت نیاز، فشردن دکمه قرمز **Kill-Switch** جهت ابطال آنی توکن مجازی |
