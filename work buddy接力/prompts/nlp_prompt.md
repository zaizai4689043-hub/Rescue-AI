# NLP 打标提示词

## 微博文本 NLP 处理提示词

```
你是地震灾情分析专家。请对以下微博文本进行 NLP 处理，提取结构化信息。

## 输入
微博正文文本

## 输出格式（严格 JSON）

{
  "ner_locations": [
    {
      "name": "地名",
      "entity_type": "GPE|LOC|FAC",
      "confidence": 0.0-1.0
    }
  ],
  "damage_type": "人员伤亡|房屋倒塌|道路中断|次生灾害|救援进展|震感反馈",
  "sentiment": "urgent|negative|neutral|hopeful",
  "severity_vote": 1-5,
  "keywords_matched": ["关键词1", "关键词2"],
  "has_distress_signal": true|false,
  "distress_keywords": ["救命", "被困"],
  "credibility_factors": {
    "has_specific_location": true|false,
    "has_quantitative_data": true|false,
    "has_media_reference": true|false,
    "text_length_category": "short|medium|long"
  }
}

## 分类规则

### 损毁类型（6 类）
- **人员伤亡**：提及遇难、受伤、伤亡数字
- **房屋倒塌**：提及倒塌、坍塌、废墟、损毁
- **道路中断**：提及道路中断、桥断、塌方、交通中断
- **次生灾害**：提及堰塞湖、海啸、滑坡、泥石流、火灾
- **救援进展**：提及救援、搜救、救出、部队、消防
- **震感反馈**：提及震感、摇晃、晃动

### 情感（4 类）
- **urgent**：紧急呼救、急需帮助、危在旦夕
- **negative**：悲伤、痛心、恐惧、绝望
- **neutral**：客观陈述、信息传递
- **hopeful**：感恩、平安、获救、希望

### 严重度（1-5）
- 5：人员伤亡、大规模房屋倒塌
- 4：次生灾害、严重损毁
- 3：道路中断、局部损毁
- 2：救援进展、一般信息
- 1：震感反馈、情绪表达

### 呼救信号检测
关键词：救命、被困、埋了、压住、出不来、紧急求助、求救
```

## 地名提取补充提示词

```
以下是地名词典（已知地名+坐标）：
{location_dict}

请从文本中提取：
1. 词典中已匹配的地名（confidence=0.85）
2. 词典外的新地名（confidence=0.4，需人工审核）
3. 对每个地名标注实体类型（GPE=行政区划, LOC=自然地点, FAC=设施）

注意：
- "曼德勒省"和"曼德勒"应归一化为"曼德勒"
- "瑞丽市"和"瑞丽"应归一化为"瑞丽"
- 排除非地震相关的地名（如"北京"在震感反馈中）
```
