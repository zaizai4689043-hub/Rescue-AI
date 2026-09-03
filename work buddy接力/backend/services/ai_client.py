"""
DashScope AI 客户端
从 Qwen 演示版 (ai_proxy.py) 回流，统一封装所有 AI 调用
对应愿景 1：两套代码合一

使用方式：
    from services.ai_client import ai_client
    
    # 文本生成
    result = await ai_client.chat(messages, model="qwen3.8-max")
    
    # 视觉分析
    result = await ai_client.vl_chat(messages, model="qwen3.7-plus")
    
    # 结构研判（专用）
    result = await ai_client.assess_building(image_b64)
    
    # 灾情简报
    result = await ai_client.generate_brief(situation_data)
"""
import os
import json
import time
import hashlib
import urllib.request
import urllib.error
from typing import Optional

# ---- 配置 ----
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
TEXT_MODEL_DEFAULT = os.getenv("DASHSCOPE_TEXT_MODEL", "qwen3.8-max")
VL_MODEL_DEFAULT = os.getenv("DASHSCOPE_VL_MODEL", "qwen3.7-plus")

# ---- 超时 ----
VL_TIMEOUT = 20       # 视觉模型 20s
TEXT_TIMEOUT = 8      # 文本模型 8s（演示版 5s 太紧，产品版放宽到 8s）

# ---- 缓存 ----
_cache = {}
_CACHE_TTL = 60       # 60 秒
_CACHE_MAX = 200


def _cache_key(model: str, messages: list, extra: str = "") -> str:
    raw = json.dumps({"model": model, "messages": messages, "extra": extra}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[str]:
    entry = _cache.get(key)
    if not entry:
        return None
    ts, val = entry
    if time.time() - ts > _CACHE_TTL:
        _cache.pop(key, None)
        return None
    return val


def _cache_set(key: str, val: str):
    if len(_cache) >= _CACHE_MAX:
        # 淘汰最旧的
        oldest = min(_cache.items(), key=lambda x: x[1][0])
        _cache.pop(oldest[0], None)
    _cache[key] = (time.time(), val)


def _call_dashscope(model: str, messages: list, timeout: int = TEXT_TIMEOUT,
                    temperature: float = 0.7, response_format: Optional[dict] = None) -> Optional[str]:
    """调用 DashScope API，返回文本或 None（失败时）"""
    if not DASHSCOPE_API_KEY:
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
    }

    body = {
        "model": model,
        "messages": messages,
        "enable_thinking": False,    # 关闭思考模式，加速响应
        "temperature": temperature,
    }
    if response_format:
        body["response_format"] = response_format

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(DASHSCOPE_BASE_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception):
        return None


class AIClient:
    """统一 AI 客户端"""

    @staticmethod
    def chat(prompt: str, system: str = "", model: str = TEXT_MODEL_DEFAULT,
             temperature: float = 0.7, timeout: int = TEXT_TIMEOUT,
             use_cache: bool = True) -> Optional[str]:
        """文本对话"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # 缓存
        if use_cache:
            key = _cache_key(model, messages)
            cached = _cache_get(key)
            if cached:
                return cached

        result = _call_dashscope(model, messages, timeout=timeout, temperature=temperature)
        if result and use_cache:
            _cache_set(_cache_key(model, messages), result)
        return result

    @staticmethod
    def chat_json(prompt: str, system: str = "", model: str = TEXT_MODEL_DEFAULT,
                  temperature: float = 0.3, timeout: int = TEXT_TIMEOUT) -> Optional[dict]:
        """文本对话，返回 JSON"""
        result = AIClient.chat(prompt, system, model, temperature, timeout)
        if not result:
            return None
        # 尝试提取 JSON
        try:
            # 去除可能的 markdown 代码块标记
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            return None

    @staticmethod
    def vl_chat(prompt: str, image_b64: str, system: str = "",
                model: str = VL_MODEL_DEFAULT, temperature: float = 0.3,
                timeout: int = VL_TIMEOUT) -> Optional[str]:
        """视觉对话（图片 + 文本）"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        messages.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                {"type": "text", "text": prompt},
            ]
        })

        return _call_dashscope(model, messages, timeout=timeout, temperature=temperature)

    @staticmethod
    def vl_chat_json(prompt: str, image_b64: str, system: str = "",
                     model: str = VL_MODEL_DEFAULT, temperature: float = 0.3,
                     timeout: int = VL_TIMEOUT) -> Optional[dict]:
        """视觉对话，返回 JSON"""
        result = AIClient.vl_chat(prompt, image_b64, system, model, temperature, timeout)
        if not result:
            return None
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned.strip())
        except (json.JSONDecodeError, IndexError):
            return None

    # ---- 预置功能 ----

    @staticmethod
    def assess_building(image_b64: str) -> Optional[dict]:
        """建筑结构研判（Qwen-VL）"""
        prompt = """你是建筑结构专家。这是地震后的真实建筑现场影像。
请分析并返回严格 JSON：
{
  "columns": 0-100,          // 墙体匹配度
  "voids": 0-100,            // 疑似空隙
  "match_rate": 0-100,       // 承重构件匹配率
  "integrity": 0-100,        // 结构完整度
  "damage_level": "轻微|中度|严重|完全倒塌",
  "confidence": 0.0-1.0,
  "rescue_advice": "建议救援方案"
}
只返回 JSON，不要其他文字。"""
        return AIClient.vl_chat_json(prompt, image_b64)

    @staticmethod
    def explain_priority(trapped_person_data: dict) -> Optional[str]:
        """生成优先级决策理由（≤40 字）"""
        prompt = f"""你是地震救援指挥官。以下是一名被困人员信息：
{json.dumps(trapped_person_data, ensure_ascii=False, indent=2)}

请给出不超过40字的中文优先级决策理由（说明为何该优先级、建议携带装备），只返回理由文本。"""
        return AIClient.chat(prompt, temperature=0.5, timeout=6)

    @staticmethod
    def generate_brief(situation_data: dict) -> Optional[str]:
        """生成灾情简报（应急管理部风格）"""
        prompt = f"""你是应急管理部值班室简报员。已核验事实口径：
{json.dumps(situation_data, ensure_ascii=False, indent=2)}

请据此撰写不超过200字的灾情简报，采用应急管理部通报风格。
要求：数据驱动、克制不带情绪、标注信息来源和时间节点。"""
        return AIClient.chat(prompt, temperature=0.3, timeout=10)

    @staticmethod
    def generate_decision(situation_data: dict, matched_cases: list) -> Optional[dict]:
        """AI 决策助手综合研判"""
        prompt = f"""你是地震救援决策参谋。请基于以下信息给出救援决策建议。

当前灾情态势：
{json.dumps(situation_data, ensure_ascii=False, indent=2)}

匹配的历史案例：
{json.dumps(matched_cases, ensure_ascii=False, indent=2)}

请返回严格 JSON：
{{
  "priority_areas": [
    {{"name": "区域名", "reason": "优先理由", "score": 0.0-1.0, "estimated_trapped": 0}}
  ],
  "action_plan": "具体行动方案（200字内）",
  "risk_warnings": ["风险1", "风险2"],
  "resource_suggestions": ["资源建议1", "资源建议2"],
  "reference_case": "最参考价值的案例ID"
}}
只返回 JSON。"""
        return AIClient.chat_json(prompt, temperature=0.4, timeout=15)


# 全局实例
ai_client = AIClient()
