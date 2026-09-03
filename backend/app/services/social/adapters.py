"""PlatformAdapter 抽象基类与统一社情事件 schema。

统一事件字段（平台无关，上层只消费这一形态）：
    event_id      全局事件标识，形如 "{platform}-{post_id}" 或回退哈希前缀
    platform      来源平台（weibo / douyin / xiaohongshu / ...）
    raw_ref       去重键：sha256("{platform}:{post_id|text}")，入库唯一约束
    text          已做隐私剥离的正文（不含发布者昵称/UID）
    ts            事件时间（北京时间口径，naive datetime）
    geo           经纬度 + 地名（可为空）
    signal_type   信号类型（SignalType 枚举，见下方映射）
    confidence    信号可信度 0-1（地名实体置信度或上游评分）
    urgency_hint  紧急度提示 high / medium / low（派生值，非平台原始字段）
"""
import enum
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SignalType(str, enum.Enum):
    """社情信号类型（与种子数据 damage_type 中文标签一一映射）"""
    casualty = "casualty"                  # 人员伤亡
    building_collapse = "building_collapse"  # 房屋倒塌
    rescue_progress = "rescue_progress"    # 救援进展
    secondary_hazard = "secondary_hazard"  # 次生灾害
    road_blocked = "road_blocked"          # 道路中断
    felt_report = "felt_report"            # 震感反馈
    unknown = "unknown"


SIGNAL_TYPE_LABELS = {
    SignalType.casualty: "人员伤亡",
    SignalType.building_collapse: "房屋倒塌",
    SignalType.rescue_progress: "救援进展",
    SignalType.secondary_hazard: "次生灾害",
    SignalType.road_blocked: "道路中断",
    SignalType.felt_report: "震感反馈",
    SignalType.unknown: "未知",
}

_LABEL_TO_SIGNAL = {v: k for k, v in SIGNAL_TYPE_LABELS.items()}


def normalize_signal_type(raw: Optional[str]) -> SignalType:
    """把上游中文标签/英文值归一到 SignalType；无法识别落 unknown"""
    if not raw:
        return SignalType.unknown
    raw = raw.strip()
    if raw in _LABEL_TO_SIGNAL:
        return _LABEL_TO_SIGNAL[raw]
    try:
        return SignalType(raw)
    except ValueError:
        return SignalType.unknown


def derive_urgency(signal_type: SignalType, severity_vote: Optional[int] = None) -> str:
    """派生紧急度提示：人员伤亡/房屋倒塌天然高优；
    其余按上游 severity_vote（1-5）分档；无评分时给 medium。"""
    if signal_type in (SignalType.casualty, SignalType.building_collapse):
        return "high"
    if severity_vote is None:
        return "medium"
    if severity_vote >= 4:
        return "high"
    if severity_vote <= 1:
        return "low"
    return "medium"


def make_raw_ref(platform: str, post_id: Optional[str], text: str) -> str:
    """去重键：优先平台内 post_id，缺失时回退正文哈希"""
    key = post_id.strip() if post_id and post_id.strip() else text.strip()
    return hashlib.sha256(f"{platform}:{key}".encode("utf-8")).hexdigest()


class GeoPoint(BaseModel):
    """统一地理点（经纬度 + 地名，均可缺省）"""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    name: Optional[str] = None


class UnifiedSocialEvent(BaseModel):
    """统一社情事件：所有平台适配器产出物的唯一形态"""
    event_id: str
    platform: str
    raw_ref: str
    text: str
    ts: Optional[datetime] = None
    geo: Optional[GeoPoint] = None
    signal_type: SignalType = SignalType.unknown
    confidence: Optional[float] = Field(None, ge=0, le=1)
    urgency_hint: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    tags: List[str] = Field(default_factory=list)
    offset_min: Optional[int] = Field(None, description="震后分钟偏移（回放口径，实时帖为 null）")
    sentiment: Optional[str] = None
    extra: Optional[dict] = Field(None, description="平台特有字段的透传位")


class PlatformDegradedResult(BaseModel):
    """降级结果：上游不可用时的兜底说明（与 live_feed 降级链语义一致：
    不污染正式数据，只声明来源与原因）"""
    platform: str
    source: str = Field(description="降级来源标识，如 cache/mock/offline")
    reason: str
    stale: bool = True
    posts: List[UnifiedSocialEvent] = Field(default_factory=list)


class PlatformAdapter(ABC):
    """社媒平台适配器抽象基类。

    契约：
    - pull：同步拉取一次（无内置轮询；轮询/预取由调用方编排，
      标准后端不起后台线程，实时轮询仍在 8012 live_feed 服务）；
    - degrade：pull 失败时的降级出口，返回可解释的兜底结果。
    """

    #: 平台标识（子类必须覆盖）
    platform: str = "unknown"

    @abstractmethod
    def pull(self, keyword: str, limit: int = 20) -> List[UnifiedSocialEvent]:
        """拉取并归一化为统一事件；失败应抛出异常交由 degrade 处理"""
        raise NotImplementedError

    @abstractmethod
    def degrade(self, keyword: str, error: Exception) -> PlatformDegradedResult:
        """pull 失败后的降级出口"""
        raise NotImplementedError


class DouyinAdapter(PlatformAdapter):
    """抖音适配器占位——不实现。

    合规原因：抖音无面向灾情检索的官方开放通道，平台条款禁止
    自建爬虫抓取；在获得官方合作接口前，本项目不接入抖音数据。
    后续若接入，需在本类实现 pull/degrade 并复用统一事件 schema。
    """

    platform = "douyin"

    def pull(self, keyword: str, limit: int = 20) -> List[UnifiedSocialEvent]:
        raise NotImplementedError("抖音无官方通道，禁止自建爬虫，暂不接入")

    def degrade(self, keyword: str, error: Exception) -> PlatformDegradedResult:
        raise NotImplementedError("抖音无官方通道，禁止自建爬虫，暂不接入")


class XiaohongshuAdapter(PlatformAdapter):
    """小红书适配器占位——不实现。

    合规原因：小红书无面向灾情检索的官方开放通道，平台条款禁止
    自建爬虫抓取；在获得官方合作接口前，本项目不接入小红书数据。
    后续若接入，需在本类实现 pull/degrade 并复用统一事件 schema。
    """

    platform = "xiaohongshu"

    def pull(self, keyword: str, limit: int = 20) -> List[UnifiedSocialEvent]:
        raise NotImplementedError("小红书无官方通道，禁止自建爬虫，暂不接入")

    def degrade(self, keyword: str, error: Exception) -> PlatformDegradedResult:
        raise NotImplementedError("小红书无官方通道，禁止自建爬虫，暂不接入")
