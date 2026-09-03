# AI地震救援平台 - 新功能架构与信息层级规划

## 1. 设计愿景

### 1.1 核心理念
**"快速响应 · 智能决策 · 协同作战"**

在紧急救援场景中，每一秒都至关重要。新架构将围绕三个核心原则重构：
1. **速度优先**: 减少操作路径，关键信息一屏可见
2. **智能辅助**: AI深度融入工作流，主动推送建议而非被动问答
3. **协同高效**: 多角色实时协作，信息无缝流转

### 1.2 目标用户画像

| 角色 | 核心需求 | 使用场景 | 痛点 |
|------|----------|----------|------|
| **指挥员** | 全局态势感知、资源统筹、决策支持 | 指挥中心大屏、桌面端 | 信息分散、决策依据不足 |
| **现场救援队** | 任务接收、位置导航、实时上报 | 移动端、平板 | 网络不稳定、操作复杂 |
| **医疗人员** | 伤员分类、医疗资源调度、伤情追踪 | 移动端、临时站点 | 伤员信息不完整 |
| **志愿者协调员** | 人员分配、技能匹配、状态管理 | 桌面端、移动端 | 人员闲置或过载 |
| **数据分析师** | 趋势预测、评估报告、历史对比 | 桌面端 | 数据导出困难 |

---

## 2. 新信息架构

### 2.1 一级导航重构 (从9个精简为5个)

```
┌─────────────────────────────────────────────┐
│  🚨 应急指挥  │  🗺️ 态势地图  │  📦 资源中心  │   人员管理  │  🤖 AI助手  │
└─────────────────────────────────────────────┘
```

#### 模块映射关系

| 原模块 | 新归属 | 理由 |
|--------|--------|------|
| Dashboard | → 应急指挥 | 作为指挥中心的默认视图 |
| DisasterMap | → 态势地图 | 独立为核心功能 |
| DisasterReport | → 应急指挥 (快捷入口) | 高频操作，放在首页 |
| DisasterList | → 应急指挥 (子页面) | 作为灾情管理的列表视图 |
| ResourceCenter | → 资源中心 | 保持独立，强化资源管理 |
| VolunteerManage | → 人员管理 | 与受困者、救援队统一管理 |
| AssessmentReport | → 应急指挥 (分析页) | 作为数据分析的一部分 |
| TrackedPersons | → 人员管理 | 人员维度的统一管理 |
| AIAssistant | → AI助手 | 升级为全局智能中枢 |
| UserManage | → 系统设置 (隐藏) | 低频操作，移至设置 |

### 2.2 二级导航结构

```
🚨 应急指挥
├── 📊 指挥大屏 (Dashboard)
│   ├── 实时态势概览
│   ├── 关键指标监控
│   └── 预警通知中心
├── 📝 灾情管理
│   ├── 快速上报 (浮动按钮)
│   ├── 灾情列表
│   │   ├── 待确认
│   │   ├── 处理中
│   │   └── 已归档
│   └── 灾情详情
├── 📈 数据分析
│   ├── 趋势分析
│   ├── 评估报告
│   └── 历史对比
└── ⚙️ 系统设置
    ├── 用户管理
    ├── 权限配置
    └── 系统日志

🗺️ 态势地图
├── 🌍 全景地图
│   ├── 灾情标记层
│   ├── 资源分布层
│   ├── 人员位置层
│   └── 风险区域层
├── 🔍 专题视图
│   ├── 救援路线规划
│   ├── 避难所分布
│   └── 医疗点覆盖
└── 📡 实时监控
    ├── 无人机画面
    ├── 卫星影像
    └── 传感器数据

📦 资源中心
├── 📋 资源清单
│   ├── 物资库存
│   ├── 设备台账
│   ── 车辆调度
├── 🚚 调度管理
│   ├── 待调度
│   ├── 运输中
│   └── 已送达
├── 📊 资源分析
│   ├── 消耗趋势
│   ├── 缺口预警
│   └── 补给建议
└── 🏪 仓库管理
    ├── 仓库列表
    └── 出入库记录

👥 人员管理
├── 🆘 受困者追踪
│   ├── 待搜救
│   ├── 搜救中
│   ├── 已救出
│   └── 已转移
├── 🦺 救援队伍
│   ├── 队伍列表
│   ├── 任务分配
│   ── 行动轨迹
├──  志愿者管理
│   ├── 志愿者池
│   ├── 技能标签
│   ── 排班管理
└── 🏥 医疗人员
    ├── 医护人员
    ├── 伤员分诊
    ── 医疗资源

🤖 AI助手 (全局悬浮)
├──  智能问答
├──  主动建议
│   ├── 救援优先级推荐
│   ├── 资源调配优化
│   └── 风险预警
├── 📊 分析报告
│   ├── 自动生成日报
│   └── 趋势预测
└── 🎓 知识库
    ├── 救援预案
    ── 最佳实践
```

