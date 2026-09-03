#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task #4：weibo 解析与降级链自动化测试（仅标准库，unittest）。

覆盖 live_feed.py：
  1. 夹具解析   —— _parse_weibo(真实探针 _weibo_probe.json) 产出 20 条、字段非空、id 无重复
  2. 时间解析   —— _parse_created 对微博原生格式/ISO/epoch/异常输入的口径
  3. 话题提取   —— #话题# 正则提取；无话题时 tags 为空不报错
  4. 隐私剥离   —— 解析输出不含昵称/UID/user 嵌套字段
  5. 降级链     —— mock subprocess 抛 FileNotFoundError/TimeoutExpired → _weibo_fetch 受控异常；
                   weibo 模式 build_response 冷缓存秒回空帖+stale；预取循环吞异常不退出
  6. 顶层键候选 —— {"data": [...]}、嵌套 {"data":{"statuses":[...]}}、裸 list、非法结构等防御性路径
  7. 拾取延迟   —— WP9：latency_min = polled_at − created_at（1 位小数，解析失败 null）；
                   顶层 latency_stats {n, median_min, p90_min}；不传拾取时刻时恒 null（不回归）

运行：python3 backend/Qwen\ 初版/scripts/test_weibo_parse.py [-v]
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
from datetime import datetime, timezone, timedelta
from unittest import mock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))                       # .../Qwen 初版/scripts
PARENT_DIR = os.path.dirname(BASE_DIR)                                      # .../Qwen 初版（含中文与空格）
PROBE_JSON = os.path.join(PARENT_DIR, 'data', '_weibo_probe.json')

# live_feed 是正常模块名，但所在目录含中文与空格 → 用 importlib 显式按路径加载
_spec = importlib.util.spec_from_file_location('live_feed', os.path.join(PARENT_DIR, 'live_feed.py'))
lf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lf)


def load_probe():
    with open(PROBE_JSON, encoding='utf-8') as f:
        return json.load(f)


class TestProbeFixtureParse(unittest.TestCase):
    """夹具解析：真实探针（顶层键 statuses，20 条）"""

    @classmethod
    def setUpClass(cls):
        cls.posts = lf._parse_weibo(load_probe())

    def test_yields_20_posts(self):
        self.assertEqual(len(self.posts), 20)

    def test_fields_non_empty(self):
        for p in self.posts:
            self.assertTrue(p['id'], 'id 不应为空')
            self.assertTrue(p['text'].strip(), 'text 不应为空')
            self.assertTrue(p['created_at'], 'created_at 不应为空')

    def test_ids_unique(self):
        ids = [p['id'] for p in self.posts]
        self.assertEqual(len(ids), len(set(ids)), 'id 出现重复')

    def test_output_schema(self):
        """输出契约字段齐全，且 offset_min 为 null（weibo 真实帖无震后偏移口径）；
        不传拾取时刻时 latency_min 恒 null（保持既有调用方式不回归）"""
        for p in self.posts:
            for k in ('id', 'text', 'created_at', 'tags', 'offset_min', 'live', 'latency_min'):
                self.assertIn(k, p)
            self.assertIsNone(p['offset_min'])
            self.assertIsNone(p['latency_min'])
            self.assertTrue(p['live'])

    def test_created_at_matches_format(self):
        """夹具中全部 created_at 为微博原生格式，应统一解析为 'YYYY-MM-DD HH:MM'"""
        fmt = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')
        for p in self.posts:
            self.assertRegex(p['created_at'], fmt, 'created_at 格式异常: %r' % p['created_at'])


