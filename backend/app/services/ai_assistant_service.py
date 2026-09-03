"""AI救援助手 - Qwen 优先，预设回答兜底（三层降级链的第二级）。"""
from datetime import datetime

from app.services import dashscope_client

# 救援参谋人设（约束输出简短、专业、可执行）
SYSTEM_PROMPT = (
    "你是 RescueAI 地震救援指挥中心的AI参谋，服务于地震黄金72小时应急指挥。"
    "回答必须专业、简洁（150字以内）、可执行，聚焦灾情研判、资源调度、救援优先级。"
    "不确定时明确说明，不编造具体数字。直接给出结论和建议，不要寒暄。"
)

PRESET_ANSWERS = {
    "哪里最需要救援": (
        "根据当前灾情数据，3号区域（建筑倒塌类灾情最密集）需要优先救援，"
        "预计受困人数20-50人。建议优先派遣搜救队。"
    ),
    "最近医疗点": (
        "最近的医疗点位于距当前位置约2.3公里的XX医院，目前可接收伤员。已为您规划路线。"
    ),
    "资源调度建议": (
        "当前可用资源：物资120件、设备45台、救援人员80人。"
        "建议向灾区A调配物资50件、救援人员20人。"
    ),
    "余震风险": (
        "根据历史数据模型分析，未来24小时内发生5级以上余震的概率约为35%。"
        "建议救援人员注意安全防护。"
    ),
    "default": (
        "我是AI地震救援助手，可以回答关于灾情分析、资源调度、救援路线等问题。"
        "请尝试提问：'哪里最需要救援？'、'最近医疗点在哪？'、'资源调度建议'、'余震风险如何？'"
    ),
}

SUGGESTIONS = [
    "哪里最需要救援？",
    "最近医疗点在哪？",
    "资源调度建议",
    "余震风险如何？",
]


def _preset_reply(message: str) -> str:
    """预设关键词匹配回答（降级路径，保留原有引擎）"""
    reply = PRESET_ANSWERS["default"]
    for keyword, answer in PRESET_ANSWERS.items():
        if keyword == "default":
            continue
        if keyword in message:
            reply = answer
            break
    return reply


def get_reply(message: str) -> dict:
    """根据用户消息返回回答：Qwen 优先，任何失败回落预设引擎。

    响应 shape 保持 {reply, timestamp, suggestions} 不变（前端 AIAssistant.vue 依赖），
    新增 provider 字段（"qwen"/"fallback"）供前端显示数据来源角标。
    """
    provider = "fallback"
    reply = _preset_reply(message)

    if dashscope_client.is_configured():
        ok, data = dashscope_client.chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.5,
        )
        text = dashscope_client.extract_text(data) if ok else None
        if text and text.strip():
            reply = text.strip()
            provider = "qwen"

    return {
        "reply": reply,
        "timestamp": datetime.utcnow().isoformat(),
        "suggestions": SUGGESTIONS,
        "provider": provider,
    }