### 2.3 跨模块数据流

```
─────────────┐     ┌──────────────┐     ┌─────────────┐
│  灾情上报    │────▶│  态势地图     │◀────│  AI分析引擎  │
│  (手动/自动) │     │  (可视化)     │     │  (智能决策)  │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  资源调度     │◀────┐
                    │  (自动匹配)   │     │
                    └──────┬───────┘     │
                           │             │
                    ┌──────▼───────┐     │
                    │  人员指派     │─────
                    │  (技能匹配)   │
                    └──────────────┘
```

---

## 3. 核心功能重新设计

### 3.1 应急指挥模块

#### 3.1.1 指挥大屏 (新Dashboard)

**设计理念**: "一屏掌握全局，三秒做出决策"

**布局结构**:
```
┌─────────────────────────────────────────────────────────┐
│  [时间轴] T+02:34:17  │  黄金72h倒计时: 69:25:43       │
├─────────────┬───────────────────────┬─────────────────┤
│             │                       │                 │
│  🚨 紧急预警 │   🗺️ 迷你地图预览      │  📊 关键指标    │
│  (滚动列表)  │   (可点击跳转)         │  • 灾情总数      │
│             │                       │  • 待救援        │
│  • 余震预警   │                       │  • 资源缺口      │
│  • 道路中断   │                       │  • 受困人数      │
│  • 通信故障   │                       │                 │
│             │                       │                 │
├─────────────┴───────────────────────┴─────────────────┤
│                                                         │
│   24小时灾情趋势  │  🔥 热点区域TOP5  │  📦 资源状态  │
│  (折线图)          │  (柱状图)         │  (环形图)      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  🆕 最新灾情 (自动刷新)                                  │
│  ┌─────────────────────────────────────────────────┐  │
│  │ [严重] 建筑倒塌 - XX小区3号楼 | 需要救援 ✅       │  │
│  │ 2分钟前 | 坐标: 31.23, 121.47 | 查看详情 ▶       │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**关键特性**:
1. **实时数据流**: WebSocket推送，无需手动刷新
2. **智能排序**: 按严重程度+时间综合排序
3. **一键操作**: 每条灾情旁直接显示"派遣救援队"按钮
4. **语音播报**: 重大事件自动语音提醒 (可关闭)
5. **快捷键支持**: 
   - `R`: 快速上报灾情
   - `M`: 打开地图
   - `Space`: 暂停/继续自动刷新

#### 3.1.2 快速上报流程优化

**当前问题**: 表单字段过多，紧急情况下填写耗时

**新方案**: 三步极速上报
```
步骤1: 定位 (自动获取GPS / 地图选点 / 地址搜索)
       ↓
步骤2: 拍照/录像 (自动识别灾情类型 + AI预填描述)
       ↓
步骤3: 确认提交 (可选补充: 严重程度、是否需救援)
```

**AI增强**:
- 图像识别自动判断: 地震/倒塌/滑坡等
- NLP从照片描述中提取关键词
- 根据位置自动关联附近资源

### 3.2 态势地图模块

#### 3.2.1 分层可视化

**图层控制**:
```
 灾情标记 (按严重程度着色)
 救援队伍 (实时位置 + 任务状态)
