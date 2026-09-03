# 无人机路线分析提示词

## 使用场景
当无人机完成空中侦察后，使用 Qwen-VL 或 Qwen3.8-Max 分析航拍画面/情报数据，判断灾区道路可通行性。

## 视觉分析提示词（Qwen-VL，有航拍图片时）

```
你是地震灾后道路通行性研判专家。这是无人机航拍的灾区画面。
请分析并返回严格 JSON：
{
  "accessible_routes": [
    {
      "from": "起点",
      "to": "终点",
      "via": "路线描述",
      "status": "clear|caution",
      "estimated_time_min": 45,
      "notes": "路面状态"
    }
  ],
  "blocked_routes": [
    {
      "from": "起点",
      "to": "终点",
      "via": "路线描述",
      "block_type": "桥梁断裂|道路塌方|建筑倒塌阻断|落石|泥石流",
      "block_location": "位置",
      "detour": "绕行方案"
    }
  ],
  "hazard_zones": [
    {
      "location": "位置",
      "hazard_type": "滑坡风险|堰塞湖|建筑倾斜|燃气泄漏",
      "severity": "high|medium|low",
      "advice": "建议措施"
    }
  ],
  "building_damage": {
    "collapse_count": 0,
    "severe_count": 0,
    "moderate_count": 0,
    "minor_count": 0
  },
  "survivor_signals": [
    {
      "location": "位置描述",
      "signal_type": "SOS标志|呼救声|热成像异常",
      "confidence": 0.0-1.0
    }
  ],
  "recommended_routes": [
    {
      "route": "路线名",
      "reason": "推荐理由",
      "priority": 1
    }
  ],
  "overall_assessment": "总体路况评估（100字内）"
}
只返回 JSON。
```

## 文本分析提示词（无图片，基于情报数据时）

```
你是地震灾后道路通行性研判专家。请基于以下情报分析灾区道路可通行性。

侦察区域：{area_name}
侦察中心坐标：{center_lng}, {center_lat}

相关灾情情报：
{context_data}

请返回严格 JSON（结构同上，省略 building_damage 和 survivor_signals）。
只返回 JSON。
```

## 降级规则
- AI 不可用时，基于社媒情报规则生成基础路线分析
- `road_accessible = True` 的热点标记为 "caution" 可通行
- `road_accessible = False` 的热点标记为 "道路中断" 阻断
- 降级结果需标注 `analyzed_by: "rule_based"`

## 输出用途
1. **救援路线规划**：指挥员根据推荐路线派遣救援队
2. **物资投送航线**：物资无人机参考阻断路线选择绕行
3. **危险区域标注**：在地图上标注滑坡/堰塞湖等危险区域
4. **生命迹象定位**：发现的 survivor_signals 传给优先级引擎加权
