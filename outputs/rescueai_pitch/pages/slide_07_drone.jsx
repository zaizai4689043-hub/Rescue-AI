<Slide style={{ padding: '20px 64px', background: '#0F172A' }}>
  {/* A 区：标题块 */}
  <Box style={{ height: 84, justifyContent: 'center' }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>问题三 · 路线怎么规划？<span style={{ color: '#22D3EE' }}>AI 决策 + 无人机空中救援</span></Text>
    <Box style={{ width: 64, height: 3, marginTop: 10, background: 'linear-gradient(90deg, #F59E0B, #22D3EE)', borderRadius: 2 }} />
  </Box>
  {/* B 区：左大图 + 右侧文字 */}
  <Box style={{ height: 516, flexDirection: 'row', gap: 32 }}>
    {/* 左 55%：无人机主视觉 */}
    <Box style={{ width: 620, borderRadius: 14, overflow: 'hidden', position: 'relative', border: '1px solid rgba(34,211,238,0.25)' }}>
      <Image src='resources/images/drone_hero.png' style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      <Box style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', padding: '28px 22px 16px 22px', background: 'linear-gradient(0deg, rgba(15,23,42,0.92) 20%, rgba(15,23,42,0) 100%)' }}>
        <Text style={{ fontSize: 14, color: 'rgba(241,245,249,0.85)', fontFamily: 'Source Han Sans SC' }}>数字孪生仿真驱动 · 大疆 Cloud API / MAVLink 真机遥测协议已预留</Text>
      </Box>
    </Box>
    {/* 右 45%：决策 + 无人机功能 */}
    <Box style={{ flex: 1, justifyContent: 'center', gap: 13 }}>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.25)', borderRadius: 12, padding: '13px 16px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 5 }}>
          <FAIcon name='compass' style={{ fill: '#22D3EE', width: 19, height: 19 }} />
          <Text style={{ fontSize: 16.5, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>AI 决策助手：先给方案，再谈路线</Text>
        </Box>
        <Text style={{ fontSize: 14, color: 'rgba(241,245,249,0.7)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>当前灾情特征与 <span style={{ color: '#F59E0B', fontWeight: 'bold' }}>8 个历史案例</span>（汶川/鲁甸/泸定等）十维加权匹配，输出优先区域、数据依据、行动方案与风险预警。</Text>
      </Box>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 12, padding: '13px 16px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 5 }}>
          <FAIcon name='box-open' style={{ fill: '#F59E0B', width: 19, height: 19 }} />
          <Text style={{ fontSize: 16.5, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>物资精准投送</Text>
        </Box>
        <Text style={{ fontSize: 14, color: 'rgba(241,245,249,0.7)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>按优先级排序飞抵断路灾民点，医疗包/食品/通信设备「最后一公里」直达，突破道路中断限制。</Text>
      </Box>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 12, padding: '13px 16px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 5 }}>
          <FAIcon name='video' style={{ fill: '#F59E0B', width: 19, height: 19 }} />
          <Text style={{ fontSize: 16.5, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>航拍研判路线</Text>
        </Box>
        <Text style={{ fontSize: 14, color: 'rgba(241,245,249,0.7)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>4K 灾情视频与图片实时回传，道路损毁、建筑坍塌、被困分布一屏看清，帮救援人员确定最优进入路线。</Text>
      </Box>
      <Box style={{ background: 'rgba(30,41,59,0.55)', border: '1px solid rgba(34,211,238,0.25)', borderRadius: 12, padding: '13px 16px' }}>
        <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 5 }}>
          <FAIcon name='sync-alt' style={{ fill: '#22D3EE', width: 19, height: 19 }} />
          <Text style={{ fontSize: 16.5, fontWeight: 'bold', color: '#F1F5F9', fontFamily: 'Source Han Sans SC' }}>巡逻监视留存</Text>
        </Box>
        <Text style={{ fontSize: 14, color: 'rgba(241,245,249,0.7)', lineHeight: 1.55, fontFamily: 'Source Han Sans SC' }}>预设航线持续巡航，AI 识别新坍塌/火灾蔓延等异常，全程录像为复盘与理赔留存证据链。</Text>
      </Box>
    </Box>
  </Box>
  {/* C 区：页脚 */}
  <Box style={{ height: 40, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'Source Han Sans SC' }}>RescueAI · Physical AI for Earthquake Rescue</Text>
    <Text style={{ fontSize: 14, color: 'rgba(148,163,184,0.6)', fontFamily: 'JetBrains Mono' }}>07 / 10</Text>
  </Box>
</Slide>
