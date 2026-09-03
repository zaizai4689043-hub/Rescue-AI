"""社情平台化适配层（Task #6 折中方案）。

设计意图（对齐《work buddy接力/架构设计.md》数据采集层）：
各社媒平台的接入差异收敛到 PlatformAdapter 之后，上层（入库/检索/热力图）
只消费统一事件 schema（UnifiedSocialEvent），不感知平台细节。

实时链路现状：复赛前实时拉取仍由 8012 端口独立服务
`backend/Qwen 初版/live_feed.py` 承担；本层不做后台预取，
仅提供架构证据（统一 schema + 适配器接口）与离线回填入库能力。
"""
from app.services.social.adapters import (
    GeoPoint,
    UnifiedSocialEvent,
    PlatformAdapter,
    PlatformDegradedResult,
    SignalType,
    SIGNAL_TYPE_LABELS,
    normalize_signal_type,
    derive_urgency,
    make_raw_ref,
)
from app.services.social.weibo_adapter import WeiboAdapter
from app.services.social.service import ingest_event, batch_ingest

__all__ = [
    "GeoPoint",
    "UnifiedSocialEvent",
    "PlatformAdapter",
    "PlatformDegradedResult",
    "SignalType",
    "SIGNAL_TYPE_LABELS",
    "normalize_signal_type",
    "derive_urgency",
    "make_raw_ref",
    "WeiboAdapter",
    "ingest_event",
    "batch_ingest",
]
