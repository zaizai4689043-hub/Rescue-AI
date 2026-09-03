"""AI参谋研判服务：针对单条社情帖生成双方案处置建议 + 三维可信度拆解。

两条生成路径：
- Qwen 路径：有密钥时调用真实模型，prompt 要求严格 JSON，鲁棒解析 + 结构校验
- 规则路径：无密钥/调用失败/解析失败时的兜底（移植 rescueai-dashboard.html 的 generatePlans）

降级契约与 dashscope_client 一致：永不抛异常，永远返回可渲染的结构。
"""
import json
import re
from typing import Dict, List, Optional

from app.services import dashscope_client
from app.services.social.adapters import SIGNAL_TYPE_LABELS, SignalType

# 规则引擎方案库（键=signal_type 英文值，移植自大屏 generatePlans）
_RULE_PLANS: Dict[str, dict] = {
    "casualty": {
        "a": ("立即派遣医疗急救队+担架转运", ["有明确伤亡报告", "位置可定位", "需现场分诊"]),
        "b": ("协调就近医院开通绿色通道", ["减少转运时间", "医院资源待确认", "可同步空中转运"]),
    },
    "building_collapse": {
        "a": ("重型搜救队+生命探测仪进场", ["建筑结构不稳", "可能有埋压人员", "需防二次坍塌"]),
        "b": ("无人机侦察+热成像搜索", ["降低救援风险", "覆盖范围大", "夜间可用"]),
    },
    "road_blocked": {
        "a": ("工程抢险队疏通+临时便道", ["影响救援通道", "物资运输受阻", "可评估绕行方案"]),
        "b": ("空投应急物资保障基本需求", ["地面通行恢复需时", "空投覆盖有限", "优先保障生命线"]),
    },
    "secondary_hazard": {
        "a": ("地质监测+预警疏散", ["滑坡/堰塞湖风险", "下游居民需转移", "持续监测必要"]),
        "b": ("设置警戒区+远程监控", ["人力有限时适用", "自动化监测补充", "及时预警即可"]),
    },
    "felt_report": {
        "a": ("信息发布+安抚引导", ["无直接灾情", "公众关注度高", "需防止恐慌"]),
        "b": ("纳入舆情监测持续关注", ["无需现场处置", "可作为辅助信息", "低优先级"]),
    },
    "rescue_progress": {
        "a": ("汇总通报+资源调配优化", ["已有救援力量在场", "需统筹协调", "信息更新及时"]),
        "b": ("媒体发布+公众沟通", ["提振信心", "减少重复报警", "信息公开透明"]),
    },
    "unknown": {
        "a": ("哨兵持续监听+人工复核", ["信号类型不明", "需补充信息", "暂不动用资源"]),
        "b": ("纳入低优先级观察队列", ["无明确灾情要素", "防止资源浪费", "后续自动降级"]),
    },
}

_ADVISORY_SYSTEM_PROMPT = (
    "你是地震救援指挥中心的AI参谋。针对一条灾情社情信号，生成处置方案研判。"
    "严格输出 JSON（不要任何解释、不要 markdown 代码围栏），结构如下："
    '{"plans":[{"label":"方案A","recommended":true,"title":"...","evidence":["...","...","..."]},'
    '{"label":"方案B","recommended":false,"title":"...","evidence":["...","...","..."]}],'
    '"credibility":{"timeliness":0-100,"location_accuracy":0-100,"cross_validation":0-100}}。'
    "evidence 每项不超过12字，title 不超过20字。"
)


def _clamp(v: float, lo: int = 15, hi: int = 95) -> int:
    return int(max(lo, min(hi, round(v))))


def _rule_credibility(confidence: Optional[float]) -> dict:
    """可信度拆解启发式（沿用大屏：时效/定位/交叉验证三档递减）"""
    base = _clamp((confidence or 0.5) * 100)
    return {
        "timeliness": _clamp(base + 5),
        "location_accuracy": _clamp(base - 5),
        "cross_validation": _clamp(base - 10),
    }


def _rule_plans(signal_type: str) -> List[dict]:
    """规则引擎双方案（移植大屏 generatePlans）"""
    p = _RULE_PLANS.get(signal_type, _RULE_PLANS["unknown"])
    return [
        {"label": "方案A", "recommended": True, "title": p["a"][0], "evidence": list(p["a"][1])},
        {"label": "方案B", "recommended": False, "title": p["b"][0], "evidence": list(p["b"][1])},
    ]


def _validate_parsed(parsed: dict) -> Optional[dict]:
    """结构校验 Qwen 输出；不合法返回 None 触发规则兜底"""
    plans = parsed.get("plans")
    cred = parsed.get("credibility")
    if not isinstance(plans, list) or len(plans) < 2:
        return None
    if not isinstance(cred, dict):
        return None
    for key in ("timeliness", "location_accuracy", "cross_validation"):
        if not isinstance(cred.get(key), (int, float)):
            return None
    norm_plans = []
    for i, p in enumerate(plans[:2]):
        if not isinstance(p, dict) or not p.get("title"):
            return None
        norm_plans.append({
            "label": p.get("label") or f"方案{'AB'[i]}",
            "recommended": bool(p.get("recommended", i == 0)),
            "title": str(p["title"])[:60],
            "evidence": [str(e)[:40] for e in (p.get("evidence") or [])[:4]],
        })
    return {
        "plans": norm_plans,
        "credibility": {
            "timeliness": _clamp(cred["timeliness"]),
            "location_accuracy": _clamp(cred["location_accuracy"]),
            "cross_validation": _clamp(cred["cross_validation"]),
        },
    }


def _robust_parse_json(text: str) -> Optional[dict]:
    """鲁棒 JSON 解析：剥代码围栏 → 直接解析 → 正则提取首个 {...}"""
    if not text:
        return None
    text = text.strip()
    # 剥 ``` 围栏
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 提取首个 {...} 块
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def generate_advisory(
    text: str,
    signal_type: str = "unknown",
    geo_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    confidence: Optional[float] = None,
    urgency_hint: Optional[str] = None,
    sentiment: Optional[str] = None,
) -> dict:
    """生成参谋研判：Qwen 优先，规则兜底。

    返回 {plans, credibility, provider}。provider ∈ ("qwen", "rules")。
    """
    type_label = SIGNAL_TYPE_LABELS.get(signal_type) or signal_type or "未知"

    if dashscope_client.is_configured():
        user_prompt = (
            f"社情原文：{text[:400]}\n"
            f"信号类型：{type_label}\n"
            f"位置：{geo_name or '未知'}（纬度{latitude}, 经度{longitude}）\n"
            f"紧急度：{urgency_hint or 'medium'}，情绪：{sentiment or '未知'}，"
            f"定位置信度：{confidence if confidence is not None else 0.5}"
        )
        ok, data = dashscope_client.chat_completion(
            messages=[
                {"role": "system", "content": _ADVISORY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        raw_text = dashscope_client.extract_text(data) if ok else None
        parsed = _robust_parse_json(raw_text) if raw_text else None
        validated = _validate_parsed(parsed) if parsed else None
        if validated:
            validated["provider"] = "qwen"
            return validated
        # Qwen 失败/结构不合法 → 落规则引擎

    return {
        "plans": _rule_plans(signal_type),
        "credibility": _rule_credibility(confidence),
        "provider": "rules",
    }
