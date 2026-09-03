# 社情感知演示数据说明

本目录为黑客松演示页「社情感知」面板的数据产物，由
`backend/Qwen 初版/scripts/build_social_posts.py` 一键生成（幂等，可重复运行覆盖）。

## 数据来源与授权

- 来源：公开学术数据集《The Weibo data text about the Myanmar earthquake in 2025》
  （2025-03-28 缅甸 7.9 级地震相关中文微博，原始 53,340 条）。
- 授权与合规处理：
  - 用户昵称列与数字 UID 列已**整列丢弃**（匿名化要求）；
  - 正文中的 @提及、t.cn 短链、用户主页链接已剥离；
  - 输出中 `post_id` 为原始文本 ID 的不可逆哈希（`wb-` 前缀），无法反查用户；
  - 产出前自动合规校验（无数字 UID 模式、无 @提及、无短链）。
- 数据仅用于演示展示，不用于训练或二次分发。

## 文件清单

| 文件 | 用途 | 结构 |
| --- | --- | --- |
| `social_posts.json` | **主数据**，前端面板直接内嵌/读取 | 数组，52 条（精选 50 条 + 2 条 Sky Villa 定向补录） |
| `labels.json` | post_id → 标签映射，供面板按类型高亮/过滤 | 对象，键为 post_id |
| `funnel.json` | 数据漏斗统计，供演示页展示清洗过程 | 单对象 |

## social_posts.json 单条字段

```json
{
  "post_id": "wb-xxxxxxxxxxxx",
  "text": "微博正文（已匿名化清洗，可含 1 个保留话题标签）",
  "time": "2025-03-28T15:44:06",
  "offset_after_quake_min": 84,
  "extracted_location": {"name": "瑞丽市", "longitude": 97.85, "latitude": 24.01, "entity": "GPE", "confidence": 0.85},
  "damage_type": "人员伤亡",
  "keywords_matched": ["受伤", "救援", "震感"],
  "sentiment": "urgent",
  "severity_vote": 5,
  "source": "微博(匿名化)",
  "source_type": "social_media"
}
```

- `offset_after_quake_min`：相对发震时刻 2025-03-28T14:20（北京时间）的分钟数，可为负。
- `damage_type` 六类：人员伤亡 / 房屋倒塌 / 道路中断 / 次生灾害 / 救援进展 / 震感反馈。
- `sentiment` 四类：urgent / negative / neutral / hopeful。
- `severity_vote` 映射：人员伤亡 5 / 房屋倒塌 5 / 次生灾害 4 / 道路中断 3 / 救援进展 2 / 震感反馈 1。
- `extracted_location.confidence`：0.85 = 内置地名词典命中；0.4 = 未命中，回退震中坐标（22.05, 95.84）。

## 已知数据偏差（如实说明）

1. **坐标偏差**：原始数据集经纬度列（G/H）仅 1.3% 有值且为发帖人所在城市（中国为主），
   与灾区无关，故**未使用**；本数据坐标来自 LLM 抽取地名 + 内置地名词典，
   未命中时回退震中坐标并降低 confidence。
2. **类别不均衡**：灾害类别（伤亡、倒塌）在精选集中天然偏多，
   「救援进展」「次生灾害」类实质微博较少，已通过定向抽样补足至每类 ≥3 条。
3. **重复内容偏多**：原始数据 25.2% 为「愿平安」类情绪转发，已按正文去重。
4. **噪声已剔除**：2 条 2025-01-09 无关日期数据已移除。
5. **Sky Villa 定向补录（#24）**：首版精选集未覆盖 P0 区域「曼德勒 Sky Villa 公寓」，
   从原始数据集定向检索（Sky Villa/天空公寓，命中 77 条）后补入 2 条最实质真实帖文
   （同款匿名化管线，≤120 字），使优先级排序社情证据链完整。

## 重新生成

```bash
cd backend/Qwen\ 初版/scripts
python3 build_social_posts.py
```

依赖：openpyxl、requests；API Key 从 `backend/.env` 的 `DASHSCOPE_API_KEY` 读取（qwen-plus）。
运行结束后中间缓存自动清理，本目录仅保留上述三个 JSON 与本 README。

> ⚠️ **数据漂移警告**：重跑脚本后必须手动把 `data/social_posts.json` 同步回 `代码1.2-ai.html` 的 `SOCIAL_POSTS` 内嵌块，否则页面数据不会更新。