class TestParseCreated(unittest.TestCase):
    """时间解析：以代码实际口径为准——成功统一输出 'YYYY-MM-DD HH:MM'（北京时间），失败回落原文，缺字段 None"""

    def test_weibo_native_format(self):
        self.assertEqual(lf._parse_created('Fri Aug 28 23:04:01 +0800 2026'), '2026-08-28 23:04')

    def test_epoch_seconds(self):
        self.assertEqual(lf._parse_created(1787929441), '2026-08-28 23:04')

    def test_epoch_millis(self):
        self.assertEqual(lf._parse_created(1787929441000), '2026-08-28 23:04')

    def test_epoch_string(self):
        self.assertEqual(lf._parse_created('1787929441'), '2026-08-28 23:04')

    def test_iso_with_offset(self):
        self.assertEqual(lf._parse_created('2026-08-28T23:04:01+08:00'), '2026-08-28 23:04')

    def test_plain_datetime_string(self):
        self.assertEqual(lf._parse_created('2026-08-28 23:04:01'), '2026-08-28 23:04')

    def test_unrecognized_falls_back_to_raw(self):
        self.assertEqual(lf._parse_created('3分钟前'), '3分钟前')

    def test_missing_returns_none(self):
        self.assertIsNone(lf._parse_created(None))
        self.assertIsNone(lf._parse_created(''))
        self.assertIsNone(lf._parse_created('   '))


class TestTopicTags(unittest.TestCase):
    """话题提取：#…# 正则；无话题时 tags 为空不报错"""

    def test_extract_from_text(self):
        row = {'id': '1', 'text': '#四川隆昌发生5.1级地震# 震感挺强烈的。'}
        self.assertEqual(lf._parse_weibo([row])[0]['tags'], ['四川隆昌发生5.1级地震'])

    def test_multiple_topics(self):
        row = {'id': '2', 'text': '#缅甸地震# 现场情况 #余震# 持续更新'}
        self.assertEqual(lf._parse_weibo([row])[0]['tags'], ['缅甸地震', '余震'])

    def test_no_topic_no_error(self):
        row = {'id': '3', 'text': '只是普通的一条帖子，没有任何话题'}
        self.assertEqual(lf._parse_weibo([row])[0]['tags'], [])

    def test_upstream_topics_key_takes_precedence(self):
        """上游已给 topics 时不再从文本提取（按代码实际逻辑）"""
        row = {'id': '4', 'text': '#文本话题# 内容', 'topics': ['上游话题']}
        self.assertEqual(lf._parse_weibo([row])[0]['tags'], ['上游话题'])

    def test_tags_capped_at_6(self):
        row = {'id': '5', 'text': '#a# #b# #c# #d# #e# #f# #g# #h#'}
        self.assertEqual(len(lf._parse_weibo([row])[0]['tags']), 6)

    def test_probe_has_tagged_posts(self):
        """真实夹具中至少存在一条带话题的帖（话题来自 #…# 提取，夹具无 topics 键）"""
        posts = lf._parse_weibo(load_probe())
        self.assertTrue(any(p['tags'] for p in posts), '夹具中应至少一条帖含话题词')


class TestPrivacyStripping(unittest.TestCase):
    """隐私剥离：丢弃发布者昵称/UID/user 嵌套字段，仅保留文本与时间"""

    @classmethod
    def setUpClass(cls):
        cls.probe = load_probe()
        cls.posts = lf._parse_weibo(cls.probe)

    def test_output_schema_is_flat(self):
        """输出键固定为契约七字段（WP9 新增 latency_min），不存在 user/screen_name/uid 等发布者字段"""
        expected = {'id', 'text', 'created_at', 'tags', 'offset_min', 'live', 'latency_min'}
        for p in self.posts:
            self.assertEqual(set(p.keys()), expected)

    def test_probe_raw_has_user_but_output_drops_it(self):
        """夹具原始数据含 user 嵌套字段（含 screen_name/id），解析输出不应残留"""
        self.assertTrue(any(isinstance(r.get('user'), dict) for r in self.probe['statuses']),
                        '前置条件：夹具原始数据应含 user 字段')
        blob = json.dumps(self.posts, ensure_ascii=False)
        self.assertNotIn('"user"', blob)
        self.assertNotIn('screen_name', blob)

    def test_uid_not_leaked_via_textless_path(self):
        """构造带 user 的单条 → 输出中 uid/screen_name 不外泄"""
        row = {'id': '9', 'text': '#地震# 测试',
               'user': {'id': 123456789, 'screen_name': '某用户昵称', 'uid': 'u-999'}}
        p = lf._parse_weibo([row])[0]
        blob = json.dumps(p, ensure_ascii=False)
        self.assertNotIn('某用户昵称', blob)
        self.assertNotIn('123456789', blob)
        self.assertNotIn('u-999', blob)


