<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* B 区：左标题 + 右七步链（自定义章节页版式，无独立 A 区标题块） */}
  <Box style={{ height: 640, flexDirection: 'row', gap: 44, paddingTop: 24 }}>
    {/* 左：章节标题栏（窄） */}
    <Box style={{ width: 300, justifyContent: 'center', gap: 18 }}>
      <Text style={{ fontSize: 15, color: '#22D3EE', fontFamily: 'JetBrains Mono', letterSpacing: 3 }}>PRODUCT PIPELINE</Text>
      <Text style={{ fontSize: 42, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC', lineHeight: 1.25 }}>产品全景<br />七步链路</Text>
      <Box style={{ width: 64, height: 3, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
      <Text style={{ fontSize: 17, color: 'rgba(241,245,249,0.7)', lineHeight: 1.7, fontFamily: 'Source Han Sans SC' }}>
        从 ICL 预警信号到无人机空中救援，一条链路回答震后三问：感知 → 研判 → 决策 → 执行。
      </Text>
      <Box style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.3)', borderRadius: 10, padding: '12px 16px', marginTop: 6 }}>
        <Text style={{ fontSize: 14, color: '#22D3EE', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>已用缅甸地震 53,340 条真实微博数据完成全链路验证</Text>
      </Box>
    </Box>
    {/* 右：七步纵向链 */}
    <Box style={{ flex: 1, justifyContent: 'center', gap: 10 }}>
      {[
        { n: '1', t: 'ICL 预警触发', d: '成都高新减灾研究所主导研发 · 任何地震信号即刻启动', c: '#22D3EE' },
        { n: '2', t: '社媒数据监测', d: '真实数据集验证 · 企业微博 API 接口已预留', c: '#22D3EE' },
        { n: '3', t: 'NLP 智能解析', d: 'NER 地名 · 情感标色 · 损毁标签 · 4 层噪声过滤', c: '#22D3EE' },
        { n: '4', t: '灾情热力图', d: '地名聚合 · 出现频次 × 严重程度加权 → 回答「哪里最严重」', c: '#F59E0B' },
        { n: '5', t: 'P0–P3 优先级排序', d: '呼救信号加权 + 资源约束 → 回答「先救哪里」', c: '#F59E0B' },
        { n: '6', t: 'AI 简报 + 决策助手', d: 'Qwen3.8-Max 通报风格简报 · 8 案例十维匹配给方案', c: '#F59E0B' },
        { n: '7', t: '无人机空中救援', d: '物资精准投送 + 航拍回传 → 回答「路线怎么规划」', c: '#F59E0B' },
      ].map((s, i) => (
        <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 14, background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.18)', borderRadius: 10, padding: '10px 16px' }}>
          <Box style={{ width: 34, height: 34, borderRadius: 17, background: s.c === '#F59E0B' ? 'rgba(245,158,11,0.15)' : 'rgba(34,211,238,0.12)', border: `1.5px solid ${s.c}`, justifyContent: 'center', alignItems: 'center' }}>
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: s.c, fontFamily: 'JetBrains Mono' }}>{s.n}</Text>
          </Box>
          <Box style={{ flex: 1 }}>
            <Text style={{ fontSize: 17, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>{s.t}</Text>
          </Box>
          <Box style={{ flex: 1.6 }}>
            <Text style={{ fontSize: 13.5, color: 'rgba(241,245,249,0.62)', fontFamily: 'Source Han Sans SC', lineHeight: 1.4 }}>{s.d}</Text>
          </Box>
        </Box>
      ))}
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>04 / 10</Text>
  </Box>
</Slide>
