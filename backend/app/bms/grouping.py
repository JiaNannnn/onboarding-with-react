import os
from typing import Dict, List, Any
import json
import logging
import time
from openai import OpenAI
import random
import re
import hashlib
from pathlib import Path
import datetime
import functools
import gc
import tracemalloc
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Create cache directory if it doesn't exist
CACHE_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'cache'))
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Create a directory to store API responses for debugging
API_RESPONSES_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'api_responses'))
API_RESPONSES_DIR.mkdir(exist_ok=True, parents=True)

def performance_monitor(func):
    """
    装饰器，用于监控函数的执行时间和内存使用情况
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 启动内存跟踪
        tracemalloc.start()
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行前内存快照
        before_memory = tracemalloc.get_traced_memory()
        
        try:
            # 执行原始函数
            result = func(*args, **kwargs)
            return result
        finally:
            # 记录结束时间
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 执行后内存快照
            after_memory = tracemalloc.get_traced_memory()
            
            # 计算内存差异
            memory_diff = after_memory[1] - before_memory[1]
            
            # 停止内存跟踪
            tracemalloc.stop()
            
            # 触发垃圾回收
            gc.collect()
            
            # 记录执行统计信息
            logger.info(f"函数 {func.__name__} 执行统计:")
            logger.info(f"  - 执行时间: {execution_time:.2f}秒")
            logger.info(f"  - 峰值内存使用: {after_memory[1] / (1024*1024):.2f} MB")
            logger.info(f"  - 内存使用增长: {memory_diff / (1024*1024):.2f} MB")
            
            # 如果执行时间过长，记录警告
            if execution_time > 5.0:  # 超过5秒视为较长
                logger.warning(f"函数 {func.__name__} 执行时间过长: {execution_time:.2f}秒")
            
            # 如果内存使用过大，记录警告
            if after_memory[1] / (1024*1024) > 100:  # 超过100MB视为较大
                logger.warning(f"函数 {func.__name__} 内存使用过大: {after_memory[1] / (1024*1024):.2f} MB")
    
    return wrapper

class DeviceGrouper:
    def __init__(self):
        # Initialize OpenAI client with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        self.max_retries = 3
        
        # For debugging purposes, log if we're using a placeholder key
        if api_key and api_key.startswith("sk-"):
            if len(api_key) < 10 or api_key == "sk-xxxx":
                logger.warning("Using placeholder OpenAI API key. AI-based grouping may not work correctly.")
        
        # Initialize cache
        self.enable_cache = True  # Can be set via environment variable
        if os.getenv("DISABLE_AI_CACHE", "").lower() in ("true", "1", "yes"):
            self.enable_cache = False
        
        # Cache timeout in seconds (default: 24 hours)
        self.cache_timeout = int(os.getenv("AI_CACHE_TIMEOUT", 86400))

    @performance_monitor
    def process(self, raw_points: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Execute semantic grouping of points using GPT-4o model"""
        try:
            if not raw_points:
                return {}
            
            # First check if we have a valid cache for these points
            if self.enable_cache:
                cache_key = self._generate_cache_key(raw_points)
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    logger.info("Using cached AI grouping result")
                    return cached_result
            
            # Try AI-based grouping with fewer retries to save costs
            max_ai_retries = int(os.getenv("MAX_AI_RETRIES", "2"))  # Reduced from 5 to 2
            last_error = None
            
            for retry in range(max_ai_retries):
                try:
                    logger.info(f"Attempt {retry+1}/{max_ai_retries} for AI-based grouping")
                    ai_result = self._group_with_ai(raw_points)
                    
                    # Validate result structure
                    if not isinstance(ai_result, dict):
                        raise ValueError(f"AI result is not a dictionary: {type(ai_result)}")
                    
                    # Validate and fix each group
                    fixed_result = {}
                    for device_type, devices in ai_result.items():
                        if not isinstance(devices, dict):
                            logger.warning(f"Fixing invalid device group structure for {device_type}")
                            if isinstance(devices, list):
                                fixed_result[device_type] = {"Unknown": devices}
                            else:
                                continue
                        else:
                            valid_devices = {}
                            for instance, points_list in devices.items():
                                if isinstance(points_list, list):
                                    valid_devices[instance] = points_list
                                else:
                                    logger.warning(f"Skipping invalid points list for {device_type} {instance}")
                            
                            if valid_devices:
                                fixed_result[device_type] = valid_devices
                    
                    logger.info(f"AI-based grouping successful on attempt {retry+1}")
                    
                    # Cache the successful result
                    if self.enable_cache and fixed_result:
                        self._save_to_cache(cache_key, fixed_result)
                    
                    return fixed_result
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    logger.warning(f"AI-based grouping attempt {retry+1} failed: {str(e)}")
                    
                    # Don't retry on certain error types - save API costs
                    if "rate limit" in error_str or "billing" in error_str or "quota" in error_str:
                        logger.error(f"API limit exceeded. Skipping further attempts: {str(e)}")
                        break
                    
                    # Check if we have a type error that would make retrying pointless
                    if "object has no attribute" in error_str or "type" in error_str:
                        logger.error(f"Type error detected. Skipping further attempts: {str(e)}")
                        break
                    
                    if retry < max_ai_retries - 1:
                        # Add exponential backoff with jitter
                        backoff_time = 2 ** retry + (0.1 * random.random())
                        logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        logger.error(f"All AI-based grouping attempts failed. Last error: {str(e)}")
            
            # Only use fallback if all AI attempts failed
            logger.info("Falling back to traditional grouping method")
            return self._fallback_grouping(raw_points)
            
        except Exception as e:
            logger.error(f"Error in process method: {str(e)}")
            raise ValueError(f"Error processing points: {str(e)}")
    
    def _generate_cache_key(self, points: List[str]) -> str:
        """Generate a unique cache key for a list of points"""
        # Sort to ensure same points in different order produce the same key
        sorted_points = sorted(points)
        # Create a string representation and hash it
        point_str = json.dumps(sorted_points)
        return hashlib.md5(point_str.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Dict[str, Dict[str, List[str]]] or None:
        """Retrieve grouping results from cache if available and not expired"""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if cache is expired
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.cache_timeout:
            logger.info(f"Cache expired (age: {file_age:.1f}s, timeout: {self.cache_timeout}s)")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_result = json.load(f)
                
                # 验证缓存结果的格式，检查是否是预期的嵌套字典结构
                if not isinstance(cached_result, dict):
                    logger.error(f"缓存结果格式错误: 预期是字典，实际类型 {type(cached_result).__name__}")
                    return None
                
                # 修复可能的数据结构问题
                fixed_result = {}
                for device_type, devices in cached_result.items():
                    # 处理"Other"特殊情况 - 有时它可能是列表而不是字典
                    if device_type == "Other" and isinstance(devices, list):
                        logger.warning(f"修复 'Other' 类别 - 从列表转换为字典结构")
                        # 将列表转换为字典结构
                        fixed_result[device_type] = {"Unknown": devices}
                        continue
                    
                    # 常规验证 - 设备应该是字典
                    if not isinstance(devices, dict):
                        logger.error(f"缓存结果中的设备组格式错误: 设备类型 {device_type} 的值不是字典而是 {type(devices).__name__}")
                        
                        # 尝试转换 - 如果是列表，将其转换为字典
                        if isinstance(devices, list) and len(devices) > 0:
                            logger.warning(f"尝试将设备类型 {device_type} 的列表转换为字典")
                            fixed_result[device_type] = {"Unknown": devices}
                            continue
                        else:
                            # 无法修复，跳过这个设备类型
                            continue
                    
                    # 设备值格式正确，添加到修复后的结果
                    fixed_result[device_type] = {}
                    
                    for device_id, points in devices.items():
                        # 验证points是否是列表类型
                        if not isinstance(points, list):
                            logger.error(f"缓存结果中的点位列表格式错误: 设备 {device_id} 的点位不是列表而是 {type(points).__name__}")
                            # 尝试修复：如果值是单个字符串或其他类型，转换为列表
                            if isinstance(points, str):
                                fixed_result[device_type][device_id] = [points]
                                logger.warning(f"已自动修复 {device_id} 的点位格式: 将字符串转换为列表")
                            elif points is None:
                                # 如果为None，创建空列表
                                fixed_result[device_type][device_id] = []
                                logger.warning(f"已自动修复 {device_id} 的点位格式: 将None转换为空列表")
                            elif isinstance(points, dict):
                                # 如果是字典，使用字典的值
                                try:
                                    values_list = list(points.values())
                                    fixed_result[device_type][device_id] = values_list
                                    logger.warning(f"已自动修复 {device_id} 的点位格式: 将字典值转换为列表")
                                except:
                                    # 无法转换，跳过
                                    logger.error(f"无法修复 {device_id} 的点位格式，跳过此设备")
                                    continue
                            else:
                                # 其他类型，尝试转换为列表
                                try:
                                    fixed_result[device_type][device_id] = list(points)
                                    logger.warning(f"已尝试将 {device_id} 的点位转换为列表")
                                except:
                                    # 无法转换，跳过此设备
                                    logger.error(f"无法将 {device_id} 的点位转换为列表，跳过此设备")
                                    continue
                        else:
                            # 点位格式正确，直接添加
                            fixed_result[device_type][device_id] = points
                
                # 如果所有设备类型都被筛掉了，返回None表示缓存无效
                if not fixed_result:
                    logger.error("所有设备组都格式错误，缓存无效")
                    return None
                
                logger.info("成功从缓存加载并验证了分组结果")
                return fixed_result
        except Exception as e:
            logger.warning(f"Error reading cache: {str(e)}")
            return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Dict[str, List[str]]]) -> None:
        """Save grouping results to cache in JSON format"""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved AI grouping result to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")

    @performance_monitor    
    def _save_api_response(self, response_data: dict, api_type: str = "openai_grouping") -> None:
        """Save API response data as JSON for analysis and debugging"""
        # Create timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a random suffix to avoid collisions
        suffix = ''.join(random.choices('0123456789abcdef', k=6))
        # Create filename
        filename = f"{api_type}_response_{timestamp}_{suffix}.json"
        response_file = API_RESPONSES_DIR / filename
        
        try:
            # Save to the original location
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved mapping API response to: {response_file}")
            
            # Also save to the new location using the save_openai_response function
            try:
                # Import the save_openai_response function
                from tools.save_openai_responses import save_openai_response
                
                # Save the response using the new function
                saved_path = save_openai_response(
                    response_data=response_data,
                    response_type=api_type
                )
                
                if saved_path:
                    logger.info(f"Also saved OpenAI response to: {saved_path}")
            except ImportError:
                logger.warning("Could not import save_openai_response function. Saving only to original location.")
            except Exception as e:
                logger.warning(f"Error saving to additional location: {str(e)}")
                
        except Exception as e:
            logger.warning(f"Error saving API response: {str(e)}")

    @performance_monitor
    def _group_with_ai(self, raw_points: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Group points using the OpenAI API."""
        try:
            # Enhanced prompt with better guidance for device type identification
            prompt = self._create_enhanced_grouping_prompt(raw_points)
            
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,  # Low temperature for consistent results
                messages=[
                    {"role": "system", "content": "You are an expert HVAC engineer who specializes in building management systems and point naming conventions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract and save relevant parts of the response for saving
            response_data = {
                "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                "model": getattr(response, "model", self.model),
                "content": getattr(response.choices[0].message, "content", "No content"),
                "usage": {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0)
                }
            }
            
            # Save API response for debugging
            self._save_api_response(response_data, api_type="openai_grouping")
            
            # Parse the response
            try:
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Validate structure
                if not isinstance(result, dict):
                    raise ValueError("API response is not a valid dictionary")
                
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse API response as JSON")
                raise ValueError("Invalid JSON format in API response")
                
        except Exception as e:
            logger.error(f"Error in _group_with_ai: {str(e)}")
            raise

    def _create_enhanced_grouping_prompt(self, raw_points: List[str]) -> str:
        """
        Create an enhanced prompt for point grouping that handles measurement prefixes better.
        This improved version recognizes when a point name starts with a measurement device/method
        but actually refers to a different device type.
        """
        point_list = json.dumps(raw_points, indent=2)
        
        return f"""
You are an expert in HVAC systems and BMS point naming conventions. I need you to analyze and group these building management system points by both device type and device instance (ID).

IMPORTANT: Look beyond just the prefix of a point name. Many points start with measurement prefixes (DPM, VSD, etc.) 
but actually refer to specific equipment. For example:
- "DPM_CWP_2.kW" should be grouped as a Condenser Water Pump (CWP), not as "DPM"
- "VSD_AHU3_Speed" should be grouped as an Air Handling Unit (AHU), not as "VSD"
- "CT_4.TripStatus" should be grouped as a Cooling Tower (CT), not by its first letter only

Common device types in HVAC:
- AHU: Air Handling Unit
- VAV: Variable Air Volume box
- FCU: Fan Coil Unit 
- CWP: Chilled Water Pump
- CHWP: Chilled Water Pump
- CHPL: Chiller Plant
- CT: Cooling Tower
- CH: Chiller
- HWP: Hot Water Pump
- HW: Hot Water
- BLR: Boiler
- FAN: Fan
- ZONE: Zone/Room sensor
- PMT: Power Meter
- WST: Weather Station

POINT LIST:
{point_list}

Please group these points by:
1. Device Type (e.g., AHU, Chiller, Pump)
2. Device Instance (specific ID or unit number)

Format your response as a JSON object with the following structure:
{{
  "DEVICE TYPE 1": {{
    "DEVICE ID 1": ["point1", "point2"],
    "DEVICE ID 2": ["point3", "point4"]
  }},
  "DEVICE TYPE 2": {{
    "DEVICE ID 3": ["point5", "point6"]
  }}
}}

Use your expertise to identify the actual equipment being monitored, not just prefixes in the names.
"""

    def _fallback_grouping(self, raw_points: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Fallback method for grouping when AI fails."""
        result = {}
        
        # Enhanced pattern recognition for common HVAC device types
        device_patterns = {
            "AHU": [r'AHU', r'RTU'],
            "VAV": [r'VAV', r'VAVBOX'],
            "CHILLER": [r'CH[0-9]', r'CHILLER', r'^CH_'],
            "PUMP": [r'(?:^|\W)CWP', r'(?:^|\W)HWP', r'(?:^|\W)PUMP'],
            "FCU": [r'FCU', r'FANCOIL'],
            "COOLING_TOWER": [r'(?:^|\W)CT[0-9]', r'(?:^|\W)CT_', r'COOLINGTOWER', r'COOLING_TOWER'],
            "BOILER": [r'BLR', r'BOILER'],
            "FAN": [r'(?:^|\W)FAN[0-9]', r'(?:^|\W)FAN_'],
            "ZONE": [r'(?:^|\W)RM[0-9]', r'(?:^|\W)ROOM', r'(?:^|\W)ZONE'],
        }
        
        # Special case for handling measurement prefixes
        measurement_prefixes = {
            "DPM": ["CWP", "HWP", "PUMP", "CHILLER", "AHU", "CT", "FAN"],
            "VSD": ["CWP", "HWP", "PUMP", "AHU", "FAN"],
            "TMP": ["CWP", "HWP", "PUMP", "CHILLER", "AHU", "CT", "ZONE"],
            "PRS": ["CWP", "HWP", "PUMP", "CHILLER", "AHU", "CT"],
            "ALM": ["CWP", "HWP", "PUMP", "CHILLER", "AHU", "CT", "BOILER"],
            "KW": ["CWP", "HWP", "PUMP", "CHILLER", "AHU", "CT", "BOILER"],
        }
        
        for point in raw_points:
            # Clean up the point name for processing
            point_clean = point.replace('.', '_').strip()
            
            # Check if this point starts with a measurement prefix
            assigned = False
            for prefix, device_checks in measurement_prefixes.items():
                if point_clean.startswith(prefix):
                    # Extract the parts after the prefix
                    remaining = point_clean[len(prefix):].strip("_")
                    
                    # Check if any known device type appears after the measurement prefix
                    for device_type, patterns in device_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, remaining, re.IGNORECASE):
                                # Create device type entry if it doesn't exist
                                if device_type not in result:
                                    result[device_type] = {}
                                
                                # Extract device ID if possible, default to 'Unknown'
                                device_id = self._extract_device_id(remaining, device_type)
                                if device_id not in result[device_type]:
                                    result[device_type][device_id] = []
                                    
                                result[device_type][device_id].append(point)
                                assigned = True
                                break
                        if assigned:
                            break
                if assigned:
                    break
            
            # If not assigned through measurement prefix, use regular pattern matching
            if not assigned:
                for device_type, patterns in device_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, point_clean, re.IGNORECASE):
                            # Create device type entry if it doesn't exist
                            if device_type not in result:
                                result[device_type] = {}
                            
                            # Extract device ID if possible, default to 'Unknown'
                            device_id = self._extract_device_id(point_clean, device_type)
                            if device_id not in result[device_type]:
                                result[device_type][device_id] = []
                                
                            result[device_type][device_id].append(point)
                            assigned = True
                            break
                    if assigned:
                        break
            
            # If still not assigned, assign to 'Other'
            if not assigned:
                if 'Other' not in result:
                    result['Other'] = {'Unknown': []}
                result['Other']['Unknown'].append(point)
        
        return result

    def _extract_device_id(self, point_name: str, device_type: str) -> str:
        """
        Extract device ID from point name based on device type.
        
        Args:
            point_name: Point name to extract ID from
            device_type: Type of device
            
        Returns:
            Device ID
        """
        # Default extraction pattern
        id_pattern = r'(\d+)'
        
        # Device-specific extraction patterns
        if device_type == "AHU":
            match = re.search(r'AHU[_\s-]*(\d+)', point_name, re.IGNORECASE)
            return f"AHU_{match.group(1)}" if match else "Unknown"
        elif device_type == "VAV":
            match = re.search(r'VAV[_\s-]*(\d+)', point_name, re.IGNORECASE)
            return f"VAV_{match.group(1)}" if match else "Unknown"
        elif device_type == "CHILLER":
            match = re.search(r'CH[_\s-]*(\d+)', point_name, re.IGNORECASE)
            return f"CH_{match.group(1)}" if match else "Unknown" 
        elif device_type == "PUMP":
            # Handle different pump types (CWP, HWP, etc.)
            if "CWP" in point_name.upper():
                match = re.search(r'CWP[_\s-]*(\d+)', point_name, re.IGNORECASE)
                return f"CWP_{match.group(1)}" if match else "CWP_Unknown"
            elif "HWP" in point_name.upper():
                match = re.search(r'HWP[_\s-]*(\d+)', point_name, re.IGNORECASE)
                return f"HWP_{match.group(1)}" if match else "HWP_Unknown"
            else:
                match = re.search(r'PUMP[_\s-]*(\d+)', point_name, re.IGNORECASE)
                return f"PUMP_{match.group(1)}" if match else "PUMP_Unknown"
        elif device_type == "COOLING_TOWER":
            match = re.search(r'CT[_\s-]*(\d+)', point_name, re.IGNORECASE)
            return f"CT_{match.group(1)}" if match else "Unknown"
        
        # Generic extraction for other device types
        match = re.search(id_pattern, point_name)
        return f"{device_type}_{match.group(1)}" if match else f"{device_type}_Unknown"
    
    def _apply_grouping_to_all_points(self, all_points: List[str], existing_groups: Dict) -> Dict:
        """Apply the discovered grouping patterns to all points, including those not in the initial batch"""
        # Extract the first 100 points that were already processed
        processed_points = all_points[:100]
        remaining_points = all_points[100:]
        
        # Create a copy of the existing groups
        result = {}
        # 确保输出结构的一致性
        result["Other"] = {"Unknown": []}
        
        # 验证输入结构
        if not isinstance(existing_groups, dict):
            logger.error(f"_apply_grouping_to_all_points: 输入的分组不是字典类型，而是 {type(existing_groups).__name__}")
            # 如果输入结构无效，直接使用传统分组
            return self._fallback_grouping(all_points)
            
        for device_type, devices in existing_groups.items():
            # 确保设备值是字典类型
            if not isinstance(devices, dict):
                logger.warning(f"设备组 {device_type} 不是字典类型，而是 {type(devices).__name__}，正在修复")
                if isinstance(devices, list):
                    # 如果是列表，转换为字典
                    result[device_type] = {"Unknown": devices}
                    continue
                else:
                    # 如果不是字典也不是列表，创建空字典
                    result[device_type] = {}
                    continue
            
            # 复制设备值
            result[device_type] = {}
            for device_id, points in devices.items():
                # 确保点位是列表类型
                if not isinstance(points, list):
                    logger.warning(f"设备 {device_id} 的点位不是列表类型，而是 {type(points).__name__}，正在修复")
                    if isinstance(points, str):
                        # 如果是字符串，转换为列表
                        result[device_type][device_id] = [points]
                    else:
                        try:
                            # 尝试转换为列表
                            result[device_type][device_id] = list(points)
                        except:
                            # 无法转换，创建空列表
                            result[device_type][device_id] = []
                else:
                    # 正常复制
                    result[device_type][device_id] = points.copy()
        
        # Try to match remaining points to the existing patterns
        for point in remaining_points:
            matched = False
            
            # Look for exact device IDs in the point name
            for device_type, devices in existing_groups.items():
                # 确保设备值是字典类型
                if not isinstance(devices, dict):
                    continue
                    
                for device_id in devices.keys():
                    # If the device ID is found in the point name, add it to that group
                    if device_id in point:
                        if device_id not in result[device_type]:
                            result[device_type][device_id] = []
                        result[device_type][device_id].append(point)
                        matched = True
                        break
                
                if matched:
                    break
            
            # If not matched by device ID, try to match by device type keywords
            if not matched:
                point_upper = point.upper()
                for device_type in existing_groups.keys():
                    # 跳过非字典类型的设备值
                    if not isinstance(existing_groups[device_type], dict):
                        continue
                        
                    device_type_upper = device_type.upper()
                    
                    # Check if the device type is in the point name
                    if device_type_upper in point_upper:
                        # Extract a device identifier
                        parts = point.split('_')
                        device_id = next((part for part in parts if device_type_upper in part.upper()), parts[0])
                        
                        if device_id not in result[device_type]:
                            result[device_type][device_id] = []
                        
                        result[device_type][device_id].append(point)
                        matched = True
                        break
            
            # If still not matched, place in the most relevant device type or "Other"
            if not matched:
                # Check for common device type indicators
                device_indicators = {
                    'AHU': ['AHU', 'MAT', 'SAT', 'RAT'],
                    'FCU': ['FCU', 'FAN COIL'],
                    'CH': ['CH', 'CHILLER', 'CHPL'],
                    'CT': ['CT', 'COOLING TOWER'],
                    'PUMP': ['PUMP', 'CWP', 'CHWP', 'HWP'],
                    'METER': ['METER', 'DPM', 'ENERGY'],
                    'VAV': ['VAV', 'TERMINAL']
                }
                
                for device_type, indicators in device_indicators.items():
                    if any(ind in point_upper for ind in indicators):
                        if device_type not in result:
                            result[device_type] = {}
                        
                        # Create a new device instance
                        device_id = point.split('.')[0] if '.' in point else point
                        
                        if device_id not in result[device_type]:
                            result[device_type][device_id] = []
                        
                        result[device_type][device_id].append(point)
                        matched = True
                        break
                
                # If still no match, place in "Other"
                if not matched:
                    if "Other" not in result:
                        result["Other"] = {}
                    
                    # Use the first segment as the device ID
                    device_id = point.split('.')[0] if '.' in point else point
                    
                    if device_id not in result["Other"]:
                        result["Other"][device_id] = []
                    
                    result["Other"][device_id].append(point)
        
        # 最终验证输出结构
        for device_type in list(result.keys()):
            if not isinstance(result[device_type], dict):
                logger.warning(f"修复输出结构的设备类型 {device_type} 的值为字典")
                result[device_type] = {"Unknown": []} if not isinstance(result[device_type], list) else {"Unknown": result[device_type]}
            
            for device_id in list(result[device_type].keys()):
                if not isinstance(result[device_type][device_id], list):
                    logger.warning(f"修复输出结构的设备 {device_id} 的点位列表")
                    result[device_type][device_id] = [result[device_type][device_id]] if isinstance(result[device_type][device_id], str) else []
        
        return result

    def _ontology_grouping(self, points: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """
        Group points using industry standard ontologies like Brick Schema or Project Haystack
        
        This implementation uses a simplified ontology approach with more structured rules than
        the basic fallback grouping, but without requiring a full ontology engine.
        """
        logger.info("Starting ontology-based grouping")
        
        # Define ontology rules for different equipment types
        # Each rule has patterns to identify the equipment and specific point types
        ontology_rules = {
            'AHU': {
                'patterns': ['AHU', 'AIR HANDLING UNIT'],
                'point_types': {
                    'Temperature': ['SAT', 'RAT', 'MAT', 'SUPPLY AIR TEMP', 'RETURN AIR TEMP', 'MIXED AIR TEMP'],
                    'Pressure': ['SUPPLY PRESSURE', 'STATIC PRESSURE', 'SP'],
                    'Damper': ['DAMPER', 'OAD', 'OUTSIDE AIR DAMPER', 'RETURN DAMPER', 'RELIEF DAMPER'],
                    'Fan': ['FAN', 'SUPPLY FAN', 'RETURN FAN', 'SF', 'RF'],
                    'Valve': ['VALVE', 'COOLING VALVE', 'HEATING VALVE'],
                    'Status': ['STATUS', 'ALARM', 'FAULT'],
                    'Speed': ['SPEED', 'VFD', 'FREQUENCY']
                }
            },
            'VAV': {
                'patterns': ['VAV', 'VARIABLE AIR VOLUME', 'TERMINAL'],
                'point_types': {
                    'Temperature': ['SAT', 'RAT', 'DAT', 'SPACE TEMP', 'ZONE TEMP', 'DISCHARGE TEMP'],
                    'Flow': ['FLOW', 'AIR FLOW', 'CFM'],
                    'Setpoint': ['SETPOINT', 'SP', 'COOLING SP', 'HEATING SP'],
                    'Damper': ['DAMPER', 'DAMPER POS'],
                    'Valve': ['VALVE', 'REHEAT VALVE'],
                    'Occupancy': ['OCC', 'OCCUPANCY', 'OCCUPIED']
                }
            },
            'Chiller': {
                'patterns': ['CHILLER', 'CH', 'CHPL'],
                'point_types': {
                    'Temperature': ['CHWS', 'CHWR', 'SUPPLY TEMP', 'RETURN TEMP'],
                    'Pressure': ['PRESSURE', 'HEAD PRESSURE', 'SUCTION PRESSURE'],
                    'Flow': ['FLOW', 'WATER FLOW'],
                    'Power': ['POWER', 'KW', 'LOAD'],
                    'Current': ['CURRENT', 'AMPS'],
                    'Status': ['STATUS', 'ALARM', 'FAULT', 'RUN STATUS']
                }
            },
            'Pump': {
                'patterns': ['PUMP', 'CWP', 'CHWP', 'HWP'],
                'point_types': {
                    'Status': ['STATUS', 'ON/OFF', 'ENABLE'],
                    'Speed': ['SPEED', 'VFD', 'FREQUENCY'],
                    'Pressure': ['PRESSURE', 'DIFF PRESSURE', 'DISCHARGE PRESSURE'],
                    'Flow': ['FLOW'],
                    'Power': ['POWER', 'KW'],
                    'Current': ['CURRENT', 'AMPS']
                }
            },
            'Boiler': {
                'patterns': ['BOILER', 'BOIL'],
                'point_types': {
                    'Temperature': ['HWS', 'HWR', 'SUPPLY TEMP', 'RETURN TEMP'],
                    'Pressure': ['PRESSURE', 'STEAM PRESSURE'],
                    'Status': ['STATUS', 'ENABLE', 'ALARM'],
                    'Flow': ['FLOW', 'WATER FLOW'],
                    'Setpoint': ['SETPOINT', 'SP']
                }
            },
            'Room': {
                'patterns': ['ROOM', 'RM', 'ZONE', 'SPACE'],
                'point_types': {
                    'Temperature': ['TEMP', 'TEMPERATURE', 'SPACE TEMP', 'ZONE TEMP'],
                    'Humidity': ['HUMIDITY', 'RH', 'RELATIVE HUMIDITY'],
                    'CO2': ['CO2', 'CARBON DIOXIDE'],
                    'Occupancy': ['OCC', 'OCCUPANCY', 'MOTION'],
                    'Setpoint': ['SETPOINT', 'SP', 'COOLING SP', 'HEATING SP']
                }
            },
            'Meter': {
                'patterns': ['METER', 'DPM', 'ENERGY METER'],
                'point_types': {
                    'Power': ['POWER', 'KW', 'DEMAND'],
                    'Energy': ['ENERGY', 'KWH', 'CONSUMPTION'],
                    'Voltage': ['VOLTAGE', 'VOLTS'],
                    'Current': ['CURRENT', 'AMPS'],
                    'Flow': ['FLOW', 'WATER FLOW', 'GAS FLOW']
                }
            }
        }
        
        # Initialize result dictionary
        result = {}
        
        # First pass: identify equipment types and instances
        for point in points:
            point_upper = point.upper()
            matched_type = None
            
            # Try to match the point to an equipment type
            for equip_type, rule in ontology_rules.items():
                patterns = rule['patterns']
                if any(pat in point_upper for pat in patterns):
                    matched_type = equip_type
                    break
            
            # If no match was found, check against patterns dictionary
            if not matched_type:
                for key, patterns in {
                    'AHU': ['AHU', 'AIR HANDLING UNIT', 'MAT', 'SAT', 'RAT'],
                    'VAV': ['VAV', 'VARIABLE AIR VOLUME', 'TERMINAL'],
                    'CHILLER': ['CH', 'CHILLER', 'CHPL', 'CH-SYS'],
                    'PUMP': ['PUMP', 'CWP', 'CHWP', 'HWP', 'P-'],
                    'BOILER': ['BOILER', 'BOIL']
                }.items():
                    if any(pat in point_upper for pat in patterns):
                        matched_type = key
                        break
            
            # If still no match, use 'Other'
            if not matched_type:
                matched_type = 'Other'
            
            # Extract device ID using specialized method
            device_id = self._extract_device_id(point, matched_type)
            if not device_id:
                device_id = f"Unknown_{matched_type}"
            
            # Add to the result structure
            if matched_type not in result:
                result[matched_type] = {}
            
            if device_id not in result[matched_type]:
                result[matched_type][device_id] = []
            
            result[matched_type][device_id].append(point)
        
        # Enhanced rules for device ID extraction
        # Second pass: for each equipment type, apply specialized rules to refine grouping
        refined_result = {}
        
        for equip_type, devices in result.items():
            refined_result[equip_type] = {}
            
            for device_id, points_list in devices.items():
                # Special case for VAVs - they're often associated with room/zone numbers
                if equip_type == 'VAV' and len(points_list) > 1:
                    # Try to group by zone/room if applicable
                    zone_groups = self._group_by_zone(points_list)
                    if zone_groups:
                        for zone_id, zone_points in zone_groups.items():
                            refined_device_id = f"{device_id}_{zone_id}"
                            refined_result[equip_type][refined_device_id] = zone_points
                        continue
                
                # For other types, just copy the points
                refined_result[equip_type][device_id] = points_list
        
        return refined_result
    
    def _group_by_zone(self, points: List[str]) -> Dict[str, List[str]]:
        """Group points by zone/room ID if applicable"""
        # Common zone/room patterns
        zone_patterns = [
            r'ZONE[_\s]?(\d+)',
            r'RM[_\s]?(\d+)',
            r'ROOM[_\s]?(\d+)',
            r'SPACE[_\s]?(\d+)'
        ]
        
        # Try to extract zone IDs
        zones = {}
        
        for point in points:
            point_upper = point.upper()
            zone_id = None
            
            # Try to match each pattern
            for pattern in zone_patterns:
                match = re.search(pattern, point_upper)
                if match:
                    zone_id = match.group(1)
                    break
            
            # If no zone ID was found, use 'Unknown'
            if not zone_id:
                zone_id = 'Unknown'
            
            # Add to zones dictionary
            if zone_id not in zones:
                zones[zone_id] = []
            
            zones[zone_id].append(point)
        
        # If only one zone was found, don't bother with subgrouping
        if len(zones) <= 1:
            return {}
        
        return zones 