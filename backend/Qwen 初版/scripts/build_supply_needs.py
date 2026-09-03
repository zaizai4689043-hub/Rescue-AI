# -*- coding: utf-8 -*-
"""
build_supply_needs.py — 物资需求 + 失联帖 双管线(克隆 build_social_posts.py 模式)

流程:
  1. 加载 Myanmar.xlsx(昵称/UID 列整列丢弃) -> 匿名化清洗 -> 正文去重 -> 限定震后窗口
  2. 物资需求: 严格口径初筛(需求意图词 × 物资实体词 × 缅甸地名)
     -> qwen-plus 逐条打标 is_substantive/demand_type/location_hint(0.5s间隔)
     -> 精选 15-20 条(text ≤120字) + 六类聚合统计 + 真实援助锚点
  3. 失联帖: 关键词(失联/通讯中断/联系不上/找不到人)初筛 -> LLM 打标
     -> 精选 15 条(强制含 2500 学生失联案例), 同样匿名化与截断
  4. 产出 data/supply_needs.json + data/lost_contact.json -> 合规校验

幂等: 可重复运行; LLM 打标结果缓存于 data/.cache/needs_labels.json 避免重跑烧钱。
体积红线: 两个 JSON 合计 ≤45KB, 脚本自动校验。
注意: API Key 仅从 backend/.env 读取, 全程不明文输出。
"""

import hashlib
import json
import os
import re
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
CACHE_DIR = os.path.join(DATA_DIR, ".cache")
CACHE_PATH = os.path.join(CACHE_DIR, "needs_labels.json")   # LLM 打标缓存(保留, 重跑免费)
SUPPLY_OUT = os.path.join(DATA_DIR, "supply_needs.json")
LOST_OUT = os.path.join(DATA_DIR, "lost_contact.json")

QUAKE_TIME = datetime(2025, 3, 28, 14, 20, 0)   # 发震时刻(北京时间)
WINDOW_START = datetime(2025, 3, 28, 14, 0, 0)  # 仅保留震后窗口内的帖子
TEXT_LIMIT = 120                                 # 单条正文截断上限(字)
SIZE_BUDGET = 45 * 1024                          # 两个 JSON 合计体积红线
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = "qwen-plus"
API_INTERVAL = 0.5                               # 防限流间隔(秒)

SUPPLY_MIN, SUPPLY_MAX = 15, 20                  # 物资需求精选区间
LOST_N = 15                                      # 失联帖精选条数

# 物资需求严格口径: 需求意图词 × 物资实体词 × 缅甸地名, 三者同时命中才入候选
INTENT_WORDS = ["急需", "告急", "求助", "缺乏", "募捐", "急缺", "募集", "求援"]
SUPPLY_WORDS = ["帐篷", "饮用水", "食品", "药品", "献血", "毛毯", "医疗",
                "食物", "净水", "棉被", "被褥", "血袋", "物资", "急救"]
MYANMAR_PLACES = ["曼德勒", "内比都", "仰光", "实皆", "缅甸", "马圭", "勃固", "掸邦", "瓦城"]

# 失联帖关键词
LOST_WORDS = ["失联", "通讯中断", "联系不上", "找不到人", "失去联系", "断联"]

# 2500 学生失联案例定位锚点(楚天都市报 3/29: 曼德勒一华文学院约2500名校外学生因通讯中断失联)
PIN_MARKERS = ["2500", "2,500", "两千五百", "两千五"]

DEMAND_TYPES = ["急救", "饮水", "食品", "帐篷", "毛毯", "献血", "其他"]
LOST_TYPES = ["个人失联", "群体失联", "通讯中断", "寻人求助"]

# 真实援助锚点(来源: 多源核验事实底稿)
AID_ANCHORS = [
    {"anchor": "中国红十字会紧急人道援助",
     "detail": "150万元现汇+300顶帐篷、2000床毛巾被、600张折叠床、2000个赈济家庭包",
     "time_bj": "2025-03-29", "source": "新华社/红会官网/驻缅使馆"},
    {"anchor": "WHO 血袋告急",
     "detail": "WHO 3/29报告灾区急缺创伤包、血袋、麻醉剂; 3/30起灾区最急需食物、饮用水、帐篷",
     "time_bj": "2025-03-29", "source": "联合国新闻/中青报"},
    {"anchor": "中国政府1亿元援助",
     "detail": "3/29 14:12宣布向缅甸提供1亿元紧急人道主义援助, 派出两支救援队, 首批物资3/31启运",
     "time_bj": "2025-03-29 14:12", "source": "国家国际发展合作署/外交部"},
]