class TestDegradeChain(unittest.TestCase):
    """降级：subprocess 异常 → _weibo_fetch 抛受控 RuntimeError；服务逻辑不挂"""

    def test_file_not_found_raises_controlled(self):
        with mock.patch.object(lf.subprocess, 'run', side_effect=FileNotFoundError):
            with self.assertRaises(RuntimeError) as ctx:
                lf._weibo_fetch('地震')
            self.assertIn('未安装', str(ctx.exception))

    def test_timeout_expired_raises_controlled(self):
        with mock.patch.object(lf.subprocess, 'run',
                               side_effect=subprocess.TimeoutExpired(cmd='weibo', timeout=25)):
            with self.assertRaises(RuntimeError) as ctx:
                lf._weibo_fetch('地震')
            self.assertIn('超时', str(ctx.exception))

    def test_nonzero_exit_auth_error(self):
        done = mock.Mock(returncode=1, stderr='please login first'.encode(), stdout=b'')
        with mock.patch.object(lf.subprocess, 'run', return_value=done):
            with self.assertRaises(RuntimeError) as ctx:
                lf._weibo_fetch('地震')
            self.assertIn('未认证', str(ctx.exception))

    def test_invalid_json_output(self):
        done = mock.Mock(returncode=0, stdout=b'not-json', stderr=b'')
        with mock.patch.object(lf.subprocess, 'run', return_value=done):
            with self.assertRaises(RuntimeError) as ctx:
                lf._weibo_fetch('地震')
            self.assertIn('非合法 JSON', str(ctx.exception))

    def test_zero_parseable_posts(self):
        done = mock.Mock(returncode=0, stdout=b'{"statuses": []}', stderr=b'')
        with mock.patch.object(lf.subprocess, 'run', return_value=done):
            with self.assertRaises(RuntimeError) as ctx:
                lf._weibo_fetch('地震')
            self.assertIn('0 条', str(ctx.exception))

    def test_build_response_cold_cache_weibo_mode(self):
        """weibo 模式且从未预取成功 → 秒回 {source:weibo, posts:[], stale:true}，绝不抛异常"""
        saved = (dict(lf._cfg), dict(lf._cache))
        try:
            lf._cfg.update(mode='weibo', q='测试降级')
            lf._cache.update(ts=0.0, data=None, key=None)
            resp = lf.build_response()
            self.assertEqual(resp['source'], 'weibo')
            self.assertEqual(resp['posts'], [])
            self.assertTrue(resp['stale'])
            self.assertIn('polled_at', resp)
        finally:
            lf._cfg.update(saved[0])
            lf._cache.update(saved[1])

    def test_build_response_serves_cached_success(self):
        """预取成功刷缓存后，build_response 秒回该缓存且 stale:False"""
        saved = (dict(lf._cfg), dict(lf._cache))
        try:
            lf._cfg.update(mode='weibo', q='测试缓存')
            cached = {'source': 'weibo', 'polled_at': lf._now_iso(), 'stale': False,
                      'posts': [{'id': 'c1', 'text': '#地震# 缓存帖', 'created_at': '2026-08-28 23:04',
                                 'tags': ['地震'], 'offset_min': None, 'live': True}]}
            lf._cache.update(ts=0.0, data=cached, key=('weibo', '测试缓存'))
            resp = lf.build_response()
            self.assertIs(resp, cached)
            self.assertFalse(resp['stale'])
        finally:
            lf._cfg.update(saved[0])
            lf._cache.update(saved[1])

    def test_prefetch_loop_swallows_fetch_failure(self):
        """预取循环在 _weibo_fetch 抛异常时不退出、不污染缓存（patch sleep 只跑一轮）"""
        saved = (dict(lf._cfg), dict(lf._cache))
        try:
            lf._cfg.update(mode='weibo', interval=1, q='测试预取')
            lf._cache.update(ts=0.0, data=None, key=None)

            def fake_sleep(_s):
                raise KeyboardInterrupt           # 第一轮结束后终止 while True

            with mock.patch.object(lf, '_weibo_fetch', side_effect=RuntimeError('模拟预取失败')), \
                 mock.patch.object(lf.time, 'sleep', side_effect=fake_sleep):
                with self.assertRaises(KeyboardInterrupt):
                    lf._weibo_prefetch_loop()
            # 失败后缓存保持空（降级产物不回写缓存）
            self.assertIsNone(lf._cache['data'])
        finally:
            lf._cfg.update(saved[0])
            lf._cache.update(saved[1])


