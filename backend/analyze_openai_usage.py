#!/usr/bin/env python
"""
OpenAI API Usage Analyzer

此脚本分析api_responses目录中的所有JSON文件，
计算token使用量、API调用次数和估计成本。
"""

import json
import os
from pathlib import Path
import datetime
import argparse
from collections import defaultdict
import matplotlib.pyplot as plt

# OpenAI模型定价(2024年3月价格，单位：美元/1K tokens)
MODEL_PRICING = {
    "gpt-4o": {
        "prompt": 0.01,
        "completion": 0.03
    },
    "gpt-4-turbo": {
        "prompt": 0.01,
        "completion": 0.03
    },
    "gpt-4": {
        "prompt": 0.03,
        "completion": 0.06
    },
    "gpt-3.5-turbo": {
        "prompt": 0.0015,
        "completion": 0.002
    }
}

def parse_date_from_filename(filename):
    """从文件名中解析日期"""
    try:
        # 文件名格式: openai_response_20240326_123045_abcdef.json
        date_part = filename.split('_')[2]  # 20240326
        return datetime.datetime.strptime(date_part, "%Y%m%d").date()
    except (IndexError, ValueError):
        # 如果无法解析日期，返回今天的日期
        return datetime.date.today()

def get_model_prices(model):
    """获取模型的定价"""
    # 处理不同模型名称变体
    model_lower = model.lower()
    
    if "gpt-4o" in model_lower:
        return MODEL_PRICING["gpt-4o"]
    elif "gpt-4-turbo" in model_lower:
        return MODEL_PRICING["gpt-4-turbo"]
    elif "gpt-4" in model_lower:
        return MODEL_PRICING["gpt-4"]
    elif "gpt-3.5" in model_lower:
        return MODEL_PRICING["gpt-3.5-turbo"]
    else:
        # 默认使用gpt-4o的价格
        print(f"警告: 未知模型 '{model}', 使用gpt-4o定价")
        return MODEL_PRICING["gpt-4o"]

