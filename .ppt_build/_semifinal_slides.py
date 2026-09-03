# -*- coding: utf-8 -*-
"""复赛专有章节（任务 #14）：Agent 架构 / 工具调用 / 风险边界 / 评测指标。

沿用 build_ppt.py 的样式函数（page_header / tbox / rect / bar / footer）与设计常量，
内容全部来自仓库既有文档，数字原样引用，不虚构：
  - 评测指标：outputs/评测指标.md §6「PPT 浓缩版」10 条
  - Agent 架构：README.md 核心能力/仓库结构 + backend/Qwen 初版/演示须知.md 两幕七步闭环
  - 工具调用：README.md 快速开始/路线图 + 演示须知「真实数据来源」「真机接入方式」
  - 风险边界：数据来源与合规说明.md（四/六/七章）
"""


def add_semifinal_slides(ctx, which):
    """which ∈ {'agent', 'tools', 'risk', 'metrics'}；ctx 为 build_ppt 的命名空间。"""
    globals().update(ctx)
    {'agent': _slide_agent, 'tools': _slide_tools,
     'risk': _slide_risk, 'metrics': _slide_metrics}[which]()


# =====================================================================
# 复赛新增 · Agent 架构（插入于核心能力之后、数据底座之前）
# =====================================================================
def _slide_agent():
    s = new_slide(asset('bg_content.png'))
    page_header(s, 'AGENT ARCHITECTURE', 'Agent 架构：感知→聚合→研判→决策→交付')
    steps = [
        ('感知', C_ACCENT, 'ICL 预警 × 微博社情 × USGS 余震目录，双通道互为校验'),
        ('聚合', C_ACCENT, '清洗 → 去重 → NER 地名上图，53,340 条漏斗至 52 条精选'),
        ('研判', C_PURPLE, 'Qwen-VL 结构四值 · Qwen3.8-Max 灾情简报 / 余震参谋'),
        ('决策', C_AMBER, 'P0–P3 优先级引擎，逐档附社情证据链，逐条可解释'),
        ('交付', C_GREEN, '一键派遣 → 五阶段状态机 → 复盘参谋；余震联动保安全'),
    ]
    sx = 1.5
    for i, (name, c, txt) in enumerate(steps):
        rect(s, sx, 4.0, 5.35, 1.7, fill='0D1A24', edge=c, edge_w=1.4)
        tbox(s, sx, 4.0, 5.35, 1.7,
             [[(name, dict(font=F_CN, size=17, color=C_WHITE, bold=True))]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 4:
            a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Cm(sx + 5.42), Cm(4.4), Cm(0.72), Cm(0.9))
            a.fill.solid()
            a.fill.fore_color.rgb = RGBColor.from_string(c)
            a.line.fill.background()
            a.shadow.inherit = False
        tbox(s, sx, 5.95, 5.35, 2.7, [[(txt, dict(font=F_CN, size=11.5, color=C_DIM))]],
             line_spacing=1.15)
        sx += 6.2
    tbox(s, 1.5, 8.8, 30.8, 0.8, [
        [('同一闭环支撑两幕演示：第一幕「历史重演」真实数据回测验证，第二幕「数字孪生沙盘」推演展开（七步链路贯穿两幕）。',
          dict(font=F_CN, size=12.5, color=C_WHITE, bold=True))]])
    cards = [
        (C_ACCENT, '双演示载体', [
            '主演示：Qwen 初版（ai_proxy.py + 单页指挥中心，真 AI · 零依赖，评委演示唯一入口）',
            '标准平台：FastAPI + Vue3 建设中，平台化合入按 Roadmap 推进']),
        (C_AMBER, '实时层适配器', [
            'live_feed.py（端口 8012）：mock 离线流 ↔ weibo 官方通道，按需切换',
            '主页面零耦合：重演 / 保险丝模式对实时层零触发，接入与否不影响主流程']),
        (C_GREEN, '三级降级保险丝', [
            '真 AI → 预录兜底 → ?sim=1 纯仿真（0 个 AI 请求 · 0 网络依赖）',
            '断网 / 断密钥全流程可演示 —— 降级是产品能力，不是应急补丁']),
    ]
    cx = 1.5
    for c, h1, items in cards:
        rect(s, cx, 9.85, 10.1, 6.9)
        bar(s, cx + 0.55, 10.4, 1.5, 0.16, c)
        tbox(s, cx + 0.55, 10.75, 9.0, 1.0,
             [[(h1, dict(font=F_CN, size=16.5, color=C_WHITE, bold=True))]])
        lines = [[('·  ', dict(font=F_CN, size=12, color=c, bold=True)),
                  (t, dict(font=F_CN, size=12, color=C_DIM))] for t in items]
        tbox(s, cx + 0.55, 12.0, 9.0, 4.5, lines, space_after=9, line_spacing=1.18)
        cx += 10.55
    rect(s, 1.5, 17.05, 30.8, 1.05, fill='0D1A24', edge='1F4A5E')
    tbox(s, 2.1, 17.2, 29.8, 0.8, [
        [('定位红线：', dict(font=F_CN, size=12, color=C_AMBER, bold=True)),
         ('Agent 只做聚合、研判与排序 —— 辅助决策，不替代专业救援判断；一切行动以现场指挥部为准。',
          dict(font=F_CN, size=12, color=C_DIM))]])
    footer(s)


# =====================================================================
# 复赛新增 · 工具调用（插入于 Agent 架构之后、数据底座之前）
# =====================================================================
def _slide_tools():
    s = new_slide(asset('bg_content.png'))
    page_header(s, 'TOOL CALLING', '工具调用：Agent 的六项工具与通道，状态如实标注')
    rows = [
        ('weibo-cli · 微博官方实时检索', '实时社情通道：认证获批后切换真实时社情流', '申请中', C_AMBER,
         '认证与订阅申请中；明确不自建爬虫、不使用无官方背书的第三方聚合接口'),
        ('DashScope · Qwen3.8-Max（文本）', '灾情简报 / 优先级决策理由 / 余震参谋 / 喊话 / 复盘', '已接入', C_GREEN,
         '经 ai_proxy 代理统一调用；视觉 20s / 文本 5s 超时自动兜底'),
        ('Qwen-VL 多模态（视觉）', '震后照片结构研判四值：墙体匹配 / 承重构件 / 疑似空隙 / 结构完整度', '已接入', C_GREEN,
         '支持换图重测，非硬编码默认值（实测渲染 ≠ 硬编码假值）'),
        ('USGS ComCat / ICL 预警快照', '震情目录历史回放（us7000pn9s）× 国内预警能力对照与离线快照降级', '已接入', C_GREEN,
         'ICL 来自成都高新减灾研究所；断网自动回落离线快照（offline:true）'),
        ('无人机遥测接口（DJI Cloud API / MAVLink）', 'DRONE_TELEMETRY_SCHEMA 帧协议 → POST /drone/telemetry', '预留', C_PURPLE,
         '当前数字孪生仿真驱动；同一协议三步替换实机，画面逻辑零改动'),
        ('Playwright 验收 harness', '10 脚本 / ≈90 项断言回归，覆盖重演 / 研判 / 救援 / 复盘 / 弱网', '已接入', C_GREEN,
         '每次改动自动回归，杜绝「现场才坏」'),
    ]
    ry = 4.0
    for name, role, badge, c, note in rows:
        rect(s, 1.5, ry, 30.8, 1.95)
        bar(s, 2.0, ry + 0.32, 0.16, 1.3, c)
        tbox(s, 2.4, ry + 0.22, 16.6, 1.6, [
            [(name, dict(font=F_CN, size=13.5, color=C_WHITE, bold=True))],
            [(role, dict(font=F_CN, size=11, color=C_DIM))]], space_after=2)
        tbox(s, 19.3, ry + 0.55, 7.3, 1.0,
             [[(note, dict(font=F_CN, size=10, color=C_FAINT))]], line_spacing=1.1)
        rect(s, 27.3, ry + 0.48, 4.3, 0.95, fill='101826', edge=c, edge_w=1.2, radius=0.22)
        tbox(s, 27.3, ry + 0.48, 4.3, 0.95,
             [[(badge, dict(font=F_CN, size=12.5, color=c, bold=True))]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        ry += 2.2
    rect(s, 1.5, 17.3, 30.8, 0.85, fill='0D1A24', edge='1F4A5E')
    tbox(s, 2.1, 17.42, 29.8, 0.7, [
        [('状态口径与《数据来源与合规说明.md》一致：', dict(font=F_CN, size=11.5, color=C_ACCENT, bold=True)),
         ('已接入 = 演示可跑可复现；申请中 = 以官方渠道授权为准；预留 = 接口已就绪、未接外部系统。',
          dict(font=F_CN, size=11.5, color=C_DIM))]])
    footer(s)


# =====================================================================
# 复赛新增 · 风险边界（插入于工程可靠性之后、实战印证之前）
# =====================================================================
def _slide_risk():
    s = new_slide(asset('bg_content.png'))
    page_header(s, 'RISK BOUNDARIES', '风险边界：先把「不做什么」说清楚')
    def _card(cx, cy, w, c, h1, items):
        rect(s, cx, cy, w, 4.35)
        bar(s, cx + 0.5, cy + 0.45, 1.4, 0.16, c)
        tbox(s, cx + 0.5, cy + 0.8, w - 1.0, 0.9,
             [[(h1, dict(font=F_CN, size=15.5, color=C_WHITE, bold=True))]])
        lines = [[('·  ', dict(font=F_CN, size=11.5, color=c, bold=True)),
                  (t, dict(font=F_CN, size=11.5, color=C_DIM))] for t in items]
        tbox(s, cx + 0.5, cy + 1.85, w - 1.0, 2.35, lines, space_after=5, line_spacing=1.12)
    _card(1.5, 4.0, 15.3, C_GREEN, '合规获取 · 不自建爬虫', [
        '仅经微博开放平台官方通道（weibo-cli / 官方商业 API），认证与订阅申请中',
        '不使用无官方背书的第三方聚合接口；取得正式授权前不接入任何实时社媒数据'])
    _card(17.0, 4.0, 15.3, C_GREEN, '脱敏管线 · 自动合规校验', [
        '昵称列与数字 UID 列整列丢弃；@提及、t.cn 短链、用户主页链接全部剥离',
        'post_id 为不可逆哈希；产出前自动校验不通过即拦截；仅演示、不训练、不二次分发'])
    _card(1.5, 8.65, 15.3, C_ACCENT, '辅助决策定位 · 不替代专业判断', [
        '一切简报 / 评分 / 优先级 / 建议均为辅助参考，系统不承担任何行动指令职能',
        '一切救援行动以现场指挥部与专业救援力量的判断为准'])
    _card(17.0, 8.65, 15.3, C_AMBER, '谣言过滤 · 交叉验证', [
        '去重 / 辟谣 / 机器人识别 / 地理围栏四层过滤；社情信号与官方通报交叉验证',
        '无社情匹配的区域如实显示「社情信号 ×0 · 依据官方通报」，不编造；模型推断均附依据与置信度'])
    rect(s, 1.5, 13.3, 19.9, 4.35, fill='1A1014', edge='5C3A44')
    bar(s, 2.0, 13.75, 1.4, 0.16, C_RED)
    tbox(s, 2.0, 14.1, 18.9, 0.9,
         [[('口径红线管理（内置 prompt 与页面文案，勿改）', dict(font=F_CN, size=15.5, color=C_WHITE, bold=True))]])
    tbox(s, 2.0, 15.1, 18.9, 2.4, [
        [('·  ', dict(font=F_CN, size=11.5, color=C_RED, bold=True)),
         ('震级双口径并列：CENC 7.9 / USGS Mw 7.7，引用须注明来源', dict(font=F_CN, size=11.5, color=C_DIM))],
        [('·  ', dict(font=F_CN, size=11.5, color=C_RED, bold=True)),
         ('死亡「截至 3/29 晚通报 1,644 人，持续更新中」；社媒伤亡数字约震后 5 分钟流传，不可直接作为通报口径',
          dict(font=F_CN, size=11.5, color=C_DIM))],
        [('·  ', dict(font=F_CN, size=11.5, color=C_RED, bold=True)),
         ('首条涉震微博早于主震 1 分 46 秒 —— 社媒是最快的第一传感器，但数字以官方通报为准',
          dict(font=F_CN, size=11.5, color=C_DIM))]],
        space_after=5, line_spacing=1.12)
    _card(21.8, 13.3, 10.5, C_PURPLE, '三级降级保险丝', [
        '真 AI → 预录兜底 → ?sim=1 纯仿真',
        '断网 / 断密钥全流程可演示，页面降级不崩、无感切换'])
    rect(s, 1.5, 17.85, 30.8, 0.35)
    tbox(s, 2.1, 17.87, 29.8, 0.35, [
        [('依据：《数据来源与合规说明.md》（V1.0，复赛「数据来源与合规说明」必交项）—— 逐项授权、脱敏与边界可核查',
          dict(font=F_CN, size=10.5, color=C_FAINT))]])
    footer(s)


# =====================================================================
# 复赛新增 · 评测指标（插入于风险边界之后、实战印证之前）
# =====================================================================
def _slide_metrics():
    s = new_slide(asset('bg_content.png'))
    page_header(s, 'EVALUATION METRICS', '评测指标：十条实测数字，全部答得上来')
    blocks = [
        ('时效', C_ACCENT, [
            ('≈3.0s', 'AI 灾情简报冷启动端到端出稿，双口径震级与 1,644 死亡口径自动合规'),
            ('≈3.3~4.0s', 'Qwen-VL 纯模型调用；含坍塌推演动画端到端 ≈17s'),
            ('1.6~2.4s', '余震参谋触发到建议上屏'),
            ('0.97~1.0s', '喊话气泡端到端（缓存）/ 兜底 65ms，≤2s 全达标')]),
        ('质量', C_AMBER, [
            ('8/8', '决策理由全域被困者全覆盖'),
            ('16.4 分', '空投目标 = 引擎第一名曼德勒市区，交叉核验 = 8'),
            ('85%/4/3/20%', '结构研判四值真实渲染，无硬编码假值')]),
        ('管线', C_PURPLE, [
            ('53,340→52', '社情漏斗：→ 40,595 → 9,617 → 65 → 52'),
            ('100 / 0', 'LLM 甄别 100 次调用 0 失败')]),
        ('可靠', C_GREEN, [
            ('= 0', '?sim=1 外部请求（五处复测一致）'),
            ('3/3', '代理宕机自动兜底，秒回 ≤1.0s'),
            ('0.5~2.0ms', '实时社情层 HTTP 秒回，上游失联自动降级不阻塞')]),
        ('回归', C_RED, [
            ('10 / ≈90', '验收脚本 / 断言全绿'),
            ('9 项', '回测口径逐项吻合')]),
    ]
    layout = [(1.5, 4.0, 15.3, 7.9), (17.0, 4.0, 15.3, 7.9),
              (1.5, 12.2, 9.9, 5.1), (11.95, 12.2, 10.2, 5.1), (22.6, 12.2, 9.7, 5.1)]
    for (name, c, items), (x, y, w, h) in zip(blocks, layout):
        rect(s, x, y, w, h)
        bar(s, x + 0.5, y + 0.42, 1.4, 0.15, c)
        tbox(s, x + 0.5, y + 0.75, w - 1.0, 0.8,
             [[(name, dict(font=F_CN, size=15, color=C_WHITE, bold=True))]])
        paras = []
        for big, txt in items:
            paras.append([(big, dict(font=F_EN, size=17, color=c, bold=True))])
            paras.append([(txt, dict(font=F_CN, size=10.5, color=C_DIM))])
            paras.append([('', dict(font=F_CN, size=4))])
        tbox(s, x + 0.5, y + 1.7, w - 1.0, h - 1.9, paras, space_after=1, line_spacing=1.08)
    rect(s, 1.5, 17.65, 30.8, 0.62, fill='0D1A24', edge='1F4A5E')
    tbox(s, 2.1, 17.73, 29.8, 0.5, [
        [('数字原样引自《评测指标实测报告》§「PPT 浓缩版」：',
          dict(font=F_CN, size=10.5, color=C_ACCENT, bold=True)),
         ('2026-08-28 当日本机真 AI 模式实测（非保险丝，fallbackCount=0）；完整报告见 outputs/评测指标.md。',
          dict(font=F_CN, size=10.5, color=C_DIM))]])
    footer(s)
