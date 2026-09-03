<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* A 区：标题块 */}
  <Box style={{ height: 84, justifyContent: 'center' }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>真实数据 · <span style={{ color: '#F59E0B' }}>全链路验证</span></Text>
    <Box style={{ width: 64, height: 3, marginTop: 10, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
  </Box>
  {/* B 区：巨型数字非对称排布 */}
  <Box style={{ height: 516, justifyContent: 'center', gap: 30 }}>
    {/* 第一行：主锚点 53340 + 次锚点 8 */}
    <Box style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 60 }}>
      <Box>
        <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 1, marginBottom: 4 }}>缅甸地震真实微博数据集</Text>
        <Text style={{ fontSize: 104, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono', lineHeight: 1.0 }}>53,340</Text>
        <Text style={{ fontSize: 16, color: 'rgba(241,245,249,0.65)', fontFamily: 'Source Han Sans SC', marginTop: 6 }}>条社媒数据完成全链路验证 · 72% 集中在发震当天 · 已匿名化</Text>
      </Box>
      <Box style={{ paddingBottom: 8 }}>
        <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 1, marginBottom: 4 }}>历史救援案例知识库</Text>
        <Text style={{ fontSize: 72, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono', lineHeight: 1.0 }}>8</Text>
        <Text style={{ fontSize: 15, color: 'rgba(241,245,249,0.65)', fontFamily: 'Source Han Sans SC', marginTop: 6 }}>汶川 → 缅甸 · 十维加权匹配</Text>
      </Box>
    </Box>
    {/* 第二行：两个次级数字 + 洞察 */}
    <Box style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 60 }}>
      <Box>
        <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 1, marginBottom: 4 }}>AI 灾情简报生成耗时</Text>
        <Text style={{ fontSize: 64, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono', lineHeight: 1.0 }}>&lt;3s</Text>
        <Text style={{ fontSize: 15, color: 'rgba(241,245,249,0.65)', fontFamily: 'Source Han Sans SC', marginTop: 6 }}>Qwen3.8-Max · 应急管理部通报风格 · ≤200 字</Text>
      </Box>
      <Box>
        <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 1, marginBottom: 4 }}>首条涉震微博早于主震</Text>
        <Text style={{ fontSize: 64, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'JetBrains Mono', lineHeight: 1.0 }}>1<span style={{ fontSize: 30 }}>分</span>46<span style={{ fontSize: 30 }}>秒</span></Text>
        <Text style={{ fontSize: 15, color: 'rgba(241,245,249,0.65)', fontFamily: 'Source Han Sans SC', marginTop: 6 }}>社媒成为地面实况的补充感知源</Text>
      </Box>
    </Box>
    {/* 数据来源条 */}
    <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.2)', borderRadius: 10, padding: '12px 18px' }}>
      <Text style={{ fontSize: 14, color: 'rgba(241,245,249,0.7)', lineHeight: 1.6, fontFamily: 'Source Han Sans SC' }}>
        <span style={{ color: '#22D3EE', fontWeight: 'bold' }}>数据来源（可查验）</span>　震情目录 USGS ComCat · 社媒数据 缅甸地震微博数据集 · 伤亡与救援锚点 新华社/央视/应急管理部/WHO · 预警数据 ICL（成都高新减灾研究所）
      </Text>
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>09 / 10</Text>
  </Box>
</Slide>