class TestTopLevelKeyVariants(unittest.TestCase):
    """顶层键候选兼容：按代码候选键列表（data/statuses/items/list/cards/result，含二次嵌套）"""

    ROW_A = {'id': 'a1', 'text': '#地震# 变体A', 'created_at': '2026-08-28 23:04:01'}
    ROW_B = {'id': 'b2', 'text': '#余震# 变体B', 'created_at': '2026-08-28 23:05:00'}

    def test_statuses_key(self):
        self.assertEqual(len(lf._parse_weibo({'statuses': [self.ROW_A]})), 1)

    def test_data_list(self):
        self.assertEqual(len(lf._parse_weibo({'data': [self.ROW_A, self.ROW_B]})), 2)

    def test_data_nested_statuses(self):
        self.assertEqual(len(lf._parse_weibo({'data': {'statuses': [self.ROW_A]}})), 1)

    def test_items_list_cards_result(self):
        for key in ('items', 'list', 'cards', 'result'):
            posts = lf._parse_weibo({key: [self.ROW_A]})
            self.assertEqual(len(posts), 1, '候选键 %s 应可解析' % key)

    def test_bare_list(self):
        self.assertEqual(len(lf._parse_weibo([self.ROW_A, self.ROW_B])), 2)

    def test_unrecognized_structure_raises(self):
        with self.assertRaises(ValueError):
            lf._parse_weibo({'foo': [self.ROW_A]})

    def test_non_json_type_raises(self):
        with self.assertRaises(ValueError):
            lf._parse_weibo('纯字符串不是 JSON 对象')

    def test_missing_fields_row_skipped(self):
        rows = [self.ROW_A, {'id': 'no-text'}, {'text': '没有 id'}, '非 dict 噪声']
        posts = lf._parse_weibo(rows)
        self.assertEqual([p['id'] for p in posts], ['a1'])

    def test_duplicate_ids_deduped(self):
        posts = lf._parse_weibo([self.ROW_A, dict(self.ROW_A)])
        self.assertEqual(len(posts), 1)

    def test_text_alias_keys(self):
        """text 缺失时按代码候选回退 raw_text/long_text/content"""
        for alias in ('raw_text', 'long_text', 'content'):
            posts = lf._parse_weibo([{'id': alias, alias: '#话题# 别名文本'}])
            self.assertEqual(len(posts), 1, '别名键 %s 应可解析' % alias)

    def test_id_alias_keys(self):
        """id 缺失时按代码候选回退 idstr/mid"""
        self.assertEqual(lf._parse_weibo([{'idstr': 'x1', 'text': 't'}])[0]['id'], 'x1')
        self.assertEqual(lf._parse_weibo([{'mid': 'x2', 'text': 't'}])[0]['id'], 'x2')

    def test_max_posts_cap(self):
        rows = [{'id': str(i), 'text': '帖 %d' % i} for i in range(lf.MAX_POSTS + 10)]
        self.assertEqual(len(lf._parse_weibo(rows)), lf.MAX_POSTS)


