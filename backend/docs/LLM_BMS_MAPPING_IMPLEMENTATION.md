# LLM驱动的BMS点位映射实施方案

## 背景与目标

BMS（建筑管理系统）测点命名在不同系统、不同建筑中存在极大的差异性和不确定性。传统基于规则的映射方法难以适应这种多样性，需要不断添加硬编码规则。而利用LLM（大型语言模型）的语义理解能力，可以更灵活地处理各种命名约定，同时我们只需要严格控制输出格式即可确保系统一致性。

**核心目标：**
- 充分利用LLM的语义理解能力解析BMS测点名称
- 确保输出格式符合EnOS schema规范
- 实现更高的映射准确率
- 减少硬编码规则，提高系统适应性

## 架构设计

### 1. LLM映射流程

```
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│                 │      │                  │      │                  │
│  测点数据收集   │──────▶   上下文构建     │──────▶   LLM映射调用    │
│                 │      │                  │      │                  │
└─────────────────┘      └──────────────────┘      └────────┬─────────┘
                                                            │
                                                            ▼
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│                 │      │                  │      │                  │
│    映射存储     │◀─────│    格式验证      │◀─────│    结果解析      │
│                 │      │                  │      │                  │
└─────────────────┘      └──────────────────┘      └──────────────────┘
```

### 2. 核心组件

#### 2.1 上下文构建器（Context Builder）

负责为每个测点构建丰富的上下文信息，帮助LLM更准确地理解测点含义。

包含信息：
- 设备类型和设备ID
- 测点名称和类型
- 单位和示例值
- 同一设备的相关测点列表
- EnOS schema约束说明

#### 2.2 LLM映射引擎（LLM Mapping Engine）

负责调用LLM API，发送prompt并接收响应。

功能：
- 管理API调用
- 处理重试逻辑
- 错误处理
- 性能监控和日志记录

#### 2.3 格式验证器（Format Validator）

负责验证LLM返回的映射结果是否符合EnOS schema格式要求。

验证规则：
- 检查JSON格式有效性
- 验证设备类型前缀一致性
- 确认类别字段有效性（raw/calc）
- 验证测量类型是否在允许列表中

#### 2.4 备用策略管理器（Fallback Manager）

当LLM返回的结果不满足格式要求时，提供备用映射策略。

策略顺序：
1. 使用反思层建议的映射
2. 使用设备类型对应的默认测量类型
3. 构建最小合规的EnOS点位名

#### 2.5 反思系统集成（Reflection System Integration）

将映射结果与反思层集成，收集成功映射模式，用于未来参考。

## 实施细节

### 1. 改进的Prompt设计

```
You are an expert in mapping Building Management System (BMS) points to EnOS schema.

Device Point Context:
- Device Type: {device_type}
- Device ID: {device_id}
- Point Name: {point_name}
- Point Type: {point_type}
- Unit: {unit}
- Value Example: {value}
- Related points in same device: {related_points}

Task: Map this BMS point to the corresponding EnOS point name.
The EnOS point name MUST follow the format: DEVICE_TYPE_CATEGORY_MEASUREMENT_TYPE_POINT

Format requirements:
1. DEVICE_TYPE must be "{device_type}" or its standard abbreviation.
2. CATEGORY must be "raw" or "calc"
3. MEASUREMENT_TYPE must be one of: temp, power, status, speed, pressure, flow, 
   humidity, position, energy, current, voltage, frequency, level, occupancy, 
   setpoint, mode, command, alarm, damper, valve, state, volume
4. POINT can include additional context for the specific point

BMS naming conventions:
- Temperature points often use "temp", "tmp", or "temperature" in their names
- Status points often use "status", "state", "on", "off"
- Power points may include "kW", "power", "demand"
- Energy points may include "kWh", "energy", "consumption"
- Flow points may include "flow", "cfm", "gpm"

Return ONLY a valid JSON object containing the mapped EnOS point with the following structure:
{
    "enos_point": "DEVICE_TYPE_CATEGORY_MEASUREMENT_TYPE_POINT"
}
```

### 2. 实施映射引擎

```python
def map_point_with_llm(self, raw_point: str, device_type: str, context: Dict) -> Optional[str]:
    """
    使用LLM映射BMS点位到EnOS schema
    
    Args:
        raw_point: 原始BMS点位名称
        device_type: 设备类型
        context: 上下文信息
    
    Returns:
        映射后的EnOS点位名称，失败则返回None
    """
    # 1. 构建上下文
    prompt = self._build_mapping_context(raw_point, device_type, context)
    
    # 2. 调用LLM API
    for attempt in range(self.max_retries):
        try:
            response = self._call_llm_api(prompt)
            
            # 3. 解析响应
            result = self._parse_llm_response(response)
            
            # 4. 验证格式
            if self._validate_enos_format(result, device_type):
                return result
            else:
                # 记录错误并重试
                logger.warning(f"LLM返回格式无效: {result}, 尝试 {attempt+1}/{self.max_retries}")
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}, 尝试 {attempt+1}/{self.max_retries}")
            
            if attempt == self.max_retries - 1:
                break
            time.sleep(self._calculate_backoff_time(attempt))
    
    # 5. 使用备用策略
    return self._apply_fallback_strategy(raw_point, device_type, context)
```

### 3. 备用策略设计