☑ 资源分布 (仓库/物资点)
☑ 受困者位置 (仅授权可见)
☑ 风险区域 (余震预测/滑坡风险)
☑ 交通路况 (畅通/拥堵/中断)
☑ 医疗设施 (医院/临时医疗点)
☑ 避难场所
```

**交互优化**:
- **框选批量操作**: 矩形框选多个灾情，批量分配救援队
- **热力图模式**: 切换查看灾情密度分布
- **时间轴回放**: 拖动时间轴查看灾情演变过程
- **路线规划**: 点击两点自动生成最优救援路线 (考虑路况)

#### 3.2.2 AR实景叠加 (未来扩展)

通过手机摄像头，在实景中标注:
- 前方建筑的灾情等级
- 最近救援队的方向和距离
- 安全通道指示

### 3.3 资源中心模块

#### 3.3.1 智能调度算法

**当前问题**: 手动选择目标位置，效率低

**新方案**: AI推荐调度方案
```
输入: 灾情位置 + 所需资源类型 + 紧急程度
输出: 
  ✓ 推荐仓库 (距离最近 + 库存充足)
  ✓ 最优路线 (避开危险区域)
  ✓ 预计到达时间
  ✓ 备选方案 (主仓库不足时的组合调度)
```

**可视化呈现**:
```
┌──────────────────────────────────────────────────┐
│  📦 AI调度建议                                    │
├──────────────────────────────────────────────────┤
│  ✅ 方案A (推荐) - 综合评分: 92分                  │
│  • 来源: 浦东仓库 (距离3.2km, 库存充足)            │
│  • 物资: 帐篷×50, 饮用水×200箱, 急救包×100        │
│  • 路线: 人民大道 → 世纪大道 (避开坍塌路段)        │
│  • ETA: 18分钟 (预计14:35到达)                     │
│  • 风险: 低 (余震概率<5%)                          │
│                                                    │
│  ⚠️ 方案B (备选) - 综合评分: 78分                  │
│  • 来源: 徐汇仓库 (距离5.8km, 需调拨)              │
│  • 物资: 帐篷×30, 饮用水×150箱 (部分缺货)          │
│  • 路线: 淮海路 → 延安高架                         │
│  • ETA: 28分钟                                     │
│  • 风险: 中 (交通拥堵可能性60%)                    │
│                                                    │
│  [确认调度] [调整数量] [查看地图] [取消]           │
└──────────────────────────────────────────────────┘
```

**算法逻辑**:
```javascript
function recommendDispatch(disasterLocation, resourceType, urgency) {
  // 1. 筛选可用仓库 (库存 > 需求量)
  const availableWarehouses = warehouses.filter(w => 
    w.inventory[resourceType] >= requiredQuantity &&
    w.status === 'operational'
  );
  
  // 2. 计算综合评分
  const scored = availableWarehouses.map(warehouse => {
    const distanceScore = calculateDistanceScore(warehouse, disasterLocation); // 0-100
    const inventoryScore = calculateInventoryScore(warehouse, resourceType);   // 0-100
    const riskScore = calculateRiskScore(warehouse, disasterLocation);         // 0-100
    
    // 权重配置 (可根据紧急程度动态调整)
    const weights = {
      distance: urgency === 'critical' ? 0.5 : 0.3,
      inventory: 0.3,
      risk: urgency === 'critical' ? 0.2 : 0.4
    };
    
    return {
      warehouse,
      score: distanceScore * weights.distance + 
             inventoryScore * weights.inventory + 
             riskScore * weights.risk,
      eta: estimateETA(warehouse, disasterLocation),
      route: findOptimalRoute(warehouse, disasterLocation),
    };
  });
  
  // 3. 排序并返回Top 3方案
  return scored.sort((a, b) => b.score - a.score).slice(0, 3);
}
```

**人工干预点**:
- 可手动调整各仓库的分配数量
- 可强制指定特定仓库 (覆盖AI推荐)
- 可标记某条路线为"不可用" (触发重新规划)

---

## 4. 数据模型设计

### 4.1 核心实体定义

#### 灾情 (Disaster)
```typescript
interface Disaster {
  id: number
  title: string                              // 灾情标题
  disaster_type: DisasterType                // 灾情类型
  severity: 1 | 2 | 3 | 4 | 5               // 严重程度 (1-5级)
  status: DisasterStatus                     // 状态
  latitude: number                           // 纬度
  longitude: number                          // 经度
  address?: string                           // 详细地址
  description?: string                       // 详细描述
  is_rescue_requested: boolean               // 是否需要救援
  images?: string[]                          // 现场照片URL数组
  reported_by: string                        // 上报人ID
  created_at: string                         // ISO时间戳
  updated_at: string                         // ISO时间戳
}

