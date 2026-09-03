#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RescueAI 实时社情层轮询服务（任务5·路径A）：mock 回放 / weibo-cli 真实检索，仅标准库。

输出契约：GET /live/social → {source: "weibo"|"mock"|"cache", polled_at, stale, posts:[{id,text,created_at,tags,live:true,offset_min}], (weibo 模式另附顶层 latency_stats)}
offset_min 口径：mock 帖取自 data/social_posts.json 同 id 记录的震后分钟偏移（数）；weibo 真实帖时间未知 → null，前端按此分流插入。
latency_min 口径（WP9，仅 weibo 模式）：系统拾取延迟 = polled_at − created_at（分钟，保留 1 位小数）；
created_at 解析失败 → null；顶层附 latency_stats:{n, median_min, p90_min}（仅统计非 null 项）。该延迟含轮询周期，是系统拾取口径而非平台传播口径。
weibo 模式：后台预取线程每 --interval 秒调一次 weibo-cli，仅成功时刷缓存；HTTP /live/social 永远秒回当前缓存，
从未成功过则返回 {source:'weibo', posts:[], polled_at, stale:true}——请求内不存在阻塞上游调用的路径；降级产物（缓存兜底/mock）一律不回写缓存，防降级链污染。
mock 模式：请求内即时生成（行为不变）。隐私：丢弃发布者昵称/UID，仅保留文本与时间。
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOCIAL_JSON = os.path.join(BASE_DIR, 'data', 'social_posts.json')
TZ_CST = timezone(timedelta(hours=8))          # 北京时间（与演示页 time 字段口径一致）
MAX_POSTS = 50                                  # 单次响应帖数上限
WEIBO_TIMEOUT = 25                              # weibo-cli 调用超时（秒）
CACHE_TTL = 60                                  # 同参请求内存缓存默认有效期（秒），实际取 --interval；防前端高频轮询打爆上游
MOCK_TICK_SEC = 25                              # mock 模式渐进吐帖节拍（秒/条）
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) RescueAI-LiveFeed/1.0'

_cfg = {'mode': 'mock', 'interval': 30, 'q': '地震'}
_cache = {'ts': 0.0, 'data': None, 'key': None}
_lock = threading.Lock()


def _now_iso():
    return datetime.now(TZ_CST).isoformat(timespec='seconds')


