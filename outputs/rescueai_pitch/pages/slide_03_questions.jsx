<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* 背景网格装饰 */}
  <Box style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0.05 }}>
    <svg width={1280} height={720} viewBox='0 0 1280 720'>
      {[0,1,2,3,4,5,6,7,8,9,10].map(i => (
        <line key={'v'+i} x1={i*128} y1='0' x2={i*128} y2='720' stroke='#22D3EE' strokeWidth='1' />
      ))}
      {[0,1,2,3,4,5].map(i => (
        <line key={'h'+i} x1='0' y1={i*128} x2='1280' y2={i*128} stroke='#22D3EE' strokeWidth='1' />
      ))}
    </svg>
  </Box>
  <Box style={{ position: 'relative', zIndex: 1, height: '100%', justifyContent: 'center', alignItems: 'center', gap: 40 }}>
    <Box style={{ alignItems: 'center' }}>
      <Text style={{ fontSize: 15, color: '#22D3EE', fontFamily: 'JetBrains Mono', letterSpacing: 4, marginBottom: 14 }}>EARTHQUAKE RESPONSE · 震后三问</Text>
      <Text style={{ fontSize: 22, color: 'rgba(241,245,249,0.7)', fontFamily: 'Source Han Sans SC' }}>每一位指挥官面前，永远是三个问题</Text>
    </Box>
    {/* 三问纵排大字 */}
    <Box style={{ gap: 30, alignItems: 'flex-start' }}>
      <Box style={{ flexDirection: 'row', alignItems: 'baseline', gap: 26 }}>
        <Text style={{ fontSize: 30, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono' }}>01</Text>
        <Text style={{ fontSize: 54, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>哪里<span style={{ color: '#F59E0B' }}>最严重</span>？</Text>
        <Text style={{ fontSize: 18, color: 'rgba(148,163,184,0.9)', fontFamily: 'Source Han Sans SC', marginLeft: 8 }}>灾情分布看不见</Text>
      </Box>
      <Box style={{ flexDirection: 'row', alignItems: 'baseline', gap: 26 }}>
        <Text style={{ fontSize: 30, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono' }}>02</Text>
        <Text style={{ fontSize: 54, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>先救<span style={{ color: '#F59E0B' }}>哪里</span>？</Text>
        <Text style={{ fontSize: 18, color: 'rgba(148,163,184,0.9)', fontFamily: 'Source Han Sans SC', marginLeft: 8 }}>资源永远不够用</Text>
      </Box>
      <Box style={{ flexDirection: 'row', alignItems: 'baseline', gap: 26 }}>
        <Text style={{ fontSize: 30, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'JetBrains Mono' }}>03</Text>
        <Text style={{ fontSize: 54, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>救援路线<span style={{ color: '#F59E0B' }}>怎么规划</span>？</Text>
        <Text style={{ fontSize: 18, color: 'rgba(148,163,184,0.9)', fontFamily: 'Source Han Sans SC', marginLeft: 8 }}>道路中断成孤岛</Text>
      </Box>
    </Box>
    <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 6 }}>
      <Box style={{ width: 48, height: 2, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)' }} />
      <Text style={{ fontSize: 18, color: 'rgba(241,245,249,0.75)', fontFamily: 'Source Han Sans SC' }}>RescueAI 用一条七步链路，逐一回答</Text>
      <Box style={{ width: 48, height: 2, background: 'linear-gradient(90deg, #22D3EE, #F59E0B)' }} />
    </Box>
  </Box>
</Slide>
