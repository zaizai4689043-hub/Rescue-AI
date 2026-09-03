# -*- coding: utf-8 -*-
"""
build_social_posts.py — 2025 缅甸地震微博数据集清洗 + LLM 离线打标

流程: 匿名化 -> 去噪去重 -> 灾情关键词初筛 -> 均衡抽样100条
      -> qwen-plus 逐条打标 -> 精选30-50条 -> 地名词典赋坐标
      -> 产出 data/ 三个文件(social_posts.json 主数据 / labels.json 标签映射 /
         funnel.json 漏斗统计) -> 合规校验

幂等: 可重复运行, 每次全量重算并覆盖输出。
注意: API Key 仅从 backend/.env 读取, 全程不明文输出。
"""

import hashlib
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime

import openpyxl
import requests

# ---------------- 路径与常量 ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))            # backend/Qwen 初版/scripts
PROJ_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))  # 仓库根目录
XLSX_PATH = os.path.join(
    PROJ_DIR, "temp_myquake",
    "entity_The Weibo data text about the Myanmar earthquake in 2025",
    "Myanmar.xlsx",
)
ENV_PATH = os.path.join(PROJ_DIR, "backend", ".env")
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
OUT_PATH = os.path.join(DATA_DIR, "social_posts.json")
LABELS_PATH = os.path.join(DATA_DIR, "labels.json")    # post_id -> 标签映射
FUNNEL_PATH = os.path.join(DATA_DIR, "funnel.json")    # 数据漏斗统计
CACHE_PATH = os.path.join(BASE_DIR, "_label_cache.json")  # 打标缓存(中间文件,成功运行后自动清理)

QUAKE_TIME = datetime(2025, 3, 28, 14, 20, 0)   # 发震时刻(北京时间)
NOISE_DATE = "2025-01-09"                        # 需剔除的噪声日期
SAMPLE_N = 100                                   # 送 LLM 打标的抽样条数
MIN_KEEP, MAX_KEEP = 30, 50                      # 精选目标区间
PER_TYPE_MIN = 3                                 # 每类 damage_type 至少条数
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = "qwen-plus"
API_INTERVAL = 0.5                               # 防限流间隔(秒)

# 实质灾情关键词(含道路中断类变体)
KEYWORDS = [
    "倒塌", "坍塌", "伤亡", "遇难", "受伤", "被困", "失联", "救援",
    "物资", "安置", "断裂", "裂缝", "滑坡", "海啸", "震感", "疏散",
    "医院", "废墟", "道路中断", "交通中断", "道路损毁", "路面断裂",
    "桥断", "断路", "封路", "道路受损",
]
# damage_type -> severity 映射
SEVERITY_MAP = {
    "人员伤亡": 5, "房屋倒塌": 5, "道路中断": 3,
    "次生灾害": 4, "救援进展": 2, "震感反馈": 1,
}
DAMAGE_TYPES = list(SEVERITY_MAP.keys())
SENTIMENTS = ["urgent", "negative", "neutral", "hopeful"]

# damage_type 定向抽样的特征词(解决稀缺类型在轮转抽样中被稀释的问题)
TYPE_BOOST = {
    "救援进展": ["救援队", "救援人员", "救援力量", "搜救", "救出", "获救", "驰援", "赶赴灾区", "医疗队", "消防员赶到"],
    "道路中断": ["道路中断", "交通中断", "道路损毁", "桥断", "断路", "封路", "道路受损", "路面断裂"],
}
BOOST_PER_TYPE = 3

# 地名词典(纬度, 经度)。注意: 数据集 G/H 列经纬度为发帖人位置且已对调, 不作为坐标来源。
PLACE_DICT = {
    # 缅甸
    "曼德勒": (21.97, 96.08), "内比都": (19.76, 96.07), "仰光": (16.87, 96.20),
    "实皆": (21.88, 95.97), "密支那": (25.38, 97.40), "震中": (22.05, 95.84),
    "缅甸": (22.05, 95.84),
    # 中国(震感城市)
    "昆明": (24.88, 102.83), "大理": (25.61, 100.27), "瑞丽": (24.01, 97.85),
    "保山": (25.12, 99.16), "德宏": (24.43, 98.58), "成都": (30.57, 104.07),
    "雅安": (30.01, 103.04),
}
EPICENTER = (22.05, 95.84)

# 话题标签相关性打分词
TOPIC_SCORE_WORDS = ["地震", "缅甸", "救援", "震", "平安", "灾情", "受灾", "倒塌", "伤亡"]

# ---------------- 文本清洗 ----------------
RE_MENTION = re.compile(r"@[A-Za-z0-9_\u4e00-\u9fff\.\-·]{1,30}")
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_ZWSP = re.compile(r"[\u200b\u200c\u200d\ufeff]")
RE_EMOJI = re.compile(r"\[[^\[\]]{1,8}\]")
RE_TOPIC = re.compile(r"#[^#\s]{1,30}#")
RE_MULTI_SPACE = re.compile(r"\s+")


