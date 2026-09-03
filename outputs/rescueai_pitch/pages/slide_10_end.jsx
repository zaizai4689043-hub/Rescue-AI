<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* 背景微光装饰 */}
  <Box style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'radial-gradient(ellipse at 50% 42%, rgba(245,158,11,0.07) 0%, rgba(15,23,42,0) 55%)' }} />
  <Box style={{ position: 'relative', zIndex: 1, height: '100%', justifyContent: 'center', alignItems: 'center', gap: 44 }}>
    {/* 存活率递减条 */}
    <Box style={{ alignItems: 'center', gap: 14 }}>
      <Text style={{ fontSize: 15, color: 'rgba(148,163,184,1)', fontFamily: 'JetBrains Mono', letterSpacing: 2 }}>被埋人员存活率 · 黄金 72 小时</Text>
      <Box style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 28 }}>
        <Box style={{ alignItems: 'center', gap: 6 }}>
          <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono' }}>80%</Text>
          <Box style={{ width: 88, height: 10, borderRadius: 5, background: '#F59E0B', opacity: 0.95 }} />
          <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.6)', fontFamily: 'Source Han Sans SC' }}>24h</Text>
        </Box>
        <Box style={{ alignItems: 'center', gap: 6 }}>
          <Text style={{ fontSize: 30, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono', opacity: 0.75 }}>50%</Text>
          <Box style={{ width: 88, height: 10, borderRadius: 5, background: '#F59E0B', opacity: 0.6 }} />
          <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.6)', fontFamily: 'Source Han Sans SC' }}>48h</Text>
        </Box>
        <Box style={{ alignItems: 'center', gap: 6 }}>
          <Text style={{ fontSize: 26, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono', opacity: 0.5 }}>30%</Text>
          <Box style={{ width: 88, height: 10, borderRadius: 5, background: '#F59E0B', opacity: 0.35 }} />
          <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.6)', fontFamily: 'Source Han Sans SC' }}>72h</Text>
        </Box>
      </Box>
      <Text style={{ fontSize: 16, color: 'rgba(241,245,249,0.65)', fontFamily: 'Source Han Sans SC' }}>救援拼的不是人力，是时间。</Text>
    </Box>
    {/* 金句 */}
    <Box style={{ alignItems: 'center', gap: 20 }}>
      <Box style={{ width: 72, height: 3, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
      <Text style={{ fontSize: 46, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC', textAlign: 'center', lineHeight: 1.4 }}>
        AI 不替代救援者，<br />它做的只是把<span style={{ color: '#F59E0B' }}>时间</span>抢回来。
      </Text>
      <Box style={{ width: 72, height: 3, background: 'linear-gradient(90deg, #22D3EE, #F59E0B)', borderRadius: 2 }} />
    </Box>
    {/* 品牌落款 */}
    <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
      <svg width={30} height={30} viewBox='0 0 40 40'>
        <path d='M20 2 36 8v10c0 10-7 17-16 20C11 35 4 28 4 18V8Z' fill='none' stroke='#F59E0B' strokeWidth='2.4' />
        <path d='M20 12v16M12 20h16' stroke='#22D3EE' strokeWidth='3.2' strokeLinecap='round' />
      </svg>
      <Text style={{ fontSize: 17, fontWeight: 'bold', color: 'rgba(241,245,249,0.85)', fontFamily: 'Source Han Sans SC' }}>RescueAI</Text>
      <Text style={{ fontSize: 13, color: 'rgba(148,163,184,0.8)', fontFamily: 'JetBrains Mono', letterSpacing: 2 }}>PHYSICAL AI FOR EARTHQUAKE RESCUE</Text>
    </Box>
  </Box>
</Slide>
