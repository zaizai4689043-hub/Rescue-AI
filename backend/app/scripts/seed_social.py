#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""社情离线回填脚本：把已清洗的种子数据回填进标准后端 social_posts 表。

数据来源（以实际存在者为准）：
    backend/Qwen 初版/data/social_posts.json（缅甸 7.9 级地震社情样本，约 52 条，
    已完成匿名化：不含发布者昵称/UID）。

运行方式（须在 backend 目录下，DATABASE_URL 为相对路径）：
    python -m app.scripts.seed_social

幂等：按 raw_ref 哈希去重，重复运行不会产生重复记录。
"""
import json
import os
from datetime import datetime
from typing import List

from app.database import Base, SessionLocal, engine
from app.models.social_post import SocialPost  # noqa: F401  注册模型
from app.services.social import batch_ingest
from app.services.social.adapters import (
    GeoPoint,
    UnifiedSocialEvent,
    derive_urgency,
    make_raw_ref,
    normalize_signal_type,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# backend/app/scripts/ → backend/Qwen 初版/data/social_posts.json
SEED_JSON = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "Qwen 初版", "data", "social_posts.json")
)


def _seed_to_event(p: dict, idx: int) -> UnifiedSocialEvent | None:
    """种子记录 → 统一事件（字段映射与隐私口径同 live_feed mock 通道）"""
    text = (p.get("text") or "").strip()
    if not text:
        return None
    post_id = str(p.get("post_id") or f"seed-{idx}")
    loc = p.get("extracted_location") or {}
    lat, lng = loc.get("latitude"), loc.get("longitude")
    geo = None
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        geo = GeoPoint(latitude=float(lat), longitude=float(lng), name=loc.get("name"))
    ts = None
    if p.get("time"):
        try:
            ts = datetime.fromisoformat(str(p["time"]))
        except ValueError:
            ts = None
    signal = normalize_signal_type(p.get("damage_type"))
    severity = p.get("severity_vote")
    return UnifiedSocialEvent(
        event_id=f"weibo-{post_id}",
        platform="weibo",                      # 种子数据全部来自微博（匿名化）
        raw_ref=make_raw_ref("weibo", post_id, text),
        text=text,
        ts=ts,
        geo=geo,
        signal_type=signal,
        confidence=loc.get("confidence"),
        urgency_hint=derive_urgency(signal, severity),
        tags=[k for k in (p.get("keywords_matched") or []) if k][:6],
        offset_min=p.get("offset_after_quake_min"),
        sentiment=p.get("sentiment"),
    )


def main():
    if not os.path.isfile(SEED_JSON):
        raise SystemExit(f"种子数据不存在: {SEED_JSON}")
    with open(SEED_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list) or not raw:
        raise SystemExit("种子数据为空")

    events: List[UnifiedSocialEvent] = []
    for i, p in enumerate(raw):
        ev = _seed_to_event(p, i) if isinstance(p, dict) else None
        if ev is not None:
            events.append(ev)

    Base.metadata.create_all(bind=engine)      # 确保 social_posts 表存在
    db = SessionLocal()
    try:
        summary = batch_ingest(db, events)
    finally:
        db.close()
    print("[seed_social] 回填完成:", json.dumps(summary, ensure_ascii=False))
    print(f"[seed_social] 种子文件: {SEED_JSON}")


if __name__ == "__main__":
    main()