type DisasterType = 
  | 'earthquake'        // 地震/主震
  | 'aftershock'        // 余震
  | 'building_collapse' // 建筑倒塌
  | 'road_damage'       // 道路损毁
  | 'landslide'         // 滑坡
  | 'secondary_hazard'  // 次生灾害

type DisasterStatus = 
  | 'reported'      // 已上报
  | 'confirmed'     // 已确认
  | 'processing'    // 处理中
  | 'resolved'      // 已解决
```

#### 资源 (Resource)
```typescript
interface Resource {
  id: number
  name: string                           // 资源名称
  resource_type: ResourceType            // 资源类型
  quantity: number                       // 当前数量
  original_quantity: number              // 原始数量 (用于追踪消耗)
  unit: string                           // 单位 (个/箱/辆/顶)
  location: string                       // 当前位置
  warehouse_id?: number                  // 所属仓库ID
  status: ResourceStatus                 // 状态
  description?: string                   // 描述
  dispatched_to?: string                 // 调度目标位置 (当status='dispatched')
  dispatched_at?: string                 // 调度时间
  created_at: string
  updated_at: string
}

type ResourceType = 
  | 'material'     // 物资
  | 'equipment'    // 设备
  | 'personnel'    // 人员
  | 'vehicle'      // 车辆

type ResourceStatus = 
  | 'available'   // 可用
  | 'dispatched'  // 调度中
  | 'consumed'    // 已消耗
  | 'damaged'     // 已损坏
```

#### 志愿者 (Volunteer)
```typescript
interface Volunteer {
  id: number
  name: string                           // 姓名
  phone: string                          // 手机号
  skills: VolunteerSkill[]               // 技能标签
  status: VolunteerStatus                // 状态
  current_location?: string              // 当前位置
  assigned_task_id?: number              // 当前任务ID
  latitude?: number                      // 实时纬度 (GPS)
  longitude?: number                     // 实时经度 (GPS)
  last_active_at?: string                // 最后活跃时间
  created_at: string
}

type VolunteerSkill = 
  | 'medical'          // 医疗
  | 'search_rescue'    // 搜救
  | 'driving'          // 驾驶
  | 'translation'      // 翻译
  | 'cooking'          // 后勤
  | 'communication'    // 通讯
  | 'engineering'      // 工程
  | 'psychology'       // 心理疏导

type VolunteerStatus = 
  | 'available'    // 待命
  | 'assigned'     // 已分配
  | 'on_mission'   // 任务中
  | 'off_duty'     // 休息
```

#### 受困者 (TrappedPerson) - 新增
```typescript
interface TrappedPerson {
  id: number
  name?: string                          // 姓名 (未知可为空)
  gender?: 'male' | 'female' | 'unknown' // 性别
  age_estimate?: number                  // 估计年龄
  location: string                       // 发现位置描述
  latitude?: number                      // 纬度
  longitude?: number                     // 经度
  status: TrappedStatus                  // 救援状态
  priority: TrappedPriority              // 救治优先级
  condition?: string                     // 伤情描述
  trapped_reason?: string                // 受困原因 (坍塌/掩埋等)
  reported_by: string                    // 上报人ID
  rescued_by?: number                    // 救援队ID
  rescued_at?: string                    // 救出时间
  transferred_to?: string                // 转移至 (医院/避难所)
  created_at: string
  updated_at: string
}

type TrappedStatus = 
  | 'waiting'      // 待救援
  | 'searching'    // 搜救中
  | 'rescued'      // 已救出
  | 'transferred'  // 已转移

