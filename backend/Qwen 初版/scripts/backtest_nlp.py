#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WP6：分类回测（52 条人工标签 × nlp_service 同源分类逻辑），仅标准库。

口径（依据 outputs/评委建议优化方案.md 措施 2.a / 2.c，披露措辞不夸大）：
  - 数据：data/social_posts.json（52 条正文）× data/labels.json（52 条人工标签
    post_id → {damage_type, sentiment}）；
  - 被测逻辑：work buddy接力/backend/services/nlp_service.py 的关键词分类
    （损毁类型 6 类计数取最大 + 情感 4 类计数、urgent 优先、无命中回退默认类）。
    该模块顶部 `from services.ai_client import ai_client` 在独立运行时不可用，
    故按路径 importlib 加载并以最小 stub 顶替 services.ai_client（ai_client
    在分类纯函数中未被使用）；若加载仍失败，回退为 AST 抽取其三个词典常量 +
    与源码逐句一致的纯函数复刻，保证「测的就是演示用的那套词典/规则」。
  - 产出：damage_type 与 sentiment 两维度的混淆矩阵、逐类与宏平均
    precision / recall / F1、准确率；另顺带计算定位覆盖率
    （命中 LOCATION_DICT 地名词典的帖数占比，WP8 §2.7 口径）；
  - 落盘：data/backtest_result.json，并打印 Markdown 表格。

边界声明（写报告时须原文保留）：样本量 52、历史数据集（2025-03-28 缅甸地震）、
非独立测试集（标签与演示数据同源），结果仅作演示级口径，不构成泛化性能承诺。

