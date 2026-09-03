# -*- coding: utf-8 -*-
"""
fetch_aftershocks.py — 抓取 2025-03-28 缅甸主震后 2 小时余震目录(USGS ComCat)

产出: data/aftershocks.json
  - mainshock: 主震参数(窗口内第一条 M7.7, 单独存)
  - aftershocks: [[震后分钟偏移, mag, lon, lat], ...] (剔除主震)
  - meta: 口径说明与统计

零依赖(仅 urllib), 幂等可重复运行。
"""

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
OUT_PATH = os.path.join(DATA_DIR, "aftershocks.json")

# 震后前 2 小时窗口(UTC), 震中 300km 内 M>=4, 按时间升序
API_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson"
    "&starttime=2025-03-28T06:20:00"
    "&endtime=2025-03-28T08:25:00"
    "&latitude=22.05&longitude=95.84&maxradiuskm=300"
    "&minmagnitude=4&orderby=time"
)
TIMEOUT = 60


def parse_iso(ts):
    """解析 USGS 时间: geojson 中为 epoch 毫秒(int), 兼容 ISO8601 字符串。"""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))


def format_bj(dt_utc):
    """UTC datetime -> 北京时间字符串(不依赖 zoneinfo)。"""
    return (dt_utc + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def main():
    print(f"[请求] {API_URL}")
    req = urllib.request.Request(API_URL, headers={"User-Agent": "RescueAI-demo/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        payload = json.load(resp)

    feats = payload.get("features", [])
    total = len(feats)
    print(f"[返回] {total} 条事件")
    if total == 0:
        raise SystemExit("USGS 返回 0 条, 请检查网络或时间窗口")

    # 主震识别: 窗口内最大震级事件(M7.7)。orderby=time 返回降序,
    # 按最大震级定位对升/降序均鲁棒。
    ms = max(feats, key=lambda f: f["properties"]["mag"])
    if ms["properties"]["mag"] < 7.0:
        raise SystemExit("窗口内未找到 M>=7 主震, 请检查查询参数")
    ms_p = ms["properties"]
    ms_t = parse_iso(ms_p["time"])
    mainshock = {
        "event_id": ms["id"],
        "time_utc": ms_t.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_bj": format_bj(ms_t),
        "mag": ms_p["mag"],
        "lon": round(ms["geometry"]["coordinates"][0], 3),
        "lat": round(ms["geometry"]["coordinates"][1], 3),
        "depth_km": round(ms["geometry"]["coordinates"][2], 1),
        "place": ms_p.get("place"),
    }
    print(f"[主震] M{mainshock['mag']} @ {mainshock['time_bj']} (北京) {mainshock['event_id']}")

    # 剔除主震, 其余按时间升序转为 [震后分钟偏移, mag, lon, lat]
    rest = sorted((f for f in feats if f["id"] != ms["id"]),
                  key=lambda f: f["properties"]["time"])
    aftershocks = []
    for f in rest:
        p = f["properties"]
        t = parse_iso(p["time"])
        offset_min = round((t - ms_t).total_seconds() / 60.0, 1)
        lon, lat, _ = f["geometry"]["coordinates"]
        aftershocks.append([offset_min, p["mag"], round(lon, 3), round(lat, 3)])

    out = {
        "mainshock": mainshock,
        "aftershocks": aftershocks,
        "meta": {
            "catalog": "USGS ComCat (FDSN Event API, format=geojson)",
            "window_utc": "2025-03-28T06:20:00 ~ 08:25:00 (主震后约2小时)",
            "filter": "震中(22.05°N,95.84°E)300km内, M>=4.0, 按时间升序",
            "offset_basis": "分钟偏移相对主震发震时刻",
            "total_events_in_window": total,
            "aftershocks_output": len(aftershocks),
            "note": "主震已剔除并单独存于 mainshock 字段; 深度单位km",
        },
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(OUT_PATH)
    print(f"[产出] {OUT_PATH} ({len(aftershocks)} 条余震, {size} bytes)")
    for a in aftershocks:
        print(f"  +{a[0]:>6}min  M{a[1]}  ({a[3]}, {a[2]})")


if __name__ == "__main__":
    main()
