# 前端重构计划 (基于C4模型)

## 重构目标

根据C4模型架构文档，优化前端映射系统，提高代码组织性、可维护性和可扩展性。特别关注EnOS点位映射功能的增强以及批处理能力的改进。

## 重构范围

1. **API层**：优化bmsClient接口和封装方式
2. **Hooks层**：增强useBMSClient和增加模块化的映射质量分析工具
3. **Context层**：扩展MappingContext功能支持批处理和质量分析
4. **UI组件层**：重构MapPoints页面组件以支持所有新功能

## 详细实施计划

### 1. API层重构

**目标文件**: `src/api/bmsClient.ts` 和 `src/api/core/apiClient.ts`

- 拆分大型bmsClient类为更细粒度的模块
  - 基础通信模块
  - 设备与点位发现模块
  - 映射与分组模块
  - 文件操作模块
- 增强类型安全性
- 优化错误处理机制
- 添加批处理相关接口的完整支持

### 2. Hooks层重构

**目标文件**: `src/hooks/useBMSClient.ts` 和 `src/hooks/enhancedMapping.ts`

- 创建新的 `useEnhancedMapping` hook，专门处理映射质量分析
- 优化 `useBMSClient` hook中的批处理机制
- 提取通用的设备类型分析功能到独立模块
- 优化状态管理，将异步操作处理抽象为可重用模式

### 3. Context层重构

**目标文件**: `src/contexts/MappingContext.tsx`

- 扩展MappingContext状态以支持批处理进度追踪
- 添加映射质量分析结果存储
- 实现更高级的映射搜索和过滤功能
- 优化上下文重渲染性能

### 4. 组件层重构

**目标文件**: `src/pages/MapPoints/MapPoints.tsx` 和相关子组件

- 将MapPoints页面拆分为多个更小的组件
  - 文件上传组件
  - 点位表格组件 
  - 映射控制组件
  - 映射质量指示器组件
  - 批处理进度组件
- 添加映射质量分析可视化
- 实现映射改进流程的用户界面
- 优化大数据集的性能

### 5. 新功能实现

- **设备类型分析**：添加自动识别和分类设备类型的功能
- **批处理进度追踪**：实现实时进度条和状态更新
- **映射质量分析**：添加可视化指标和改进建议
- **第二轮映射优化**：实现用户触发的映射改进流程

## 实施顺序

1. API层重构（保持向后兼容性）
2. Hooks层增强
3. Context层扩展
4. 组件层重构
5. 新功能集成
6. 性能优化

## 验证与测试

- 确保每个重构步骤后，现有功能继续正常工作
- 为新功能编写单元测试
- 进行端到端测试验证完整流程