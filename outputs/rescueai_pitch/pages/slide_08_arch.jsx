<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* A 区：标题块 */}
  <Box style={{ height: 84, justifyContent: 'center' }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>技术路线 · <span style={{ color: '#22D3EE' }}>四层解耦架构</span></Text>
    <Box style={{ width: 64, height: 3, marginTop: 10, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
  </Box>
  {/* B 区：左窄导航 + 右分层架构 */}
  <Box style={{ height: 516, flexDirection: 'row', gap: 32 }}>
    {/* 左：技术原则（窄栏） */}
    <Box style={{ width: 300, justifyContent: 'center', gap: 14 }}>
      <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC', lineHeight: 1.4 }}>为真实救援场景<br />而生的工程设计</Text>
      {[
        { t: '四层解耦', d: '各层独立可替换，数据流单向贯通' },
        { t: '真机可替换', d: '无人机遥测协议与真机标准一致' },
        { t: '全链路降级', d: 'AI 超时/断网自动兜底，演示永不中断' },
        { t: '双模型协同', d: 'Qwen3.8-Max 文本 + Qwen3.7-Plus 视觉' },
      ].map((x, i) => (
        <Box key={i} style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
          <FAIcon name='check-circle' style={{ fill: '#22D3EE', width: 18, height: 18 }} />
          <Box>
            <Text style={{ fontSize: 15.5, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>{x.t}</Text>
            <Text style={{ fontSize: 13, color: 'rgba(241,245,249,0.6)', lineHeight: 1.45, fontFamily: 'Source Han Sans SC' }}>{x.d}</Text>
          </Box>
        </Box>
      ))}
    </Box>
    {/* 右：四层纵向架构 */}
    <Box style={{ flex: 1, justifyContent: 'center', gap: 8 }}>
      {[
        { n: '数据采集层', en: 'DATA INGESTION', c: '#22D3EE', items: ['社媒数据集（53,340 条真实微博）', 'ICL 地震预警（成都高新减灾研究所）', 'USGS ComCat 余震目录', '卫星影像底图'] },
        { n: 'NLP 处理层', en: 'NLP ENGINE', c: '#22D3EE', items: ['NER 地名提取（LLM + 词典降级）', '四维情感分析标色', '六类损毁类型标签', '可信度评分 0–1'] },
        { n: '分析决策层', en: 'ANALYTICS & DECISION', c: '#F59E0B', items: ['灾情热点聚合 · 频次×严重度', 'P0–P3 动态优先级引擎', '多维分析仪表盘', 'Qwen 简报生成 · 案例匹配决策'] },
        { n: '救援执行层', en: 'EXECUTION', c: '#F59E0B', items: ['无人机物资精准投送', '4K 空中侦察航拍', '巡逻监视全程留存', '真机遥测协议接入'] },
      ].map((l, i) => (
        <Box key={i}>
          <Box style={{ flexDirection: 'row', alignItems: 'center', background: 'rgba(30,41,59,0.55)', border: `1px solid ${l.c === '#F59E0B' ? 'rgba(245,158,11,0.35)' : 'rgba(34,211,238,0.3)'}`, borderRadius: 12, padding: '12px 18px', gap: 16 }}>
            <Box style={{ width: 150 }}>
              <Text style={{ fontSize: 17.5, fontWeight: 'bold', color: l.c, fontFamily: 'Source Han Sans SC' }}>{l.n}</Text>
              <Text style={{ fontSize: 10, color: 'rgba(148,163,184,0.8)', fontFamily: 'JetBrains Mono', letterSpacing: 1 }}>{l.en}</Text>
            </Box>
            <Box style={{ flex: 1, flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
              {l.items.map((it, j) => (
                <Box key={j} style={{ background: l.c === '#F59E0B' ? 'rgba(245,158,11,0.08)' : 'rgba(34,211,238,0.07)', borderRadius: 6, padding: '4px 10px' }}>
                  <Text style={{ fontSize: 12.5, color: 'rgba(241,245,249,0.8)', fontFamily: 'Source Han Sans SC' }}>{it}</Text>
                </Box>
              ))}
            </Box>
          </Box>
          {i < 3 && (
            <Box style={{ alignItems: 'center', height: 14, justifyContent: 'center' }}>
              <svg width={20} height={14} viewBox='0 0 20 14'>
                <path d='M10 2v8M5 7l5 5 5-5' fill='none' stroke='rgba(148,163,184,0.6)' strokeWidth='1.8' strokeLinecap='round' />
              </svg>
            </Box>
          )}
        </Box>
      ))}
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>08 / 10</Text>
  </Box>
</Slide>
