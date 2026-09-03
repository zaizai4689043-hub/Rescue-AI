#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T16 子任务B：真实 Key 经本地代理测量 Qwen-VL 结构研判延迟 + 校验 JSON 输出
用法: python3 t16_vl_latency.py [图片路径] [轮次]  （默认 building_a.jpg，1 轮）"""
import base64, json, sys, time, urllib.request

PROXY = 'http://127.0.0.1:8010/ai/proxy'
BASE = '/Users/zaizai/Downloads/AI地震救援/backend/Qwen 初版/assets/'
# 与前端 AI.assessBuildings 完全一致的 prompt，保证语义可比
PROMPT = ('你是建筑结构专家。这是缅甸曼德勒 2025 年 7.9 级地震后的真实震后建筑现场影像，'
          '请做震后建筑损毁评估（评估倒塌程度、承重构件、可能的生存空隙与危险等级）：'
          'columns=画面中可见的竖向承重构件（柱、角柱、主要承重墙）数量(整数)；'
          'voids=倒塌废墟中可能形成生存空隙的空间数(整数)；'
          'match_rate=建筑轮廓可辨识、可与原始形制比对的程度(0-100)；'
          'integrity=当前结构完整度(0-100)；damage_level=损毁等级：轻微|中等|严重|倒塌；'
          'confidence(0-1)；rescue_advice=40字内中文救援建议（结合曼德勒砖混结构特点与危险等级）。只返回严格 JSON。')

def run(img, rounds):
    with open(img, 'rb') as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode()
    body = {'model': 'qwen3.7-plus',
            'messages': [{'role': 'user', 'content': [
                {'type': 'text', 'text': PROMPT},
                {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}]}]}
    data_bytes = json.dumps(body).encode()
    lat = []
    for r in range(rounds):
        t0 = time.time()
        req = urllib.request.Request(PROXY, data=data_bytes, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        dt = time.time() - t0
        lat.append(dt)
        if data.get('fallback'):
            print('[%s] round%d FALLBACK: %s' % (img.split('/')[-1], r, data.get('reason')))
            continue
        txt = data['choices'][0]['message']['content']
        i, j = txt.find('{'), txt.rfind('}')
        try:
            obj = json.loads(txt[i:j + 1])
            print('[%s] round%d latency=%.2fs JSON_OK damage_level=%s columns=%s voids=%s match_rate=%s integrity=%s'
                  % (img.split('/')[-1], r, dt, obj.get('damage_level'), obj.get('columns'), obj.get('voids'), obj.get('match_rate'), obj.get('integrity')))
        except Exception as e:
            print('[%s] round%d latency=%.2fs PARSE_FAIL: %s RAW=%s' % (img.split('/')[-1], r, dt, e, txt[:200]))
    if lat:
        print('[%s] 平均延迟=%.2fs  最小=%.2fs  最大=%.2fs' % (img.split('/')[-1], sum(lat)/len(lat), min(lat), max(lat)))

if __name__ == '__main__':
    img = sys.argv[1] if len(sys.argv) > 1 else (BASE + 'building_a.jpg')
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    run(img, rounds)