```python
def _apply_fallback_strategy(self, raw_point: str, device_type: str, context: Dict) -> str:
    """
    当LLM映射失败时应用备用策略
    
    策略优先级:
    1. 反思层建议
    2. 点位名称模式匹配
    3. 设备类型默认映射
    """
    # 策略1: 尝试从反思层获取建议
    if self.enable_reflection and hasattr(self, 'reflection_system'):
        suggestion = self.reflection_system.suggest_mapping({
            'pointName': raw_point, 
            'deviceType': device_type
        })
        
        if suggestion.get('success') and suggestion.get('suggested_mapping'):
            return suggestion['suggested_mapping']
    
    # 策略2: 基于点位名称的简单模式匹配
    point_lowercase = raw_point.lower()
    
    # 提取可能的测量类型
    measurement_type = "status"  # 默认为status
    
    if "temp" in point_lowercase or "temperature" in point_lowercase:
        measurement_type = "temp"
    elif "kw" in point_lowercase and not "kwh" in point_lowercase:
        measurement_type = "power"
    elif "kwh" in point_lowercase or "energy" in point_lowercase:
        measurement_type = "energy"
    elif "pressure" in point_lowercase or "pres" in point_lowercase:
        measurement_type = "pressure"
    elif "flow" in point_lowercase:
        measurement_type = "flow"
    elif "humid" in point_lowercase or "rh" in point_lowercase:
        measurement_type = "humidity"
    
    # 策略3: 构建最小合规的EnOS点位名
    device_prefix = self._get_expected_enos_prefix(device_type)
    fallback_point = f"{device_prefix}_raw_{measurement_type}"
    
    return fallback_point
```

### 4. 增强格式验证

```python
def _validate_enos_format(self, enos_point: str, device_type: str) -> bool:
    """验证EnOS点位名称格式
    
    格式要求:
    - 必须包含至少3个下划线分隔的部分
    - 第一部分必须与设备类型或其标准缩写匹配
    - 第二部分必须是'raw'或'calc'
    - 第三部分必须是有效的测量类型
    """
    if not enos_point:
        return False
        
    parts = enos_point.split('_')
    if len(parts) < 3:
        return False
    
    # 验证设备类型前缀
    expected_prefix = self._get_expected_enos_prefix(device_type)
    if parts[0] != expected_prefix:
        return False
    
    # 验证类别
    if parts[1] not in {'raw', 'calc'}:
        return False
    
    # 验证测量类型
    valid_measurements = {
        'temp', 'power', 'status', 'speed', 'pressure', 'flow', 'humidity', 
        'position', 'energy', 'current', 'voltage', 'frequency', 'level', 
        'occupancy', 'setpoint', 'mode', 'command', 'alarm', 'damper', 
        'valve', 'state', 'volume'
    }
    
    if parts[2] not in valid_measurements:
        return False
    
    return True
```

### 5. 从LLM响应中提取结果

```python
def _parse_llm_response(self, response: str) -> Optional[str]:
    """从LLM响应中解析EnOS点位名称
    
    处理各种可能的响应格式，提取enos_point字段
    """
    try:
        # 清理响应文本
        cleaned_response = self._clean_json_response(response)
        
        # 解析JSON
        result = json.loads(cleaned_response)
        
        # 提取enos_point字段
        if 'enos_point' in result:
            return result['enos_point']
        
        return None
    except json.JSONDecodeError:
        # 尝试使用正则表达式提取enos_point
        import re
        match = re.search(r'"enos_point"\s*:\s*"([^"]+)"', response)
        if match:
            return match.group(1)
        
        return None
```

## 实施计划

### 阶段一：基础实施（2周）

1. **设计与架构** (3天)
   - 更新现有架构以整合新的LLM映射流程
   - 设计改进的上下文构建流程
   - 更新单元测试计划

2. **核心组件开发** (7天)
   - 实现改进的映射引擎
   - 开发上下文构建器
   - 增强格式验证器
   - 实现备用策略管理器

3. **测试与调整** (4天)
   - 单元测试每个组件
   - 集成测试完整流程
   - 性能测试和优化

### 阶段二：反思层集成（1周）

1. **反思系统对接** (3天)
   - 将映射结果与反思层集成
   - 实现记忆化映射模式
   - 更新策略选择机制

2. **质量评估框架** (2天)
   - 实现映射质量评估指标
   - 开发映射质量监控仪表板

### 阶段三：部署与优化（1周）

1. **部署准备** (2天)
   - 准备部署文档
   - 更新API文档
   - 环境配置和迁移计划

2. **部署与监控** (3天)
   - 系统部署
   - 设置监控和警报
   - 建立性能基准

## 评估指标

1. **映射成功率**
   - 基准：当前系统的映射成功率
   - 目标：提高10%以上

2. **格式合规率**
   - 目标：LLM返回结果99%符合EnOS格式要求

3. **处理新设备类型的能力**
   - 目标：无需代码修改支持新设备类型的准确率达80%以上

4. **处理异常命名的能力**
   - 目标：处理非标准命名测点的成功率达75%以上

5. **系统响应时间**
   - 基准：当前平均处理时间
   - 目标：保持或提高现有性能

## 风险与缓解措施

1. **LLM API稳定性**
   - 风险：LLM服务可能存在中断或延迟
   - 缓解：实现完善的重试机制和备用策略

2. **映射准确性**
   - 风险：某些特殊领域的测点可能映射错误
   - 缓解：建立质量评估框架和人工审核流程

3. **性能开销**
   - 风险：LLM调用可能增加处理时间
   - 缓解：实现有效的缓存策略和批处理

4. **成本控制**
   - 风险：大量LLM调用可能增加成本
   - 缓解：实现高效的反思层来减少重复调用，优化缓存策略

## 结论

通过利用LLM强大的语义理解能力，结合严格的格式控制和反思层学习，我们可以构建一个更灵活、更准确的BMS测点映射系统。这种方法将大大减少硬编码规则的需求，提高系统处理各种命名约定的能力，同时保持输出的一致性和可预测性。

这种平衡方法既尊重了BMS领域的不确定性和多样性，又确保了系统输出的标准化，为建筑管理系统数据的有效集成和分析奠定基础。