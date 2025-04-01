# OpenAI API 响应存档

此目录包含所有OpenAI API调用的响应JSON存档，用于以下目的：

1. **分析使用情况**: 跟踪API调用数量、tokens使用量和成本
2. **调试问题**: 当AI响应出现问题时，可以查看原始请求和响应
3. **改进提示**: 分析哪些提示效果好，哪些需要改进
4. **审计**: 保留所有API调用的完整记录，便于合规需求

## 文件命名规则

文件按照以下格式命名：
- `openai_response_YYYYMMDD_HHMMSS_<random>.json`: 普通AI分组API响应
- `openai_error_YYYYMMDD_HHMMSS_<random>.json`: AI分组API错误
- `openai_mapping_response_YYYYMMDD_HHMMSS_<random>.json`: 点位映射API响应
- `openai_mapping_error_YYYYMMDD_HHMMSS_<random>.json`: 点位映射API错误

## 文件内容

每个响应文件包含两个主要部分：

1. **请求信息**:
   - 模型名称(model)
   - 提示信息(prompt)
   - 温度设置(temperature)
   - 其他请求参数

2. **响应信息**:
   - 响应ID(id)
   - 返回内容(content)
   - 使用的tokens(usage)
   - 响应时间戳(timestamp)

## 数据管理

这些文件会随着时间积累变多，建议定期:

1. 用脚本整理和分析token使用量
2. 将旧文件归档到子目录中
3. 设置数据保留策略，例如只保留最近30天的数据

```python
# 示例分析脚本
import json
import os
from pathlib import Path

def analyze_token_usage():
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_calls = 0
    
    for file in Path("api_responses").glob("*.json"):
        with open(file, "r") as f:
            try:
                data = json.load(f)
                if "response" in data and "usage" in data["response"]:
                    usage = data["response"]["usage"]
                    total_prompt_tokens += usage.get("prompt_tokens", 0)
                    total_completion_tokens += usage.get("completion_tokens", 0)
                    total_calls += 1
            except:
                continue
    
    print(f"总API调用次数: {total_calls}")
    print(f"总提示tokens: {total_prompt_tokens}")
    print(f"总完成tokens: {total_completion_tokens}")
    print(f"总tokens: {total_prompt_tokens + total_completion_tokens}")
    
    # 按照OpenAI定价计算成本 (仅为示例，请根据实际使用的模型更新价格)
    # 假设使用gpt-4o
    prompt_cost = total_prompt_tokens * 0.00001  # $0.01/1K tokens
    completion_cost = total_completion_tokens * 0.00003  # $0.03/1K tokens
    total_cost = prompt_cost + completion_cost
    
    print(f"估计成本: ${total_cost:.2f}")

if __name__ == "__main__":
    analyze_token_usage()
```

此目录由系统自动创建和管理。请避免手动删除这些文件，除非您确定不再需要它们。 