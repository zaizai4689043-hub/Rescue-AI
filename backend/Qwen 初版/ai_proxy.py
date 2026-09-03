#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RescueAI 本地零依赖代理：静态托管演示页 + DashScope 转发 + USGS 震情转发（仅标准库）"""
import hashlib
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_REAL = os.path.realpath(BASE_DIR)
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), '.env')
DASHSCOPE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
USGS_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson'
# ICL 地震预警列表（成都高新减灾研究所，免鉴权）；start_at/updates 为必带参数，缺失会返回 {"code":-1,"字段错误"}
ICL_URL = 'https://mobile-new.chinaeew.cn/v1/earlywarnings?start_at=&updates='
ICL_SNAPSHOT = os.path.join(BASE_DIR, 'data', 'icl_warnings_snapshot.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) RescueAI-LocalProxy/1.0'

_ai_cache = {}          # key=(model, payload_hash) -> (ts, bytes)
_seismic_cache = {'ts': 0.0, 'data': None}
_icl_cache = {'ts': 0.0, 'data': None}   # /icl/warnings 内存缓存（ts/data，同 _seismic_cache 约定）

MAX_BODY = 2 * 1024 * 1024          # POST /ai/proxy 请求体上限 2MB，防无上限读取 OOM
CACHE_TTL = 60                      # AI 响应缓存有效期（秒）
CACHE_MAX = 200                     # 缓存条目上限，超出删最旧
ORIGIN_RE = re.compile(r'^http://(127\.0\.0\.1|localhost)(:\d+)?$')  # 仅本机来源
# 前端可透传给 DashScope 的参数白名单（其余请求体参数仍丢弃）；
# enable_thinking 默认代理侧注入 false（qwen3.8/3.7 默认思考模式响应慢，易触发前端超时）
PASS_KEYS = ('enable_thinking', 'temperature', 'response_format')

# 快照文件也读取失败时的内嵌最小样例（ICL 字段格式，带 offline 兜底标识）
OFFLINE_ICL = {
    "code": 0, "message": "",
    "offline": True,   # 兜底标识：前端据此把标签改为「离线快照数据」
    "data": [
        {"eventId": 1784356492, "epicenter": "四川宜宾市高县", "magnitude": 5.1,
         "depth": 5, "epiIntensity": 7, "startAt": 1785694905000, "updates": 2, "sourceType": 1},
        {"eventId": 1784356491, "epicenter": "新疆阿克苏地区乌什县", "magnitude": 4.6,
         "epiIntensity": 6, "startAt": 1785305399100, "updates": 3, "sourceType": 2},
        {"eventId": 1784343985, "epicenter": "新疆克孜勒苏州阿克陶县", "magnitude": 4.4,
         "epiIntensity": 5.6, "startAt": 1784353639800, "updates": 2, "sourceType": 2},
    ],
}


def _icl_snapshot():
    """读取 data/icl_warnings_snapshot.json 快照并附加 offline:true；失败回落内嵌最小样例"""
    try:
        with open(ICL_SNAPSHOT, encoding='utf-8') as f:
            snap = json.load(f)
        if not snap.get('data'):
            raise ValueError('快照 data 为空')
        snap['offline'] = True
        return snap
    except Exception as e:
        print('[icl] 快照读取失败，回落内嵌样例:', e)
        return OFFLINE_ICL


OFFLINE_QUAKE = {  # 断网 / 上游异常时的内嵌离线样例（USGS GeoJSON 格式）
    "type": "FeatureCollection",
    "offline": True,   # 兜底标识：前端据此把标签改为「离线样例数据」
    "metadata": {"generated": 0, "title": "USGS Earthquakes (offline sample)",
                 "status": 200, "count": 4, "api": "offline"},
    "features": [
        {"type": "Feature", "id": "sample001", "properties": {
            "mag": 4.2, "place": "San Juan Bautista, CA", "time": 1672555748370,
            "type": "earthquake", "sig": 271, "title": "M 4.2 - San Juan Bautista, CA"},
         "geometry": {"type": "Point", "coordinates": [-121.199, 36.595, 8.4]}},
        {"type": "Feature", "id": "sample002", "properties": {
            "mag": 3.1, "place": "10km SW of Idyllwild, CA", "time": 1672554912000,
            "type": "earthquake", "sig": 148, "title": "M 3.1 - 10km SW of Idyllwild, CA"},
         "geometry": {"type": "Point", "coordinates": [-116.766, 33.700, 14.2]}},
        {"type": "Feature", "id": "sample003", "properties": {
            "mag": 2.7, "place": "12km NE of Ridgecrest, CA", "time": 1672553500120,
            "type": "earthquake", "sig": 112, "title": "M 2.7 - 12km NE of Ridgecrest, CA"},
         "geometry": {"type": "Point", "coordinates": [-117.590, 35.697, 6.1]}},
        {"type": "Feature", "id": "sample004", "properties": {
            "mag": 3.6, "place": "8km W of Cobb, CA", "time": 1672552870450,
            "type": "earthquake", "sig": 199, "title": "M 3.6 - 8km W of Cobb, CA"},
         "geometry": {"type": "Point", "coordinates": [-122.770, 38.820, 2.9]}},
    ],
}


def load_api_key():
    """从 backend/.env 简单字符串解析 DASHSCOPE_API_KEY（不在日志中输出明文）"""
    try:
        with open(ENV_PATH, encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^\s*DASHSCOPE_API_KEY\s*=\s*(.+?)\s*$', line)
                if m:
                    return m.group(1).strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def _cache_put(key, data):
    """写缓存：顺带清理过期项；总条数超限时删最旧（防只写不清的内存泄漏）"""
    now = time.time()
    for k in [k for k, (ts, _) in _ai_cache.items() if now - ts >= CACHE_TTL]:
        del _ai_cache[k]
    if len(_ai_cache) >= CACHE_MAX:
        oldest = min(_ai_cache, key=lambda k: _ai_cache[k][0])
        del _ai_cache[oldest]
    _ai_cache[key] = (now, data)


def http_get(url, timeout=25, as_json=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})  # 不带 Accept-Encoding，避免 gzip 未解压
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode('utf-8')) if as_json else raw