class TestPickupLatency(unittest.TestCase):
    """WP9 系统拾取延迟：latency_min = polled_at − created_at（分钟，1 位小数，解析失败 null）"""

    CST = timezone(timedelta(hours=8))
    POLLED = datetime(2026, 8, 28, 23, 14, 1, tzinfo=CST)

    def test_native_format_latency(self):
        row = {'id': '1', 'text': 't', 'created_at': 'Fri Aug 28 23:04:01 +0800 2026'}
        p = lf._parse_weibo([row], polled_dt=self.POLLED)[0]
        self.assertEqual(p['latency_min'], 10.0)

    def test_epoch_latency_rounded_to_1_decimal(self):
        row = {'id': '2', 'text': 't', 'created_at': 1787929441}     # 2026-08-28 23:04:01 +0800
        polled = datetime(2026, 8, 28, 23, 10, 31, tzinfo=self.CST)
        p = lf._parse_weibo([row], polled_dt=polled)[0]
        self.assertEqual(p['latency_min'], 6.5)

    def test_unparseable_created_at_yields_null(self):
        row = {'id': '3', 'text': 't', 'created_at': '3分钟前'}
        p = lf._parse_weibo([row], polled_dt=self.POLLED)[0]
        self.assertIsNone(p['latency_min'])

    def test_missing_created_at_yields_null(self):
        p = lf._parse_weibo([{'id': '4', 'text': 't'}], polled_dt=self.POLLED)[0]
        self.assertIsNone(p['latency_min'])

    def test_no_polled_dt_keeps_null(self):
        """不传拾取时刻（既有调用方式）→ 全部 null，不影响存量行为"""
        row = {'id': '5', 'text': 't', 'created_at': 'Fri Aug 28 23:04:01 +0800 2026'}
        p = lf._parse_weibo([row])[0]
        self.assertIsNone(p['latency_min'])

    def test_probe_fixture_latency_all_numeric(self):
        """真实探针夹具（20 条均可解析）传入拾取时刻后全部非 null"""
        posts = lf._parse_weibo(load_probe(), polled_dt=self.POLLED)
        self.assertEqual(len(posts), 20)
        for p in posts:
            self.assertIsInstance(p['latency_min'], (int, float))

    def test_latency_stats_median_p90(self):
        posts = [{'latency_min': v} for v in [1.0, 2.0, 3.0, 4.0, 10.0]]
        st = lf._latency_stats(posts)
        self.assertEqual(st, {'n': 5, 'median_min': 3.0, 'p90_min': 10.0})

    def test_latency_stats_even_median_and_null_skip(self):
        posts = [{'latency_min': 1.0}, {'latency_min': None},
                 {'latency_min': 2.0}, {'latency_min': 3.0}]
        st = lf._latency_stats(posts)
        self.assertEqual(st, {'n': 3, 'median_min': 2.0, 'p90_min': 3.0})

    def test_latency_stats_empty(self):
        self.assertEqual(lf._latency_stats([]), {'n': 0, 'median_min': None, 'p90_min': None})
        self.assertEqual(lf._latency_stats([{'latency_min': None}]),
                         {'n': 0, 'median_min': None, 'p90_min': None})

    def test_weibo_fetch_attaches_latency(self):
        """_weibo_fetch 成功路径：每条帖携带数值型 latency_min（拾取时刻在调用前固定）"""
        probe = json.dumps(load_probe()).encode('utf-8')
        done = mock.Mock(returncode=0, stdout=probe, stderr=b'')
        with mock.patch.object(lf.subprocess, 'run', return_value=done):
            posts = lf._weibo_fetch('地震')
        self.assertEqual(len(posts), 20)
        for p in posts:
            self.assertIn('latency_min', p)
            self.assertIsInstance(p['latency_min'], (int, float))

    def test_build_response_cold_cache_has_latency_stats(self):
        """weibo 冷缓存响应也携带顶层 latency_stats（空统计，不报错）"""
        saved = (dict(lf._cfg), dict(lf._cache))
        try:
            lf._cfg.update(mode='weibo', q='测试延迟统计')
            lf._cache.update(ts=0.0, data=None, key=None)
            resp = lf.build_response()
            self.assertEqual(resp['latency_stats'], {'n': 0, 'median_min': None, 'p90_min': None})
        finally:
            lf._cfg.update(saved[0])
            lf._cache.update(saved[1])


if __name__ == '__main__':
    print('=' * 62)
    print('Task #4: weibo 解析与降级链自动化测试')
    print('  live_feed: %s' % os.path.join(PARENT_DIR, 'live_feed.py'))
    print('  探针夹具: %s' % PROBE_JSON)
    print('=' * 62)
    unittest.main(verbosity=2)
