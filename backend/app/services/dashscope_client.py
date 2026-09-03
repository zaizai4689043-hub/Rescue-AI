"""DashScope（通义千问）客户端 - 复刻 Qwen 初版/ai_proxy.py 的代理契约。

契约要点（与主演示代理保持一致，便于行为对齐）：
- 参数白名单：仅透传 enable_thinking / temperature / response_format，默认注入 enable_thinking=false
  （qwen3 系默认思考模式响应慢，前端易超时，见 ai_proxy.py 注释）
- 缓存：(model, sha256(payload)) 为键，TTL 60s，上限 200 条
- 降级契约：永不向调用方抛异常，失败返回 (False, {"fallback": True, "reason": ...})
"""
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings

DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
TIMEOUT_SEC = 25          # 与 ai_proxy.py 一致
CACHE_TTL = 60            # AI 响应缓存有效期（秒）
CACHE_MAX = 200           # 缓存条目上限
MAX_REASON_LEN = 200      # 降级 reason 截断，防日志注入式超长输出

# 模块级缓存：key=(model, payload_hash) -> (ts, data_dict)
_cache: Dict[Tuple[str, str], Tuple[float, dict]] = {}


def is_configured() -> bool:
    """是否配置了可用的 DashScope 密钥"""
    return bool(settings.DASHSCOPE_API_KEY)


def _cache_get(key: Tuple[str, str]) -> Optional[dict]:
    item = _cache.get(key)
    if item and time.time() - item[0] < CACHE_TTL:
        return item[1]
    return None


def _cache_put(key: Tuple[str, str], data: dict) -> None:
    if len(_cache) >= CACHE_MAX:
        oldest = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest]
    _cache[key] = (time.time(), data)


def _fallback(reason: str) -> Tuple[bool, dict]:
    return False, {"fallback": True, "reason": reason[:MAX_REASON_LEN]}


def chat_completion(
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    json_mode: bool = False,
    model: Optional[str] = None,
) -> Tuple[bool, dict]:
    """调用 DashScope chat completptions（OpenAI 兼容模式）。

    返回 (ok, data)：ok=True 时 data 为上游完整响应；失败时 data 为
    {"fallback": True, "reason": ...}。永不抛异常。
    """
    if not is_configured():
        return _fallback("未配置 DASHSCOPE_API_KEY")
    if not messages:
        return _fallback("messages 为空")

    model = model or settings.DASHSCOPE_TEXT_MODEL
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "enable_thinking": False,  # 默认关闭思考模式，保证响应速度
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    # 缓存（仅对确定性请求生效）
    payload_hash = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    cache_key = (model, payload_hash)
    cached = _cache_get(cache_key)
    if cached is not None:
        return True, cached

    try:
        resp = httpx.post(
            DASHSCOPE_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            },
            timeout=TIMEOUT_SEC,
        )
    except httpx.TimeoutException:
        return _fallback(f"DashScope 请求超时(>{TIMEOUT_SEC}s)")
    except Exception as e:  # 网络/连接等一切异常 → 降级，绝不外抛
        return _fallback(f"DashScope 请求异常: {e}")

    if resp.status_code != 200:
        return _fallback(f"DashScope HTTP {resp.status_code}: {resp.text[:120]}")

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return _fallback("DashScope 响应非合法 JSON")

    if not data.get("choices"):
        return _fallback("DashScope 响应缺少 choices")

    _cache_put(cache_key, data)
    return True, data


def extract_text(data: dict) -> Optional[str]:
    """从 chat completions 响应中安全提取助手文本，失败返回 None"""
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
