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
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
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

    def _save_api_response(self, response_data: dict, api_type: str = "openai") -> None:
        """Save API response data as JSON for analysis and debugging"""
        # Create timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a random suffix to avoid collisions
        suffix = ''.join(random.choices('0123456789abcdef', k=6))
        # Create filename
        filename = f"{api_type}_response_{timestamp}_{suffix}.json"
        response_file = API_RESPONSES_DIR / filename
        
        try:
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved API response to: {response_file}")
        except Exception as e:
            logger.warning(f"Error saving API response: {str(e)}")

    @performance_monitor
    def _group_with_ai(self, points: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Group points using AI-based analysis"""
        try:
            # Format points for AI processing
            points_text = "\n".join(points)
            
            # Create the prompt
            prompt = f"""Given these BMS point names, group them by device type and instance.
Return the result as a JSON object where:
- Top level keys are device types (e.g., "AHU", "FCU")
- Second level keys are device instances (e.g., "1", "2")
- Values are arrays of point names belonging to that device

Example format:
{{
    "AHU": {{
        "1": ["AHU1_SAT", "AHU1_RAT"],
        "2": ["AHU2_SAT", "AHU2_RAT"]
    }},
    "FCU": {{
        "1": ["FCU1_SAT", "FCU1_RAT"]
    }}
}}

Points to group:
{points_text}"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that groups BMS points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            # Parse the response
            try:
                result = json.loads(response.choices[0].message.content)
                
                # Validate the result structure
                if not isinstance(result, dict):
                    raise ValueError("AI response is not a dictionary")
                
                # Validate and fix each group
                fixed_result = {}
                for device_type, devices in result.items():
                    if not isinstance(devices, dict):
                        logger.warning(f"Fixing invalid device group structure for {device_type}")
                        if isinstance(devices, list):
                            # If it's a list, put all points under "Unknown" instance
                            fixed_result[device_type] = {"Unknown": devices}
                        else:
                            # Skip invalid entries
                            continue
                    else:
                        # Validate device instances
                        valid_devices = {}
                        for instance, points_list in devices.items():
                            if isinstance(points_list, list):
                                valid_devices[instance] = points_list
                            else:
                                logger.warning(f"Skipping invalid points list for {device_type} {instance}")
                        
                        if valid_devices:
                            fixed_result[device_type] = valid_devices
                
                return fixed_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {str(e)}")
                raise ValueError(f"Failed to parse AI response: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in AI grouping: {str(e)}")
            raise

    @performance_monitor
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

    def _fallback_grouping(self, points: List[str], use_ontology: bool = False) -> Dict[str, Dict[str, List[str]]]:
        """Improved fallback grouping in case AI-based grouping fails"""
        # More comprehensive patterns for common BMS device types
        patterns = {
            'AHU': ['AHU', 'AIR HANDLING UNIT', 'MAT', 'SAT', 'RAT'],
            'FCU': ['FCU', 'FAN COIL', 'FANCOIL'],
            'CH': ['CH', 'CHILLER', 'CHPL', 'CH-SYS'],
            'CHP': ['CHP', 'CHILLER PLANT'],
            'BOILER': ['BOILER', 'BOIL'],
            'PUMP': ['PUMP', 'CWP', 'CHWP', 'HWP', 'P-'],
            'CT': ['CT', 'COOLING TOWER'],
            'VAV': ['VAV', 'VARIABLE AIR VOLUME', 'TERMINAL'],
            'RTU': ['RTU', 'ROOF TOP UNIT'],
            'EF': ['EF', 'EXHAUST FAN'],
            'SF': ['SF', 'SUPPLY FAN'],
            'RF': ['RF', 'RETURN FAN'],
            'METER': ['METER', 'DPM', 'ENERGY METER'],
            'LIGHTING': ['LIGHTING', 'LIGHT', 'LT-'],
            'ROOM': ['ROOM', 'RM-', 'ZONE', 'SPACE'],
            'OTHER': ['OTHER', 'UNKNOWN']
        }
        
        # If ontology-based grouping is requested, use more structured rules
        if use_ontology:
            logger.info("Using ontology-based grouping rules")
            return self._ontology_grouping(points)
        
        # Initialize the result
        result = {}
        
        # 保证"Other"类别始终是字典格式
        result["OTHER"] = {}
        
        for point in points:
            # Convert to uppercase for pattern matching
            point_upper = point.upper()
            
            # Try to match the point to a device type
            matched_type = None
            for device_type, indicators in patterns.items():
                if any(ind in point_upper for ind in indicators):
                    matched_type = device_type
                    break
            
            # If no match was found, use 'OTHER'
            if not matched_type:
                matched_type = 'OTHER'
            
            # If this is the first point of this type, initialize the dictionary
            if matched_type not in result:
                result[matched_type] = {}
            
            # Try to extract a device ID
            device_id = self._extract_device_id(point, matched_type)
            
            # If we couldn't extract a device ID, use a generic one
            if not device_id:
                device_id = f"Unknown_{len(result[matched_type]) + 1}"
            
            # Add the device ID to the result if needed
            if device_id not in result[matched_type]:
                result[matched_type][device_id] = []
            
            # Add the point to the result
            result[matched_type][device_id].append(point)
        
        # 确保所有设备类型都有子字典，即使是空的
        for device_type in list(result.keys()):
            if not isinstance(result[device_type], dict):
                logger.warning(f"修复设备类型 {device_type} 的数据格式，将非字典值替换为字典")
                if isinstance(result[device_type], list):
                    # 如果是列表，将其转换为字典
                    result[device_type] = {"Unknown": result[device_type]}
                else:
                    # 如果不是列表，创建空字典
                    result[device_type] = {}
            
            # 确保每个设备ID下都是列表
            for device_id in list(result[device_type].keys()):
                if not isinstance(result[device_type][device_id], list):
                    logger.warning(f"修复设备 {device_id} 的点位格式，将非列表值替换为列表")
                    if isinstance(result[device_type][device_id], str):
                        result[device_type][device_id] = [result[device_type][device_id]]
                    else:
                        try:
                            result[device_type][device_id] = list(result[device_type][device_id])
                        except:
                            result[device_type][device_id] = []
        
        # 如果OTHER类别是空的，确保有一个默认子字典
        if not result["OTHER"]:
            result["OTHER"]["Unknown"] = []
        
        return result

    def _extract_device_id(self, point: str, device_type: str) -> str:
        """Extract a device ID from a point name based on common patterns"""
        # Convert to uppercase for consistent matching
        point_upper = point.upper()
        device_type_upper = device_type.upper()
        
        # Common regex patterns for device IDs
        patterns = [
            # Pattern for AHU-1, FCU-2, etc.
            rf'{device_type_upper}[_\s-]?(\d+)',
            # Pattern for AHU.1.SAT, etc.
            rf'{device_type_upper}\.(\d+)',
            # Pattern for values after underscore with the device type
            rf'{device_type_upper}[_\s]([A-Z0-9]+)[_\s]',
            # Pattern for numbers at the beginning
            r'^(\d+)[_\s]',
            # Pattern for generic ID extraction
            r'([A-Z0-9]+\d+)[\._\s]'
        ]
        
        # Try to match each pattern
        for pattern in patterns:
            match = re.search(pattern, point_upper)
            if match:
                return match.group(1)
        
        # If no match was found, try to extract a value with digits
        words = re.findall(r'[A-Z]+\d+', point_upper)
        if words:
            for word in words:
                if device_type_upper in word:
                    return word
            # Return the first word with digits
            return words[0]
        
        # If still no match, split by common separators and return the first part
        for sep in ['_', '.', '-', ' ']:
            if sep in point:
                return point.split(sep)[0]
        
        # Last resort: return the point name itself
        return point

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