def clean_text(raw):
    """匿名化+去噪清洗正文, 返回 (清洗后文本, 保留的话题标签或None)。"""
    t = RE_ZWSP.sub("", raw)
    t = RE_URL.sub("", t)
    t = RE_MENTION.sub("", t)
    t = RE_EMOJI.sub("", t)
    topics = RE_TOPIC.findall(t)
    t = RE_TOPIC.sub("", t)
    t = RE_MULTI_SPACE.sub(" ", t).strip()
    # 话题标签: 保留 1 个最相关, 无相关则全部去掉
    kept_topic = None
    if topics:
        def score(tp):
            return sum(1 for w in TOPIC_SCORE_WORDS if w in tp)
        best = max(topics, key=score)
        if score(best) > 0:
            kept_topic = best
    return t, kept_topic


def matched_keywords(text):
    return [k for k in KEYWORDS if k in text]


def anon_id(textid):
    """将原始数字 textid 哈希为匿名短 ID(base36 字母数字混排, 避免纯数字 UID 模式)。"""
    digest = hashlib.sha1(str(textid).encode("utf-8")).digest()
    n = int.from_bytes(digest[:8], "big")
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = chars[r] + s
    s = (s + "0" * 12)[:12]
    if re.search(r"\d{9,}", s):  # 极端情况强制打散
        s = s[:4] + "w" + s[4:8] + "b" + s[8:]
    return "wb-" + s


# ---------------- 数据加载与漏斗 ----------------
def load_and_clean():
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active
    total = 0
    dropped_noise = 0
    records = []          # {textid, text, topic, time, keywords}
    seen = set()          # 正文去重
    dup_count = 0

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if row is None:
            continue
        # 列索引: 0 rowid, 1 userid(实为昵称,丢弃), 2 username(实为UID,丢弃),
        #          3 userlocation, 4 textid, 5 text, 6 geolon(实为纬度,不用),
        #          7 geolat(实为经度,不用), 8 creat_time
        total += 1
        textid, text, creat_time = row[4], row[5], row[8]
        if not text or not creat_time:
            continue
        ts = str(creat_time)
        if ts.startswith(NOISE_DATE):
            dropped_noise += 1
            continue
        cleaned, topic = clean_text(str(text))
        if len(cleaned) < 8:
            continue
        if cleaned in seen:
            dup_count += 1
            continue
        seen.add(cleaned)
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        kws = matched_keywords(cleaned)
        if not kws:
            continue
        records.append({
            "textid": str(textid), "text": cleaned, "topic": topic,
            "time": dt, "keywords": kws,
        })
    wb.close()
    return total, dropped_noise, dup_count, records


# ---------------- 均衡抽样 ----------------
def stratified_sample(records, n=SAMPLE_N, seed=42):
    """按主关键词分组轮转取样 + 稀缺类型定向名额, 03-28 当天优先。"""
    rng = random.Random(seed)
    groups = defaultdict(list)
    for r in records:
        groups[r["keywords"][0]].append(r)
    for g in groups.values():
        rng.shuffle(g)  # 组内随机
        g.sort(key=lambda r: r["time"].date() != QUAKE_TIME.date())  # 当天优先(稳定排序)

    picked, seen_ids = [], set()

    def take(cand):
        if cand["textid"] not in seen_ids and len(cand["text"]) > 40:
            seen_ids.add(cand["textid"])
            picked.append(cand)
            return True
        return False

    # 定向名额: 稀缺类型特征词命中且正文较长的优先入样
    for tname, words in TYPE_BOOST.items():
        pool = [r for r in records
                if any(w in r["text"] for w in words) and len(r["text"]) > 40]
        pool.sort(key=lambda r: (r["time"].date() != QUAKE_TIME.date(), -len(r["text"])))
        added = 0
        for cand in pool:
            if added >= BOOST_PER_TYPE:
                break
            if take(cand):
                added += 1

    # 轮转: 每轮每组取 1 条
    keys = sorted(groups.keys(), key=lambda k: -len(groups[k]))
    while len(picked) < n and any(groups[k] for k in keys):
        for k in keys:
            if len(picked) >= n:
                break
            while groups[k]:
                cand = groups[k].pop(0)
                if take(cand):
                    break
    return picked


# ---------------- LLM 打标 ----------------
def load_api_key():
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DASHSCOPE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key
    raise RuntimeError("未在 backend/.env 找到 DASHSCOPE_API_KEY")


