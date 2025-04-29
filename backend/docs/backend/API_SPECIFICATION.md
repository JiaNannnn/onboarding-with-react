# BMS 后端 API 规范

## 概述

本文档详细说明了 BMS (Building Management System) 后端 API 的规范，包括端点、请求格式、响应格式以及各种功能的使用说明。

## 基础 URL

所有 API 请求都应以以下 URL 为基础：

```
http://localhost:5000
```

## API 端点

### 健康检查

#### Ping 端点

```
GET /api/ping
```

用于测试 API 服务器是否正在运行。

**响应**:
```json
{
  "status": "ok"
}
```

### 点位管理 API

#### AI 点位分组

```
POST /api/points/ai-grouping
```

使用 AI 技术对 BMS 点位进行语义分组。

**请求**:
```json
{
  "points": ["AHU1_SAT", "AHU1_RAT", "FCU1_SAT", "FCU2_SAT"]
}
```

**响应**:
```json
{
  "success": true,
  "grouped_points": {
    "AHU": {
      "AHU1": ["AHU1_SAT", "AHU1_RAT"]
    },
    "FCU": {
      "FCU1": ["FCU1_SAT"],
      "FCU2": ["FCU2_SAT"]
    }
  },
  "stats": {
    "total_points": 4,
    "equipment_types": 2,
    "equipment_instances": 3
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "Error message"
}
```

#### 点位映射到 EnOS

```
POST /api/bms/map-points
```

将 BMS 点位映射到 EnOS 模型路径。

**请求**:
```json
{
  "points": [
    {
      "id": "point1",
      "pointName": "AHU1_SAT",
      "pointType": "Temperature",
      "unit": "°C",
      "description": "Supply Air Temperature",
      "deviceType": "AHU",   // 可选，如果不提供，系统会从点位名称推断
      "deviceId": "AHU1"     // 可选
    }
  ],
  "mappingConfig": {
    "targetSchema": "default",
    "matchingStrategy": "ai",
    "batchMode": true,        // 可选，启用批处理模式
    "batchSize": 20,          // 可选，每批处理的点位数量
    "deviceTypes": ["AHU", "FCU", "CH"]  // 可选，优先处理的设备类型
  }
}
```

**响应**:
```json
{
  "success": true,
  "mappings": [
    {
      "mapping": {
        "pointId": "point1",
        "enosPoint": "AHU_raw_supply_air_temp",
        "status": "mapped"
      },
      "original": {
        "pointName": "AHU1_SAT",
        "pointType": "Temperature",
        "deviceType": "AHU",
        "deviceId": "AHU1",
        "unit": "°C",
        "value": "N/A"
      }
    }
  ],
  "stats": {
    "total": 1,
    "mapped": 1,
    "errors": 0
  }
}
```

**注意**: 
- 如果未提供 `deviceType`，系统会自动尝试从点位名称推断设备类型
- 例如，从 "CT_1.TripStatus" 推断出设备类型为 "CT"（冷却塔）
- 批处理模式允许按设备类型分批处理大量点位，减少单次API负载

**错误响应**:
```json
{
  "success": false,
  "error": "Failed to map points: [error details]"
}
```

### 设备发现 API

#### 获取网络配置

```
POST /api/networks
```

获取用于设备发现的可用网络选项。

**请求**:
```json
{
  "apiGateway": "https://ag-eu2.envisioniot.com",
  "accessKey": "your-access-key",
  "secretKey": "your-secret-key",
  "orgId": "your-org-id",
  "assetId": "your-asset-id"
}
```

**响应**:
```json
{
  "networks": [
    {
      "id": "network-1",
      "name": "192.168.1.0/24",
      "description": "Local Network",
      "ipAddress": "192.168.1.0/24",
      "macAddress": "",
      "isActive": true
    }
  ],
  "status": "success"
}
```

#### 设备发现

```
POST /api/v1/devices/discover
```

在选定网络上启动设备发现。

**请求**:
```json
{
  "networks": ["192.168.1.0/24"],
  "protocol": "bacnet"
}
```

**响应**:
```json
{
  "message": "Device discovery initiated",
  "taskId": "abc123",
  "status": "processing"
}
```

#### 检查设备发现状态

```
GET /api/v1/devices/discover/{task_id}
```

检查设备发现任务的状态。

**响应**:
```json
{
  "status": "completed",
  "result": {
    "devices": [
      {
        "instanceNumber": 1001,
        "name": "AHU-1",
        "address": "192.168.1.101",
        "model": "Model XYZ",
        "vendor": "Vendor ABC"
      }
    ],
    "count": 1
  }
}
```

### 点位搜索 API

#### 启动点位搜索

```
POST /api/v1/points/search
```

启动跨多个设备的点位搜索。

**请求**:
```json
{
  "deviceIds": [1001, 1002],
  "protocol": "bacnet"
}
```

**响应**:
```json
{
  "message": "Points search initiated",
  "taskId": "xyz789",
  "status": "processing"
}
```

#### 检查点位搜索状态

```
GET /api/v1/tasks/{task_id}
```

检查点位搜索任务的状态。

**响应**:
```json
{
  "status": "completed",
  "result": {
    "status": "success",
    "message": "Points search completed",
    "device_tasks": {
      "1001": {
        "task_id": "subtask1",
        "status": "completed",
        "point_count": 15
      }
    }
  },
  "pointCount": 15
}
```

## 错误处理

所有 API 端点在发生错误时都将返回一个包含 `success: false` 和 `error` 消息的 JSON 响应。HTTP 状态码将反映错误的性质：

- `400 Bad Request`: 请求格式无效
- `401 Unauthorized`: 缺少或无效的认证凭据
- `404 Not Found`: 请求的资源不存在
- `500 Internal Server Error`: 服务器内部错误

示例错误响应:
```json
{
  "success": false,
  "error": "Missing 'points' array in request body"
}
```

## CORS 支持

所有 API 端点都支持跨源资源共享 (CORS)，包括以下响应头：

- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization`

预检请求 (OPTIONS) 将返回适当的 CORS 头，无需进一步处理。

## 重试策略

为提高可靠性，客户端应实施以下重试策略：

1. 网络错误：使用指数退避重试 (最多 3 次)
2. 500 错误：最多重试 2 次
3. 429 错误 (速率限制)：等待指定的时间后重试

## 版本控制

API 已版本化，最新版本为 v1，可通过以下路径访问：

```
/api/v1/[resource]
```

旧版 API 端点 (无版本前缀) 将继续支持，但在未来可能会被弃用。建议使用最新的版本化端点。 