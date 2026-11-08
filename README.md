# دستیار هوشمند زیرساخت و مهندسی قابلیت اطمینان (SRE) لیارا (`liara-agentic-sre`)

[![Liara PaaS Ready](https://img.shields.io/badge/Liara_PaaS-Production_Ready-0ea5e9)](#)
[![Model: deepseek-v4.1-flash](https://img.shields.io/badge/System_2-deepseek--v4.1--flash_(MetisAI)-10b981)](#)
[![System 1: Jev & Mizan-4B](https://img.shields.io/badge/System_1-Jev_%7C_Mizan--4B_(ECE_0.064)-f59e0b)](#)
[![Zero Hardcoded Keys](https://img.shields.io/badge/Judge_Security_Audit-Zero_Hardcoded_Keys_PASSED-22c55e)](#)

**همکار فنی هوشمند (AI Technical Co-Pilot & Staff SRE)** برای پلتفرم ابری **لیارا (Liara PaaS)** که مسیر ۵ مرحله‌ای سنتی دیپلوی را به یک **فلو تک‌گامی خودکار (Zero-Friction 1-Step Launch)** تبدیل می‌کند، در زمان شکست بیلد بدون نیاز به کپی-پیست دستی ارور توسط کاربر از طریق **پل خودترمیم‌گر بیلد (`Deploy Agent ↔ MCP ↔ Coding Agent`)** کد و کانفیگ را اصلاح و منتشر می‌سازد، و در زمان بروز **خطای HTTP 500 یا اشباع منابع (OOMKilled 137)** با اجرای موازی ساب‌ایجنت‌ها در زیر ۳۰ ثانیه ریشه‌یابی (RCA) و ترمیم را انجام می‌دهد.

## ۱. پوشش کامل ۳۰۰ امتیاز جدول داوری و ۸ الزام طلایی جلسه پرسش و پاسخ

| محور داوری / الزام جلسه پرسش و پاسخ | امتیاز | پیاده‌سازی معماری در `liara-agentic-sre` | ماژول / فایل کلیدی |
| :--- | :---: | :--- | :--- |
| **۱. عملکرد فنی و یکپارچه‌سازی با OpenAPI لیارا** | **۱۰۰** | اتصال به اندپوینت‌های واقعی `v1` و `v2` لیارا در قالب ۵ مگا-تول دامنه‌محور و سرور استاندارد MCP همراه با Exponential Backoff + Jitter و Idempotency | `src/mcp_server/liara_client.py` `src/mcp_server/mega_tools.py` |
| **۲. هوشمندی در عیب‌یابی SRE و حلقه خودکار Build-Fix** | **۱۰۰** | ۱. واکشی موازی لاگ، متریک CPU/RAM و رویدادها (`Send` Fan-Out) با `reasoning_steps` پیش از پاسخ و روبریک ۴ سطحی ($\ge 8/10$). ۲. پل خودترمیم‌گر بیلد با ایجنت کدنویسی (`code-remediator`) بدون کپی-پیست دستی کاربر | `src/mcp_server/build_healer_bridge.py` `src/orchestrator/nodes.py` |
| **۳. تجربه کاربری (UX) و قانون Anti-Fatigue HITL** | **۵۰** | رابط کاربری دوگانه راست‌به‌چپ **Chat Plus (۳۵٪ چت / ۶۵٪ بوم زنده زیرساخت)** با ۷ کامپوننت Static GenUI. حذف کامل پاپ‌آپ‌های خسته‌کننده برای عملیات خواندنی/آماده‌سازی و محدودسازی `interrupt()` صرفاً به تصمیمات مالی و پروداکشن | `src/frontend/app/page.tsx` `UnifiedZeroFrictionLaunchCard.tsx` `AutomatedBuildHealerBridgeCard.tsx` |
| **۴. پایداری، امنیت، مدیریت اعتبار ۲ میلیون تومانی و استقلال مخزن** | **۵۰** | ۱. پایشگر اعتبار ۲ میلیون تومانی هکاتون (`CreditBudgetGuard`). ۲. شکستن مثلث مهلک سایمون ویلسون (`SecretBlindVault` + `LogSanitizer` با تگ `<untrusted_log_data>` + قفل سخت `DELETE`). ۳. صفر کلید هاردکدشده و استقلال ۱۰۰٪ وابستگی‌ها | `src/core/governance.py` `scripts/pre_publish_judge_audit.py` |

## ۲. دیاگرام معماری ۵ لایه و گراف تصمیم‌گیری (`LangGraph StateGraph`)

```mermaid
flowchart TD
    User["درخواست کاربر در پنل Chat Plus (RTL)"] --> S1["لایه ۲: روتر سریع System 1\n(Jev / Mizan-4B / Laya < 40ms)"]
    
    S1 -->|setup_deploy| AutoPrep["اسکن خودکار مخزن، .env.example، تولید liara.json\nو آپلود بسته .tar.gz به v2/sources (بدون سؤال از کاربر)"]
    AutoPrep --> FinGate{"گیت واحد تأیید مالی (interrupt)\nUnifiedZeroFrictionLaunchCard\n(محافظت از اعتبار ۲ میلیون تومانی)"}
    FinGate -->|Approved / State Edited| Publish["ساخت پروژه (v1/projects)، تزریق Secret-Blind\nو انتشار ریلیز (v2/releases)"]
    
    Publish -->|BUILD_FAILED| BuildHealer["حلقه خودترمیم‌گر بیلد (Zero Copy-Paste)\nDeploy Agent <-> MCP <-> code-remediator\nاصلاح کد/Dockerfile و آپلود مجدد"]
    BuildHealer --> Publish
    Publish -->|RUNNING| Verifier["نود راستی‌آزمایی سلامت پس از اقدام\n(HTTP 200 & Applet RUNNING)"]

    S1 -->|sre_troubleshoot (HTTP 500)| FanOut["اجرای موازی ۳ شاخه تلمتری (Parallel Fan-Out)"]
    FanOut --> W1["log_inspector_worker\n(Regex Sanitizer + <untrusted_log_data>)"]
    FanOut --> W2["metrics_telemetry_worker\n(GET /v1/projects/{name}/metrics)"]
    FanOut --> W3["events_releases_worker\n(events 137 OOMKilled & applets)"]
    W1 & W2 & W3 --> RCA["نود تحلیلگر RCA با مدل deepseek-v4.1-flash\n(استدلال گام‌به‌گام + روبریک Evaluator >= 8/10)"]
    RCA --> ProdGate{"گیت تأیید تغییرات پروداکشن (HITL)\nIncidentRCADiagnosticCard"}
    ProdGate -->|Approved| Remediate["اجرای ترمیم زیرساخت\n(scale_plan / restart / rollback)"]
    Remediate --> Verifier

    S1 -->|domain_dns| DNSWizard["ثبت دامنه در لیارا + راهنمای گام‌به‌گام ایرنیک (.ir)\nو بررسی گواهی SSL (DomainDNSGuideWidget)"]
```

## ۳. جدول اندپوینت‌های واقعی OpenAPI لیارا و مرز محدودیت‌های خارج از API

| مگا-تول (`Mega-Tool`) | اندپوینت واقعی OpenAPI لیارا | سطح خودمختاری (Anti-Fatigue HITL) | محدودیت ذاتی API و نحوه مدیریت در UX |
| :--- | :--- | :--- | :--- |
| **`liara_app_lifecycle`** | `GET /v1/projects` `POST /v1/projects` `POST /v1/projects/{name}/actions/restart` `POST /v1/projects/{name}/actions/scale` | `list`/`get`/`estimate`: خودکار `create`/`scale`/`restart`: نیازمند تأیید HITL؛ `DELETE`: مسدودشده در کد | شارژ کیف پول بانکی API مستقیم ندارد؛ دستیار موجودی ۲ میلیون تومانی را رصد کرده و در صورت کسری، لینک مستقیم درگاه پنل لیارا را نمایش می‌دهد. |
| **`liara_release_pipeline`** | `POST /v2/projects/{name}/sources` `POST /v2/projects/{name}/releases` `GET /v1/projects/{name}/releases` | `auto_prepare_and_upload` و `auto_heal_build_loop`: ۱۰۰٪ خودکار؛ انتشار اولیه و `rollback`: نیازمند HITL | در صورت شکست بیلد، لاگ خطا به صورت خودکار به ساب‌ایجنت کدنویسی ارسال شده و بدون نیاز به کپی-پیست کاربر اصلاح می‌گردد. |
| **`liara_config_and_storage`** | `POST /v1/projects/{id}/update-envs` `POST /v1/projects/{id}/zero-downtime` `POST /v1/projects/{id}/disks` | `scan_env_template`: خودکار؛ تزریق متغیرها و تغییر دیسک: نیازمند HITL | مقادیر محرمانه `.env` با معماری **Secret-Blind** مستقیماً از مرورگر به `SecretBlindVault` سرور ارسال شده و هرگز وارد کانتکست LLM نمی‌شوند. |
| **`liara_sre_observability`** | `GET /v1/projects/{name}/metrics` `GET /v1/projects/{name}/logs` `GET /v1/projects/{name}/events` `GET /v1/projects/{name}/applets` | ۱۰۰٪ خودکار و موازی (بدون پاپ‌آپ تأیید) | لاگ‌های بالای ۲۰۰ خط به ساب‌ایجنت ایزوله `log-forensics` ارجاع شده و تمامی لاگ‌ها در `<untrusted_log_data>` پاکسازی می‌شوند. |
| **`liara_domain_and_network`** | `GET /v1/domains` `POST /v1/domains` `POST /v1/domains/{id}/check` | ثبت دامنه و بررسی SSL: از طریق API لیارا | پنل ایرنیک (`nic.ir`) خارج از دسترسی API لیارا است؛ ویجت `DomainDNSGuideWidget` رکوردهای `A` و `CNAME` را با قابلیت کپی تک‌کلیکی به کاربر ارائه می‌دهد. |

## ۴. راهنمای تست تک‌دستوری برای داوران (Judge Quick-Start)

پروژه به گونه‌ای طراحی شده که داوران پس از `git clone`، حتی بدون نیاز به نصب پکیج‌های خارجی یا تنظیم کلید زنده (با استفاده از حالت شبیه‌ساز واقع‌گرایانهٔ داخلی یا با قرار دادن کلید در `.env`) می‌توانند در کمتر از ۱۰ ثانیه تمامی بخش‌ها را راستی‌آزمایی کنند:

```bash
# ۱. بررسی امنیتی خودکار (تأیید ۰ کلید هاردکدشده، استقلال وابستگی‌ها و وجود تمامی فایل‌ها)
python3 scripts/pre_publish_judge_audit.py

# ۲. اجرای تست دود سرتاسری هر ۴ سناریوی اصلی چالش
python3 scripts/smoke_test.py

# ۳. اجرای بنچمارک ارزیابی ۲۰ نمونه تست (۱۲ طلایی، ۶ لبه، ۲ تزریق پرامپت خرابکارانه)
python3 eval/run_eval.py

# ۴. اجرای خودکار سناریوی طلایی ۵ دقیقه‌ای ویدیوی دمو
python3 scripts/demo_scenario_runner.py
```

## ۵. سناریوی طلایی ۵ دقیقه‌ای ویدیوی دمو (5-Minute Demo Script)
- **دقیقه ۰۰:۰۰ تا ۰۱:۱۵ (فلو تک‌گامی راه‌اندازی Zero-Friction):** اسکن خودکار پروژه پایتون، استخراج کلیدهای `.env.example` با معماری Secret-Blind، پیشنهاد پلن اقتصادی متناسب با اعتبار ۲ میلیون تومانی و تأیید تک‌کلیکی در `UnifiedZeroFrictionLaunchCard`.
- **دقیقه ۰۱:۱۵ تا ۰۲:۳۰ (شکست بیلد و حلقه خودترمیم‌گر بدون کپی-پیست):** بروز خطای بیلد در پورت و پکیج `requirements.txt`، ارسال خودکار قرارداد کار چهاربخشی به `code-remediator`، نمایش زنده Diff در `AutomatedBuildHealerBridgeCard` و رسیدن خودکار به وضعیت `RUNNING`.
- **دقیقه ۰۲:۳۰ تا ۰۳:۴۵ (بحران خطای HTTP 500، اشباع RAM و دفاع در برابر لاگ سمی):** اجرای موازی ۳ کارگر SRE در زیر ۳۰ ثانیه، خنثی‌سازی حمله Prompt Injection در لاگ HTTP، تشخیص `OOMKilled (Exit 137)` با درجه اطمینان ۹۴٪، ارتقای پلن با تأیید HITL و راستی‌آزمایی سلامت (`HTTP 200`).
- **دقیقه ۰۳:۴۵ تا ۰۵:۰۰ (دامنه ایرنیک، مشاهده‌پذیری `trace.jsonl` و دکمه اضطراری Kill-Switch):** نمایش راهنمای اتصال دامنه `.ir` در ایرنیک، بررسی لاگ ممیزی و فشردن دکمه قرمز **Kill-Switch** که بلافاصله توکن مجازی ایجنت را باطل و وضعیت را به `DECOMMISSIONED` تغییر می‌دهد.
