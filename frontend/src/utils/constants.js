export const DISASTER_TYPES = [
  { value: 'earthquake', label: '地震/主震' },
  { value: 'aftershock', label: '余震' },
  { value: 'building_collapse', label: '建筑倒塌' },
  { value: 'road_damage', label: '道路损毁' },
  { value: 'landslide', label: '滑坡' },
  { value: 'secondary_hazard', label: '次生灾害' },
]

export const DISASTER_STATUS = [
  { value: 'reported', label: '已上报', type: 'warning' },
  { value: 'confirmed', label: '待批准', type: '' },
  { value: 'processing', label: '处理中', type: 'primary' },
  { value: 'dispatched', label: '已派遣', type: 'primary' },
  { value: 'verify', label: '核验中', type: 'warning' },
  { value: 'resolved', label: '已闭环', type: 'success' },
]

/** 指挥大屏任务优先级色（对齐大屏：P0红/P1橙/P2黄） */
export const PRIORITY_COLORS = { P0: '#FB4B6B', P1: '#FFB020', P2: '#FADB14' }

/** SLA 响应窗口（秒）：看板倒计时口径（大屏用） */
export const SLA_WINDOWS = { P0: 180, P1: 300, P2: 500 }

/** Dashboard 统计口径的 SLA 窗口（秒，按 severity） */
export const SLA_WINDOWS_BY_SEVERITY = { 5: 1800, 4: 1800, 3: 3600, 2: 7200, 1: 7200 }

/** 社情信号类型标签（对齐后端 SIGNAL_TYPE_LABELS） */
export const SIGNAL_TYPE_LABELS = {
  casualty: '人员伤亡',
  building_collapse: '房屋倒塌',
  rescue_progress: '救援进展',
  secondary_hazard: '次生灾害',
  road_blocked: '道路中断',
  felt_report: '震感反馈',
  unknown: '未知信号',
}

export const SEVERITY_LABELS = { 1: '轻微', 2: '一般', 3: '较重', 4: '严重', 5: '极其严重' }
export const SEVERITY_COLORS = { 1: '#2DD4BF', 2: '#38E1FF', 3: '#FFB020', 4: '#FB4B6B', 5: '#DC143C' }

/** 英文key → 中文标签 快速映射 */
export const DISASTER_TYPE_MAP = {
  earthquake: '地震',
  aftershock: '余震',
  building_collapse: '建筑倒塌',
  road_damage: '道路损毁',
  landslide: '滑坡',
  secondary_hazard: '次生灾害',
}

/** 救援请求选项 */
export const RESCUE_REQUEST_OPTIONS = [
  { value: false, label: '不需要救援' },
  { value: true, label: '需要救援' },
]

/** 灾情类型 → 地图/列表图标映射 */
export const DISASTER_ICONS = {
  'earthquake': 'Place',
  'aftershock': 'RefreshRight',
  'building_collapse': 'OfficeBuilding',
  'road_damage': 'Van',
  'landslide': 'Sunny',
  'secondary_hazard': 'WarningFilled',
}

/** 根据严重程度返回灾情标记颜色 */
export function getDisasterMarkerColor(severity) {
  if (severity >= 4) return '#F56C6C'
  if (severity === 3) return '#E6A23C'
  return '#67C23A'
}

export const DISASTER_LEVELS = [
  { value: '特别重大', label: '特别重大' },
  { value: '重大', label: '重大' },
  { value: '较大', label: '较大' },
  { value: '一般', label: '一般' },
]

export const USER_ROLES = [
  { value: 'admin', label: '管理员' },
  { value: 'commander', label: '指挥员' },
  { value: 'rescuer', label: '救援队员' },
  { value: 'medic', label: '医疗人员' },
]

export const RESOURCE_TYPES = [
  { value: 'material', label: '物资' },
  { value: 'equipment', label: '设备' },
  { value: 'personnel', label: '人员' },
  { value: 'vehicle', label: '车辆' },
]

export const RESOURCE_STATUS = [
  { value: 'available', label: '可用', type: 'success' },
  { value: 'dispatched', label: '调度中', type: 'warning' },
  { value: 'consumed', label: '已消耗', type: 'info' },
  { value: 'damaged', label: '已损坏', type: 'danger' },
]

export const VOLUNTEER_STATUS = [
  { value: 'available', label: '待命', type: 'success' },
  { value: 'assigned', label: '已分配', type: 'warning' },
  { value: 'on_mission', label: '任务中', type: 'primary' },
  { value: 'off_duty', label: '休息', type: 'info' },
]

export const VOLUNTEER_SKILLS = [
  { value: 'medical', label: '医疗' },
  { value: 'search_rescue', label: '搜救' },
  { value: 'driving', label: '驾驶' },
  { value: 'translation', label: '翻译' },
  { value: 'cooking', label: '后勤' },
  { value: 'communication', label: '通讯' },
  { value: 'engineering', label: '工程' },
  { value: 'psychology', label: '心理疏导' },
]

export const RESOURCE_TYPE_MAP = Object.fromEntries(RESOURCE_TYPES.map(t => [t.value, t.label]))
export const RESOURCE_STATUS_MAP = Object.fromEntries(RESOURCE_STATUS.map(s => [s.value, s.label]))
export const VOLUNTEER_STATUS_MAP = Object.fromEntries(VOLUNTEER_STATUS.map(s => [s.value, s.label]))
export const VOLUNTEER_SKILL_MAP = Object.fromEntries(VOLUNTEER_SKILLS.map(s => [s.value, s.label]))

export const DAMAGE_LEVELS = [
  { value: 'minor', label: '轻微损毁', color: '#2DD4BF' },
  { value: 'moderate', label: '中度损毁', color: '#FFB020' },
  { value: 'severe', label: '严重损毁', color: '#FB4B6B' },
  { value: 'complete', label: '完全倒塌', color: '#DC143C' },
]

export const TRAPPED_STATUS = [
  { value: 'waiting', label: '待搜救', type: 'danger' },
  { value: 'searching', label: '搜救中', type: 'warning' },
  { value: 'rescued', label: '已救出', type: 'success' },
  { value: 'transferred', label: '已转移', type: 'info' },
]

export const TRAPPED_PRIORITY = [
  { value: 'red', label: '红色 - 立即救治', color: '#FB4B6B' },
  { value: 'yellow', label: '黄色 - 延迟救治', color: '#FFB020' },
  { value: 'green', label: '绿色 - 轻伤', color: '#2DD4BF' },
  { value: 'black', label: '黑色 - 死亡/临终', color: '#93A6C4' },
]
