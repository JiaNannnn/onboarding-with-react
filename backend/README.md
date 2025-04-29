# BMS Points API with AI-Based Grouping and Mapping

This API provides endpoints for managing Building Management System (BMS) points with AI-powered grouping and mapping capabilities.

## Features

- Fetch points from BMS systems
- Group points by device type using AI (OpenAI GPT-4o)
- Map points to standardized schemas using AI
- EnOS integration for BMS data
- Asynchronous task processing with Celery
- API status and documentation endpoints

## Requirements

- Python 3.8+
- Redis (for Celery task queue)
- OpenAI API key (for AI-based features)

## Quick Start

### Setup with Deployment Script

The easiest way to get started is to use the deployment script:

```bash
# Show help message
python deploy.py

# Install dependencies and setup environment
python deploy.py --install --setup-env --openai-key "your-openai-api-key"

# Run tests
python deploy.py --test

# Run the API server
python deploy.py --run --env development --port 5000
```

### Manual Setup

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
pip install openai==1.7.0 pandas==2.1.0
```

4. Create a `.env` file with your configuration:

```
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
```

5. Run the API server:

```bash
python run.py --port 5000 --env development
```

## API Endpoints

### Status Endpoint

```
GET /api/status
```

Returns the API status, version, and available endpoints.

### Points Search

```
POST /api/bms/fetch-points
GET /api/bms/fetch-points/{task_id}
```

Initiates a points search task and checks its status.

### Device Points

```
GET /api/bms/device-points/{asset_id}/{device_instance}
GET /api/bms/device-points/status/{task_id}
```

Fetches points for a specific device and checks the task status.

### Group Points

```
POST /api/group-points
```

Groups BMS points by device type using AI.

#### Request Format

```json
{
  "points": ["ZN-T", "ZN-SP", "ZN-H", "AHU1-SA-T", "AHU1-SA-P", "AHU1-SA-F"],
  "credentials": {
    "apiGateway": "https://example.com",
    "accessKey": "your-access-key",
    "secretKey": "your-secret-key",
    "orgId": "your-org-id",
    "assetId": "your-asset-id"
  }
}
```

### Map Points

```
POST /api/map-points
```

Maps BMS points to standardized schemas using AI.

#### Request Format

```json
{
  "points": [
    {
      "name": "ZN-T",
      "device_type": "VAV"
    }
  ],
  "credentials": {
    "apiGateway": "https://example.com",
    "accessKey": "your-access-key",
    "secretKey": "your-secret-key",
    "orgId": "your-org-id",
    "assetId": "your-asset-id"
  }
}
```

## API Cost Optimization

The system uses caching to minimize OpenAI API usage costs:

1. **Result Caching**: Responses from the AI grouping API are cached based on a hash of the input points. Identical grouping requests will use the cached result instead of making a new API call.

2. **Reduced Retries**: The system uses intelligent retry logic that avoids retries for specific error types like rate limits or type errors that won't be resolved by retrying.

3. **Cache Control**: Configure cache behavior with these environment variables:
   - `DISABLE_AI_CACHE=true|false` - Enable/disable the cache (default: false)
   - `AI_CACHE_TIMEOUT=86400` - Cache expiration in seconds (default: 24 hours)
   - `MAX_AI_RETRIES=2` - Maximum retry attempts for AI-based grouping (default: 2)

4. **Fallback Mechanism**: When AI processing fails, the system automatically falls back to pattern-based grouping and reports the actual method used in the response.

5. **Smart Sampling**: The AI model processes only a sample of points (up to 100) to identify patterns, then applies those patterns to the remaining points without additional API calls.

6. **Data Structure Validation**: The system performs comprehensive validation of cached data structures to ensure they match the expected format before use, preventing type-related errors:
   - Validates that grouped points are correctly stored as nested dictionaries
   - Automatically converts single string values to lists when appropriate
   - Provides detailed error logging when cached data cannot be properly validated
   - Includes runtime type checking in API routes to handle unexpected data formats gracefully

7. **高级数据修复**: 系统包含强大的数据修复功能，自动处理各种格式错误：
   - 智能修复"Other"类别的特殊格式问题（常见的列表vs字典结构冲突）
   - 自动将不兼容的数据类型转换为预期格式
   - 保持嵌套结构的一致性和完整性
   - 详细记录所有格式修复操作，便于问题追踪

Cache files are stored in the `/cache` directory and are automatically managed based on the cache timeout setting.

### Expected Cache Format

The system expects a specific nested structure for cached data:

```python
{
    "device_type1": {                    # 第一级：设备类型（字典）
        "device_instance1": [            # 第二级：设备实例（字典）
            "point1", "point2", ...      # 第三级：点位列表（数组）
        ],
        "device_instance2": [ ... ]
    },
    "device_type2": { ... },
    "Other": {                           # 特殊类别：未识别设备
        "unknown_device1": [ ... ],
        "Unknown": [ ... ]               # 默认分组
    }
}
```

格式验证确保每一级都符合预期的数据类型，缺失或错误的结构会被自动修复或报告。

### Troubleshooting Cache Issues

If you encounter problems with the caching system:

1. **Clear the cache**: Remove files from the `/cache` directory to force new API calls
   ```bash
   # Windows
   rmdir /s /q cache
   mkdir cache
   
   # Linux/Mac
   rm -rf cache && mkdir cache
   ```

2. **Check logs**: Examine the application logs for validation errors with these patterns:
   - `缓存结果格式错误: 预期是字典，实际类型...` - 整体缓存格式不正确
   - `缓存结果中的设备组格式错误: 设备类型...` - 设备类型值不是字典
   - `缓存结果中的点位列表格式错误: 设备...` - 点位不是列表
   - `已自动修复...` - 系统成功修复了格式问题

3. **Disable caching**: Set `DISABLE_AI_CACHE=true` to bypass cache problems temporarily

4. **Update cache timeout**: Reduce `AI_CACHE_TIMEOUT` to automatically invalidate older cached results

5. **检查UnicodeError**: 中文日志可能在某些环境下出现编码问题，设置环境变量`PYTHONIOENCODING=utf-8`解决

### Cache Health Tool

A cache health check tool is available to scan your cache files for potential problems:

```bash
python tools/check_cache_health.py
```

The tool reports:
- Number of valid vs. invalid cache files
- Common format problems
- Suggestions for cache cleanup

## OpenAI API Response Logging

All OpenAI API calls are automatically logged to JSON files in the `/api_responses` directory. This provides:

1. **Transparency**: Full record of all API requests and responses for auditing
2. **Cost Analysis**: Tracking of token usage for budgeting purposes
3. **Debugging**: Detailed error information when API calls fail
4. **Optimization**: Insight into prompt efficiency and response quality

### Analyzing API Usage

Use the included analysis script to check API usage statistics:

```bash
# Basic usage - shows all-time stats
python analyze_openai_usage.py

