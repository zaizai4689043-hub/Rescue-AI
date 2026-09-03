#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T16 子任务A：用真实 Key 经本地代理预跑「AI 复盘参谋」，录制 FALLBACK_RESULTS.review 预录文案
prompt 与前端 reviewPrompt() 完全一致；用一次典型演示收尾快照预录。"""
import json, time, urllib.request

PROXY = 'http://127.0.0.1:8010/ai/proxy'

# 与前端 reviewPrompt(st) 一致；st 取一次典型完整演示快照
st = {'found': 8, 'rescued': 4, 'cover': 100,
      'struct': '结构研判：损毁等级倒塌、承重构件3处、疑似生存空隙2处、结构完整度约25%', 'rpDone': 4}
prompt = ('你是地震救援复盘参谋。本次演练统计：已发现被困 ' + str(st['found']) + ' 人、已成功营救 ' + str(st['rescued'])
          + ' 人、搜索覆盖率 ' + str(st['cover']) + '%、' + st['struct'] + '、历史重演完成 ' + str(st['rpDone'])
          + '/4 段。请用不超过150字总结「如果地震再来一次，AI 能做什么」。基调克制务实，AI 定位为救援者的辅助与提速，'
          '致敬一线救援者，不夸大、不替代专业判断。只返回总结文本。')

body = {'model': 'qwen3.8-max', 'messages': [{'role': 'user', 'content': prompt}]}
t0 = time.time()
req = urllib.request.Request(PROXY, data=json.dumps(body).encode(),
                             headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read().decode())
print('latency=%.2fs' % (time.time() - t0))
if data.get('fallback'):
    print('FALLBACK:', data.get('reason'))
else:
    txt = data['choices'][0]['message']['content'].strip().strip('"')
    print('LEN=%d 字' % len(txt))
    print('REVIEW_TEXT_START')
    print(txt)
    print('REVIEW_TEXT_END')