LOST_HIGHLIGHT = {
    "title": "曼德勒一所华文学院约2500名校外学生因通讯中断失联",
    "time_bj": "2025-03-29",
    "detail": "该学院早晚制+全日制, 震时约2500名校外学生无法统计安危, 校方公布电话求援并急需大型救灾设备",
    "source": "楚天都市报(数据集内对应微博已核验)",
}

# ---------------- 文本清洗(匿名化, 与 build_social_posts.py 同口径) ----------------
RE_MENTION = re.compile(r"@[A-Za-z0-9_\u4e00-\u9fff\.\-·]{1,30}")
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_ZWSP = re.compile(r"[\u200b\u200c\u200d\ufeff]")
RE_EMOJI = re.compile(r"\[[^\[\]]{1,8}\]")
RE_TOPIC = re.compile(r"#[^#\s]{1,30}#")
RE_MULTI_SPACE = re.compile(r"\s+")
RE_EMPTY_BRACKET = re.compile(r"【\s*】")   # 话题剥离后残留的空括号
RE_UID = re.compile(r"\d{9,}")


def clean_text(raw):
    """匿名化+去噪清洗正文: 去@/链接/表情/话题标签(话题全部剥离, 防异常伤亡词条混入)。"""
    t = RE_ZWSP.sub("", raw)
    t = RE_URL.sub("", t)
    t = RE_MENTION.sub("", t)
    t = RE_EMOJI.sub("", t)
    t = RE_TOPIC.sub("", t)
    t = RE_EMPTY_BRACKET.sub("", t)
    t = RE_MULTI_SPACE.sub(" ", t).strip()
    return t


def anon_id(textid):
    """原始数字 textid -> 不可逆哈希匿名短 ID(同 build_social_posts.py)。"""
    digest = hashlib.sha1(str(textid).encode("utf-8")).digest()
    n = int.from_bytes(digest[:8], "big")
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = chars[r] + s
    s = (s + "0" * 12)[:12]
    if re.search(r"\d{9,}", s):
        s = s[:4] + "w" + s[4:8] + "b" + s[8:]
    return "wb-" + s


