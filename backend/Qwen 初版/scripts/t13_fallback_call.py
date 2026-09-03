#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T13：用真实 Key 经本地代理对曼德勒真实倒塌照片跑一次 qwen3.7-plus 震后损毁评估，输出原始响应"""
import base64, json, re, urllib.request

PROXY = 'http://127.0.0.1:8010/ai/proxy'
IMG = '/Users/zaizai/Downloads/AI地震救援/backend/Qwen 初版/assets/building_a.jpg'

PROMPT = ('你是建筑结构专家。这是缅甸曼德勒 2025 年 7.9 级地震后的真实倒塌建筑现场照片。'
          '请做震后建筑损毁评估：columns=画面中可见的竖向承重构件（柱、角柱、主要承重墙）数量(整数)；'
          'voids=倒塌废墟中可能形成生存空隙的空间数(整数)；'
          'match_rate=建筑轮廓可辨识、可与原始形制比对的程度(0-100)；'
          'integrity=当前结构完整度(0-100)；'
          'damage_level=损毁等级：轻微|中等|严重|倒塌；'
          'confidence(0-1)；rescue_advice=40字内中文救援建议（结合曼德勒砖混结构特点）。只返回严格 JSON。')

with open(IMG, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
body = {'model': 'qwen3.7-plus',
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': PROMPT},
            {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}]}]}
req = urllib.request.Request(PROXY, data=json.dumps(body).encode(),
                             headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read().decode())
if data.get('fallback'):
    print('FALLBACK:', data.get('reason'))
else:
    txt = data['choices'][0]['message']['content']
    print('RAW_OUTPUT_START')
    print(txt)
    print('RAW_OUTPUT_END')
    m = re.match(re.compile(r'.*', re.S), txt)
    i, j = txt.find('{'), txt.rfind('}')
    try:
        print('PARSED_JSON:', json.dumps(json.loads(txt[i:j + 1]), ensure_ascii=False))
    except Exception as e:
        print('PARSE_FAIL:', e)
