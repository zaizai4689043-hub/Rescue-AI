#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T13：把 data/supply_needs.json 与 data/lost_contact.json 内嵌为 JS 常量注入演示页（零 fetch）"""
import io, json, os

BASE = '/Users/zaizai/Downloads/AI地震救援/backend/Qwen 初版'
HTML = os.path.join(BASE, '代码1.2-ai.html')

def compact(path):
    with io.open(path, encoding='utf-8') as f:
        return json.dumps(json.load(f), ensure_ascii=False, separators=(',', ':'))

supply = compact(os.path.join(BASE, 'data', 'supply_needs.json'))
lost = compact(os.path.join(BASE, 'data', 'lost_contact.json'))

block = ('/* ================= T13：物资需求信号与失联信号真实数据（data/supply_needs.json · data/lost_contact.json，零 fetch） ================= */\n'
         '/* 微博数据集（匿名化）：20 条物资需求信号（六类聚合 stats + 三个援助锚点 aid_anchors）；15 条失联/通讯中断帖（pinned_case=2500 学生失联案例） */\n'
         'const SUPPLY_NEEDS=' + supply + ';\n'
         'const LOST_CONTACT=' + lost + ';\n'
         '/* ================= T13 内嵌数据结束 ================= */\n')

with io.open(HTML, encoding='utf-8') as f:
    html = f.read()

marker = '/* ================= T12 内嵌数据结束 ================= */\n'
assert html.count(marker) == 1, 'marker not unique'
if 'const SUPPLY_NEEDS=' in html:
    print('already injected, skip')
else:
    html = html.replace(marker, marker + block, 1)
    with io.open(HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print('injected OK, block bytes:', len(block))
