<Slide style={{ padding: 0, background: '#0F172A' }}>
  <Box style={{ position: 'relative', width: '100%', height: '100%' }}>
    {/* L1 全幅主视觉 */}
    <Image src='resources/images/cover_hero.png' style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
    {/* 左侧暗色渐变蒙版，保证文字可读 */}
    <Box style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(90deg, rgba(15,23,42,0.95) 22%, rgba(15,23,42,0.72) 52%, rgba(15,23,42,0.18) 100%)' }} />
    {/* 骑线文字区 */}
    <Box style={{ position: 'relative', zIndex: 1, height: '100%', padding: '72px 72px 56px 72px', justifyContent: 'space-between' }}>
      {/* 品牌区 */}
      <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
        <svg width={40} height={40} viewBox='0 0 40 40'>
          <path d='M20 2 36 8v10c0 10-7 17-16 20C11 35 4 28 4 18V8Z' fill='none' stroke='#F59E0B' strokeWidth='2.4' />
          <path d='M20 12v16M12 20h16' stroke='#22D3EE' strokeWidth='3.2' strokeLinecap='round' />
        </svg>
        <Box>
          <Text style={{ fontSize: 22, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>RescueAI</Text>
          <Text style={{ fontSize: 11, color: 'rgba(148,163,184,0.9)', fontFamily: 'JetBrains Mono', letterSpacing: 2 }}>PHYSICAL AI FOR EARTHQUAKE RESCUE</Text>
        </Box>
      </Box>
      {/* 主标题区 */}
      <Box style={{ maxWidth: 760 }}>
        <Text style={{ fontSize: 15, color: '#22D3EE', fontFamily: 'JetBrains Mono', letterSpacing: 3, marginBottom: 20 }}>AI 地震救援平台 · 产品介绍</Text>
        <Text style={{ fontSize: 52, fontWeight: 'bold', color: '#F1F5F9', lineHeight: 1.3, fontFamily: 'Source Han Sans SC', textShadow: '0 4px 24px rgba(0,0,0,0.5)' }}>
          让 AI 把社媒上的每一句<span style={{ color: '#F59E0B' }}>呼救</span>，<br />
          变成地图上的<span style={{ color: '#22D3EE' }}>坐标</span>和<span style={{ color: '#F59E0B' }}>优先级</span>。
        </Text>
        <Text style={{ fontSize: 18, color: 'rgba(241,245,249,0.75)', lineHeight: 1.6, marginTop: 24, fontFamily: 'Source Han Sans SC' }}>
          基于 2025 年 3 月 28 日缅甸 M7.7 地震真实数据的全链路验证
        </Text>
      </Box>
      {/* 底部信息条 */}
      <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 28 }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Box style={{ width: 8, height: 8, borderRadius: 4, background: '#22D3EE' }} />
          <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.7)', fontFamily: 'JetBrains Mono' }}>53,340 条真实微博数据验证</Text>
        </Box>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Box style={{ width: 8, height: 8, borderRadius: 4, background: '#F59E0B' }} />
          <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.7)', fontFamily: 'JetBrains Mono' }}>8 个历史救援案例知识库</Text>
        </Box>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Box style={{ width: 8, height: 8, borderRadius: 4, background: '#22D3EE' }} />
          <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.7)', fontFamily: 'JetBrains Mono' }}>无人机真机协议已预留</Text>
        </Box>
      </Box>
    </Box>
  </Box>
</Slide>