LABEL_PROMPT = (
    "你是地震灾情信息分析员。判断下面这条关于2025年缅甸地震的微博是否包含实质性灾情信息,"
    "并严格输出一个JSON对象(不要任何解释、不要markdown代码块)。字段要求:\n"
    '{"is_substantive": bool, '
    '"damage_type": "房屋倒塌"|"人员伤亡"|"道路中断"|"次生灾害"|"救援进展"|"震感反馈", '
    '"sentiment": "urgent"|"negative"|"neutral"|"hopeful", '
    '"extracted_places": ["地名1", ...], '
    '"summary_reason": "10字内理由"}\n'
    "is_substantive 为 true 表示真实描述了灾情/救援/震感等实质内容,"
    "纯祈祷、转发口号、无关闲聊为 false。\n"
    "extracted_places 输出文中出现的具体地名(城市/地区), 没有则空数组。\n"
    "微博正文:\n"
)


def parse_llm_json(raw):
    """从模型输出中提取 JSON 对象, 容忍 markdown 包裹; 字段非法时容错修正。"""
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no json object")
    obj = json.loads(s[start:end + 1])
    # 字段校验与容错
    obj["is_substantive"] = bool(obj.get("is_substantive", False))
    if obj.get("damage_type") not in DAMAGE_TYPES:
        # 找最接近的合法类型, 否则回退为震感反馈
        cand = str(obj.get("damage_type", ""))
        match = next((t for t in DAMAGE_TYPES if t in cand or cand in t), None)
        obj["damage_type"] = match or "震感反馈"
    if obj.get("sentiment") not in SENTIMENTS:
        obj["sentiment"] = "neutral"
    places = obj.get("extracted_places")
    obj["extracted_places"] = [str(p) for p in places][:5] if isinstance(places, list) else []
    obj["summary_reason"] = str(obj.get("summary_reason", ""))[:20]
    return obj


def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def label_posts(posts, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    cache = load_cache()
    calls, fails = 0, 0
    labeled = []
    for idx, p in enumerate(posts, 1):
        ck = anon_id(p["textid"])
        if ck in cache:
            p["label"] = cache[ck]
            labeled.append(p)
            print(f"  [{idx}/{len(posts)}] cache type={cache[ck]['damage_type']} {p['text'][:25]}...")
            continue
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你严格按要求输出JSON,不加任何多余文字。"},
                {"role": "user", "content": LABEL_PROMPT + p["text"][:400]},
            ],
            "temperature": 0.1,
        }
        obj = None
        for attempt in range(2):  # 失败重试 1 次
            calls += 1
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                obj = parse_llm_json(content)
                break
            except Exception:
                obj = None
                time.sleep(1.5)
        if obj is None:
            fails += 1
            print(f"  [{idx}/{len(posts)}] 打标失败, 丢弃: {p['text'][:30]}...")
        else:
            p["label"] = obj
            cache[ck] = obj
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            labeled.append(p)
            print(f"  [{idx}/{len(posts)}] ok type={obj['damage_type']} "
                  f"sub={obj['is_substantive']} {p['text'][:25]}...")
        time.sleep(API_INTERVAL)
    return labeled, calls, fails


# ---------------- 精选 ----------------
def final_select(labeled):
    subs = [p for p in labeled if p["label"]["is_substantive"]]
    non_subs = [p for p in labeled if not p["label"]["is_substantive"]]

    def info(p):
        return -(len(p["text"]) + (10 if p["topic"] else 0))  # 信息量大的优先

    by_type = defaultdict(list)
    for p in subs:
        by_type[p["label"]["damage_type"]].append(p)
    fallback = defaultdict(list)  # 非实质条目兑底池
    for p in non_subs:
        fallback[p["label"]["damage_type"]].append(p)
    for g in list(by_type.values()) + list(fallback.values()):
        g.sort(key=info)

    picked, used = [], set()

    def take(p):
        if p["textid"] not in used:
            used.add(p["textid"])
            picked.append(p)

    # 每类先取至少 PER_TYPE_MIN 条(实质优先, 不足时用兑底池补)
    for t in DAMAGE_TYPES:
        for p in by_type[t][:PER_TYPE_MIN]:
            take(p)
        if len(by_type[t]) < PER_TYPE_MIN:
            for p in fallback[t][:PER_TYPE_MIN - len(by_type[t])]:
                take(p)
    # 余量按类型条数少者优先补齐到 MAX_KEEP
    remaining = [p for t in DAMAGE_TYPES for p in by_type[t][PER_TYPE_MIN:]]
    remaining.sort(key=lambda p: (len(by_type[p["label"]["damage_type"]]), info(p)))
    for p in remaining:
        if len(picked) >= MAX_KEEP:
            break
        take(p)
    picked.sort(key=lambda p: p["time"])
    return picked[:MAX_KEEP], len(subs), len(labeled)


