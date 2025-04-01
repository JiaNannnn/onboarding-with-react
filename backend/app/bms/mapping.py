import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import time
from openai import OpenAI
import random
import datetime
import hashlib
import sys
from functools import lru_cache
from ..bms.grouping import performance_monitor

logger = logging.getLogger(__name__)

# 使用与grouping.py相同的API响应存储目录
API_RESPONSES_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'api_responses'))
API_RESPONSES_DIR.mkdir(exist_ok=True, parents=True)

# 创建缓存目录
CACHE_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'mapper'))
CACHE_DIR.mkdir(exist_ok=True, parents=True)

class EnOSMapper:
    def __init__(self):
        # Initialize OpenAI client with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.enos_schema = self._load_enos_schema()
        self.max_retries = 5  # Increased from 3 to 5
        self.confidence_threshold = 0.4  # Lowered threshold to accept more mappings
        
        # 内存缓存大小配置
        self.cache_size = int(os.getenv("ENOS_MAPPER_CACHE_SIZE", "1000"))
        self.mem_cache = {}  # Simple in-memory cache for API responses
        
        # 文件缓存配置
        self.enable_file_cache = True
        if os.getenv("DISABLE_MAPPING_CACHE", "").lower() in ("true", "1", "yes"):
            self.enable_file_cache = False
        
        # 缓存超时时间（默认：7天）
        self.cache_timeout = int(os.getenv("MAPPING_CACHE_TIMEOUT", 604800))
        
        # 统计信息
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        
        # For debugging purposes, log if we're using a placeholder key
        if api_key and api_key.startswith("sk-"):
            if len(api_key) < 10 or api_key == "sk-xxxx":
                logger.warning("Using placeholder OpenAI API key. AI-based mapping may not work correctly.")
    
    @performance_monitor    
    def _save_api_response(self, response_data: dict, api_type: str = "openai_mapping") -> None:
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
            logger.info(f"Saved mapping API response to: {response_file}")
        except Exception as e:
            logger.warning(f"Error saving API response: {str(e)}")
    
    def _load_enos_schema(self) -> Dict:
        """Load the EnOS schema to provide as context to the AI model"""
        try:
            # Try multiple possible locations for the schema
            possible_paths = [
                Path(__file__).parent / 'enos.json',
                Path(__file__).parent.parent.parent / 'enos.json',
                # Add absolute path as another option
                Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'enos.json'))
            ]
            
            # Log all paths being checked
            for path in possible_paths:
                logger.info(f"Checking for EnOS schema at: {path} (exists: {path.exists()})")
            
            for schema_path in possible_paths:
                if schema_path.exists():
                    try:
                        with open(schema_path, 'r', encoding='utf-8') as f:
                            schema = json.load(f)
                            logger.info(f"Successfully loaded EnOS schema with {len(schema)} device types from {schema_path}")
                            return schema
                    except Exception as e:
                        logger.error(f"Error loading schema from {schema_path}: {str(e)}")
            
            # If not found in relative paths, try absolute path as a last resort
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            absolute_path = os.path.join(base_dir, 'enos.json')
            logger.info(f"Trying absolute path: {absolute_path}")
            
            if os.path.exists(absolute_path):
                try:
                    with open(absolute_path, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                        logger.info(f"Successfully loaded EnOS schema with {len(schema)} device types from {absolute_path}")
                        return schema
                except Exception as e:
                    logger.error(f"Error loading schema from absolute path: {str(e)}")
            
            logger.error("Could not find enos.json in any expected location")
            return {}
        except Exception as e:
            logger.error(f"Failed to load EnOS schema: {str(e)}")
            return {}
    
    def _generate_cache_key(self, point: str, device_type: str) -> str:
        """生成用于缓存的唯一键"""
        # 创建字符串并哈希它
        key_str = f"{point}|{device_type}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """从内存或文件缓存中获取映射结果"""
        # 首先检查内存缓存
        if cache_key in self.mem_cache:
            self.cache_hits += 1
            logger.debug(f"内存缓存命中: {cache_key}")
            return self.mem_cache[cache_key]
        
        # 然后检查文件缓存
        if self.enable_file_cache:
            cache_file = CACHE_DIR / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
            
            # 检查缓存是否过期
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.cache_timeout:
                logger.debug(f"缓存已过期 (age: {file_age:.1f}s, timeout: {self.cache_timeout}s)")
                return None
            
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    result = cache_data.get("enos_path")
                    
                    # 添加到内存缓存
                    self._update_mem_cache(cache_key, result)
                    
                    self.cache_hits += 1
                    logger.debug(f"文件缓存命中: {cache_key}")
                    return result
            except Exception as e:
                logger.warning(f"读取缓存出错: {str(e)}")
        
        self.cache_misses += 1
        return None
    
    def _save_to_cache(self, cache_key: str, enos_path: str, point: str, device_type: str) -> None:
        """保存映射结果到内存和文件缓存"""
        # 保存到内存缓存
        self._update_mem_cache(cache_key, enos_path)
        
        # 保存到文件缓存
        if self.enable_file_cache:
            cache_file = CACHE_DIR / f"{cache_key}.json"
            
            try:
                # 保存更多的元数据，便于调试
                cache_data = {
                    "enos_path": enos_path,
                    "point": point,
                    "device_type": device_type,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "model": self.model
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"保存到文件缓存: {cache_file}")
            except Exception as e:
                logger.warning(f"保存缓存出错: {str(e)}")
    
    def _update_mem_cache(self, key: str, value: str) -> None:
        """更新内存缓存，保持大小限制"""
        # 如果缓存已满，移除最早的项
        if len(self.mem_cache) >= self.cache_size:
            # 简单的策略：移除第一个项
            self.mem_cache.pop(next(iter(self.mem_cache)), None)
        
        # 添加新项
        self.mem_cache[key] = value
    
    @performance_monitor
    def map_point(self, raw_point: str, device_type: str) -> Optional[str]:
        """Map a raw point to EnOS schema using semantic understanding"""
        if not raw_point or not device_type:
            return None
        
        # 生成缓存键
        cache_key = self._generate_cache_key(raw_point, device_type)
        
        # 检查缓存
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"缓存命中 for {raw_point}")
            return cached_result
        
        # Normalize device type to match expected EnOS schema keys
        device_type = self._normalize_device_type(device_type)
            
        # Try AI-based mapping with retries and better logging
        for retry in range(self.max_retries):
            try:
                logger.info(f"尝试 {retry+1}/{self.max_retries} 用AI映射点位 {raw_point}")
                self.api_calls += 1
                result = self._map_with_ai(raw_point, device_type)
                if result:
                    # 保存到缓存
                    self._save_to_cache(cache_key, result, raw_point, device_type)
                    return result
                # If AI mapping returned None but didn't raise an exception,
                # no need to retry - proceed to fallback
                break
            except Exception as e:
                logger.warning(f"AI映射尝试 {retry+1} 失败, 点位 {raw_point}: {str(e)}")
                if retry < self.max_retries - 1:
                    # Add exponential backoff with jitter
                    backoff_time = min(30, 2 ** retry + (0.1 * random.random()))
                    logger.info(f"等待 {backoff_time:.2f} 秒后重试...")
                    time.sleep(backoff_time)
                    continue
        
        # Fall back to traditional mapping if AI fails
        logger.info(f"使用传统映射方法 for {raw_point}")
        fallback_result = self._fallback_mapping(raw_point, device_type)
        if fallback_result:
            # 也缓存传统映射的结果
            self._save_to_cache(cache_key, fallback_result, raw_point, device_type)
        return fallback_result
    
    def get_cache_stats(self) -> Dict:
        """返回缓存统计信息"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / max(total_requests, 1) * 100
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": hit_rate,
            "api_calls": self.api_calls,
            "mem_cache_size": len(self.mem_cache),
            "mem_cache_limit": self.cache_size
        }
    
    def _normalize_device_type(self, device_type: str) -> str:
        """Normalize device type to match expected EnOS schema keys"""
        # Map of common abbreviations to their schema names
        type_mapping = {
            'FCU': 'FCU',
            'AHU': 'AHU',
            'VAV': 'VAV',
            'CHILLER': 'CHILLER',
            'CH': 'CHILLER',
            'CHPL': 'CHILLER',
            'BOILER': 'BOILER',
            'BOIL': 'BOILER',
            'CWP': 'PUMP',
            'CHWP': 'PUMP',
            'HWP': 'PUMP',
            'PUMP': 'PUMP',
            'CT': 'COOLING_TOWER',
            'RTU': 'RTU',
            'METER': 'METER',
            'DPM': 'METER',
            'EF': 'EXHAUST_FAN',
            'UNKNOWN': 'OTHER'
        }
        
        # Try to match the device type to a known key
        device_type_upper = device_type.upper()
        for key, value in type_mapping.items():
            if key in device_type_upper:
                return value
        
        # If no match, return the original device type
        return device_type
    
    @performance_monitor
    def _map_with_ai(self, raw_point: str, device_type: str) -> Optional[str]:
        """Use rule-based mapping instead of GPT-4o to map a BMS point to EnOS schema"""
        try:
            logger.info(f"Using rule-based mapping for {raw_point} (device_type: {device_type})")
            
            # Make sure we have a valid device type
            if not device_type or device_type not in self.enos_schema:
                logger.warning(f"Invalid device type: {device_type}")
                device_type = self._infer_device_type(raw_point)
                logger.info(f"Inferred device type: {device_type}")
            
            # If we still don't have a valid device type, try a generic one
            if not device_type or device_type not in self.enos_schema:
                logger.warning(f"Could not determine valid device type for {raw_point}")
                # Use a common device type as fallback
                device_type = "AHU"
            
            # Get available points for this device type
            available_points = []
            if device_type in self.enos_schema and 'points' in self.enos_schema[device_type]:
                available_points = list(self.enos_schema[device_type]['points'].keys())
            
            logger.info(f"Available points for {device_type}: {len(available_points)}")
            
            # Simple rule-based mapping logic
            point_lowercase = raw_point.lower()
            point_mapping = None
            
            # Try to match based on patterns
            if "temp" in point_lowercase or "tmp" in point_lowercase or "temperature" in point_lowercase:
                if "supply" in point_lowercase or "sa" in point_lowercase or "sat" in point_lowercase:
                    point_mapping = "supplyTemperature"
                elif "return" in point_lowercase or "ra" in point_lowercase or "rat" in point_lowercase:
                    point_mapping = "returnTemperature"
                elif "zone" in point_lowercase or "room" in point_lowercase or "space" in point_lowercase:
                    point_mapping = "zoneTemperature"
                elif "outdoor" in point_lowercase or "oat" in point_lowercase or "outside" in point_lowercase:
                    point_mapping = "outdoorTemperature"
                else:
                    point_mapping = "temperature"
            
            elif "hum" in point_lowercase or "humidity" in point_lowercase or "rh" in point_lowercase:
                if "zone" in point_lowercase or "room" in point_lowercase:
                    point_mapping = "zoneHumidity"
                elif "supply" in point_lowercase or "sa" in point_lowercase:
                    point_mapping = "supplyHumidity"
                elif "return" in point_lowercase or "ra" in point_lowercase:
                    point_mapping = "returnHumidity"
                else:
                    point_mapping = "humidity"
            
            elif "pres" in point_lowercase or "pressure" in point_lowercase:
                if "supply" in point_lowercase or "sa" in point_lowercase or "discharge" in point_lowercase:
                    point_mapping = "supplyPressure"
                elif "return" in point_lowercase or "ra" in point_lowercase:
                    point_mapping = "returnPressure"
                else:
                    point_mapping = "pressure"
            
            elif "flow" in point_lowercase or "cfm" in point_lowercase:
                if "supply" in point_lowercase or "sa" in point_lowercase:
                    point_mapping = "supplyAirflow"
                elif "return" in point_lowercase or "ra" in point_lowercase:
                    point_mapping = "returnAirflow"
                else:
                    point_mapping = "airflow"
            
            elif "damper" in point_lowercase or "valve" in point_lowercase:
                if "position" in point_lowercase or "pos" in point_lowercase:
                    if "cool" in point_lowercase or "chw" in point_lowercase:
                        point_mapping = "coolingValvePosition"
                    elif "heat" in point_lowercase or "hw" in point_lowercase:
                        point_mapping = "heatingValvePosition"
                    else:
                        point_mapping = "valvePosition"
                else:
                    point_mapping = "damperPosition"
            
            elif "setpoint" in point_lowercase or "sp" in point_lowercase or "set point" in point_lowercase:
                if "temp" in point_lowercase or "temperature" in point_lowercase:
                    point_mapping = "temperatureSetpoint"
                elif "pressure" in point_lowercase or "pres" in point_lowercase:
                    point_mapping = "pressureSetpoint"
                elif "humidity" in point_lowercase or "hum" in point_lowercase or "rh" in point_lowercase:
                    point_mapping = "humiditySetpoint"
                else:
                    point_mapping = "setpoint"
            
            elif "status" in point_lowercase or "state" in point_lowercase:
                if "fan" in point_lowercase:
                    point_mapping = "fanStatus"
                elif "pump" in point_lowercase:
                    point_mapping = "pumpStatus"
                elif "alarm" in point_lowercase or "fault" in point_lowercase:
                    point_mapping = "alarmStatus"
                else:
                    point_mapping = "status"
            
            elif "speed" in point_lowercase or "freq" in point_lowercase or "frequency" in point_lowercase:
                if "fan" in point_lowercase:
                    point_mapping = "fanSpeed"
                elif "pump" in point_lowercase:
                    point_mapping = "pumpSpeed"
                else:
                    point_mapping = "speed"
            
            elif "mode" in point_lowercase:
                point_mapping = "operationMode"
            
            # Look for direct matches in the available points
            for enos_point in available_points:
                if point_mapping and enos_point.lower().endswith(point_mapping.lower()):
                    logger.info(f"Direct mapping found for {raw_point} to {enos_point}")
                    return enos_point
            
            # If no direct mapping, try closest match with available points
            if point_mapping:
                # Try to find point in available points with closest name
                closest_match = None
                min_distance = float('inf')
                
                for ap in available_points:
                    # Prioritize points that contain the mapping term
                    if point_mapping.lower() in ap.lower():
                        distance = self._levenshtein_distance(point_mapping.lower(), ap.lower())
                        if distance < min_distance:
                            min_distance = distance
                            closest_match = ap
                
                # Use closest match if it's reasonably close
                if closest_match:
                    logger.info(f"Mapped {raw_point} to {closest_match} (closest match to {point_mapping})")
                    return closest_match
            
            # If semantic mapping fails, try direct point name mapping
            for ap in available_points:
                # Check if any part of the raw point name is in the available point
                if any(part in ap.lower() for part in point_lowercase.split('.')):
                    logger.info(f"Direct name match for {raw_point} to {ap}")
                    return ap
            
            # If still no match, use a generic point based on device type
            default_points = {
                "AHU": "AHU_raw_supply_air_temp",
                "FCU": "FCU_raw_zone_air_temp",
                "VAV": "VAV_raw_airflow",
                "CHILLER": "CH_raw_temp_chws",
                "PUMP": "PUMP_raw_status"
            }
            
            default_point = default_points.get(device_type)
            if default_point and default_point in available_points:
                logger.info(f"Using default mapping for {raw_point}: {default_point}")
                return default_point
            
            # Last resort: use the first available point
            if available_points:
                first_point = available_points[0]
                logger.info(f"Using first available point for {raw_point}: {first_point}")
                return first_point
            
            # If we get here, we couldn't map the point
            logger.warning(f"Could not map {raw_point} to any EnOS point")
            return None
            
        except Exception as e:
            logger.error(f"Error in rule-based mapping for {raw_point}: {str(e)}")
            return None
    
    def _infer_device_type(self, point_name: str) -> str:
        """Infer device type from point name"""
        point_lower = point_name.lower()
        
        if "ahu" in point_lower or "air handler" in point_lower:
            return "AHU"
        elif "fcu" in point_lower or "fan coil" in point_lower:
            return "FCU"
        elif "vav" in point_lower:
            return "VAV"
        elif "chiller" in point_lower or "chw" in point_lower or "chilled water" in point_lower:
            return "CHILLER"
        elif "boiler" in point_lower or "hot water" in point_lower or "hw" in point_lower:
            return "BOILER"
        elif "pump" in point_lower:
            return "PUMP"
        
        # Default to AHU if we can't determine
        return "AHU"
    
    @performance_monitor
    def _fallback_mapping(self, raw_point: str, device_type: str) -> Optional[str]:
        """Enhanced fallback mapping for common BMS point types"""
        # First check if the device type is in our schema
        if device_type not in self.enos_schema:
            logger.warning(f"Device type {device_type} not found in EnOS schema")
            # Try more generic device types
            if device_type in ['CWP', 'CHWP', 'HWP'] and 'PUMP' in self.enos_schema:
                device_type = 'PUMP'
            elif device_type in ['CH', 'CHPL'] and 'CHILLER' in self.enos_schema:
                device_type = 'CHILLER'
            elif device_type == 'CT' and 'COOLING_TOWER' in self.enos_schema:
                device_type = 'COOLING_TOWER'
            elif device_type == 'DPM' and 'METER' in self.enos_schema:
                device_type = 'METER'
            else:
                # Still not found, try the first available type as last resort
                if self.enos_schema:
                    first_type = next(iter(self.enos_schema.keys()))
                    logger.warning(f"Using {first_type} as fallback device type for {device_type}")
                    device_type = first_type
                else:
                    # No schema at all, we can't map this point
                    return None
        
        point_lower = raw_point.lower()
        enos_points = self.enos_schema.get(device_type, {}).get('points', {})
        
        if not enos_points:
            logger.warning(f"No points defined for device type {device_type}")
            return None
        
        # Expanded semantic categories for BMS points
        categories = {
            'temperature': ['temp', 'temperature', 'sat', 'rat', 'mat', 'oat', 'chw', 'hw', 'chwst', 'hwst', 'cwt'],
            'humidity': ['humidity', 'humid', 'rh', 'moist'],
            'pressure': ['pressure', 'press', 'static', 'dp', 'differential', 'psi'],
            'flow': ['flow', 'cfm', 'gpm', 'volume', 'airflow'],
            'speed': ['speed', 'frequency', 'hz', 'rpm', 'vfd', 'drive'],
            'valve': ['valve', 'damper', 'vav', 'position', 'vpos', 'dpos'],
            'setpoint': ['setpoint', 'sp', 'set', 'setting', 'stpt', 'setp'],
            'status': ['status', 'state', 'alarm', 'fault', 'failure', 'run', 'mode', 'on', 'off', 'enabled'],
            'energy': ['energy', 'power', 'kwh', 'kw', 'consumption', 'demand'],
            'occupancy': ['occupancy', 'occupied', 'presence', 'occ'],
            'command': ['command', 'cmd', 'control', 'enable', 'disable', 'start', 'stop']
        }
        
        # First try direct matching of point names with more flexible comparison
        for enos_point_name in enos_points.keys():
            enos_lower = enos_point_name.lower()
            enos_parts = set(enos_lower.split('_'))
            point_parts = set(point_lower.replace('.', '_').replace('-', '_').split('_'))
            
            # Direct match in the name or significant overlap in parts
            if (enos_lower in point_lower or 
                point_lower in enos_lower or 
                len(enos_parts.intersection(point_parts)) >= min(2, len(enos_parts)//2)):
                return enos_point_name
        
        # Then try semantic category matching with improved algorithm
        for category, terms in categories.items():
            # Check if the point belongs to this category
            if any(term in point_lower for term in terms):
                # Find EnOS points in the same category
                matching_enos_points = [
                    name for name in enos_points.keys() 
                    if any(term in name.lower() for term in terms)
                ]
                
                if matching_enos_points:
                    # Use the best match (shortest Levenshtein distance)
                    best_match = min(matching_enos_points, 
                                    key=lambda x: self._levenshtein_distance(point_lower, x.lower()))
                    return best_match
                
        # If all else fails, try a generic mapping based on common BMS point types
        fallback_mappings = {
            'temp': 'temperature',
            'humidity': 'humidity',
            'press': 'pressure',
            'flow': 'flow',
            'speed': 'speed',
            'valve': 'valve_position',
            'damper': 'damper_position',
            'alarm': 'alarm',
            'status': 'status',
            'run': 'run_status',
            'cmd': 'command',
            'setpoint': 'setpoint',
            'sp': 'setpoint',
            'energy': 'energy',
            'power': 'power'
        }
        
        # Try to find a generic mapping
        for key, value in fallback_mappings.items():
            if key in point_lower:
                # Look for any point with this value
                for enos_point in enos_points.keys():
                    if value in enos_point.lower():
                        return enos_point
        
        # No match found - as a last resort, return the first point for this device type
        if enos_points:
            first_point = next(iter(enos_points.keys()))
            logger.warning(f"Using {first_point} as last-resort fallback for {raw_point}")
            return first_point
        
        return None
        
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1] 