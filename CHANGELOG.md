# `CHANGELOG.md` — تاریخچهٔ نسخه‌ها و تصمیمات معماری

## [1.0.0] - 2026-10-22 (نسخه نهایی آماده داوری هکاتون لیارا - StarCoach)
### افزوده‌شده (Added)
- **معماری ۵ لایهٔ سیستم زنده (فصل ۱۴ کوئرا):** پیاده‌سازی کامل لایه دانش پایدار (`CLAUDE.md` و `MEMORY.md`)، گراف ارکستراسیون `LangGraph StateGraph`، ساب‌ایجنت‌های ایزوله (`.claude/agents/`)، مهارت‌های با افشای تدریجی (`.claude/skills/`) و سرور استاندارد MCP (`src/mcp_server/`).
- **فلو تک‌گامی راه‌اندازی (Zero-Friction 1-Step Launch):** جایگزینی ۵ مرحلهٔ دستی پنل سنتی لیارا با اسکن خودکار مخزن، استخراج Secret-Blind کلیدهای `.env.example`، پیشنهاد اقتصادی‌ترین پلن متناسب با اعتبار ۲ میلیون تومانی هکاتون و کارت تجمیعی `UnifiedZeroFrictionLaunchCard.tsx`.
- **پل خودترمیم‌گر خطای بیلد (`BuildAutoHealerBridge`):** ارتباط خودکار و بدون کپی-پیست بین ایجنت دیپلوی و ایجنت کدنویسی (`code-remediator` / Claude Code / OpenCode / `dsh`) بر پایهٔ قرارداد کار چهاربخشی (`INPUT`, `OUTPUT`, `ACCEPTANCE`, `BOUNDARIES`).
- **موتور دوگانهٔ System 1 + System 2:** آداپتور خودبسندهٔ `deepseek-v4.1-flash` روی MetisAI DeepSeek Wrapper به همراه موتور تصمیم‌گیری سریع System 1 (`Jev` / `Mizan-4B` / `Kev` / `Laya` با `OptionStabilityHook`).
- **حاکمیت هوش مصنوعی و شکستن مثلث مهلک سایمون ویلسون:** پیاده‌سازی `SecretBlindVault`، `LogSanitizer` با تگ `<untrusted_log_data>`، مسدودسازی سخت `DELETE /v1/projects/{name}`، پایشگر اعتبار ۲ میلیون تومانی (`CreditBudgetGuard`) و کلید اضطراری `AgentKillSwitch`.
- **ممیزی امنیتی و ارزیابی خودکار:** افزودن `scripts/pre_publish_judge_audit.py` (تضمین صفر کلید هاردکدشده برای اسکنرهای داوری)، `scripts/smoke_test.py` و `eval/run_eval.py`.
