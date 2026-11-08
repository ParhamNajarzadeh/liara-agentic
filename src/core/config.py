"""Zero-Hardcoded-Keys Configuration Loader (`src/core/config.py`).

Strictly loads all API credentials and runtime settings from environment variables
or `.env` files. Designed to work seamlessly with `pydantic-settings` when installed,
or fallback to pure `pydantic.BaseModel` + `.env` parser in minimal environments.
Never contains any hardcoded API keys (`METIS_API_KEY`, `LIARA_API_TOKEN`, etc.).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    HAS_PYDANTIC_SETTINGS = True
except ImportError:
    HAS_PYDANTIC_SETTINGS = False
    BaseSettings = BaseModel  # type: ignore[misc,assignment]


def _load_dotenv_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """Parse `.env` file without external dependency if python-dotenv is absent."""
    loaded: Dict[str, str] = {}
    candidates = [
        env_path,
        Path.cwd() / "workspace" / ".env",
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / "workspace" / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            for raw_line in candidate.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                loaded[key] = val
                if key not in os.environ:
                    os.environ[key] = val
            break
    return loaded


class Settings(BaseSettings):  # type: ignore[misc]
    """Centralized configuration for Liara Agentic SRE Assistant.

    All sensitive credentials default to empty strings and are populated
    exclusively from environment variables (`.env`).
    """

    # --- MetisAI DeepSeek Wrapper (System 2 Reasoning & Tool Calling) ---
    metis_api_key: str = Field(default="", description="MetisAI API Key loaded from METIS_API_KEY")
    metis_deepseek_base_url: str = Field(
        default="https://api.metisai.ir/deepseek/v1",
        description="Primary MetisAI DeepSeek wrapper endpoint inside Iran",
    )
    metis_deepseek_fallback_base_url: str = Field(
        default="https://api.tapsage.com/deepseek/v1",
        description="Fallback TapSage endpoint for external cloud environments",
    )
    metis_anthropic_base_url: str = Field(
        default="https://api.metisai.ir/deepseek/anthropic",
        description="MetisAI Anthropic-compatible endpoint for Claude Code",
    )
    metis_primary_model: str = Field(
        default="deepseek-v4.1-flash",
        description="Primary cost-efficient tool-calling model (NEVER append [1m])",
    )
    metis_heavy_reasoning_model: str = Field(
        default="deepseek-v4-pro",
        description="Deep SRE reasoning fallback model (NEVER append [1m])",
    )
    metis_secondary_fallback_model: str = Field(
        default="gpt-4o-mini",
        description="Secondary emergency model fallback",
    )

    # --- System 1 Fast Decision Engine (Jev / Mizan-4B / Kev / Laya) ---
    metis_typesafe_base_url: str = Field(
        default="https://api.metisai.ir/api/v1/wrapper/typesafe",
        description="MetisAI TypeSafe Jev /v1/systemone base URL",
    )
    mizan_local_url: str = Field(
        default="http://127.0.0.1:8080/v1/systemone",
        description="Local Persian System-1 model xmanii/Mizan-4B server endpoint",
    )
    kev_local_url: str = Field(
        default="http://127.0.0.1:8009/v1/systemone",
        description="Local long-context System-1 model jaredpalmer/kev endpoint",
    )
    laya_enabled: bool = Field(
        default=True,
        description="Enable NandhaKishorM/laya multilingual System-1 router with OptionStabilityHook",
    )

    # --- Liara PaaS OpenAPI (v1 & v2) ---
    liara_api_token: str = Field(
        default="",
        description="Scoped virtual agent token loaded from LIARA_API_TOKEN",
    )
    liara_api_base_url: str = Field(
        default="https://api.liara.ir",
        description="Official Liara OpenAPI base URL",
    )
    liara_dns_base_url: str = Field(
        default="https://dns-service.liara.ir",
        description="Official Liara DNS service OpenAPI base URL",
    )
    liara_virtual_agent_identity: str = Field(
        default="liara-sre-virtual-agent",
        description="Dedicated virtual agent identity for immutable audit logs",
    )
    liara_simulator_mode: bool = Field(
        default=True,
        description="Enable deterministic realistic simulator when live token is absent or for offline judge testing",
    )

    # --- Governance, Hackathon Budget & Token Context Limits ---
    hackathon_initial_credit_tomans: int = Field(
        default=2_000_000,
        description="Initial 2,000,000 Tomans Liara hackathon credit budget",
    )
    short_ttl_seconds: int = Field(
        default=3600,
        description="Short-lived virtual token TTL (1 hour default)",
    )
    context_window_limit_tokens: int = Field(
        default=128_000,
        description="Effective working context window budget before compaction trigger",
    )
    compaction_utilization_threshold: float = Field(
        default=0.70,
        description="Trigger context compaction at 70% window utilization (Ch. 10 Lesson 04)",
    )
    compaction_max_turns: int = Field(
        default=40,
        description="Trigger context compaction after 40 conversation turns",
    )
    max_auto_build_heal_attempts: int = Field(
        default=2,
        description="Maximum autonomous build-fix retries via coding agent bridge",
    )
    workspace_dir: str = Field(
        default="workspace",
        description="Relative or absolute path to working directory for project scans and trace logs",
    )

    if HAS_PYDANTIC_SETTINGS:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> "Settings":
        """Load settings deterministically from environment variables and `.env`."""
        _load_dotenv_file(env_path)
        metis_key = (
            os.environ.get("METIS_API_KEY", "").strip()
            or os.environ.get("OPENAI_API_KEY", "").strip()
            or os.environ.get("DEEPSEEK_API_KEY", "").strip()
        )
        liara_tok = os.environ.get("LIARA_API_TOKEN", "").strip()
        sim_env = os.environ.get("LIARA_SIMULATOR_MODE", "").strip().lower()
        if sim_env in ("0", "false", "no") and liara_tok:
            sim_mode = False
        elif liara_tok and not sim_env:
            sim_mode = False
        else:
            sim_mode = True

        env_map = {
            "metis_api_key": metis_key,
            "metis_deepseek_base_url": os.environ.get(
                "METIS_DEEPSEEK_BASE_URL", "https://api.metisai.ir/deepseek/v1"
            ),
            "metis_deepseek_fallback_base_url": os.environ.get(
                "METIS_DEEPSEEK_FALLBACK_BASE_URL", "https://api.tapsage.com/deepseek/v1"
            ),
            "metis_anthropic_base_url": os.environ.get(
                "METIS_ANTHROPIC_BASE_URL", "https://api.metisai.ir/deepseek/anthropic"
            ),
            "metis_primary_model": os.environ.get(
                "METIS_PRIMARY_MODEL", "deepseek-v4.1-flash"
            ),
            "metis_heavy_reasoning_model": os.environ.get(
                "METIS_HEAVY_REASONING_MODEL", "deepseek-v4-pro"
            ),
            "metis_secondary_fallback_model": os.environ.get(
                "METIS_SECONDARY_FALLBACK_MODEL", "gpt-4o-mini"
            ),
            "metis_typesafe_base_url": os.environ.get(
                "METIS_TYPESAFE_BASE_URL", "https://api.metisai.ir/api/v1/wrapper/typesafe"
            ),
            "mizan_local_url": os.environ.get(
                "MIZAN_LOCAL_URL", "http://127.0.0.1:8080/v1/systemone"
            ),
            "kev_local_url": os.environ.get(
                "KEV_LOCAL_URL", "http://127.0.0.1:8009/v1/systemone"
            ),
            "laya_enabled": os.environ.get("LAYA_ENABLED", "true").lower() in ("1", "true", "yes"),
            "liara_api_token": os.environ.get("LIARA_API_TOKEN", ""),
            "liara_api_base_url": os.environ.get("LIARA_API_BASE_URL", "https://api.liara.ir"),
            "liara_dns_base_url": os.environ.get(
                "LIARA_DNS_BASE_URL", "https://dns-service.liara.ir"
            ),
            "liara_virtual_agent_identity": os.environ.get(
                "LIARA_VIRTUAL_AGENT_IDENTITY", "liara-sre-virtual-agent"
            ),
            "liara_simulator_mode": sim_mode,
            "hackathon_initial_credit_tomans": int(
                os.environ.get("HACKATHON_INITIAL_CREDIT_TOMANS", "2000000")
            ),
            "short_ttl_seconds": int(os.environ.get("SHORT_TTL_SECONDS", "3600")),
            "context_window_limit_tokens": int(
                os.environ.get("CONTEXT_WINDOW_LIMIT_TOKENS", "128000")
            ),
            "compaction_utilization_threshold": float(
                os.environ.get("COMPACTION_UTILIZATION_THRESHOLD", "0.70")
            ),
            "compaction_max_turns": int(os.environ.get("COMPACTION_MAX_TURNS", "40")),
            "max_auto_build_heal_attempts": int(
                os.environ.get("MAX_AUTO_BUILD_HEAL_ATTEMPTS", "2")
            ),
            "workspace_dir": os.environ.get("WORKSPACE_DIR", "workspace"),
        }
        # Enforce MetisAI technical rule: NEVER append [1m] to DeepSeek model names
        for model_key in ("metis_primary_model", "metis_heavy_reasoning_model"):
            if "[1m]" in env_map[model_key]:
                env_map[model_key] = str(env_map[model_key]).replace("[1m]", "").strip()
        return cls(**env_map)

    def get_coding_agent_harness_env(self) -> Dict[str, str]:
        """Return environment configuration for connecting Claude Code or DeepSeek Harness (dsh) to MetisAI."""
        return {
            "ANTHROPIC_BASE_URL": self.metis_anthropic_base_url,
            "ANTHROPIC_AUTH_TOKEN": "${METIS_API_KEY}",
            "ANTHROPIC_MODEL": self.metis_primary_model,
            "CLAUDE_CODE_SUBAGENT_MODEL": self.metis_primary_model,
            "DEEPSEEK_BASE_URL": self.metis_deepseek_base_url,
            "DEEPSEEK_API_KEY": "${METIS_API_KEY}",
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings.from_env()