def truncate(text, limit=TEXT_LIMIT, focus=None):
    """截断到 limit 字以内; focus 词存在时以其为窗口中心, 避免关键信息被裁掉。"""
    if len(text) <= limit:
        return text
    prefix, start = "", 0
    if focus:
        pos = text.find(focus)
        if pos > 0:
            start = max(0, min(pos - limit // 3, len(text) - limit))
            if start > 0:
                prefix = "…"
    seg_len = limit - len(prefix) - 1
    return prefix + text[start:start + seg_len] + "…"


# ---------------- 数据加载 ----------------
def load_candidates():
    """单次遍历, 同时产出物资需求与失联两类候选。"""
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active
    total, supply_cands, lost_cands = 0, [], []
    seen = set()

    for row in ws.iter_rows(min_row=2, values_only=True):
        if row is None:
            continue
        # 列索引同 build_social_posts.py: 0 rowid, 1 userid(实为昵称,丢弃),
        # 2 username(实为UID,丢弃), 3 userlocation, 4 textid, 5 text,
        # 6 geolon(对调,不用), 7 geolat(对调,不用), 8 creat_time
        total += 1
        textid, text, creat_time = row[4], row[5], row[8]
        if not text or not creat_time:
            continue
        try:
            dt = datetime.strptime(str(creat_time), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if dt < WINDOW_START:      # 震前帖子与灾害需求/失联无关
            continue
        cleaned = clean_text(str(text))
        if len(cleaned) < 12 or cleaned in seen:
            continue
        seen.add(cleaned)
        rec = {"textid": str(textid), "text": cleaned, "time": dt}

        if (any(w in cleaned for w in INTENT_WORDS)
                and any(w in cleaned for w in SUPPLY_WORDS)
                and any(p in cleaned for p in MYANMAR_PLACES)):
            supply_cands.append(rec)
        if any(w in cleaned for w in LOST_WORDS):
            # 独立副本: 同一帖可能同时命中两类, 避免两条管线的 label 互相覆盖
            lost_cands.append(dict(rec))
    wb.close()
    return total, supply_cands, lost_cands


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


SUPPLY_PROMPT = (
    "你是地震救援物资需求分析员。判断这条关于2025年缅甸地震的微博是否表达了"
    "**实质性的物资需求/求助/募捐行动**(如灾区急需某类物资、发起募捐、求助求援)。"
    "纯科普、单纯转发新闻标题、祈祷口号、无关闲聊判 false。"
    "严格输出一个JSON对象(不要解释、不要markdown代码块):\n"
    '{"is_substantive": bool, '
    '"demand_type": "急救"|"饮水"|"食品"|"帐篷"|"毛毯"|"献血"|"其他", '
    '"location_hint": "需求指向的地点(城市/地区,没有则空字符串)", '
    '"reason": "10字内理由"}\n'
    "分类规则: 药品/医疗器械/医疗队归\"急救\"; 献血/血源归\"献血\"; "
    "饮用水/净水归\"饮水\"; 食物/粮食归\"食品\"; 帐篷/安置归\"帐篷\"; "
    "毛毯/棉被/衣物归\"毛毯\"; 多类混合或无法归类取\"其他\"。\n"
    "微博正文:\n"
)

LOST_PROMPT = (
    "你是地震失联信息分析员。判断这条关于2025年缅甸地震的微博是否包含"
    "**实质性的失联/通讯中断信息**(个人或群体联系不上、某地通讯中断、寻人求助)。"
    "单纯新闻转述、科普、祈祷口号判 false。"
    "严格输出一个JSON对象(不要解释、不要markdown代码块):\n"
    '{"is_substantive": bool, '
    '"lost_type": "个人失联"|"群体失联"|"通讯中断"|"寻人求助", '
    '"subject_hint": "失联对象或地点(10字内,没有则空字符串)", '
    '"reason": "10字内理由"}\n'
    "微博正文:\n"
)


def parse_llm_json(raw, kind):
    """从模型输出中提取 JSON, 字段非法时容错修正。kind: 'supply'|'lost'。"""
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no json object")
    obj = json.loads(s[start:end + 1])
    obj["is_substantive"] = bool(obj.get("is_substantive", False))
    if kind == "supply":
        if obj.get("demand_type") not in DEMAND_TYPES:
            obj["demand_type"] = "其他"
        obj["location_hint"] = str(obj.get("location_hint", ""))[:20]
    else:
        if obj.get("lost_type") not in LOST_TYPES:
            obj["lost_type"] = "通讯中断" if obj["is_substantive"] else "个人失联"
        obj["subject_hint"] = str(obj.get("subject_hint", ""))[:20]
    return obj


def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def label_records(records, api_key, cache, prompt, kind, tag):
    """逐条打标(带缓存), 返回 (已打标列表, 调用次数, 失败数)。"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    calls, fails = 0, 0
    labeled = []
    for idx, r in enumerate(records, 1):
        ck = f"{kind}:{anon_id(r['textid'])}"
        if ck in cache:
            r["label"] = cache[ck]
            labeled.append(r)
            continue
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你严格按要求输出JSON,不加任何多余文字。"},
                {"role": "user", "content": prompt + r["text"][:400]},
            ],
            "temperature": 0.1,
        }
        obj = None
        for _ in range(2):  # 失败重试 1 次
            calls += 1
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                obj = parse_llm_json(content, kind)
                break
            except Exception:
                obj = None
                time.sleep(1.5)
        if obj is None:
            fails += 1
            print(f"  [{tag} {idx}/{len(records)}] 打标失败, 丢弃")
        else:
            r["label"] = obj
            cache[ck] = obj
            save_cache(cache)
            labeled.append(r)
            if idx % 25 == 0 or idx == len(records):
                print(f"  [{tag} {idx}/{len(records)}] 进度 ok")
        time.sleep(API_INTERVAL)
    return labeled, calls, fails


# ---------------- 精选 ----------------
def is_pinned(r):
    """2500 学生失联案例识别。"""
    t = r["text"]
    return any(m in t for m in PIN_MARKERS) and ("学生" in t or "学校" in t or "学院" in t)


def select_supply(labeled):
    """实质需求优先, 按 demand_type 轮转均衡, 选 15-20 条。"""
    subs = [r for r in labeled if r["label"]["is_substantive"]]
    by_type = defaultdict(list)
    for r in subs:
        by_type[r["label"]["demand_type"]].append(r)
    for g in by_type.values():
        g.sort(key=lambda r: (r["time"].date() != QUAKE_TIME.date(), -len(r["text"])))

    picked, used = [], set()

    def take(r):
        if r["textid"] not in used:
            used.add(r["textid"])
            picked.append(r)

    # 轮转: 每轮每类取 1 条, 直到达到 SUPPLY_MAX 或取空
    while len(picked) < SUPPLY_MAX and any(by_type.values()):
        for t in DEMAND_TYPES:
            if len(picked) >= SUPPLY_MAX:
                break
            if by_type[t]:
                take(by_type[t].pop(0))
    if len(picked) < SUPPLY_MIN:
        print(f"  [警告] 实质需求仅 {len(picked)} 条, 低于目标下限 {SUPPLY_MIN}")
    picked.sort(key=lambda r: r["time"])
    return picked, len(subs)


def select_lost(labeled):
    """实质失联信息优先, 强制含 2500 学生案例, 选 LOST_N 条。"""
    subs = [r for r in labeled if r["label"]["is_substantive"]]
    pinned = [r for r in labeled if is_pinned(r)]
    if not pinned:
        print("  [警告] 数据集中未找到 2500 学生失联案例! 需人工检查")
    subs.sort(key=lambda r: (r["time"].date() != QUAKE_TIME.date(), -len(r["text"])))

    picked, used = [], set()

    def take(r):
        if r["textid"] not in used:
            used.add(r["textid"])
            picked.append(r)

    for r in pinned[:1]:          # 强制锚点优先入位
        take(r)
    for r in subs:
        if len(picked) >= LOST_N:
            break
        take(r)
    if len(picked) < LOST_N:      # 不足时用非实质条目兜底
        for r in labeled:
            if len(picked) >= LOST_N:
                break
            take(r)
    picked.sort(key=lambda r: r["time"])
    return picked[:LOST_N], len(subs), len(pinned)


# ---------------- 产出 ----------------
def offset_min(dt):
    return int((dt - QUAKE_TIME).total_seconds() // 60)


def build_supply_output(picked, funnel):
    items = []
    for r in picked:
        lab = r["label"]
        items.append({
            "post_id": anon_id(r["textid"]),
            "text": truncate(r["text"], focus=lab.get("location_hint") or None),
            "time": r["time"].isoformat(),
            "offset_after_quake_min": offset_min(r["time"]),
            "demand_type": lab["demand_type"],
            "location_hint": lab.get("location_hint", ""),
            "source": "微博(匿名化)",
        })
    stats = {t: sum(1 for i in items if i["demand_type"] == t) for t in DEMAND_TYPES}
    return {"items": items, "stats": stats, "aid_anchors": AID_ANCHORS, "meta": funnel}


def build_lost_output(picked, funnel):
    items = []
    for r in picked:
        lab = r["label"]
        focus = next((m for m in PIN_MARKERS if m in r["text"]), None) or \
            next((w for w in LOST_WORDS if w in r["text"]), None)
        items.append({
            "post_id": anon_id(r["textid"]),
            "text": truncate(r["text"], focus=focus),
            "time": r["time"].isoformat(),
            "offset_after_quake_min": offset_min(r["time"]),
            "lost_type": lab.get("lost_type", "通讯中断"),
            "subject_hint": lab.get("subject_hint", ""),
            "pinned_case": is_pinned(r),
            "source": "微博(匿名化)",
        })
    return {"items": items, "highlight": LOST_HIGHLIGHT, "meta": funnel}


# ---------------- 合规校验 ----------------
def compliance_check(items, name):
    blob = json.dumps(items, ensure_ascii=False)
    issues = []
    if RE_MENTION.search(blob):
        issues.append("发现 @提及")
    if "t.cn" in blob:
        issues.append("发现 t.cn 短链")
    if re.search(r"https?://", blob):
        issues.append("发现外链")
    for it in items:
        if RE_UID.search(it["post_id"]):
            issues.append(f"post_id 为数字UID模式: {it['post_id']}")
        if len(it["text"]) > TEXT_LIMIT:
            issues.append(f"text 超长({len(it['text'])}): {it['post_id']}")
    ok = not issues
    print(f"[合规校验 {name}]", "通过 ✔" if ok else "未通过 ✘ " + "; ".join(issues))
    return ok


# ---------------- 主流程 ----------------
def main():
    print("== 1/5 加载与初筛 ==")
    total, supply_cands, lost_cands = load_candidates()
    print(f"原始行数: {total} | 震后窗口内去重后: 物资需求候选 {len(supply_cands)} 条, "
          f"失联候选 {len(lost_cands)} 条")

    print("\n== 2/5 LLM 打标(qwen-plus, 0.5s间隔, 缓存 data/.cache/) ==")
    api_key = load_api_key()
    cache = load_cache()
    supply_labeled, s_calls, s_fails = label_records(
        supply_cands, api_key, cache, SUPPLY_PROMPT, "supply", "物资")
    lost_labeled, l_calls, l_fails = label_records(
        lost_cands, api_key, cache, LOST_PROMPT, "lost", "失联")
    print(f"LLM 调用: 物资 {s_calls} 次(失败{s_fails}), 失联 {l_calls} 次(失败{l_fails})")

    print("\n== 3/5 精选 ==")
    supply_picked, n_supply_sub = select_supply(supply_labeled)
    lost_picked, n_lost_sub, n_pinned = select_lost(lost_labeled)
    print(f"物资: 实质 {n_supply_sub}/{len(supply_labeled)} -> 精选 {len(supply_picked)} 条")
    print(f"失联: 实质 {n_lost_sub}/{len(lost_labeled)} -> 精选 {len(lost_picked)} 条 "
          f"(2500学生案例命中 {n_pinned} 条)")

    print("\n== 4/5 产出 JSON ==")
    supply_funnel = {
        "dataset": "Myanmar.xlsx(53340条微博, 昵称/UID列已整列丢弃)",
        "window": "2025-03-28 14:00 起(北京时间)",
        "filter": "需求意图词×物资实体词×缅甸地名 三重命中",
        "candidates": len(supply_cands), "labeled": len(supply_labeled),
        "substantive": n_supply_sub, "selected": len(supply_picked),
        "model": MODEL, "llm_calls": s_calls,
        "note": "text截断≤120字; 伤亡词条异常数据未采信",
    }
    lost_funnel = {
        "filter": "关键词: " + "/".join(LOST_WORDS),
        "candidates": len(lost_cands), "labeled": len(lost_labeled),
        "substantive": n_lost_sub, "selected": len(lost_picked),
        "model": MODEL, "llm_calls": l_calls,
        "note": "text截断≤120字; pinned_case=2500学生失联案例",
    }
    supply_obj = build_supply_output(supply_picked, supply_funnel)
    lost_obj = build_lost_output(lost_picked, lost_funnel)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SUPPLY_OUT, "w", encoding="utf-8") as f:
        json.dump(supply_obj, f, ensure_ascii=False, indent=2)
    with open(LOST_OUT, "w", encoding="utf-8") as f:
        json.dump(lost_obj, f, ensure_ascii=False, indent=2)
    s1, s2 = os.path.getsize(SUPPLY_OUT), os.path.getsize(LOST_OUT)
    print(f"已写出 {SUPPLY_OUT} ({len(supply_obj['items'])} 条, {s1} bytes)")
    print(f"已写出 {LOST_OUT} ({len(lost_obj['items'])} 条, {s2} bytes)")
    print(f"体积合计: {s1 + s2} bytes (红线 {SIZE_BUDGET}) "
          f"{'✔' if s1 + s2 <= SIZE_BUDGET else '✘ 超限!'}")

    print("\n== 5/5 合规校验 ==")
    ok1 = compliance_check(supply_obj["items"], "supply_needs")
    ok2 = compliance_check(lost_obj["items"], "lost_contact")

    print("\n[物资需求六类统计]", supply_obj["stats"])
    if not (ok1 and ok2 and s1 + s2 <= SIZE_BUDGET):
        raise SystemExit("存在未通过项, 请检查上方输出")
    print("\n全部通过 ✔")


if __name__ == "__main__":
    main()