运行：python3 backend/Qwen\\ 初版/scripts/backtest_nlp.py
"""
import ast
import datetime
import importlib.util
import json
import os
import sys
import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))            # .../Qwen 初版/scripts
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')       # .../Qwen 初版/data
REPO_ROOT = os.path.abspath(os.path.join(DATA_DIR, '..', '..', '..'))
NLP_PATH = os.path.join(REPO_ROOT, 'work buddy接力', 'backend', 'services', 'nlp_service.py')
SOCIAL_JSON = os.path.join(DATA_DIR, 'social_posts.json')
LABELS_JSON = os.path.join(DATA_DIR, 'labels.json')
OUT_JSON = os.path.join(DATA_DIR, 'backtest_result.json')

DAMAGE_CLASSES = ['人员伤亡', '房屋倒塌', '道路中断', '次生灾害', '救援进展', '震感反馈']
SENTIMENT_CLASSES = ['urgent', 'negative', 'neutral', 'hopeful']


# ---------------- nlp_service 加载 ----------------

def _load_via_importlib():
    """路径加载 + 最小 stub：顶替 services.ai_client（分类纯函数未使用 ai_client）"""
    stub_pkg = types.ModuleType('services')
    stub_pkg.__path__ = []
    stub_ai = types.ModuleType('services.ai_client')
    stub_ai.ai_client = None
    saved = {k: sys.modules.get(k) for k in ('services', 'services.ai_client')}
    sys.modules['services'] = stub_pkg
    sys.modules['services.ai_client'] = stub_ai
    try:
        spec = importlib.util.spec_from_file_location('services.nlp_service', NLP_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def _load_via_ast_fallback():
    """AST 抽取 LOCATION_DICT / DAMAGE_KEYWORDS / SENTIMENT_KEYWORDS，
    并以与源码逐句一致的纯函数复刻分类逻辑（仅在 importlib 路径失败时启用）"""
    with open(NLP_PATH, encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=NLP_PATH)
    consts = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ('LOCATION_DICT', 'DAMAGE_KEYWORDS', 'SENTIMENT_KEYWORDS'):
            consts[node.targets[0].id] = ast.literal_eval(node.value)
    missing = {'LOCATION_DICT', 'DAMAGE_KEYWORDS', 'SENTIMENT_KEYWORDS'} - set(consts)
    if missing:
        raise RuntimeError('AST 回退失败：源码中缺少常量 %s' % sorted(missing))

    class _Mod(object):
        pass

    mod = _Mod()
    mod.LOCATION_DICT = consts['LOCATION_DICT']
    mod.DAMAGE_KEYWORDS = consts['DAMAGE_KEYWORDS']
    mod.SENTIMENT_KEYWORDS = consts['SENTIMENT_KEYWORDS']

    class NLPService(object):
        @staticmethod
        def extract_locations(text):
            locations, seen = [], set()
            for name, (lng, lat) in mod.LOCATION_DICT.items():
                if name in text and name not in seen:
                    seen.add(name)
                    locations.append({'name': name, 'longitude': lng, 'latitude': lat,
                                      'confidence': 0.85, 'source': 'dict'})
            return locations

        @staticmethod
        def classify_damage_type(text):
            scores = {}
            for dtype, keywords in mod.DAMAGE_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in text)
                if score > 0:
                    scores[dtype] = score
            if not scores:
                return '震感反馈'
            return max(scores, key=scores.get)

        @staticmethod
        def analyze_sentiment(text):
            scores = {}
            for sentiment, keywords in mod.SENTIMENT_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in text)
                if score > 0:
                    scores[sentiment] = score
            if not scores:
                return 'neutral'
            if 'urgent' in scores:
                return 'urgent'
            return max(scores, key=scores.get)

    mod.NLPService = NLPService
    return mod


def load_nlp():
    try:
        return _load_via_importlib(), 'importlib(路径加载) + services.ai_client 最小 stub'
    except Exception as e:
        print('[backtest] importlib 加载失败（%s），回退 AST 抽取纯函数复刻' % e)
        return _load_via_ast_fallback(), 'AST 抽取词典 + 同源纯函数复刻（importlib 失败回退）'


# ---------------- 度量 ----------------

def confusion_metrics(pairs, classes):
    """pairs: [(truth, pred)]；返回混淆矩阵 + 逐类 P/R/F1 + 宏平均 + 准确率"""
    matrix = {t: {p: 0 for p in classes} for t in classes}
    for t, p in pairs:
        if t not in matrix:
            matrix[t] = {p: 0 for p in classes}
        matrix[t].setdefault(p, 0)
        matrix[t][p] += 1
    per_class, macro = {}, {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
    for c in classes:
        tp = matrix.get(c, {}).get(c, 0)
        fp = sum(matrix.get(t, {}).get(c, 0) for t in matrix if t != c)
        fn = sum(matrix.get(c, {}).get(p, 0) for p in matrix.get(c, {}) if p != c)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[c] = {'precision': round(precision, 4), 'recall': round(recall, 4),
                        'f1': round(f1, 4), 'support': tp + fn}
        macro['precision'] += precision
        macro['recall'] += recall
        macro['f1'] += f1
    n = max(1, len(classes))
    macro = {k: round(v / n, 4) for k, v in macro.items()}
    acc = sum(1 for t, p in pairs if t == p) / len(pairs) if pairs else 0.0
    return {'confusion_matrix': matrix, 'per_class': per_class,
            'macro': macro, 'accuracy': round(acc, 4), 'n': len(pairs)}


def render_markdown(title, classes, m):
    head = '| 人工标签 \\ 模型预测 | ' + ' | '.join(classes) + ' | 合计 |'
    sep = '|---' * (len(classes) + 2) + '|'
    rows = []
    for t in classes:
        row = m['confusion_matrix'].get(t, {})
        vals = [row.get(p, 0) for p in classes]
        rows.append('| **%s** | %s | %d |' % (t, ' | '.join(str(v) for v in vals), sum(vals)))
    pc = ['| %s | %.4f | %.4f | %.4f | %d |' % (c, m['per_class'][c]['precision'],
          m['per_class'][c]['recall'], m['per_class'][c]['f1'], m['per_class'][c]['support'])
          for c in classes]
    return '\n'.join(['**%s**（n=%d，accuracy=%.4f，macro P/R/F1=%.4f/%.4f/%.4f）' % (
                          title, m['n'], m['accuracy'], m['macro']['precision'],
                          m['macro']['recall'], m['macro']['f1']),
                      '', head, sep] + rows + ['', '| 类别 | precision | recall | F1 | support |',
                                               '|---|---|---|---|---|'] + pc)


def main():
    nlp, load_mode = load_nlp()
    with open(SOCIAL_JSON, encoding='utf-8') as f:
        posts = json.load(f)
    with open(LABELS_JSON, encoding='utf-8') as f:
        labels = json.load(f)
    posts = [p for p in posts if p.get('post_id') in labels]
    if len(posts) != len(labels):
        print('[backtest] 警告：标签 %d 条与可对齐帖数 %d 不一致，按交集回测' % (len(labels), len(posts)))

    dmg_pairs, senti_pairs, per_post = [], [], []
    for p in posts:
        text = p.get('text') or ''
        lab = labels[p['post_id']]
        pred_dmg = nlp.NLPService.classify_damage_type(text)
        pred_sen = nlp.NLPService.analyze_sentiment(text)
        locs = nlp.NLPService.extract_locations(text)
        dmg_pairs.append((lab['damage_type'], pred_dmg))
        senti_pairs.append((lab['sentiment'], pred_sen))
        per_post.append({'post_id': p['post_id'], 'damage_true': lab['damage_type'],
                         'damage_pred': pred_dmg, 'sentiment_true': lab['sentiment'],
                         'sentiment_pred': pred_sen,
                         'location_names_hit': [l['name'] for l in locs]})

    # WP8 定位覆盖率：命中词典地名的帖占比（词典定位法口径，非定位准确率）
    hit = [r for r in per_post if r['location_names_hit']]
    name_counts = {}
    for r in per_post:
        for nm in r['location_names_hit']:
            name_counts[nm] = name_counts.get(nm, 0) + 1
    coverage = {'total': len(per_post), 'hit': len(hit),
                'coverage': round(len(hit) / len(per_post), 4) if per_post else 0.0,
                'per_name_hit_count': dict(sorted(name_counts.items(), key=lambda kv: -kv[1])),
                'missed_post_ids': [r['post_id'] for r in per_post if not r['location_names_hit']]}

    dmg = confusion_metrics(dmg_pairs, DAMAGE_CLASSES)
    sen = confusion_metrics(senti_pairs, SENTIMENT_CLASSES)

    result = {
        'generated_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'task': 'WP6 分类回测 + WP8 定位覆盖率（口径见 outputs/评委建议优化方案.md 措施 2.a/2.c）',
        'nlp_source': NLP_PATH,
        'nlp_load_mode': load_mode,
        'labels_source': LABELS_JSON,
        'posts_source': SOCIAL_JSON,
        'n_posts': len(per_post),
        'boundary_note': '样本量 52、历史数据集、非独立测试集（标签与演示数据同源），不构成泛化性能承诺',
        'damage_type': dmg,
        'sentiment': sen,
        'location_coverage': coverage,
        'per_post': per_post,
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print('# WP6 分类回测（52 条人工标签 × nlp_service 同源逻辑）')
    print('> 被测模块：%s' % NLP_PATH)
    print('> 加载方式：%s' % load_mode)
    print('> %s' % result['boundary_note'])
    print()
    print(render_markdown('damage_type 混淆矩阵', DAMAGE_CLASSES, dmg))
    print()
    print(render_markdown('sentiment 混淆矩阵', SENTIMENT_CLASSES, sen))
    print()
    print('## WP8 定位覆盖率（词典定位法口径）')
    print('- 命中词典地名的帖数：%d / %d → 覆盖率 **%.1f%%**' % (
        coverage['hit'], coverage['total'], coverage['coverage'] * 100))
    print('- 逐地名命中计数：%s' % '、'.join('%s %d' % kv for kv in coverage['per_name_hit_count'].items()))
    print('- 无 ground truth，定位准确率不可计算，本项目不做该承诺')
    print()
    print('产物：%s' % OUT_JSON)


if __name__ == '__main__':
    main()