def analyze_token_usage(days=None, export_csv=False, show_plot=False):
    """分析Token使用情况并计算成本"""
    api_responses_dir = Path(__file__).parent / "api_responses"
    
    if not api_responses_dir.exists():
        print(f"错误: 目录 {api_responses_dir} 不存在")
        return
    
    # 过滤特定天数的文件
    cutoff_date = None
    if days:
        cutoff_date = datetime.date.today() - datetime.timedelta(days=days)
    
    # 汇总数据
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_calls = 0
    errors = 0
    
    # 按模型统计
    model_stats = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0})
    
    # 按日期统计
    daily_stats = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0, "errors": 0})
    
    # 按API类型统计
    api_type_stats = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0, "errors": 0})
    
    # 按请求类型统计 (grouping vs mapping)
    request_type_stats = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0, "errors": 0})
    
    # 错误类型统计
    error_type_stats = defaultdict(int)
    
    # 点位统计 (针对mapping请求)
    point_stats = {}
    
    print(f"正在分析 {api_responses_dir} 中的API响应文件...")
    
    # 计算文件总数来显示进度
    total_files = len(list(api_responses_dir.glob("*.json")))
    processed_files = 0
    
    for file in api_responses_dir.glob("*.json"):
        if file.name == "README.md":
            continue
            
        processed_files += 1
        if processed_files % 100 == 0 or processed_files == total_files:
            print(f"已处理 {processed_files}/{total_files} 文件...")
            
        # 提取日期
        file_date = parse_date_from_filename(file.name)
        
        # 如果指定了天数，跳过旧文件
        if cutoff_date and file_date < cutoff_date:
            continue
        
        # 提取API类型
        api_type = "unknown"
        request_type = "unknown"
        
        if "_response_" in file.name:
            api_type = file.name.split('_')[0]
            
        # 判断请求类型
        if "mapping" in file.name:
            request_type = "mapping"
        elif "openai" in file.name:
            request_type = "grouping"
        
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # 处理API响应
                if "response" in data and "usage" in data["response"]:
                    usage = data["response"]["usage"]
                    model = data["response"].get("model", "unknown")
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    
                    # 更新总计
                    total_prompt_tokens += prompt_tokens
                    total_completion_tokens += completion_tokens
                    total_calls += 1
                    
                    # 计算成本
                    prices = get_model_prices(model)
                    prompt_cost = prompt_tokens * prices["prompt"] / 1000
                    completion_cost = completion_tokens * prices["completion"] / 1000
                    total_cost = prompt_cost + completion_cost
                    
                    # 更新模型统计
                    model_stats[model]["calls"] += 1
                    model_stats[model]["prompt_tokens"] += prompt_tokens
                    model_stats[model]["completion_tokens"] += completion_tokens
                    model_stats[model]["cost"] += total_cost
                    
                    # 更新日期统计
                    date_str = file_date.strftime("%Y-%m-%d")
                    daily_stats[date_str]["calls"] += 1
                    daily_stats[date_str]["tokens"] += prompt_tokens + completion_tokens
                    daily_stats[date_str]["cost"] += total_cost
                    
                    # 更新API类型统计
                    api_type_stats[api_type]["calls"] += 1
                    api_type_stats[api_type]["tokens"] += prompt_tokens + completion_tokens
                    api_type_stats[api_type]["cost"] += total_cost
                    
                    # 更新请求类型统计
                    request_type_stats[request_type]["calls"] += 1
                    request_type_stats[request_type]["tokens"] += prompt_tokens + completion_tokens
                    request_type_stats[request_type]["cost"] += total_cost
                    
                    # 如果是mapping请求，统计点位信息
                    if request_type == "mapping" and "request" in data:
                        point_name = data["request"].get("point", "")
                        if point_name:
                            if point_name not in point_stats:
                                point_stats[point_name] = {"calls": 0, "tokens": 0}
                            point_stats[point_name]["calls"] += 1
                            point_stats[point_name]["tokens"] += prompt_tokens + completion_tokens
                    
                # 处理错误信息
                elif "error" in data:
                    errors += 1
                    
                    # 提取错误类型
                    error_msg = data.get("error", "")
                    error_type = data.get("error_type", "unknown")
                    
                    if not error_type or error_type == "unknown":
                        # 尝试从错误信息中推断类型
                        if "rate limit" in error_msg.lower():
                            error_type = "rate_limit"
                        elif "timeout" in error_msg.lower():
                            error_type = "timeout"
                        elif "invalid" in error_msg.lower():
                            error_type = "invalid_request"
                        elif "key" in error_msg.lower():
                            error_type = "api_key"
                        elif "json" in error_msg.lower():
                            error_type = "json_decode"
                        else:
                            error_type = "other"
                    
                    # 更新错误统计
                    error_type_stats[error_type] += 1
                    
                    # 更新请求类型错误统计
                    request_type_stats[request_type]["errors"] += 1
                    api_type_stats[api_type]["errors"] += 1
                    
                    # 更新日期错误统计
                    date_str = file_date.strftime("%Y-%m-%d")
                    daily_stats[date_str]["errors"] += 1
                    
        except Exception as e:
            print(f"处理文件 {file.name} 时出错: {e}")
    
    # 输出结果
    print("\n===== OpenAI API 使用统计 =====")
    
    if days:
        print(f"\n过去 {days} 天的统计:")
    else:
        print("\n所有时间的统计:")
    
    print(f"总API调用次数: {total_calls}")
    print(f"错误次数: {errors} ({errors/max(total_calls+errors, 1)*100:.1f}%)")
    print(f"总提示tokens: {total_prompt_tokens:,}")
    print(f"总完成tokens: {total_completion_tokens:,}")
    print(f"总tokens: {total_prompt_tokens + total_completion_tokens:,}")
    
    # 计算总成本
    total_cost = sum(stats["cost"] for stats in model_stats.values())
    print(f"估计总成本: ${total_cost:.2f}")
    
    # 按模型分类的统计
    print("\n按模型统计:")
    for model, stats in sorted(model_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
        model_total_tokens = stats["prompt_tokens"] + stats["completion_tokens"]
        print(f"  {model}: {stats['calls']} 调用, {model_total_tokens:,} tokens, ${stats['cost']:.2f}")
    
    # 按API类型的统计
    print("\n按API类型统计:")
    for api_type, stats in sorted(api_type_stats.items(), key=lambda x: x[1]["calls"], reverse=True):
        print(f"  {api_type}: {stats['calls']} 调用, {stats['tokens']:,} tokens, ${stats['cost']:.2f}, 错误: {stats['errors']}")
    
    # 按请求类型的统计
    print("\n按请求类型统计:")
    for req_type, stats in sorted(request_type_stats.items(), key=lambda x: x[1]["calls"], reverse=True):
        if req_type == "unknown":
            continue
        success_rate = 100 * (stats["calls"] - stats["errors"]) / max(stats["calls"], 1)
        print(f"  {req_type}: {stats['calls']} 调用, {stats['tokens']:,} tokens, ${stats['cost']:.2f}, 成功率: {success_rate:.1f}%")
    
    # 错误类型统计
    if errors > 0:
        print("\n错误类型统计:")
        for error_type, count in sorted(error_type_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} ({count/errors*100:.1f}%)")
    
    # 显示点位统计的前10个最常用点位
    if point_stats:
        print("\n点位统计 (前10个最常调用):")
        for point, stats in sorted(point_stats.items(), key=lambda x: x[1]["calls"], reverse=True)[:10]:
            print(f"  {point}: {stats['calls']} 调用, {stats['tokens']:,} tokens")
    
    # 导出为CSV
    if export_csv:
        # 导出日期统计
        daily_csv_file = api_responses_dir / "usage_report_daily.csv"
        with open(daily_csv_file, "w", encoding="utf-8") as f:
            f.write("日期,调用次数,Tokens,成本($),错误数\n")
            for date, stats in sorted(daily_stats.items()):
                f.write(f"{date},{stats['calls']},{stats['tokens']},{stats['cost']:.2f},{stats['errors']}\n")
        print(f"\n导出日期CSV报告到: {daily_csv_file}")
        
        # 导出请求类型统计
        request_csv_file = api_responses_dir / "usage_report_by_type.csv"
        with open(request_csv_file, "w", encoding="utf-8") as f:
            f.write("请求类型,调用次数,Tokens,成本($),错误数,成功率(%)\n")
            for req_type, stats in sorted(request_type_stats.items(), key=lambda x: x[0]):
                success_rate = 100 * (stats["calls"] - stats["errors"]) / max(stats["calls"], 1)
                f.write(f"{req_type},{stats['calls']},{stats['tokens']},{stats['cost']:.2f},{stats['errors']},{success_rate:.1f}\n")
        print(f"导出请求类型CSV报告到: {request_csv_file}")
        
        # 导出错误类型统计
        if errors > 0:
            error_csv_file = api_responses_dir / "usage_report_errors.csv"
            with open(error_csv_file, "w", encoding="utf-8") as f:
                f.write("错误类型,数量,百分比(%)\n")
                for error_type, count in sorted(error_type_stats.items(), key=lambda x: x[0]):
                    f.write(f"{error_type},{count},{count/errors*100:.1f}\n")
            print(f"导出错误类型CSV报告到: {error_csv_file}")
    
    # 生成图表
    if show_plot and daily_stats:
        try:
            # 创建更多的图表
            plt.figure(figsize=(15, 12))
            
            dates = sorted(daily_stats.keys())
            calls = [daily_stats[date]["calls"] for date in dates]
            tokens = [daily_stats[date]["tokens"] for date in dates]
            costs = [daily_stats[date]["cost"] for date in dates]
            errors = [daily_stats[date]["errors"] for date in dates]
            
            # 调用次数图表
            plt.subplot(2, 2, 1)
            plt.bar(dates, calls, color='blue')
            plt.title('每日API调用次数')
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Token使用量图表
            plt.subplot(2, 2, 2)
            plt.bar(dates, tokens, color='green')
            plt.title('每日Token使用量')
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 成本图表
            plt.subplot(2, 2, 3)
            plt.bar(dates, costs, color='red')
            plt.title('每日成本($)')
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 错误数图表
            plt.subplot(2, 2, 4)
            plt.bar(dates, errors, color='orange')
            plt.title('每日错误数')
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            
            # 另一个图表：请求类型比较
            if len(request_type_stats) > 1:
                plt.figure(figsize=(12, 5))
                
                req_types = [t for t in request_type_stats.keys() if t != "unknown"]
                req_calls = [request_type_stats[t]["calls"] for t in req_types]
                req_tokens = [request_type_stats[t]["tokens"] for t in req_types]
                req_costs = [request_type_stats[t]["cost"] for t in req_types]
                
                plt.subplot(1, 3, 1)
                plt.bar(req_types, req_calls, color='purple')
                plt.title('请求类型调用次数')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                plt.subplot(1, 3, 2)
                plt.bar(req_types, req_tokens, color='teal')
                plt.title('请求类型Token使用量')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                plt.subplot(1, 3, 3)
                plt.bar(req_types, req_costs, color='brown')
                plt.title('请求类型成本($)')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                plt.tight_layout()
            
            # 保存图表
            plt.savefig(api_responses_dir / "usage_report_charts.png")
            print(f"生成图表到: {api_responses_dir / 'usage_report_charts.png'}")
            
            if show_plot:
                plt.show()
                
        except Exception as e:
            print(f"生成图表时出错: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='分析OpenAI API使用情况和成本')
    parser.add_argument('--days', type=int, help='分析最近几天的数据')
    parser.add_argument('--csv', action='store_true', help='导出CSV报告')
    parser.add_argument('--plot', action='store_true', help='生成使用情况图表')
    
    args = parser.parse_args()
    
    analyze_token_usage(days=args.days, export_csv=args.csv, show_plot=args.plot)

if __name__ == "__main__":
    main() 