#!/usr/bin/env python
"""
缓存健康检查工具

此工具用于检查缓存文件的健康状况，识别潜在的问题，并提供清理建议。
"""

import os
import sys
import json
import time
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 获取根目录
ROOT_DIR = Path(__file__).parent.parent
CACHE_DIR = ROOT_DIR / "cache"
CACHE_TIMEOUT = int(os.getenv("AI_CACHE_TIMEOUT", 86400))  # 默认24小时

def check_json_valid(file_path: Path) -> Tuple[bool, str, Any]:
    """检查JSON文件是否有效"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, "OK", data
    except Exception as e:
        return False, f"JSON解析错误: {str(e)}", None

def check_structure_valid(data: Any) -> Tuple[bool, str, List[str]]:
    """检查数据结构是否符合预期"""
    issues = []
    
    # 检查顶层是否为字典
    if not isinstance(data, dict):
        return False, f"顶层不是字典，而是 {type(data).__name__}", ["顶层格式错误"]
    
    # 检查设备类型层
    for device_type, devices in data.items():
        if not isinstance(devices, dict):
            if isinstance(devices, list):
                issues.append(f"设备类型 '{device_type}' 的值是列表而不是字典")
            else:
                issues.append(f"设备类型 '{device_type}' 的值不是字典，而是 {type(devices).__name__}")
            continue
            
        # 检查设备实例层
        for device_id, points in devices.items():
            if not isinstance(points, list):
                issues.append(f"设备 '{device_id}' 的点位不是列表，而是 {type(points).__name__}")
    
    # 检查是否存在"Other"类别
    if "Other" not in data and "OTHER" not in data:
        issues.append("缺少'Other'类别")
    
    # 如果没有问题，返回成功
    if not issues:
        return True, "结构有效", []
        
    return False, "结构问题", issues

def check_cache_health() -> Dict:
    """检查所有缓存文件的健康状况"""
    results = {
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "expired_files": 0,
        "structure_issues": 0,
        "json_issues": 0,
        "problems": [],
        "suggested_cleanups": []
    }
    
    # 获取所有缓存文件
    cache_files = list(CACHE_DIR.glob("*.json"))
    results["total_files"] = len(cache_files)
    
    if not cache_files:
        print("缓存目录为空或不存在")
        return results
    
    # 检查每个文件
    for file_path in cache_files:
        file_age = time.time() - file_path.stat().st_mtime
        
        # 检查是否过期
        if file_age > CACHE_TIMEOUT:
            results["expired_files"] += 1
            results["suggested_cleanups"].append(f"删除过期文件 {file_path.name} (已过期 {file_age/3600:.1f} 小时)")
            continue
        
        # 检查JSON是否有效
        json_valid, json_error, data = check_json_valid(file_path)
        if not json_valid:
            results["invalid_files"] += 1
            results["json_issues"] += 1
            results["problems"].append(f"文件 {file_path.name}: {json_error}")
            results["suggested_cleanups"].append(f"删除无效JSON文件 {file_path.name}")
            continue
        
        # 检查结构是否有效
        structure_valid, structure_error, issues = check_structure_valid(data)
        if not structure_valid:
            results["invalid_files"] += 1
            results["structure_issues"] += 1
            for issue in issues:
                results["problems"].append(f"文件 {file_path.name}: {issue}")
            
            # 如果问题可修复，添加修复建议
            if "Other" not in data and "OTHER" not in data:
                results["suggested_cleanups"].append(f"删除缺少'Other'类别的文件 {file_path.name}")
            elif any("列表而不是字典" in issue for issue in issues):
                results["suggested_cleanups"].append(f"删除结构不一致的文件 {file_path.name}")
            else:
                results["suggested_cleanups"].append(f"删除结构有问题的文件 {file_path.name}")
            continue
        
        # 文件有效
        results["valid_files"] += 1
    
    return results

def print_report(results: Dict) -> None:
    """打印健康检查报告"""
    print("\n===== 缓存健康检查报告 =====")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"缓存目录: {CACHE_DIR}")
    print(f"缓存超时: {CACHE_TIMEOUT} 秒 ({CACHE_TIMEOUT/3600:.1f} 小时)")
    print("\n--- 统计信息 ---")
    print(f"总文件数: {results['total_files']}")
    print(f"有效文件: {results['valid_files']} ({results['valid_files']/max(results['total_files'], 1)*100:.1f}%)")
    print(f"无效文件: {results['invalid_files']} ({results['invalid_files']/max(results['total_files'], 1)*100:.1f}%)")
    print(f"过期文件: {results['expired_files']} ({results['expired_files']/max(results['total_files'], 1)*100:.1f}%)")
    
    if results["problems"]:
        print("\n--- 发现的问题 ---")
        for i, problem in enumerate(results["problems"], 1):
            print(f"{i}. {problem}")
    
    if results["suggested_cleanups"]:
        print("\n--- 清理建议 ---")
        for i, cleanup in enumerate(results["suggested_cleanups"], 1):
            print(f"{i}. {cleanup}")
        
        # 生成清理命令
        if sys.platform == "win32":
            print("\n清理命令 (Windows PowerShell):")
            print("Remove-Item -Path cache\\*.json -Force  # 删除所有缓存")
            print("New-Item -ItemType Directory -Force -Path cache  # 重新创建缓存目录")
        else:
            print("\n清理命令 (Unix/Linux/Mac):")
            print("rm -rf cache/*.json  # 删除所有缓存")
            print("mkdir -p cache  # 确保缓存目录存在")
    
    print("\n缓存健康状态: ", end="")
    if results["invalid_files"] == 0 and results["expired_files"] == 0:
        print("✅ 良好")
    elif results["invalid_files"] / max(results["total_files"], 1) < 0.1:
        print("⚠️ 有少量问题")
    else:
        print("❌ 有严重问题")

def main():
    """主函数"""
    print("正在检查缓存健康状态...")
    
    # 检查缓存目录是否存在
    if not CACHE_DIR.exists():
        print(f"缓存目录不存在: {CACHE_DIR}")
        print("正在创建缓存目录...")
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
    
    # 执行健康检查
    results = check_cache_health()
    
    # 打印报告
    print_report(results)
    
    # 返回状态码
    if results["invalid_files"] > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 