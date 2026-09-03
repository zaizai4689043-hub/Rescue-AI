<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* A 区：标题块 */}
  <Box style={{ height: 84, justifyContent: 'center' }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>一场没有预警的地震：<span style={{ color: '#F59E0B' }}>5 小时信息空白</span></Text>
    <Box style={{ width: 64, height: 3, marginTop: 10, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
  </Box>
  {/* B 区：内容 */}
  <Box style={{ height: 516, flexDirection: 'row', gap: 40 }}>
    {/* 左：巨型数字锚点 */}
    <Box style={{ width: 400, justifyContent: 'center', gap: 28 }}>
      <Box>
        <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 1 }}>社媒流传伤亡数字 · 震后</Text>
        <Text style={{ fontSize: 88, fontWeight: 'bold', color: '#22D3EE', fontFamily: 'JetBrains Mono', lineHeight: 1.0 }}>38<span style={{ fontSize: 40 }}>min</span></Text>
      </Box>
      <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <svg width={44} height={24} viewBox='0 0 44 24'>
          <path d='M0 12h36M28 4l8 8-8 8' fill='none' stroke='#F59E0B' strokeWidth='2.5' strokeLinecap='round' />
        </svg>
        <Text style={{ fontSize: 15, color: 'rgba(241,245,249,0.6)', fontFamily: 'Source Han Sans SC' }}>官方首报滞后</Text>
      </Box>
      <Box>
        <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 1 }}>官方首次通报 · 震后</Text>
        <Text style={{ fontSize: 110, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono', lineHeight: 1.0 }}>5<span style={{ fontSize: 48 }}>h</span></Text>
      </Box>
    </Box>
    {/* 右：事实与洞察 */}
    <Box style={{ flex: 1, justifyContent: 'center', gap: 16 }}>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.25)', borderRadius: 12, padding: '18px 22px' }}>
        <Text style={{ fontSize: 19, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC', marginBottom: 6 }}>2025-03-28 · 缅甸 M7.7 地震</Text>
        <Text style={{ fontSize: 16, color: 'rgba(241,245,249,0.75)', lineHeight: 1.6, fontFamily: 'Source Han Sans SC' }}>震中距中国边境 <span style={{ color: '#F59E0B', fontWeight: 'bold' }}>294km</span>，超出地震预警约 50km 覆盖半径；缅甸无国家预警体系——<span style={{ color: '#F59E0B', fontWeight: 'bold' }}>全球没有任何预警发出</span>。</Text>
      </Box>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.25)', borderRadius: 12, padding: '18px 22px' }}>
        <Text style={{ fontSize: 19, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC', marginBottom: 6 }}>社媒成为地面实况的补充感知</Text>
        <Text style={{ fontSize: 16, color: 'rgba(241,245,249,0.75)', lineHeight: 1.6, fontFamily: 'Source Han Sans SC' }}>震后 38 分钟，社媒已在流传伤亡与坍塌信息；官方首报在 5 小时后。截至 3/29 晚通报 <span style={{ color: '#F1F5F9', fontWeight: 'bold' }}>1,644 人</span>遇难，持续更新中。</Text>
      </Box>
      <Box style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.35)', borderRadius: 12, padding: '18px 22px' }}>
        <Text style={{ fontSize: 17, color: '#F59E0B', lineHeight: 1.6, fontFamily: 'Source Han Sans SC', fontWeight: 'bold' }}>这 5 小时的信息空白，正是救援最珍贵的窗口——也是 RescueAI 要抢回的时间。</Text>
      </Box>
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>02 / 10</Text>
  </Box>
</Slide>