type TrappedPriority = 
  | 'red'     // 红色 - 立即救治 (危重伤员)
  | 'yellow'  // 黄色 - 延迟救治 (中度伤员)
  | 'green'   // 绿色 - 轻伤 (可自行行走)
  | 'black'   // 黑色 - 死亡/临终
```

#### 救援队伍 (RescueTeam) - 新增
```typescript
interface RescueTeam {
  id: number
  name: string                           // 队伍名称
  leader_id: number                      // 队长ID (关联Volunteer)
  members: number[]                      // 队员ID列表 (关联Volunteer)
  specialty: RescueSpecialty             // 专业领域
  status: TeamStatus                     // 状态
  current_location?: string              // 当前位置
  current_task_id?: number               // 当前任务ID
  equipment_ids: number[]                // 携带设备ID列表
  vehicle_id?: number                    // 车辆ID
  latitude?: number                      // 实时纬度
  longitude?: number                     // 实时经度
  created_at: string
}

type RescueSpecialty = 
  | 'structural'      // 建筑结构救援
  | 'medical'         // 医疗急救
  | 'hazmat'          // 危险品处理
  | 'water_rescue'    // 水域救援
  | 'high_angle'      // 高空救援

type TeamStatus = 
  | 'standby'     // 待命
  | 'deployed'    // 已部署
  | 'on_scene'    // 现场作业
  | 'returning'   // 返回中
```

#### 调度任务 (DispatchTask) - 新增
```typescript
interface DispatchTask {
  id: number
  task_type: 'resource' | 'personnel'    // 任务类型
  disaster_id: number                    // 关联灾情ID
  resources?: number[]                   // 调度的资源ID列表
  team_id?: number                       // 指派的救援队ID
  volunteer_ids?: number[]               // 指派的志愿者ID列表
  from_location: string                  // 出发地
  to_location: string                    // 目的地
  status: DispatchStatus                 // 任务状态
  priority: TaskPriority                 // 优先级
  estimated_arrival?: string             // 预计到达时间
  actual_arrival?: string                // 实际到达时间
  route_data?: RouteCoordinates          // 路线坐标数据
  notes?: string                         // 备注
  created_by: string                     // 创建人ID
  created_at: string
  completed_at?: string                  // 完成时间
}

type DispatchStatus = 
  | 'pending'      // 待执行
  | 'in_progress'  // 执行中
  | 'completed'    // 已完成
  | 'cancelled'    // 已取消

type TaskPriority = 
  | 'critical'  // P0 危急
  | 'high'      // P1 严重
  | 'medium'    // P2 中等
  | 'low'       // P3 一般
```

#### AI建议 (AIRecommendation) - 新增
```typescript
interface AIRecommendation {
  id: number
  type: AIRecommendationType               // 建议类型
  disaster_id?: number                     // 关联灾情
  content: string                          // 建议内容 (Markdown格式)
  confidence: number                       // 置信度 (0-1)
  reasoning: string                        // 推理依据
  suggested_actions: SuggestedAction[]     // 建议操作
  status: RecommendationStatus             // 状态
  dismissed_by?: string                    // 忽略人ID
  dismissed_at?: string                    // 忽略时间
  created_at: string
}

type AIRecommendationType = 
  | 'priority_sorting'     // 优先级排序
  | 'resource_allocation'  // 资源分配
  | 'route_optimization'   // 路线优化
  | 'risk_prediction'      // 风险预测
  | 'capacity_planning'    // 容量规划

interface SuggestedAction {
  label: string                            // 操作标签
  action_type: 'dispatch' | 'notify' | 'escalate' // 操作类型
  target_id?: number                       // 目标ID
  metadata?: Record<string, any>           // 额外参数
}

type RecommendationStatus = 
  | 'active'       // 生效中
  | 'accepted'     // 已采纳
  | 'dismissed'    // 已忽略
  | 'expired'      // 已过期
