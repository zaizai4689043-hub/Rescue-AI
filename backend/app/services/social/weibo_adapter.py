"""微博平台适配器：移植自 `backend/Qwen 初版/live_feed.py` 已实测的
`_resolve_weibo_bin / _weibo_fetch / _parse_weibo / _parse_created`（复用对象，逻辑保持一致），
输出归一化为 UnifiedSocialEvent。

隐私约定（与 live_feed 一致）：丢弃发布者昵称/UID 等字段，仅保留正文、时间与话题词。
注意：本适配器不在标准后端内起后台预取线程；实时轮询仍由 8012 端口
`live_feed.py` 承担，这里只提供可被编排调用的同步 pull/degrade。
"""
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from app.services.social.adapters import (
    GeoPoint,
    PlatformAdapter,
    PlatformDegradedResult,
    SignalType,
    UnifiedSocialEvent,
    derive_urgency,
    make_raw_ref,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TZ_CST = timezone(timedelta(hours=8))          # 北京时间（与 live_feed/演示页 time 字段口径一致）
WEIBO_TIMEOUT = 25                             # weibo-cli 调用超时（秒）
MAX_POSTS = 50                                 # 单次拉取帖数上限


def _resolve_weibo_bin() -> str:
    """稳健解析 weibo 可执行文件：优先 PATH（shutil.which），回退仓库内本地安装路径"""
    found = shutil.which("weibo")
    if found:
        return found
    # backend/app/services/social/ → 仓库根（路径含中文，不用 pathlib parents 缩写）
    repo_root = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", ".."))
    local = os.path.join(repo_root, "weibo-cli", "node_modules", ".bin", "weibo")
    if os.path.isfile(local) and os.access(local, os.X_OK):
        return local
    return "weibo"                             # 都不在 → 保持裸命令，交由 FileNotFoundError 降级链处理


def _parse_created(v) -> Optional[datetime]:
    """防御性解析 weibo-cli 的 created_at：先尝试常见格式（epoch 秒/毫秒、ISO、
    微博原生 %a %b %d %H:%M:%S %z %Y 等），成功统一转北京时间的 naive datetime；
    全部失败返回 None（由上层决定回落口径）"""
    if isinstance(v, (int, float)) and v > 0:
        ts = v / 1000 if v > 1e12 else v
        try:
            return datetime.fromtimestamp(ts, TZ_CST).replace(tzinfo=None)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(v, str) and v.strip():
        s = v.strip()
        cands = []
        try:                                   # epoch 秒/毫秒的字符串形态
            fv = float(s)
            if fv > 0:
                cands.append(datetime.fromtimestamp(fv / 1000 if fv > 1e12 else fv, TZ_CST))
        except (ValueError, OverflowError, OSError):
            pass
        try:                                   # ISO 8601
            cands.append(datetime.fromisoformat(s))
        except ValueError:
            pass
        for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                cands.append(datetime.strptime(s, fmt))
                break
            except ValueError:
                continue
        for dt in cands:
            try:
                return dt.astimezone(TZ_CST).replace(tzinfo=None)
            except (OverflowError, OSError, ValueError):
                continue
    return None


def _parse_weibo(data) -> List[dict]:
    """防御性解析 weibo search statuses/limited --output json：
    字段假设——外层 dict 时取 data/statuses/items/list 其一，本身为 list 直接用；
    单帖必须有 id + text（raw_text/text/long_text/content 任一），缺任一即跳过该条；
    隐私：丢弃 user/screen_name/uid 等发布者字段，仅保留文本与时间；按 id 去重、上限 50 条"""
    if isinstance(data, dict):
        rows = None
        for k in ("data", "statuses", "items", "list", "cards", "result"):
            v = data.get(k)
            if isinstance(v, list):
                rows = v
                break
            if isinstance(v, dict):            # data 可能再套一层 {statuses:[...]}
                for k2 in ("statuses", "items", "list", "cards"):
                    if isinstance(v.get(k2), list):
                        rows = v[k2]
                        break
                if rows is not None:
                    break
        if rows is None:
            raise ValueError("未识别的 weibo-cli 顶层结构: %s" % sorted(data.keys())[:8])
    elif isinstance(data, list):
        rows = data
    else:
        raise ValueError("weibo-cli 输出非 JSON 对象/数组")
    seen, out = set(), []
    for r in rows:
        if not isinstance(r, dict):
            continue
        pid = r.get("id") or r.get("idstr") or r.get("mid")
        text = r.get("text") or r.get("raw_text") or r.get("long_text") or r.get("content")
        if not pid or not text:
            continue                           # 字段缺失即跳过该条
        pid = str(pid)
        if pid in seen:
            continue
        seen.add(pid)
        # tags：话题词（#…#）与来源关键词的防御性合并
        tags = list(r.get("topics") or [])
        if isinstance(r.get("keywords"), list):
            tags += r.get("keywords")
        if not tags:                           # 上游无话题词时从文本提取 #话题#
            tags = re.findall(r"#(.+?)#", str(text))
        out.append({
            "id": pid,
            "text": str(text).strip(),
            "created_at": _parse_created(r.get("created_at")),
            "tags": [str(t) for t in tags if t][:6],
        })
        if len(out) >= MAX_POSTS:
            break
    return out


def _weibo_fetch(q: str, limit: int = 20) -> List[dict]:
    """subprocess 调 weibo-cli（带超时与异常捕获）；缺失/未认证/失败抛异常由上层降级"""
    # --count：帮助文档标称上限 50，服务端实际强制 ≤20（COUNT_EXCEEDS_MAX，2026-08 实测）
    count = max(1, min(int(limit), 20))
    cmd = [_resolve_weibo_bin(), "search", "statuses/limited", "--q", q, "--type", "1",
           "--count", str(count), "--output", "json"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=WEIBO_TIMEOUT)
    except FileNotFoundError:
        raise RuntimeError("weibo-cli 未安装或不在 PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError("weibo-cli 调用超时(>%ds)" % WEIBO_TIMEOUT)
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", "ignore").strip()
        if "auth" in err.lower() or "login" in err.lower() or "token" in err.lower():
            raise RuntimeError("weibo-cli 未认证: " + err[:120])
        raise RuntimeError("weibo-cli 退出码 %d: %s" % (r.returncode, err[:120]))
    try:
        data = json.loads(r.stdout.decode("utf-8", "ignore"))
    except json.JSONDecodeError:
        raise RuntimeError("weibo-cli 输出非合法 JSON")
    posts = _parse_weibo(data)
    if not posts:
        raise RuntimeError("weibo-cli 返回 0 条可解析帖")
    return posts


class WeiboAdapter(PlatformAdapter):
    """微博适配器：weibo-cli 真实检索 → 统一事件。
    失败不吞异常，由调用方捕获后走 degrade()。"""

    platform = "weibo"

    def pull(self, keyword: str, limit: int = 20) -> List[UnifiedSocialEvent]:
        rows = _weibo_fetch(keyword, limit=limit)
        events: List[UnifiedSocialEvent] = []
        for p in rows:
            pid, text = p["id"], p["text"]
            raw_ref = make_raw_ref(self.platform, pid, text)
            events.append(UnifiedSocialEvent(
                event_id=f"{self.platform}-{pid}",
                platform=self.platform,
                raw_ref=raw_ref,
                text=text,
                ts=p["created_at"],           # 真实帖时间可能解析失败 → None
                geo=None,                     # weibo-cli 检索结果无可靠地理字段
                signal_type=SignalType.unknown,  # 信号分类交给离线 NLP 层，不在采集层臆断
                confidence=None,
                urgency_hint=None,
                tags=p["tags"],
                offset_min=None,              # 真实帖无震后偏移口径
            ))
        return events

    def degrade(self, keyword: str, error: Exception) -> PlatformDegradedResult:
        """降级出口：声明失败原因、不产出任何帖子（防降级产物污染正式数据，
        与 live_feed 的降级链约定一致；离线兜底数据走 social_posts 回填，不经此路径）"""
        return PlatformDegradedResult(
            platform=self.platform,
            source="none",
            reason=str(error),
            stale=True,
            posts=[],
        )