# Show usage for the last 7 days
python analyze_openai_usage.py --days 7

# Export to CSV and generate charts
python analyze_openai_usage.py --csv --plot
```

The script shows:
- Total API calls and token usage
- Cost estimates based on current OpenAI pricing
- Breakdown by model and API type
- Daily usage trends (with charts when using --plot)

### Managing Response Data

The API response files accumulate over time, so it's recommended to:
1. Regularly analyze and review usage
2. Archive or delete older files as needed
3. Set up a data retention policy based on your needs

## Testing

Run the test suite:

```bash
pytest tests -v
```

Test with real data:

```bash
python tests/test_real_data.py
```

## Configuration

Configuration settings are defined in `config.py` with separate classes for different environments:

- `DevelopmentConfig`: For local development
- `TestingConfig`: For running tests
- `ProductionConfig`: For production deployment

## Project Structure

```
├── app/                 # Application code
│   ├── __init__.py      # App factory
│   ├── api/             # API related code
│   │   ├── __init__.py
│   │   └── routes.py    # API routes
│   ├── bms/             # BMS related code
│   │   ├── __init__.py
│   │   └── routes.py    # BMS routes
│   └── tasks/           # Celery tasks
│       ├── __init__.py
│       └── search.py    # Search tasks
├── tests/               # Test suite
├── config.py            # Configuration
├── deploy.py            # Deployment script
├── run.py               # Run script
└── requirements.txt     # Dependencies
```

## License

MIT 