def _mock_posts():
    """从 data/social_posts.json 按时间偏移渐进吐出（模拟实时流）；文件缺失回退内嵌单条"""
    try:
        with open(SOCIAL_JSON, encoding='utf-8') as f:
            posts = json.load(f)
        if not isinstance(posts, list) or not posts:
            raise ValueError('social_posts.json 为空')
        n = min(len(posts), max(1, int(time.time()) // MOCK_TICK_SEC % (len(posts) + 1)))
        sel = posts[-n:]                        # 取最新 n 条，模拟新帖持续流入
        return [{'id': str(p.get('post_id') or ('mock-%d' % i)),
                 'text': (p.get('text') or '').strip(),
                 'created_at': p.get('time') or _now_iso(),
                 'tags': [k for k in (p.get('keywords_matched') or []) if k][:6],
                 'offset_min': p.get('offset_after_quake_min'),
                 'live': True}
                for i, p in enumerate(sel) if p.get('text')]
    except Exception as e:
        print('[live] mock 数据读取失败，回落内嵌样例:', e)
        return [{'id': 'mock-fallback', 'text': '实时社情通道联调样例：缅甸地震后社媒信号持续流入',
                 'created_at': _now_iso(), 'tags': ['地震'], 'offset_min': None, 'live': True}]


def _parse_created(v):
    """防御性解析 weibo-cli 的 created_at：先尝试常见格式（epoch 秒/毫秒、ISO、微博原生 %a %b %d %H:%M:%S %z %Y 等），
    成功统一输出 'YYYY-MM-DD HH:MM'（北京时间）；全部失败才回落原文（不截断）；缺字段返回 None"""
    if isinstance(v, (int, float)) and v > 0:
        ts = v / 1000 if v > 1e12 else v
        try:
            return datetime.fromtimestamp(ts, TZ_CST).strftime('%Y-%m-%d %H:%M')
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(v, str) and v.strip():
        s = v.strip()
        cands = []
        try:                                  # epoch 秒/毫秒的字符串形态
            fv = float(s)
            if fv > 0:
                cands.append(datetime.fromtimestamp(fv / 1000 if fv > 1e12 else fv, TZ_CST))
        except (ValueError, OverflowError, OSError):
            pass
        try:                                  # ISO 8601
            cands.append(datetime.fromisoformat(s))
        except ValueError:
            pass
        for fmt in ('%a %b %d %H:%M:%S %z %Y', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M'):
            try:
                cands.append(datetime.strptime(s, fmt))
                break
            except ValueError:
                continue
        for dt in cands:
            try:
                return dt.astimezone(TZ_CST).strftime('%Y-%m-%d %H:%M')
            except (OverflowError, OSError, ValueError):
                continue
        return s                              # 全部失败 → 回落原文，不截断
    return None


def _created_dt(v):
    """与 _parse_created 同一解析链，但返回北京时间 aware datetime（解析失败/缺字段 → None）；
    供 WP9 系统拾取延迟计算使用（不改动 _parse_created 的既有输出口径）"""
    if isinstance(v, (int, float)) and v > 0:
        ts = v / 1000 if v > 1e12 else v
        try:
            return datetime.fromtimestamp(ts, TZ_CST)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(v, str) and v.strip():
        s = v.strip()
        cands = []
        try:
            fv = float(s)
            if fv > 0:
                cands.append(datetime.fromtimestamp(fv / 1000 if fv > 1e12 else fv, TZ_CST))
        except (ValueError, OverflowError, OSError):
            pass
        try:
            cands.append(datetime.fromisoformat(s))
        except ValueError:
            pass
        for fmt in ('%a %b %d %H:%M:%S %z %Y', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M'):
            try:
                cands.append(datetime.strptime(s, fmt))
                break
            except ValueError:
                continue
        for dt in cands:
            try:
                return dt.astimezone(TZ_CST)
            except (OverflowError, OSError, ValueError):
                continue
    return None


def _latency_min(created_raw, polled_dt):
    """WP9 系统拾取延迟（分钟，保留 1 位小数）：polled_at − created_at；
    created_at 解析失败或缺拾取时刻 → None（可为负：发布时间晚于轮询起点之外的对时误差，原样保留）"""
    if polled_dt is None:
        return None
    dt = _created_dt(created_raw)
    if dt is None:
        return None
    return round((polled_dt - dt).total_seconds() / 60.0, 1)


def _latency_stats(posts):
    """顶层拾取延迟统计（仅统计非 null 项）：{n, median_min, p90_min}；无有效值时全 null"""
    vals = sorted(p['latency_min'] for p in posts
                  if isinstance(p.get('latency_min'), (int, float)))
    if not vals:
        return {'n': 0, 'median_min': None, 'p90_min': None}
    n = len(vals)
    mid = n // 2
    median = vals[mid] if n % 2 else round((vals[mid - 1] + vals[mid]) / 2.0, 1)
    p90 = vals[min(n - 1, max(0, math.ceil(0.9 * n) - 1))]
    return {'n': n, 'median_min': round(median, 1), 'p90_min': round(p90, 1)}


def _parse_weibo(data, polled_dt=None):
    """防御性解析 weibo search statuses/limited --output json：
    字段假设——外层 dict 时取 data/statuses/items/list 其一，本身为 list 直接用；
    单帖必须有 id + text（raw_text/text/long_text/content 任一），缺任一即跳过该条；
    隐私：丢弃 user/screen_name/uid 等发布者字段，仅保留文本与时间；按 id 去重、上限 50 条；
    WP9：传入 polled_dt（拾取时刻）时，每条附 latency_min = polled_at − created_at（分钟，1 位小数，解析失败 null）"""
    if isinstance(data, dict):
        rows = None
        for k in ('data', 'statuses', 'items', 'list', 'cards', 'result'):
            v = data.get(k)
            if isinstance(v, list):
                rows = v
                break
            if isinstance(v, dict):            # data 可能再套一层 {statuses:[...]}
                for k2 in ('statuses', 'items', 'list', 'cards'):
                    if isinstance(v.get(k2), list):
                        rows = v[k2]
                        break
                if rows is not None:
                    break
        if rows is None:
            raise ValueError('未识别的 weibo-cli 顶层结构: %s' % sorted(data.keys())[:8])
    elif isinstance(data, list):
        rows = data
    else:
        raise ValueError('weibo-cli 输出非 JSON 对象/数组')
    seen, out = set(), []
    for r in rows:
        if not isinstance(r, dict):
            continue
        pid = r.get('id') or r.get('idstr') or r.get('mid')
        text = r.get('text') or r.get('raw_text') or r.get('long_text') or r.get('content')
        if not pid or not text:
            continue                            # 字段缺失即跳过该条
        pid = str(pid)
        if pid in seen:
            continue
        seen.add(pid)
        # tags：话题词（#…#）与来源关键词的防御性合并
        tags = list(r.get('topics') or [])
        if isinstance(r.get('keywords'), list):
            tags += r.get('keywords')
        if not tags:                            # 上游无话题词时从文本提取 #话题#
            tags = re.findall(r'#(.+?)#', str(text))
        raw_created = r.get('created_at')
        out.append({'id': pid, 'text': str(text).strip(),
                    'created_at': _parse_created(raw_created) or _now_iso(),
                    'tags': [str(t) for t in tags if t][:6],
                    'offset_min': None, 'live': True,          # weibo 真实帖无震后偏移口径 → null
                    'latency_min': _latency_min(raw_created, polled_dt)})
        if len(out) >= MAX_POSTS:
            break
    return out


def _resolve_weibo_bin():
    """稳健解析 weibo 可执行文件：优先 PATH（shutil.which），回退仓库内本地安装路径"""
    found = shutil.which('weibo')
    if found:
        return found
    repo_root = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))   # backend/Qwen 初版/ → 仓库根（路径含中文，不可用 pathlib parents 缩写）
    local = os.path.join(repo_root, 'weibo-cli', 'node_modules', '.bin', 'weibo')
    if os.path.isfile(local) and os.access(local, os.X_OK):
        return local
    return 'weibo'                            # 都不在 → 保持裸命令，交由 FileNotFoundError 降级链处理


def _weibo_fetch(q):
    """subprocess 调 weibo-cli（带超时与异常捕获）；缺失/未认证/失败抛异常由上层降级。
    WP9：拾取时刻在发起调用前固定，供每条计算系统拾取延迟"""
    # --count：帮助文档标称上限 50，服务端实际强制 ≤20（COUNT_EXCEEDS_MAX，2026-08 实测）
    cmd = [_resolve_weibo_bin(), 'search', 'statuses/limited', '--q', q, '--type', '1',
           '--count', '20', '--output', 'json']
    polled_dt = datetime.now(TZ_CST)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=WEIBO_TIMEOUT)
    except FileNotFoundError:
        raise RuntimeError('weibo-cli 未安装或不在 PATH')
    except subprocess.TimeoutExpired:
        raise RuntimeError('weibo-cli 调用超时(>%ds)' % WEIBO_TIMEOUT)
    if r.returncode != 0:
        err = (r.stderr or b'').decode('utf-8', 'ignore').strip()
        if 'auth' in err.lower() or 'login' in err.lower() or 'token' in err.lower():
            raise RuntimeError('weibo-cli 未认证: ' + err[:120])
        raise RuntimeError('weibo-cli 退出码 %d: %s' % (r.returncode, err[:120]))
    try:
        data = json.loads(r.stdout.decode('utf-8', 'ignore'))
    except json.JSONDecodeError:
        raise RuntimeError('weibo-cli 输出非合法 JSON')
    posts = _parse_weibo(data, polled_dt)
    if not posts:
        raise RuntimeError('weibo-cli 返回 0 条可解析帖')
    return posts


def _weibo_prefetch_loop():
    """weibo 模式后台预取：启动即检索、之后每 --interval 秒一次；仅成功才刷缓存。
    HTTP 线程因此永不在请求内阻塞 weibo-cli（25s 超时也隔离在后台）"""
    while True:
        try:
            posts = _weibo_fetch(_cfg['q'])
            sel = posts[:MAX_POSTS]
            resp = {'source': 'weibo', 'polled_at': _now_iso(), 'stale': False,
                    'posts': sel, 'latency_stats': _latency_stats(sel)}
            with _lock:
                _cache.update(ts=time.time(), data=resp, key=('weibo', _cfg['q']))
            print('[live] 后台预取成功: %d 条 (q=%s)' % (len(posts), _cfg['q']))
        except Exception as e:
            print('[live] 后台预取失败（继续以当前缓存/空兜底对外服务）:', e)
        time.sleep(_cfg['interval'])


def build_response():
    """组装 /live/social 响应。
    weibo 模式：永远秒回后台预取线程刷出的缓存；从未成功过 → 空帖 + stale:true。
    mock 模式：请求内即时生成 + 内存缓存（有效期跟随 --interval）；
    仅真实成功（weibo 预取成功 / mock 即时生成）才回写 _cache，降级产物不写。"""
    if _cfg['mode'] == 'weibo':
        with _lock:
            cached = _cache['data'] if _cache['key'] == ('weibo', _cfg['q']) else None
        if cached and cached.get('posts'):
            return cached                       # 秒回最近一次真实成功结果（stale:False）
        return {'source': 'weibo', 'polled_at': _now_iso(), 'stale': True, 'posts': [],
                'latency_stats': {'n': 0, 'median_min': None, 'p90_min': None}}
    key = (_cfg['mode'], _cfg['q'])
    now = time.time()
    ttl = max(10, _cfg['interval'])             # 缓存有效期跟随 --interval（mock 默认 30s）
    with _lock:
        if _cache['data'] is not None and _cache['key'] == key and now - _cache['ts'] < ttl:
            return _cache['data']
    resp = {'source': 'mock', 'polled_at': _now_iso(), 'stale': False, 'posts': _mock_posts()}
    resp['posts'] = resp['posts'][:MAX_POSTS]
    with _lock:
        _cache.update(ts=now, data=resp, key=key)
    return resp


class Handler(BaseHTTPRequestHandler):
    server_version = 'RescueAILiveFeed/1.0'

    def log_message(self, fmt, *args):
        print('[%s] %s' % (self.address_string(), fmt % args))

    def _send(self, code, body):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')   # 任务约定：CORS 允许 *（演示页跨端口直连）
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.unquote(self.path).split('?', 1)[0]
        if path == '/live/social':
            try:
                return self._send(200, build_response())
            except Exception as e:      # 兜底：任何异常也返回合法 JSON，绝不让前端拿到 5xx 裸体
                return self._send(200, {'source': 'mock', 'polled_at': _now_iso(), 'stale': True, 'posts': []})
        if path == '/health':
            return self._send(200, {'ok': True, 'mode': _cfg['mode'], 'q': _cfg['q'], 'interval': _cfg['interval']})
        return self._send(404, {'error': 'not found'})


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='RescueAI 实时社情层轮询服务（仅标准库）')
    ap.add_argument('--mode', choices=['mock', 'weibo'], default='mock', help='数据源模式（默认 mock）')
    ap.add_argument('--port', type=int, default=8012, help='监听端口（默认 8012，全工作区已核查无冲突）')
    ap.add_argument('--interval', type=int, default=None, help='上游轮询间隔秒（weibo 默认 300，mock 默认 30）')
    ap.add_argument('--q', default='地震', help='weibo 检索关键词（默认"地震"）')
    args = ap.parse_args()
    if args.interval is not None and args.interval <= 0:
        ap.error('--interval 必须为正整数（秒），收到: %s' % args.interval)
    _cfg['mode'] = args.mode
    _cfg['interval'] = args.interval if args.interval else (300 if args.mode == 'weibo' else 30)
    _cfg['q'] = args.q
    print('=' * 62)
    print('RescueAI 实时社情层轮询服务（任务5·路径A）')
    print('  模式: %s | 端口: %d | 轮询间隔: %ds | 关键词: %s' % (_cfg['mode'], args.port, _cfg['interval'], _cfg['q']))
    print('  端点: GET /live/social    健康: GET /health')
    if _cfg['mode'] == 'weibo':
        print('  weibo 模式: 后台预取每 %ds 一次（仅成功刷缓存）；/live/social 永远秒回当前缓存，从未成功则空帖+stale' % _cfg['interval'])
        threading.Thread(target=_weibo_prefetch_loop, daemon=True).start()
    else:
        print('  mock 模式: 请求内即时渐进吐帖（随 MOCK_TICK 节拍） | 隐私: 昵称/UID 已丢弃')
    next_at = datetime.now(TZ_CST) + timedelta(seconds=_cfg['interval'])
    print('  下次轮询: %s' % next_at.strftime('%H:%M:%S'))
    print('=' * 62)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
