<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* A 区：标题块 */}
  <Box style={{ height: 84, justifyContent: 'center' }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>问题一 · 哪里最严重？<span style={{ color: '#22D3EE' }}>感知 → 解析 → 灾情热力图</span></Text>
    <Box style={{ width: 64, height: 3, marginTop: 10, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
  </Box>
  {/* B 区：非对称双栏 60:40 */}
  <Box style={{ height: 516, flexDirection: 'row', gap: 32 }}>
    {/* 左 60%：灾情热力地图（SVG 结构化图示） */}
    <Box style={{ width: 640, background: 'rgba(30,41,59,0.4)', border: '1px solid rgba(34,211,238,0.2)', borderRadius: 14, padding: 14, justifyContent: 'center', alignItems: 'center' }}>
      <svg width={600} height={430} viewBox='0 0 600 430'>
        {/* 抽象区域轮廓 */}
        <path d='M120 60 Q280 20 420 55 Q520 85 540 180 Q555 280 470 350 Q360 415 230 385 Q110 355 80 250 Q55 140 120 60Z' fill='rgba(34,211,238,0.04)' stroke='rgba(34,211,238,0.35)' strokeWidth='1.5' />
        <path d='M150 120 Q300 90 430 130' fill='none' stroke='rgba(148,163,184,0.25)' strokeWidth='1' strokeDasharray='4 4' />
        <path d='M130 220 Q300 190 480 230' fill='none' stroke='rgba(148,163,184,0.25)' strokeWidth='1' strokeDasharray='4 4' />
        {/* 震中 */}
        <circle cx='270' cy='170' r='10' fill='#EF4444' opacity='0.9' />
        <circle cx='270' cy='170' r='22' fill='none' stroke='#EF4444' strokeWidth='1.5' opacity='0.5' />
        <circle cx='270' cy='170' r='36' fill='none' stroke='#EF4444' strokeWidth='1' opacity='0.25' />
        <text x='270' y='140' fill='#FCA5A5' fontSize='12' textAnchor='middle' fontFamily='JetBrains Mono'>震中 M7.7 · 深10km</text>
        {/* 实皆省 P0 大热点 */}
        <circle cx='240' cy='200' r='58' fill='rgba(239,68,68,0.22)' stroke='#EF4444' strokeWidth='2' />
        <text x='240' y='197' fill='#FCA5A5' fontSize='15' textAnchor='middle' fontWeight='bold'>实皆省</text>
        <text x='240' y='215' fill='#FCA5A5' fontSize='11' textAnchor='middle'>频次高 · 严重度极高</text>
        {/* 曼德勒 P0-P1 最大热点 */}
        <circle cx='330' cy='250' r='72' fill='rgba(249,115,22,0.18)' stroke='#F97316' strokeWidth='2' />
        <text x='330' y='246' fill='#FDBA74' fontSize='15' textAnchor='middle' fontWeight='bold'>曼德勒</text>
        <text x='330' y='264' fill='#FDBA74' fontSize='11' textAnchor='middle'>Sky Villa 倒塌 · 呼救集中</text>
        {/* 瑞丽 P2 */}
        <circle cx='470' cy='110' r='36' fill='rgba(245,158,11,0.16)' stroke='#F59E0B' strokeWidth='1.5' />
        <text x='470' y='107' fill='#FCD34D' fontSize='13' textAnchor='middle' fontWeight='bold'>瑞丽</text>
        <text x='470' y='123' fill='#FCD34D' fontSize='10' textAnchor='middle'>跨境震感</text>
        {/* 曼谷 P3 */}
        <circle cx='430' cy='340' r='26' fill='rgba(100,116,139,0.18)' stroke='#64748B' strokeWidth='1.5' />
        <text x='430' y='338' fill='#94A3B8' fontSize='12' textAnchor='middle' fontWeight='bold'>曼谷</text>
        <text x='430' y='353' fill='#94A3B8' fontSize='10' textAnchor='middle'>在建楼坍塌</text>
        {/* 图例 */}
        <text x='20' y='412' fill='rgba(148,163,184,0.8)' fontSize='11' fontFamily='JetBrains Mono'>面积 = 出现频次  ·  颜色深度 = 严重程度权重  ·  NER 地名实时聚合</text>
      </svg>
    </Box>
    {/* 右 40%：解析逻辑要点 */}
    <Box style={{ flex: 1, justifyContent: 'center', gap: 14 }}>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.25)', borderRadius: 12, padding: '14px 18px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <FAIcon name='broadcast-tower' style={{ fill: '#22D3EE', width: 20, height: 20 }} />
          <Text style={{ fontSize: 17, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>ICL 预警触发</Text>
        </Box>
        <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.7)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>成都高新减灾研究所主导研发。任何地震信号即刻启动社媒监测——不论震级，都可能有人被困。</Text>
      </Box>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.25)', borderRadius: 12, padding: '14px 18px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <FAIcon name='brain' style={{ fill: '#22D3EE', width: 20, height: 20 }} />
          <Text style={{ fontSize: 17, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>NLP 智能解析</Text>
        </Box>
        <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.7)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>4 层噪声过滤（去重/辟谣/机器人/地理围栏）后，大模型提取 NER 地名、情感标色、6 类损毁标签。</Text>
      </Box>
      <Box style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.35)', borderRadius: 12, padding: '14px 18px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <FAIcon name='map-marked-alt' style={{ fill: '#F59E0B', width: 20, height: 20 }} />
          <Text style={{ fontSize: 17, fontWeight: 'bold', color: '#F59E0B', fontFamily: 'Source Han Sans SC' }}>频次 × 严重度加权</Text>
        </Box>
        <Text style={{ fontSize: 14.5, color: 'rgba(241,245,249,0.75)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>地名按出现频次与严重程度加权聚合上图，哪里的呼喊最密集、最危急，热力图一眼可见。</Text>
      </Box>
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>05 / 10</Text>
  </Box>
</Slide>