```

### 4.2 关系图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Disaster   │◀──────│ DispatchTask │──────▶│   Resource   │
│              │ 1:N   │              │ N:M   │              │
│ - id         │       │ - disaster_id│       │ - id         │
│ - type       │       │ - resources  │       │ - type       │
│ - severity   │       │ - teams      │       │ - status     │
│ - status     │       │ - status     │       └──────────────┘
└──────┬───────┘       └──────┬───────┘
       │ 1:N                 │ N:M
       │                     │
┌──────▼───────┐       ┌─────▼────────┐       ┌──────────────┐
│TrappedPerson │       │  RescueTeam  │──────▶│  Volunteer   │
│              │       │              │ 1:N   │              │
│ - id         │       │ - id         │       │ - id         │
│ - status     │       │ - members    │       │ - skills     │
│ - priority   │       │ - specialty  │       │ - status     │
└──────────────┘       └──────────────┘       └──────────────┘
                              ▲
                              │ 生成
                     ┌────────┴────────┐
                     │ AIRecommendation│
                     │                 │
                     │ - type          │
                     │ - confidence    │
                     └─────────────────┘
```

### 4.3 数据库索引建议

```sql
-- 灾情表索引
CREATE INDEX idx_disaster_type ON disasters(disaster_type);
CREATE INDEX idx_disaster_severity ON disasters(severity);
CREATE INDEX idx_disaster_status ON disasters(status);
CREATE INDEX idx_disaster_location ON disasters(latitude, longitude);
CREATE INDEX idx_disaster_created ON disasters(created_at DESC);

-- 资源表索引
CREATE INDEX idx_resource_type ON resources(resource_type);
CREATE INDEX idx_resource_status ON resources(status);
CREATE INDEX idx_resource_warehouse ON resources(warehouse_id);

-- 调度任务索引
CREATE INDEX idx_dispatch_disaster ON dispatch_tasks(disaster_id);
CREATE INDEX idx_dispatch_status ON dispatch_tasks(status);
CREATE INDEX idx_dispatch_priority ON dispatch_tasks(priority, created_at);

-- 受困者索引
CREATE INDEX idx_trapped_status ON trapped_persons(status);
CREATE INDEX idx_trapped_priority ON trapped_persons(priority);
CREATE INDEX idx_trapped_location ON trapped_persons(latitude, longitude);

-- 救援队索引
CREATE INDEX idx_team_status ON rescue_teams(status);
CREATE INDEX idx_team_specialty ON rescue_teams(specialty);
```

### 4.4 API接口规范

#### 灾情管理
```
GET    /api/disasters?page=1&page_size=20&type=earthquake&severity=4
POST   /api/disasters                     # 创建灾情
GET    /api/disasters/:id                 # 获取详情
PUT    /api/disasters/:id                 # 更新灾情
DELETE /api/disasters/:id                 # 删除灾情
POST   /api/disasters/:id/confirm         # 确认灾情
POST   /api/disasters/:id/resolve         # 标记已解决
```

#### 资源调度
```
GET    /api/resources?page=1&type=material&status=available
POST   /api/resources
GET    /api/resources/:id
PUT    /api/resources/:id
DELETE /api/resources/:id
POST   /api/resources/:id/dispatch        # 调度资源
GET    /api/resources/recommendations?disaster_id=123&type=tent&quantity=50
```

#### 人员管理
```
GET    /api/volunteers?skill=medical&status=available
POST   /api/volunteers
GET    /api/trapped-persons?status=waiting&priority=red
POST   /api/trapped-persons
PUT    /api/trapped-persons/:id/rescue    # 标记已救出
GET    /api/rescue-teams?specialty=structural&status=standby
POST   /api/rescue-teams
POST   /api/dispatch-tasks                # 创建调度任务
```

#### AI助手
```
POST   /api/ai/chat                       # 对话接口
GET    /api/ai/recommendations?disaster_id=123
POST   /api/ai/recommendations/:id/accept # 采纳建议
POST   /api/ai/recommendations/:id/dismiss # 忽略建议
```

---

*文档版本: v1.1 (已修复截断问题)*  
*最后更新: 2026-08-29*  
*维护者: RescueAI Architecture Team*