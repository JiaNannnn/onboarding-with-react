# Issue Management

## Active Issues
```python
class CriticalIssue(BaseModel):
    issue_id: str
    description: str
    component: Literal["API", "DB", "Integration"]
    severity: Literal["P0", "P1", "P2"]
    workaround: Optional[str]
    
example_issues = []  # All critical issues have been resolved
```

## Resolved Issues
```python
resolved_issues = [
    CriticalIssue(
        issue_id="API-102",
        description="Intermittent 504s under high load",
        component="API",
        severity="P1",
        workaround="Fixed with timeout handling and concurrency controls"
    ),
    CriticalIssue(
        issue_id="API-103",
        description="AI分组功能错误: 'list' object has no attribute 'items'",
        component="API",
        severity="P1",
        workaround="添加了缓存数据结构验证和类型检查，确保缓存的数据结构符合预期的嵌套字典格式"
    ),
    CriticalIssue(
        issue_id="API-104",
        description="缓存结果中的设备组格式错误: 'Other' 的值不是字典而是列表",
        component="API",
        severity="P1",
        workaround="全面增强了数据结构修复，特别针对'Other'类别的特殊处理和各种格式转换"
    )
]
```

## Cache Format Issues
缓存结构验证问题解决方案：

1. **问题描述**: 在处理 `/bms/ai-group-points` 时，当使用缓存的分组结果时，有时会遇到 `'list' object has no attribute 'items'` 错误。错误发生在尝试遍历设备列表时，因为预期的嵌套字典结构被错误地存储或解析为其他结构。

2. **根本原因**: 
   - 缓存数据保存时未验证其结构完整性
   - 从缓存加载数据后未验证其符合预期的嵌套字典格式
   - OpenAI API响应解析时可能出现格式变化，但未被检测
   - "Other"类别的数据结构特别容易出问题，往往是列表而非预期的字典

3. **解决方案**:
   - 在缓存读取后添加全面的类型验证和修复
   - 在路由处理中增加额外的类型检查和转换
   - 对嵌套数据结构的每一层进行类型验证
   - 特别处理"Other"类别，将列表结构自动转换为字典结构

4. **预防措施**:
   - 全面修改 `_get_from_cache` 函数，添加数据验证
   - 修改 `_fallback_grouping` 函数，确保输出格式一致性
   - 修改 `_apply_grouping_to_all_points` 函数，处理各种异常格式
   - 在 `routes.py` 中的 `bms_ai_group_points` 函数中增加额外的类型检查
   - 对无法处理的数据结构提供明确的错误消息

5. **增强的数据修复功能**:
   - 自动将列表转换为字典结构 `{"Unknown": list_value}`
   - 自动将字符串转换为单元素列表 `[string_value]`
   - 尝试将各种非列表类型转换为列表
   - 输出结构的最终一致性验证

## Tech Debt Backlog
| ID  | Description                   | Impact | Effort |
|-----|-------------------------------|--------|--------|
| TD9 | Migrate to Python 3.11        | High   | Medium |
| TD4 | Refactor legacy auth code     | Medium | High   |
| TD10| 改进API缓存数据结构验证        | High   | Low    | 
| TD11| 开发缓存健康检查工具           | Medium | Medium | 