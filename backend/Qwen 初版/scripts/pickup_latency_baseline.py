#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WP9：weibo 真实通道「系统拾取延迟」历史基线（仅标准库）。

口径（依据 outputs/评委建议优化方案.md 措施 2.d）：
  拾取延迟 = polled_at − created_at（分钟），含轮询周期的固有下界，
  是系统拾取口径而非平台传播口径。

数据来源：2026-08-28 当日本机 weibo-cli 探针记录（data/_weibo_probe.json，20 条
statuses，created_at 跨 22:55:06–23:04:01 +0800）。探针响应体内无拾取时间戳，
取探针落盘文件修改时间（2026-08-28 23:04:19 +08:00）作为拾取时刻的可用最近证据——
该时刻不早于真实拾取时刻，故延迟为**略偏保守的上界估计**。
体验包有效期内的正式基线采样指引见 outputs/评测指标.md §2.8（≤2026-09-04）。

运行：python3 backend/Qwen\\ 初版/scripts/pickup_latency_baseline.py [--polled-at 'YYYY-MM-DD HH:MM:SS']
产物：data/pickup_latency_baseline.json
"""
import argparse
import datetime
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
PROBE_JSON = os.path.join(DATA_DIR, '_weibo_probe.json')
OUT_JSON = os.path.join(DATA_DIR, 'pickup_latency_baseline.json')
CST = datetime.timezone(datetime.timedelta(hours=8))

# 复用 live_feed 同源解析（目录含中文/空格 → importlib 按路径加载）
import importlib.util
_spec = importlib.util.spec_from_file_location(
    'live_feed', os.path.join(os.path.dirname(BASE_DIR), 'live_feed.py'))
lf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lf)


def main():
    ap = argparse.ArgumentParser(description='WP9 拾取延迟历史基线（探针记录重算）')
    ap.add_argument('--polled-at', default=None,
                    help="拾取时刻 'YYYY-MM-DD HH:MM:SS'（北京时间）；缺省取探针文件修改时间")
    args = ap.parse_args()

    if args.polled_at:
        polled_dt = datetime.datetime.strptime(args.polled_at, '%Y-%m-%d %H:%M:%S').replace(tzinfo=CST)
        polled_src = '命令行显式传入'
    else:
        mtime = os.path.getmtime(PROBE_JSON)
        polled_dt = datetime.datetime.fromtimestamp(mtime, CST)
        polled_src = '探针文件修改时间（mtime，延迟为略偏保守的上界估计）'

    with open(PROBE_JSON, encoding='utf-8') as f:
        probe = json.load(f)
    posts = lf._parse_weibo(probe, polled_dt=polled_dt)
    stats = lf._latency_stats(posts)

    result = {
        'generated_at': datetime.datetime.now(CST).isoformat(timespec='seconds'),
        'task': 'WP9 系统拾取延迟历史基线（探针记录重算，非体验期内实采）',
        'probe_source': PROBE_JSON,
        'probe_posts': len(posts),
        'polled_at': polled_dt.isoformat(),
        'polled_at_source': polled_src,
        'latency_stats': stats,
        'created_at_range': [min(p['created_at'] for p in posts),
                             max(p['created_at'] for p in posts)],
        'per_post_latency_min': [{'id': p['id'], 'created_at': p['created_at'],
                                  'latency_min': p['latency_min']} for p in posts],
        'boundary_note': '该延迟含轮询周期，是系统拾取口径而非平台传播口径；'
                         '体验期内（≤2026-09-04）须以 --mode weibo 实采替换本历史基线',
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print('探针帖数：%d | 拾取时刻：%s（%s）' % (len(posts), polled_dt.isoformat(), polled_src))
    print('发布时间区间：%s → %s' % tuple(result['created_at_range']))
    print('latency_stats：n=%d median=%.1f min p90=%.1f min' % (
        stats['n'], stats['median_min'], stats['p90_min']))
    print('产物：%s' % OUT_JSON)


if __name__ == '__main__':
    main()