# ---------------- 坐标与产出 ----------------
def assign_location(places):
    for pl in places:
        for name, (lat, lon) in PLACE_DICT.items():
            if name in pl or pl in name:
                return {"name": pl, "longitude": lon, "latitude": lat,
                        "entity": "GPE", "confidence": 0.85}
    return {"name": "缅甸震中区域", "longitude": EPICENTER[1], "latitude": EPICENTER[0],
            "entity": "GPE", "confidence": 0.4}


def build_output(picked):
    out = []
    for p in picked:
        lab = p["label"]
        offset_min = int((p["time"] - QUAKE_TIME).total_seconds() // 60)
        out.append({
            "post_id": anon_id(p["textid"]),
            "text": (p["topic"] + " " if p["topic"] else "") + p["text"],
            "time": p["time"].isoformat(),
            "offset_after_quake_min": offset_min,
            "extracted_location": assign_location(lab["extracted_places"]),
            "damage_type": lab["damage_type"],
            "keywords_matched": p["keywords"],
            "sentiment": lab["sentiment"],
            "severity_vote": SEVERITY_MAP[lab["damage_type"]],
            "source": "微博(匿名化)",
            "source_type": "social_media",
        })
    return out


# ---------------- 合规校验 ----------------
RE_UID = re.compile(r"\d{9,}")


def compliance_check(posts):
    blob = json.dumps(posts, ensure_ascii=False)
    issues = []
    if RE_MENTION.search(blob):
        issues.append("发现 @提及")
    if "t.cn" in blob:
        issues.append("发现 t.cn 短链")
    for p in posts:
        if RE_UID.search(p["post_id"]):
            issues.append(f"post_id 为数字UID模式: {p['post_id']}")
    ok = not issues
    print("\n[合规校验]", "通过 ✔" if ok else "未通过 ✘ " + "; ".join(issues))
    return ok


# ---------------- 主流程 ----------------
def main():
    print("== 1/6 加载与清洗 ==")
    total, dropped_noise, dup_count, records = load_and_clean()
    print(f"原始行数: {total}")
    print(f"剔除 {NOISE_DATE} 噪声: {dropped_noise} 条")
    print(f"去重剔除: {dup_count} 条 (去重后剩余 {total - dropped_noise - dup_count} 条量级)")
    print(f"关键词初筛后: {len(records)} 条")

    print("\n== 2/6 均衡抽样 ==")
    sampled = stratified_sample(records)
    print(f"抽样 {len(sampled)} 条送 LLM 打标")

    print("\n== 3/6 LLM 打标(qwen-plus) ==")
    api_key = load_api_key()
    labeled, calls, fails = label_posts(sampled, api_key)
    print(f"LLM 调用次数: {calls}, 失败丢弃: {fails}")

    print("\n== 4/6 精选 ==")
    picked, n_sub, n_lab = final_select(labeled)
    print(f"is_substantive=true: {n_sub}/{n_lab}, 精选: {len(picked)} 条")

    print("\n== 5/6 产出 JSON ==")
    out = build_output(picked)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"已写出 {OUT_PATH} ({len(out)} 条)")

    # labels.json: post_id -> 标签映射
    labels = {p["post_id"]: {"damage_type": p["damage_type"], "sentiment": p["sentiment"]}
              for p in out}
    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)
    print(f"已写出 {LABELS_PATH} ({len(labels)} 条)")

    # funnel.json: 数据漏斗统计
    dist = defaultdict(int)
    for p in out:
        dist[p["damage_type"]] += 1
    funnel = {
        "raw_rows": total,
        "noise_2025_01_09_removed": dropped_noise,
        "duplicates_removed": dup_count,
        "after_dedup": total - dropped_noise - dup_count,
        "after_keyword_filter": len(records),
        "sampled": len(sampled),
        "llm_calls": calls,
        "llm_failures": fails,
        "substantive": n_sub,
        "final": len(out),
        "damage_type_distribution": {t: dist[t] for t in DAMAGE_TYPES},
    }
    with open(FUNNEL_PATH, "w", encoding="utf-8") as f:
        json.dump(funnel, f, ensure_ascii=False, indent=2)
    print(f"已写出 {FUNNEL_PATH}")

    print("\n== 6/6 合规校验 ==")
    compliance_check(out)

    # damage_type 分布报告
    print("\n[damage_type 分布]")
    for t in DAMAGE_TYPES:
        print(f"  {t}: {dist[t]}")

    # 漏斗摘要
    print("\n[漏斗] 原始 53,340 -> 去重后 %d -> 初筛后 %d -> 打标保留 %d -> 精选 %d"
          % (total - dropped_noise - dup_count, len(records), n_sub, len(out)))
    print("[LLM] 调用 %d 次, 失败 %d 次" % (calls, fails))

    # 成功产出后清理中间缓存文件
    if os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
        print("[清理] 已删除中间缓存文件")


if __name__ == "__main__":
    main()