class Handler(BaseHTTPRequestHandler):
    server_version = 'RescueAIProxy/1.0'

    def log_message(self, fmt, *args):
        print('[%s] %s' % (self.address_string(), fmt % args))

    # ---------- CORS / Origin 校验 ----------
    def _origin_allowed(self):
        origin = self.headers.get('Origin')
        if not origin:
            return True   # 无 Origin（curl / 部分同源请求）放行
        return bool(ORIGIN_RE.match(origin))

    def _cors(self):
        origin = self.headers.get('Origin')
        if origin and ORIGIN_RE.match(origin):
            self.send_header('Access-Control-Allow-Origin', origin)   # 回显校验过的 Origin，不再用 *
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        if not self._origin_allowed():
            return self._send(403, {'error': 'forbidden origin'}, 'application/json')
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _send(self, code, body, ctype):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    # ---------- 路由 ----------
    def do_GET(self):
        path = urllib.parse.unquote(self.path).split('?', 1)[0]
        if path == '/seismic/feed':
            if not self._origin_allowed():
                return self._send(403, {'error': 'forbidden origin'}, 'application/json')
            return self._seismic()
        if path == '/icl/warnings':
            if not self._origin_allowed():
                return self._send(403, {'error': 'forbidden origin'}, 'application/json')
            return self._icl()
        self._static(path)

    def do_POST(self):
        path = urllib.parse.unquote(self.path).split('?', 1)[0]
        if path == '/drone/telemetry':
            # T14：真机遥测接入桩（Not Implemented）。预留接口，不读请求体、不碰现有路由；
            # 真机接入时替换为解析 DRONE_TELEMETRY_SCHEMA 帧并转发至前端 applyTelemetry()。
            return self._send(501, {'status': 'stub', 'message': '真机遥测接入点，支持大疆 Cloud API / MAVLink 转发，schema 见前端 DRONE_TELEMETRY_SCHEMA'}, 'application/json')
        if path != '/ai/proxy':
            return self._send(404, {'error': 'not found'}, 'application/json')
        if not self._origin_allowed():
            return self._send(403, {'error': 'forbidden origin'}, 'application/json')
        try:
            length = int(self.headers.get('Content-Length', 0))
        except (TypeError, ValueError):
            length = -1
        if length <= 0 or length > MAX_BODY:
            return self._send(400, {'error': '请求体缺失或超过 %d 字节上限' % MAX_BODY}, 'application/json')
        try:
            body = json.loads(self.rfile.read(length).decode('utf-8'))
            model = body.get('model') or 'qwen3.8-max'
            messages = body.get('messages')
            if not isinstance(messages, list) or not messages:
                raise ValueError('messages 缺失或格式错误')
            extra = {k: body[k] for k in PASS_KEYS if k in body}   # 白名单参数透传
            nocache = (self.headers.get('X-AI-Nocache') == '1')    # 前端换图/上传新图时强制绕过内存缓存，发起真实重判；响应仍写入缓存（同图后续命中省配额）
            return self._ai_proxy(model, messages, extra, nocache)
        except Exception as e:
            return self._send(200, {'fallback': True, 'reason': str(e)[:200]}, 'application/json')

    # ---------- /ai/proxy ----------
    def _ai_proxy(self, model, messages, extra, nocache=False):
        key = load_api_key()
        if not key:
            return self._send(200, {'fallback': True, 'reason': '.env 中未找到 DASHSCOPE_API_KEY'}, 'application/json')
        extra.setdefault('enable_thinking', False)   # 默认关思考（前端显式传 true 时才保留）
        payload = json.dumps({'model': model, 'messages': messages, **extra}, ensure_ascii=False).encode('utf-8')
        cache_key = (model, hashlib.sha256(payload).hexdigest())
        if not nocache:
            hit = _ai_cache.get(cache_key)
            if hit and time.time() - hit[0] < CACHE_TTL:
                return self._send(200, hit[1], 'application/json')  # 内存缓存
        try:
            req = urllib.request.Request(
                DASHSCOPE_URL, data=payload, method='POST',
                headers={'Content-Type': 'application/json',
                         'Authorization': 'Bearer ' + key, 'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read()
            data = json.loads(raw.decode('utf-8'))
            if not data.get('choices'):
                raise ValueError('上游响应缺少 choices')
            _cache_put(cache_key, data)
            self._send(200, data, 'application/json')
        except Exception as e:
            self._send(200, {'fallback': True, 'reason': str(e)[:200]}, 'application/json')

    # ---------- /seismic/feed ----------
    def _seismic(self):
        now = time.time()
        if _seismic_cache['data'] is not None and now - _seismic_cache['ts'] < 300:
            return self._send(200, _seismic_cache['data'], 'application/json')
        try:
            data = http_get(USGS_URL, timeout=25, as_json=True)
            if not data.get('features'):
                raise ValueError('上游返回空 features')
            _seismic_cache.update(ts=now, data=data)
            self._send(200, data, 'application/json')
        except Exception as e:
            print('[seismic] 回退离线样例:', e)
            self._send(200, OFFLINE_QUAKE, 'application/json')

    # ---------- /icl/warnings（ICL 地震预警，仿 /seismic/feed 模式） ----------
    def _icl(self):
        now = time.time()
        if _icl_cache['data'] is not None and now - _icl_cache['ts'] < 300:   # 300s 内存缓存
            return self._send(200, _icl_cache['data'], 'application/json')
        try:
            data = http_get(ICL_URL, timeout=10, as_json=True)   # http_get 不带 Accept-Encoding，避免 gzip
            if data.get('code') != 0 or not isinstance(data.get('data'), list) or not data['data']:
                raise ValueError('上游返回 code=%s 或空 data' % data.get('code'))
            _icl_cache.update(ts=now, data=data)
            self._send(200, data, 'application/json')
        except Exception as e:
            print('[icl] 回退快照:', e)
            self._send(200, _icl_snapshot(), 'application/json')

    # ---------- 静态托管（白名单：演示页 + assets/ vendor/ data/ 前缀） ----------
    MAIN_PAGE = '代码1.2-ai.html'
    STATIC_WHITELIST = ('assets/', 'vendor/', 'data/')

    def _static(self, path):
        if path == '/':
            path = '/' + self.MAIN_PAGE
        rel = path.lstrip('/')
        if rel != self.MAIN_PAGE and not rel.startswith(self.STATIC_WHITELIST):
            return self._send(403, {'error': 'forbidden'}, 'application/json')
        fs = os.path.realpath(os.path.join(BASE_REAL, rel))
        rel2 = os.path.relpath(fs, BASE_REAL).replace(os.sep, '/')
        # realpath 规范化后二次校验白名单，防 vendor/../scripts/... 之类路径绕过
        if rel2.startswith('..') or (rel2 != self.MAIN_PAGE and not rel2.startswith(self.STATIC_WHITELIST)):
            return self._send(403, {'error': 'forbidden'}, 'application/json')
        if not os.path.isfile(fs):
            return self._send(404, {'error': 'not found'}, 'application/json')
        ctype = mimetypes.guess_type(fs)[0] or 'application/octet-stream'
        if ctype.startswith('text/') or ctype == 'application/javascript':
            ctype += '; charset=utf-8'
        with open(fs, 'rb') as f:
            self._send(200, f.read(), ctype)


if __name__ == '__main__':
    host = os.environ.get('RESCUE_AI_PROXY_HOST', '127.0.0.1')   # 默认仅回环；确需投屏设备访问时显式设 RESCUE_AI_PROXY_HOST=0.0.0.0
    port = int(os.environ.get('RESCUE_AI_PROXY_PORT', '8010'))   # 避开 FastAPI 后端的 8000 端口
    print('RescueAI 本地代理启动: http://%s:%d/' % (host, port))
    print('演示页: http://%s:%d/    AI 代理: POST /ai/proxy    震情: GET /seismic/feed    ICL 预警: GET /icl/warnings    真机遥测(桩): POST /drone/telemetry' % (host, port))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
