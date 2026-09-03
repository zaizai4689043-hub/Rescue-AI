<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* A 区：标题块 */}
  <Box style={{ height: 84, justifyContent: 'center' }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>问题二 · 先救哪里？<span style={{ color: '#F59E0B' }}>P0–P3 动态优先级</span></Text>
    <Box style={{ width: 64, height: 3, marginTop: 10, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
  </Box>
  {/* B 区：左标题 + 右内容 */}
  <Box style={{ height: 516, flexDirection: 'row', gap: 36 }}>
    {/* 左：排序逻辑（窄栏） */}
    <Box style={{ width: 330, justifyContent: 'center', gap: 16 }}>
      <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC', lineHeight: 1.4 }}>呼救信号驱动的<br />四步排序引擎</Text>
      <Box style={{ gap: 10 }}>
        <Box style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono' }}>①</Text>
          <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.75)', lineHeight: 1.5, fontFamily: 'Source Han Sans SC' }}>基础评分 = 帖量 × 严重度 × 可信度</Text>
        </Box>
        <Box style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono' }}>②</Text>
          <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.75)', lineHeight: 1.5, fontFamily: 'Source Han Sans SC' }}>呼救加权：「救命/被困/紧急」信号区域 ×1.5</Text>
        </Box>
        <Box style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono' }}>③</Text>
          <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.75)', lineHeight: 1.5, fontFamily: 'Source Han Sans SC' }}>资源约束：已有队伍/道路中断/超 72h 逐级扣减</Text>
        </Box>
        <Box style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
          <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono' }}>④</Text>
          <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.75)', lineHeight: 1.5, fontFamily: 'Source Han Sans SC' }}>Qwen3.8-Max 生成每档排序理由，证据链可溯</Text>
        </Box>
      </Box>
      <Box style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.3)', borderRadius: 10, padding: '12px 14px' }}>
        <Text style={{ fontSize: 13.5, color: '#22D3EE', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>真实灾情里资源永远不够同时救所有地方——排序的价值，就是把最紧缺的资源投向最危急的坐标。</Text>
      </Box>
    </Box>
    {/* 右：P0-P3 四级条带 */}
    <Box style={{ flex: 1, justifyContent: 'center', gap: 12 }}>
      {[
        { p: 'P0', c: '#EF4444', bg: 'rgba(239,68,68,0.10)', bd: 'rgba(239,68,68,0.45)', t: '立即派遣', loc: '实皆省震中区 · 曼德勒 Sky Villa 公寓', d: '倒塌形态严重 · 呼救信号最密集 · 被困 60+ 小时女童与孕妇在此获救（真实案例锚点）', act: '重型破拆队 + 生命探测仪' },
        { p: 'P1', c: '#F97316', bg: 'rgba(249,115,22,0.10)', bd: 'rgba(249,115,22,0.45)', t: '优先派遣', loc: '曼德勒市区', d: '多建筑受损 · 医院学校受损 · 人口密度高', act: '搜救队 + 医疗队同步跟进' },
        { p: 'P2', c: '#F59E0B', bg: 'rgba(245,158,11,0.08)', bd: 'rgba(245,158,11,0.4)', t: '常规搜救', loc: '中国瑞丽', d: '跨境震感明显 · 房屋开裂 · 需排查次生风险', act: '边境排查 + 物资前置' },
        { p: 'P3', c: '#94A3B8', bg: 'rgba(100,116,139,0.10)', bd: 'rgba(100,116,139,0.4)', t: '持续监测', loc: '泰国曼谷', d: '在建大楼坍塌 · 距离震中远 · 舆情跟踪即可', act: '信息跟踪 + 舆情值守' },
      ].map((r, i) => (
        <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 16, background: r.bg, border: `1px solid ${r.bd}`, borderRadius: 12, padding: '12px 18px' }}>
          <Box style={{ width: 64, alignItems: 'center' }}>
            <Text style={{ fontSize: 30, fontWeight: 'bold', color: r.c, fontFamily: 'JetBrains Mono' }}>{r.p}</Text>
            <Text style={{ fontSize: 12, color: r.c, fontFamily: 'Source Han Sans SC' }}>{r.t}</Text>
          </Box>
          <Box style={{ flex: 1 }}>
            <Text style={{ fontSize: 16.5, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>{r.loc}</Text>
            <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.62)', lineHeight: 1.45, fontFamily: 'Source Han Sans SC', marginTop: 3 }}>{r.d}</Text>
          </Box>
          <Box style={{ width: 190 }}>
            <Text style={{ fontSize: 12, color: 'rgba(148,163,184,0.8)', fontFamily: 'JetBrains Mono' }}>ACTION</Text>
            <Text style={{ fontSize: 13.5, color: r.c, fontFamily: 'Source Han Sans SC', lineHeight: 1.4, marginTop: 2 }}>{r.act}</Text>
          </Box>
        </Box>
      ))}
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>06 / 10</Text>
  </Box>
</Slide>
