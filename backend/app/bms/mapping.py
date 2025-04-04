import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import time
from openai import OpenAI
from agents import Agent, Runner
import random
import datetime
import hashlib
import sys
from functools import lru_cache
from ..bms.grouping import performance_monitor
from ..bms.reflection import ReflectionSystem, MappingMemorySystem, PatternAnalysisEngine, QualityAssessmentFramework, StrategySelectionSystem
import traceback

logger = logging.getLogger(__name__)

# Directory for API responses
API_RESPONSES_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'api_responses'))
API_RESPONSES_DIR.mkdir(exist_ok=True, parents=True)

# Cache directory
CACHE_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'mapper'))
CACHE_DIR.mkdir(exist_ok=True, parents=True)

MAPPING_PROMPT = """
You are an expert in mapping Building Management System (BMS) points to EnOS schema.

Device Point Context:
- Device Type: {device_type}
- Device ID: {device_id}
- Point Name: {point_name}
- Point Type: {point_type}
- Unit: {unit}
- Value Example: {value}
- Related points in same device: {related_points}

Task: Map this BMS point to the corresponding EnOS point name.
The EnOS point name MUST follow the format: DEVICE_TYPE_CATEGORY_MEASUREMENT_TYPE_POINT

IMPORTANT RULES:
1. In the JSON response, the "enos_point" value MUST begin with a prefix that EXACTLY matches the input Device Type: {device_type} (or its standard abbreviation, such as CH for CHILLER, PUMP for PUMP, etc.). 
2. The prefix must appear before the first underscore (_). 
3. CATEGORY must be "raw" or "calc" or "write"
4. Your ENTIRE RESPONSE must be a valid JSON object with no additional text.
5. DO NOT include any explanations, commentary, or notes in your response.

Examples of CORRECT responses:
```json
{{"enos_point": "CH_raw_temp_chws"}}
```

```json
{{"enos_point": "AHU_raw_temp_rt"}}
```

Examples of mapping patterns:
- Chiller supply temperature (Device Type: CH) → {{"enos_point": "CH_raw_temp_chws"}}
- AHU return temperature (Device Type: AHU) → {{"enos_point": "AHU_raw_temp_rt"}}
- Fan power measurement (Device Type: FCU) → {{"enos_point": "FCU_raw_power_fan"}}
- Cooling Water Pump Run Status (Device Type: CWP) → {{"enos_point": "CWP_raw_status"}}
- Cooling Tower Fan Power (Device Type: CT) → {{"enos_point": "CT_raw_power_fan"}}
- Main Power Meter kWh (Device Type: DPM) → {{"enos_point": "DPM_raw_energy_active_total"}}

Your response format MUST be EXACTLY:
{{"enos_point": "DEVICE_TYPE_CATEGORY_MEASUREMENT_TYPE_POINT"}}

Do not include ANY other text, explanations, or formatting outside the JSON object.
"""

class EnOSMapper:
    # Enhance the mapping agent instructions
    _mapping_agent_instructions = """You are an expert in mapping Building Management System (BMS) points to the EnOS IoT platform schema.
Your goal is to find the **semantically best matching** EnOS point for a given raw BMS point name and its device type.

**Instructions:**
1.  **Analyze the BMS Point Name:** Break down the name (e.g., 'AHU-01.SupplyAirTempSp') into its components (device instance 'AHU-01', measurement 'SupplyAirTemp', type 'Sp').
2.  **Understand Abbreviations:** Interpret common HVAC/BMS abbreviations:
    *   `Temp`, `T`: Temperature
    *   `Sp`: Setpoint
    *   `St`: Status
    *   `Cmd`: Command
    *   `RH`: Relative Humidity
    *   `Co2`: Carbon Dioxide Level
    *   `Press`, `P`: Pressure (Static, Differential)
    *   `Flow`, `F`: Flow Rate
    *   `Pos`, `%`: Position (e.g., Valve, Damper)
    *   `Hz`: Frequency (Fan/Pump Speed)
    *   `kW`: Active Power
    *   `kWh`: Active Energy
    *   `Run`, `Start`: Running Status / Command
    *   `Stop`: Stop Command / Status
    *   `Trip`, `Fault`, `Flt`, `Fail`: Fault or Trip Status
    *   `Mode`: Operating Mode
    *   `ChW`, `CHW`: Chilled Water
    *   `CW`, `CDW`: Condenser Water / Cooling Water
    *   `SA`, `Supply`: Supply Air
    *   `RA`, `Return`: Return Air
    *   `OA`: Outside Air
    *   `MA`: Mixed Air
    *   `EV`: Evaporator related (often cooling coil)
    *   `Valve`: Valve Position or Status
    *   `Damper`: Damper Position
    *   `DP`: Differential Pressure OR Dew Point (use context)
    *   `Occ`: Occupancy Status
    *   `Eff`: Efficiency
    *   `Stat`: Status
3.  **Consider Device Type:** The device type (e.g., AHU, Chiller, FCU, Pump) is crucial context. A 'Temp' point on a Chiller is different from one on an AHU.
4.  **Target EnOS Schema:** Map to a standard EnOS point format, typically like `{DeviceType}_raw_{measurement}` or `{DeviceType}_stat_{status}` or `{DeviceType}_cmd_{command}` or `{DeviceType}_sp_{setpoint}`. Rely on your knowledge of common EnOS points for the given device type. You may be provided with a list of candidate points for reference, but prioritize semantic meaning even if the exact raw point isn't listed.
5.  **Output Format:** Respond ONLY with a JSON object containing the *best single* EnOS point mapping: `{"enosPoint": "TARGET_ENOS_POINT"}`. If no reasonable mapping exists, return `{"enosPoint": "unknown"}`. Do not include explanations or apologies in the JSON output itself.

**Example:**
BMS Point: `AHU-L5.ReturnAirTemp` (Device Type: AHU)
Semantic Meaning: Return Air Temperature for AHU on Level 5.
Correct EnOS Mapping: `AHU_raw_return_air_temp`
Output: `{"enosPoint": "AHU_raw_return_air_temp"}`

BMS Point: `CHWP-01.RunSt` (Device Type: Pump)
Semantic Meaning: Running Status for Chilled Water Pump 1.
Correct EnOS Mapping: `PUMP_stat_device_on_off` (or similar standard status point for pumps)
Output: `{"enosPoint": "PUMP_stat_device_on_off"}`
"""
    
    # Define quality score thresholds
    QUALITY_EXCELLENT = 0.9
    QUALITY_GOOD = 0.7
    QUALITY_FAIR = 0.5
    QUALITY_POOR = 0.3
    
    # Define mapping reason categories
    REASON_EXACT_MATCH = "exact_match"
    REASON_SEMANTIC_MATCH = "semantic_match"
    REASON_PARTIAL_MATCH = "partial_match"
    REASON_INFERRED = "inferred"
    REASON_FALLBACK = "fallback"

    def __init__(self):
        # Initialize OpenAI client with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.enos_schema = self._load_enos_schema()
        self.max_retries = 5
        self.confidence_threshold = 0.4
        
        # Cache configuration
        self.cache_size = int(os.getenv("ENOS_MAPPER_CACHE_SIZE", "1000"))
        self.mem_cache = {}
        
        self.enable_file_cache = True
        if os.getenv("DISABLE_MAPPING_CACHE", "").lower() in ("true", "1", "yes"):
            self.enable_file_cache = False
        
        self.cache_timeout = int(os.getenv("MAPPING_CACHE_TIMEOUT", 604800))
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        
        # Initialize enhanced reflection system
        self.enable_reflection = os.getenv("ENABLE_MAPPING_REFLECTION", "true").lower() in ("true", "1", "yes")
        if self.enable_reflection:
            logger.info("Initializing enhanced reflection system")
            self.reflection_system = ReflectionSystem()
        
        # Legacy reflection system (for backward compatibility)
        self.mapping_history = []
        self.success_patterns = {}
        self.failure_patterns = {}
        self.quality_scores_history = []
        
        # Enable reflection features
        self.enable_quality_scoring = True
        self.enable_learning = os.getenv("ENABLE_MAPPING_LEARNING", "true").lower() in ("true", "1", "yes")
        self.learning_feedback_threshold = int(os.getenv("LEARNING_FEEDBACK_THRESHOLD", "20"))
        self.reflection_log_file = os.path.join(str(CACHE_DIR.parent), "mapping_reflection.json")
        
        # Initialize the Agent with improved JSON schema definition
        try:
            # Try with detailed schema parameters
            self.mapping_agent = Agent(
                name="EnOSPointMapperAgent",
                instructions=self._mapping_agent_instructions,
                model=self.model,
                temperature=0.0,  # Reduced temperature for more deterministic outputs
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "enos_point": {
                                "type": "string",
                                "description": "The mapped EnOS point name following the DEVICE_TYPE_CATEGORY_MEASUREMENT_TYPE_POINT format"
                            }
                        },
                        "required": ["enos_point"]
                    }
                }
            )
        except TypeError:
            # Fallback to basic initialization if parameters are not supported
            logger.warning("Agent initialization with detailed schema failed. Trying simplified initialization.")
            try:
                self.mapping_agent = Agent(
                    name="EnOSPointMapperAgent",
                    instructions=self._mapping_agent_instructions,
                    model=self.model,
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
            except TypeError:
                # Final fallback to most basic initialization
                logger.warning("Agent initialization with parameters failed. Using basic initialization.")
                self.mapping_agent = Agent(
                    name="EnOSPointMapperAgent",
                    instructions=self._mapping_agent_instructions,
                    model=self.model
                )
        
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
    
    def _convert_schema_format(self, raw_schema: Dict) -> Dict:
        """
        Convert the raw schema format from enos_simlified.json to the format expected by the mapper
        
        Raw format:
        {
            "Chiller": {
                "shortName": "CH",
                "parent": "HVAC",
                "enos_model": "EnOS_HVAC_CH",
                "points": [
                    "CH_raw_status",
                    "CH_raw_trip",
                    ...
                ]
            },
            ...
        }
        
        Expected format:
        {
            "CHILLER": {
                "points": {
                    "CH_raw_status": {},
                    "CH_raw_trip": {},
                    ...
                }
            },
            ...
        }
        """
        converted_schema = {}
        
        for device_name, device_info in raw_schema.items():
            # Normalize the device name to uppercase for consistent lookups
            normalized_name = device_name.upper()
            # For devices with space in the name, also add the abbreviated form
            if " " in device_name:
                short_name = device_info.get("shortName", "").upper()
                if short_name:
                    # Add an entry with the short name (e.g., "CT" for "Cooling Tower")
                    converted_schema[short_name] = {"points": {}}
                    # Convert points array to dictionary
                    for point in device_info.get("points", []):
                        converted_schema[short_name]["points"][point] = {}
            
            # Add the main entry with the full name
            converted_schema[normalized_name] = {"points": {}}
            # Convert points array to dictionary
            for point in device_info.get("points", []):
                converted_schema[normalized_name]["points"][point] = {}
                
        logger.info(f"Converted schema format with {len(converted_schema)} device types")
        return converted_schema
        
    def _load_enos_schema(self) -> Dict:
        """Load the EnOS schema to provide as context to the AI model"""
        try:
            # Path to the simplified EnOS schema file in backend directory
            schema_path = Path('/mnt/d/Onboarding-David/onboarding-with-react/backend/enos_simlified.json')
            logger.info(f"Attempting to load EnOS schema from: {schema_path}")
            
            if schema_path.exists():
                try:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        raw_schema = json.load(f)
                        # Convert the schema to the expected format
                        logger.info(f"Raw schema structure: {list(raw_schema.keys())[:3]}... ({len(raw_schema)} device types)")
                        schema = self._convert_schema_format(raw_schema)
                        logger.info(f"Converted schema structure: {list(schema.keys())[:3]}... ({len(schema)} device types)")
                        logger.info(f"Successfully loaded and converted EnOS schema with {len(schema)} device types from {schema_path}")
                        return schema
                except Exception as e:
                    logger.error(f"Error loading schema from {schema_path}: {str(e)}")
            else:
                logger.error(f"Schema file not found at {schema_path}")
                
                # Try multiple possible locations for the schema as fallback
                possible_paths = [
                    Path(__file__).parent / 'enos_simlified.json',
                    Path(__file__).parent.parent.parent / 'enos_simlified.json',
                    Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'enos_simlified.json')),
                    Path(__file__).parent / 'enos.json'  # Try the original enos.json as well
                ]
                
                # Log all paths being checked
                for path in possible_paths:
                    logger.info(f"Checking for EnOS schema at: {path} (exists: {path.exists()})")
                
                for fallback_path in possible_paths:
                    if fallback_path.exists():
                        try:
                            with open(fallback_path, 'r', encoding='utf-8') as f:
                                raw_schema = json.load(f)
                                # Convert the schema to the expected format
                                schema = self._convert_schema_format(raw_schema)
                                logger.info(f"Successfully loaded and converted EnOS schema with {len(schema)} device types from {fallback_path}")
                                return schema
                        except Exception as e:
                            logger.error(f"Error loading schema from {fallback_path}: {str(e)}")
                
                # If not found in relative paths, try absolute path as a last resort
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                absolute_path = os.path.join(base_dir, 'enos_simlified.json')
                logger.info(f"Trying absolute path: {absolute_path}")
                
                if os.path.exists(absolute_path):
                    try:
                        with open(absolute_path, 'r', encoding='utf-8') as f:
                            raw_schema = json.load(f)
                            # Convert the schema to the expected format
                            schema = self._convert_schema_format(raw_schema)
                            logger.info(f"Successfully loaded and converted EnOS schema with {len(schema)} device types from {absolute_path}")
                            return schema
                    except Exception as e:
                        logger.error(f"Error loading schema from absolute path: {str(e)}")
            
            logger.error("Could not find enos_simlified.json in any expected location")
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
            
            # Special handling for energy meters and power monitoring points
            if "energy" in point_lowercase or "power" in point_lowercase or "kw" in point_lowercase or "kwh" in point_lowercase or device_type.upper() == "ENERGY":
                if "pump" in point_lowercase or "cwp" in point_lowercase:
                    point_mapping = "pumpPower"
                elif "fan" in point_lowercase:
                    point_mapping = "fanPower"
                elif "kwh" in point_lowercase or "consumption" in point_lowercase or "meter" in point_lowercase:
                    point_mapping = "energyConsumption"
                elif "kw" in point_lowercase or "demand" in point_lowercase:
                    point_mapping = "powerDemand"
                elif "total" in point_lowercase:
                    point_mapping = "totalPower"
                else:
                    point_mapping = "power"
            
            # Try to match based on patterns
            elif "temp" in point_lowercase or "tmp" in point_lowercase or "temperature" in point_lowercase:
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
    
    def _infer_device_type_from_name(self, point_name: str) -> str:
        """Extract device type from point name (e.g., 'CT_1.TripStatus' -> 'CT')"""
        if not point_name:
            return "UNKNOWN"
            
        # First try to extract prefix before underscore or dot
        parts = point_name.split('_', 1)
        if len(parts) > 1:
            prefix = parts[0].upper()
            # Check if this is a known device type prefix
            if prefix in {"AHU", "FCU", "CT", "CH", "CHPL", "PUMP", "CWP", "CHWP", "HWP", "VAV", "DPM", "METER"}:
                return prefix
        
        # If not found with underscore, try with dot
        parts = point_name.split('.', 1)
        if len(parts) > 1:
            # Check for pattern like "CT_1" before the dot
            prefix_parts = parts[0].split('_', 1)
            if prefix_parts:
                prefix = prefix_parts[0].upper()
                if prefix in {"AHU", "FCU", "CT", "CH", "CHPL", "PUMP", "CWP", "CHWP", "HWP", "VAV", "DPM", "METER"}:
                    return prefix
        
        # Fall back to the existing inference method
        return self._infer_device_type(point_name)
        
    def _infer_device_type(self, point_name: str) -> str:
        """Infer device type from point name content"""
        point_lower = point_name.lower()
        
        if "ahu" in point_lower or "air handler" in point_lower:
            return "AHU"
        elif "ahuenergy" in point_lower:
            return "AHU"  # Map AHUENERGY to AHU
        elif "fcu" in point_lower or "fan coil" in point_lower:
            return "FCU"
        elif "vav" in point_lower:
            return "VAV"
        elif "ct" in point_lower or "cooling tower" in point_lower:
            return "CT"
        elif "chiller" in point_lower or "chw" in point_lower or "chilled water" in point_lower:
            return "CHILLER"
        elif "boiler" in point_lower or "hot water" in point_lower or "hw" in point_lower:
            return "BOILER"
        elif "chwp" in point_lower:
            return "CHWP"
        elif "cwp" in point_lower:
            return "CWP"
        elif "hwp" in point_lower:
            return "HWP"
        elif "pump" in point_lower:
            return "PUMP"
        elif "dpm" in point_lower or "meter" in point_lower:
            return "METER"
        
        # Default to UNKNOWN if we can't determine
        return "UNKNOWN"
    
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

    def group_points_by_device(self, points: List[Dict]) -> Dict[str, Dict]:
        """Group points by their device identifier."""
        devices = {}
        for point in points:
            # Ensure we have a pointId
            point_id = point.get('pointId') or point.get('id')
            if not point_id:
                logger.warning(f"Point missing both pointId and id: {point}")
                continue
                
            device_key = f"{point['deviceType']}.{point['deviceId']}"
            if device_key not in devices:
                devices[device_key] = {
                    'type': point['deviceType'],
                    'id': point['deviceId'],
                    'points': []
                }
            devices[device_key]['points'].append(point)
        return devices

    def create_mapping_context(self, point: Dict, device_group: Dict) -> str:
        """Create context for a single point using its device group."""
        related_points = [
            p['pointName'].split('.')[-1]
            for p in device_group['points']
            if p['pointId'] != point['pointId']
        ]
        
        return MAPPING_PROMPT.format(
            device_type=device_group['type'],
            device_id=device_group['id'],
            related_points=", ".join(related_points),
            point_name=point['pointName'],
            point_type=point.get('pointType', 'unknown'),
            unit=point.get('unit', 'no-units'),
            value=point.get('presentValue', 'N/A')
        )

    def _get_expected_enos_prefix(self, device_type: str) -> str:
        """Convert device type to expected EnOS point prefix."""
        # Map of device types to their EnOS point prefixes
        prefix_mapping = {
            'FCU': 'FCU',
            'AHU': 'AHU',
            'VAV': 'VAV',
            'CHILLER': 'CH',
            'CH': 'CH',
            'CHPL': 'CH',
            'BOILER': 'BOIL',
            'BOIL': 'BOIL',
            'CWP': 'CWP',
            'CHWP': 'CHWP',
            'HWP': 'HWP',
            'PUMP': 'PUMP',
            'CT': 'CT',
            'COOLING_TOWER': 'CT',
            'RTU': 'RTU',
            'METER': 'METER',
            'DPM': 'DPM',
            'EF': 'EF',
            'EXHAUST_FAN': 'EF',
            'PAU': 'PAU',
            'WST': 'WST',
            'ENERGY': 'ENERGY',
            'POWER': 'ENERGY',
            'OTHER': 'OTHER',
            'UNKNOWN': 'UNKNOWN'
        }
        
        device_type_upper = device_type.upper()
        # First check for exact match
        if device_type_upper in prefix_mapping:
            return prefix_mapping[device_type_upper]
        
        # Then check for partial match
        for key, value in prefix_mapping.items():
            if key in device_type_upper:
                return value
        
        # If no match, return the input as fallback
        logger.warning(f"No prefix mapping found for device type: {device_type}")
        return device_type_upper

    def _validate_enos_format(self, enos_point: str, device_type: str = None) -> bool:
        """Validate that the EnOS point name follows the correct format and matches device type."""
        if not enos_point:
            logger.warning("Empty EnOS point name")
            return False
            
        parts = enos_point.split('_')
        if len(parts) < 3:
            logger.warning(f"EnOS point has too few parts: {enos_point}")
            return False
        
        # Get the actual prefix from the EnOS point
        actual_prefix = parts[0]
        
        # Check prefix against device_type if provided
        if device_type:
            expected_prefix = self._get_expected_enos_prefix(device_type)
            if actual_prefix != expected_prefix:
                logger.warning(f"Prefix mismatch: expected {expected_prefix} but got {actual_prefix} for device_type {device_type}")
                return False
        # Otherwise use a list of valid prefixes (backward compatibility)
        elif actual_prefix not in {'CH', 'AHU', 'FCU', 'PAU', 'CHWP', 'CWP', 'HWP', 'CT', 'WST', 'DPM', 'PUMP', 'VAV', 'RTU', 'METER', 'BOIL', 'EF', 'ENERGY'}:
            logger.warning(f"Invalid EnOS point prefix: {actual_prefix}")
            return False
            
        # Check category (usually 'raw')
        if parts[1] not in {'raw', 'calc'}:
            logger.warning(f"Invalid EnOS point category: {parts[1]}")
            return False
            
        # Expanded list of measurement types
        valid_measurements = {
            'temp', 'power', 'status', 'speed', 'pressure', 'flow', 'humidity', 'position',
            'energy', 'current', 'voltage', 'frequency', 'level', 'occupancy', 'setpoint',
            'mode', 'command', 'alarm', 'damper', 'valve', 'state', 'volume'
        }
        
        if parts[2] not in valid_measurements:
            logger.warning(f"Invalid EnOS point measurement type: {parts[2]}")
            return False
            
        return True

    def _clean_json_response(self, response: str) -> str:
        """
        Enhanced cleaning and normalizing of JSON responses from AI to handle various formatting issues.
        This method tries multiple approaches to extract valid JSON from potentially malformed responses.
        """
        if not response:
            return "{}"  # Return empty object for empty responses
            
        try:
            # Remove any leading/trailing whitespace
            response = response.strip()
            
            # Handle common formatting issues
            
            # 1. Remove markdown code formatting
            if response.startswith('```json') and response.endswith('```'):
                response = response[7:-3].strip()
            elif response.startswith('```') and response.endswith('```'):
                response = response[3:-3].strip()
                
            # 2. Remove explanatory text before or after JSON
            if '{' in response and '}' in response:
                first_brace = response.find('{')
                last_brace = response.rfind('}')
                if first_brace > 0 or last_brace < len(response) - 1:
                    logger.info(f"Removing text around JSON: {response}")
                    response = response[first_brace:last_brace+1]
            
            # 3. Handle quoted JSON (common API response issue)
            if response.startswith('"') and response.endswith('"'):
                # This might be a quoted JSON string
                try:
                    unquoted = json.loads(response)
                    if isinstance(unquoted, str) and '{' in unquoted and '}' in unquoted:
                        response = unquoted
                except Exception:
                    pass
                    
            # 4. Handle single-quoted strings (not valid JSON)
            if "'" in response:
                response = response.replace("'", '"')
                
            # 5. Handle escaped quotes within JSON strings
            response = re.sub(r'(?<!\\)\\(?!\\)"', '\\"', response)
            
            # Try to parse as-is to check if it's valid
            json.loads(response)
            return response
            
        except json.JSONDecodeError:
            # If we can't parse it directly, try more aggressive corrections
            logger.warning(f"JSON parsing error, attempting aggressive fixes for: {response}")
            
            # Check if response contains key patterns for enos_point
            key_patterns = ['"enos_point"', "'enos_point'", "enos_point"]
            contains_enos_key = any(pattern in response for pattern in key_patterns)
            
            if contains_enos_key:
                # Try to extract JSON object with regex
                import re
                patterns = [
                    # Standard JSON format
                    r'({[^{}]*"enos_point"\s*:\s*"[^"]*"[^{}]*})',
                    # Single-quoted keys
                    r'({[^{}]*\'enos_point\'\s*:\s*"[^"]*"[^{}]*})',
                    # Single-quoted values
                    r'({[^{}]*"enos_point"\s*:\s*\'[^\']*\'[^{}]*})',
                    # Both single-quoted
                    r'({[^{}]*\'enos_point\'\s*:\s*\'[^\']*\'[^{}]*})'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response)
                    if match:
                        extracted = match.group(1).replace("'", '"')  # Replace any single quotes with double quotes
                        try:
                            # Test if valid
                            json.loads(extracted)
                            logger.info(f"Successfully extracted JSON with regex: {extracted}")
                            return extracted
                        except json.JSONDecodeError:
                            continue
                
                # Try direct extraction between braces
                try:
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        clean_json = response[start_idx:end_idx]
                        # Clean up any single quotes
                        clean_json = clean_json.replace("'", '"')
                        # Test if valid
                        json.loads(clean_json)
                        return clean_json
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to extract JSON object: {str(e)}")
                    
                # Last resort: If we found enos_point text but couldn't parse JSON,
                # try to extract just the value with regex and construct valid JSON
                enos_value_patterns = [
                    r'"enos_point"\s*:\s*"([^"]*)"',
                    r"'enos_point'\s*:\s*'([^']*)'",
                    r'"enos_point"\s*:\s*\'([^\']*)\''
                ]
                
                for pattern in enos_value_patterns:
                    match = re.search(pattern, response)
                    if match:
                        enos_value = match.group(1)
                        constructed_json = f'{{"enos_point": "{enos_value}"}}'
                        logger.info(f"Constructed JSON from extracted value: {constructed_json}")
                        return constructed_json
            
            # Return the original, will be handled as an error in the calling function
            return response
    
    def _evaluate_mapping_quality(self, enos_point: str, point: Dict) -> tuple:
        """
        Evaluate the quality of mapping and determine the reason for the mapping.
        Returns:
            tuple: (quality_score, reason, explanation)
        """
        # Default values
        quality_score = 0.0
        reason = self.REASON_FALLBACK
        explanation = "Default fallback mapping used"
        
        # Check if generic fallback was used
        if enos_point.endswith('_raw_generic_point'):
            quality_score = 0.2
            reason = self.REASON_FALLBACK
            explanation = "Generic fallback mapping used due to failure to match specific point"
            return (quality_score, reason, explanation)
        
        # Check for exact match patterns
        point_name_lower = point['pointName'].lower()
        expected_prefix = self._get_expected_enos_prefix(point['deviceType'])
        enos_parts = enos_point.split('_')
        
        # 1. Check for device type match
        if enos_parts[0] == expected_prefix:
            quality_score += 0.4
            # Further refine based on naming patterns
            if len(enos_parts) >= 4:
                # Meaningful point name with multiple components
                quality_score += 0.2
                
                # Check if point name components appear in the ENOS point
                point_words = set(point_name_lower.replace('.', '_').replace('-', '_').split('_'))
                enos_words = set(enos_point.lower().split('_')[2:])  # Skip prefix and raw/calc
                
                word_match_count = len(point_words.intersection(enos_words))
                if word_match_count > 0:
                    quality_score += min(0.3, word_match_count * 0.1)
                    
                    if word_match_count / len(point_words) > 0.5:
                        reason = self.REASON_SEMANTIC_MATCH
                        explanation = f"Semantic match based on {word_match_count} matching terms"
                    else:
                        reason = self.REASON_PARTIAL_MATCH
                        explanation = f"Partial match with {word_match_count}/{len(point_words)} terms"
                else:
                    reason = self.REASON_INFERRED
                    explanation = "Inferred based on device type and context"
            else:
                # Simple point structure
                reason = self.REASON_INFERRED
                explanation = "Mapping inferred from limited information"
        else:
            # Device type mismatch
            quality_score = 0.1
            reason = self.REASON_FALLBACK
            explanation = f"Device type mismatch: expected {expected_prefix} but got {enos_parts[0]}"
        
        # Cap the quality score at 1.0
        quality_score = min(1.0, quality_score)
        
        return (quality_score, reason, explanation)
    
    def _log_mapping_reflection(self, point: Dict, enos_point: str, quality_score: float, 
                               reason: str, explanation: str, success: bool):
        """
        Log mapping reflection data for learning and improvement
        """
        if not self.enable_learning:
            return
            
        reflection_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "point_name": point.get('pointName', ''),
            "point_type": point.get('pointType', ''),
            "device_type": point.get('deviceType', ''),
            "enos_point": enos_point,
            "quality_score": quality_score,
            "reason": reason,
            "explanation": explanation,
            "success": success
        }
        
        # Add to in-memory history
        self.mapping_history.append(reflection_data)
        self.quality_scores_history.append(quality_score)
        
        # Update pattern dictionaries for learning
        device_type = point.get('deviceType', 'UNKNOWN')
        point_type = point.get('pointType', 'UNKNOWN')
        key = f"{device_type}:{point_type}"
        
        if success:
            if key not in self.success_patterns:
                self.success_patterns[key] = []
            self.success_patterns[key].append((point.get('pointName', ''), enos_point))
            
            # Trim to keep only recent successful patterns
            if len(self.success_patterns[key]) > self.learning_feedback_threshold:
                self.success_patterns[key] = self.success_patterns[key][-self.learning_feedback_threshold:]
        else:
            if key not in self.failure_patterns:
                self.failure_patterns[key] = []
            self.failure_patterns[key].append((point.get('pointName', ''), enos_point))
            
            # Trim to keep only recent failure patterns
            if len(self.failure_patterns[key]) > self.learning_feedback_threshold:
                self.failure_patterns[key] = self.failure_patterns[key][-self.learning_feedback_threshold:]
        
        # Periodically save reflection data to file (every 20 mappings)
        if len(self.mapping_history) % 20 == 0:
            self._save_reflection_data()
    
    def _save_reflection_data(self):
        """Save reflection data to file for persistence"""
        try:
            reflection_summary = {
                "last_updated": datetime.datetime.now().isoformat(),
                "quality_stats": {
                    "average_score": sum(self.quality_scores_history) / max(len(self.quality_scores_history), 1),
                    "excellent_count": len([s for s in self.quality_scores_history if s >= self.QUALITY_EXCELLENT]),
                    "good_count": len([s for s in self.quality_scores_history if self.QUALITY_GOOD <= s < self.QUALITY_EXCELLENT]),
                    "fair_count": len([s for s in self.quality_scores_history if self.QUALITY_FAIR <= s < self.QUALITY_GOOD]),
                    "poor_count": len([s for s in self.quality_scores_history if self.QUALITY_POOR <= s < self.QUALITY_FAIR]),
                    "unacceptable_count": len([s for s in self.quality_scores_history if s < self.QUALITY_POOR])
                },
                "top_success_patterns": {k: v[-5:] for k, v in self.success_patterns.items()},
                "top_failure_patterns": {k: v[-5:] for k, v in self.failure_patterns.items()},
                "recent_mappings": self.mapping_history[-30:] if self.mapping_history else []
            }
            
            with open(self.reflection_log_file, 'w') as f:
                json.dump(reflection_summary, f, indent=2)
                
            logger.info(f"Saved mapping reflection data to {self.reflection_log_file}")
        except Exception as e:
            logger.error(f"Failed to save reflection data: {str(e)}")
    
    def process_ai_response(self, response: str, point: Dict) -> Dict:
        """Process AI response to extract standardized EnOS point name."""
        mapping_success = True
        quality_score = 0.0
        reason = self.REASON_FALLBACK
        explanation = "Default processing"
        
        try:
            # Print raw response for debugging
            logger.info(f"Raw AI response for point '{point['pointName']}': {response}")
            
            # Check for missing device type and try to infer it
            if not point.get('deviceType'):
                # Extract device type from point name
                inferred_device_type = self._infer_device_type_from_name(point['pointName'])
                point['deviceType'] = inferred_device_type
                logger.info(f"Inferred deviceType '{inferred_device_type}' from pointName '{point['pointName']}'")
                reason = self.REASON_INFERRED
                explanation = f"Device type inferred from point name"
            
            # Enhanced error detection: check for various problematic patterns in the response
            problematic_patterns = [
                "' \"enos_point\"'",  # Common error pattern
                "'enos_point'",       # Single quotes around key
                "```json",            # Markdown formatting
                "\"error\":",         # Error response
                "explanation:",       # Explanatory text
                "I'll map",           # Conversational format
                "Let me"              # Conversational format
            ]
            
            error_detected = any(pattern in response for pattern in problematic_patterns)
            
            if error_detected or not ('{' in response and '}' in response):
                logger.warning(f"Detected problematic response format, attempting direct fixes")
                # Try to construct a valid JSON manually
                device_type_prefix = self._get_expected_enos_prefix(point['deviceType'])
                response = '{"enos_point": "' + device_type_prefix + '_raw_generic_point"}'
                logger.info(f"Using fallback response: {response}")
                reason = self.REASON_FALLBACK
                explanation = "Response format error, using fallback mapping"
                mapping_success = False
            
            # Clean the response to handle AI formatting issues
            cleaned_response = self._clean_json_response(response)
            logger.info(f"Cleaned response: {cleaned_response}")
            
            # Manual fallback for specific error cases
            if cleaned_response.startswith("'") and cleaned_response.endswith("'"):
                cleaned_response = cleaned_response[1:-1]
                logger.info(f"Removed surrounding quotes: {cleaned_response}")
            
            # Try extra hard to extract valid JSON
            try:
                # Parse the JSON response
                result = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                mapping_success = False
                
                # Make one last attempt with regex to extract {"enos_point": "..."} pattern
                import re
                matches = re.search(r'{"enos_point":\s*"([^"]+)"}', cleaned_response)
                if matches:
                    enos_point_value = matches.group(1)
                    logger.info(f"Extracted enos_point with regex: {enos_point_value}")
                    result = {"enos_point": enos_point_value}
                    reason = self.REASON_FALLBACK
                    explanation = "JSON parsing error, extracted with regex"
                else:
                    # Create a fallback mapping based on device type prefix
                    device_type_prefix = self._get_expected_enos_prefix(point['deviceType'])
                    # Get schema points for this device type
                    device_type = point['deviceType'].upper()
                    enos_schema_points = self.enos_schema.get(device_type, {}).get('points', {})
                    
                    # Use reflection system to suggest mapping if enabled
                    suggested_mapping = None
                    if self.enable_reflection and hasattr(self, 'reflection_system'):
                        suggestion = self.reflection_system.suggest_mapping(point)
                        if suggestion.get('success') and suggestion.get('suggested_mapping'):
                            suggested_mapping = suggestion.get('suggested_mapping')
                            logger.info(f"Using mapping from reflection system: {suggested_mapping}")
                            reason = self.REASON_INFERRED
                            explanation = f"Mapping suggested by reflection system: {suggestion.get('reason', '')}"
                    
                    if suggested_mapping:
                        fallback_enos_point = suggested_mapping
                    elif enos_schema_points:
                        # Use the first available point for this device type
                        fallback_enos_point = next(iter(enos_schema_points.keys()))
                        logger.info(f"Using first available point from schema: {fallback_enos_point}")
                    else:
                        # If no schema points available, construct a raw point
                        fallback_enos_point = f"{device_type_prefix}_raw_status"
                    
                    logger.warning(f"Using fallback mapping: {fallback_enos_point}")
                    result = {"enos_point": fallback_enos_point}
                    
                    if not suggested_mapping:
                        reason = self.REASON_FALLBACK
                        explanation = "JSON parsing failed, using generic fallback point"

            # Validate required fields
            if 'enos_point' not in result:
                device_type_prefix = self._get_expected_enos_prefix(point['deviceType'])
                # Get schema points for this device type
                device_type = point['deviceType'].upper()
                enos_schema_points = self.enos_schema.get(device_type, {}).get('points', {})
                
                # Use reflection system to suggest mapping if enabled
                suggested_mapping = None
                if self.enable_reflection and hasattr(self, 'reflection_system'):
                    suggestion = self.reflection_system.suggest_mapping(point)
                    if suggestion.get('success') and suggestion.get('suggested_mapping'):
                        suggested_mapping = suggestion.get('suggested_mapping')
                        logger.info(f"Using mapping from reflection system: {suggested_mapping}")
                        reason = self.REASON_INFERRED
                        explanation = f"Mapping suggested by reflection system: {suggestion.get('reason', '')}"
                
                if suggested_mapping:
                    result['enos_point'] = suggested_mapping
                elif enos_schema_points:
                    # Use the first available point for this device type
                    fallback_enos_point = next(iter(enos_schema_points.keys()))
                    logger.info(f"Using first available point from schema: {fallback_enos_point}")
                    result['enos_point'] = fallback_enos_point
                else:
                    # If no schema points available, construct a raw point
                    fallback_enos_point = f"{device_type_prefix}_raw_status"
                    result['enos_point'] = fallback_enos_point
                
                if not suggested_mapping:
                    logger.warning(f"Missing enos_point field, using fallback: {result['enos_point']}")
                    mapping_success = False
                    reason = self.REASON_FALLBACK
                    explanation = "Response missing enos_point field"

            enos_point = result['enos_point']

            # Extra validation of enos_point
            if not enos_point or not isinstance(enos_point, str):
                device_type_prefix = self._get_expected_enos_prefix(point['deviceType'])
                # Get schema points for this device type
                device_type = point['deviceType'].upper()
                enos_schema_points = self.enos_schema.get(device_type, {}).get('points', {})
                if enos_schema_points:
                    # Use the first available point for this device type
                    fallback_enos_point = next(iter(enos_schema_points.keys()))
                    logger.info(f"Using first available point from schema: {fallback_enos_point}")
                else:
                    # If no schema points available, construct a raw point
                    fallback_enos_point = f"{device_type_prefix}_raw_status"
                logger.warning(f"Invalid enos_point type, using fallback: {fallback_enos_point}")
                enos_point = fallback_enos_point
                mapping_success = False
                reason = self.REASON_FALLBACK
                explanation = "Invalid enos_point data type"
            
            # Check if enos_point starts with underscore (missing prefix)
            if enos_point.startswith('_'):
                device_type_prefix = self._get_expected_enos_prefix(point['deviceType'])
                corrected_point = f"{device_type_prefix}{enos_point}"
                logger.warning(f"Enos point missing prefix: {enos_point}, corrected to: {corrected_point}")
                enos_point = corrected_point
                mapping_success = False
                reason = self.REASON_FALLBACK
                explanation = "Missing prefix in response, added correct prefix"
                
            # Format validation with fallback - now with device type checking
            if not self._validate_enos_format(enos_point, point['deviceType']):
                logger.warning(f"Invalid EnOS point format: {enos_point}, attempting to fix")
                # Try to fix format - create a valid format based on device type and expected prefix
                expected_prefix = self._get_expected_enos_prefix(point['deviceType'])
                # Get schema points for this device type
                device_type = point['deviceType'].upper()
                enos_schema_points = self.enos_schema.get(device_type, {}).get('points', {})
                if enos_schema_points:
                    # Use the first available point for this device type
                    fallback_enos_point = next(iter(enos_schema_points.keys()))
                    logger.info(f"Using first available point from schema: {fallback_enos_point}")
                else:
                    # If no schema points available, construct a raw point
                    fallback_enos_point = f"{expected_prefix}_raw_status"
                logger.info(f"Using format-corrected fallback: {fallback_enos_point}")
                enos_point = fallback_enos_point
                mapping_success = False
                reason = self.REASON_FALLBACK
                explanation = "Invalid EnOS point format"
                
            # Evaluate mapping quality if not already determined
            if mapping_success and reason == self.REASON_FALLBACK:
                quality_score, reason, explanation = self._evaluate_mapping_quality(enos_point, point)
            elif not mapping_success:
                quality_score = 0.2  # Low quality score for fallbacks
            
            # Create basic mapping result
            mapping_result = {
                "original": {
                    "pointName": point['pointName'],
                    "deviceType": point['deviceType'],
                    "deviceId": point['deviceId'],
                    "pointType": point.get('pointType', 'unknown'),
                    "unit": point.get('unit', 'no-units'),
                    "value": point.get('presentValue', 'N/A')
                },
                "mapping": {
                    "pointId": point['pointId'],
                    "enosPoint": enos_point,
                    "status": "mapped"
                },
                "reflection": {
                    "quality_score": quality_score,
                    "reason": reason,
                    "explanation": explanation,
                    "success": mapping_success
                }
            }
            
            # Log for legacy reflection system
            self._log_mapping_reflection(point, enos_point, quality_score, reason, explanation, mapping_success)
            
            # Enhance with reflection system if enabled
            if self.enable_reflection and hasattr(self, 'reflection_system'):
                mapping_context = {
                    "strategy": "direct_pattern" if mapping_success else "fallback",
                    "original_response": response,
                    "processing_history": [
                        {"action": "initial_mapping", "result": enos_point}
                    ]
                }
                
                # Use reflection system to enhance mapping result
                enhanced_mapping = self.reflection_system.reflect_on_mapping(
                    mapping_result,
                    reference_mappings=None,  # We don't have reference mappings at this point
                    schema=self.enos_schema,
                    context=mapping_context
                )
                
                return enhanced_mapping
            
            # Return basic mapping if reflection system is not enabled
            return mapping_result
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error processing point {point.get('pointName', 'unknown')}: {error_message}")
            
            # Create an error reflection entry for legacy system
            self._log_mapping_reflection(
                point, 
                None, 
                0.0,  # Zero quality score for errors
                self.REASON_FALLBACK,
                f"Processing error: {error_message}",
                False
            )
            
            # Create basic error result
            error_result = {
                "original": {
                    "pointName": point['pointName'],
                    "deviceType": point.get('deviceType', 'UNKNOWN'),
                    "deviceId": point.get('deviceId', 'UNKNOWN'),
                    "pointType": point.get('pointType', 'unknown'),
                    "unit": point.get('unit', 'no-units'),
                    "value": point.get('presentValue', 'N/A')
                },
                "mapping": {
                    "pointId": point.get('pointId', 'unknown'),
                    "enosPoint": None,
                    "status": "error",
                    "error": error_message
                },
                "reflection": {
                    "quality_score": 0.0,
                    "reason": self.REASON_FALLBACK,
                    "explanation": f"Processing error: {error_message}",
                    "success": False
                }
            }
            
            # Process with reflection system if enabled
            if self.enable_reflection and hasattr(self, 'reflection_system'):
                try:
                    error_context = {
                        "strategy": "fallback",
                        "error": error_message,
                        "original_response": response
                    }
                    
                    # Use reflection system for error analysis
                    enhanced_error = self.reflection_system.reflect_on_mapping(
                        error_result,
                        reference_mappings=None,
                        schema=self.enos_schema,
                        context=error_context
                    )
                    
                    return enhanced_error
                except Exception as reflection_error:
                    logger.error(f"Error in reflection system: {str(reflection_error)}")
            
            # Return basic error result if reflection fails or is disabled
            return error_result

    @performance_monitor
    def map_points(self, points: List[Dict]) -> Dict:
        """Map points with device context awareness and reflection capabilities."""
        stats = {"total": 0, "mapped": 0, "errors": 0}
        all_mappings = []
        processed_mappings = [] # For batch analysis
        pattern_insights = []
        
        # Ensure schema is loaded once before processing points
        if not hasattr(self, 'simplified_schema') or not self.simplified_schema:
            self._load_simplified_schema()

        try:
            # Group points by device type for context-aware mapping
            points_by_device_type = {}
            for point in points:
                # Improved device type extraction
                device_type = point.get('deviceType')
                point_name = point.get('pointName', '')
                if not device_type:
                    device_type = self._extract_device_type_from_name(point_name)
                if not device_type:
                    # Attempt fallback extraction if needed (or use UNKNOWN)
                    device_type = self._fallback_device_type_extraction(point_name) or 'UNKNOWN'
                    logger.debug(f"Used fallback device type extraction for '{point_name}', got: {device_type}")
                
                # Ensure device_type is a hashable type (string)
                device_type_key = str(device_type).upper() # Use uppercase for consistency

                if device_type_key not in points_by_device_type:
                    points_by_device_type[device_type_key] = []
                points_by_device_type[device_type_key].append(point)

            # Process points group by group
            for device_key, group_points in points_by_device_type.items():
                logger.info(f"Processing mapping for device group: {device_key} ({len(group_points)} points)")
                
                # Optional: Pre-analyze patterns within the group (existing logic)
                pattern_analysis_result = None
                if self.enable_reflection and hasattr(self, 'reflection_system'):
                    try:
                        pattern_analysis_result = self.reflection_system.analyze_patterns(group_points)
                        if pattern_analysis_result.get('insights'):
                             pattern_insights.extend(pattern_analysis_result['insights'])
                             logger.info(f"Pattern analysis generated {len(pattern_analysis_result['insights'])} insights for {device_key}.")
                    except Exception as pattern_error:
                         logger.warning(f"Error during pattern analysis for {device_key}: {str(pattern_error)}")

                # Process each point within the group
                for point in group_points:
                    try:
                        stats["total"] += 1
                        pointName = point.get('pointName', '')
                        # Use the already determined (and potentially improved) device_type for the group
                        device_type = device_key 
                        unit = point.get('unit', '')
                        description = point.get('description', '') # Get description
                        
                        if not pointName:
                            logger.warning("Skipping point with empty name.")
                            stats["errors"] += 1
                            continue
                        
                        # Normalize the group key for schema lookup and prompt consistency
                        device_type_normalized = self._normalize_device_type(device_type)
                        
                        # --- Start Prompt Enhancement ---
                        # 1. Basic Prompt Components
                        prompt_lines = [
                            f"BMS Point Name: {pointName}",
                            f"Device Type: {device_type_normalized}" # Use consistent normalized type
                        ]
                        if unit:
                            prompt_lines.append(f"Unit: {unit}")
                        if description: # Add description to prompt if available
                            prompt_lines.append(f"Description: {description}")

                        # 2. Add Hint about abbreviations found
                        abbreviations_found = []
                        # More robust checks (case-insensitive, word boundaries where applicable)
                        p_lower = pointName.lower()
                        if "sp" in p_lower : abbreviations_found.append("Sp (Setpoint)")
                        if "temp" in p_lower or ".t" in p_lower or "rt" in p_lower or "st" in p_lower and "status" not in p_lower and "stpt" not in p_lower: 
                            # Avoid matching 'st' in 'status' or 'stpt'
                            if not any(x in p_lower for x in ['status', 'stat', 'stpt']):
                                abbreviations_found.append("Temp (Temperature)")
                        if "status" in p_lower or "stat" in p_lower or (p_lower.endswith(".st") and "chwst" not in p_lower and "cwst" not in p_lower) : abbreviations_found.append("St/Status (Status)")
                        if "cmd" in p_lower : abbreviations_found.append("Cmd (Command)")
                        if "trip" in p_lower or "flt" in p_lower or "fail" in p_lower: abbreviations_found.append("Trip/Fault (Fault Status)")
                        if "hz" in p_lower: abbreviations_found.append("Hz (Frequency/Speed)")
                        if "pos" in p_lower or "%" in pointName: abbreviations_found.append("Pos/% (Position)") # Check % in original name
                        if "kw" in p_lower and "kwh" not in p_lower: abbreviations_found.append("kW (Power)")
                        if "co2" in p_lower: abbreviations_found.append("Co2 (Carbon Dioxide)")
                        if "flow" in p_lower or "flw" in p_lower: abbreviations_found.append("Flow (Flow Rate)")
                        if "valve" in p_lower: abbreviations_found.append("Valve (Valve Position/Status)")
                        if "damper" in p_lower: abbreviations_found.append("Damper (Damper Position)")
                        # Remove duplicates
                        abbreviations_found = list(dict.fromkeys(abbreviations_found)) 

                        if abbreviations_found:
                            prompt_lines.append(f"Potential Abbreviations Detected: {', '.join(abbreviations_found)}")

                        # 3. Add reference schema points (optional, limited)
                        if device_type_normalized in self.simplified_schema:
                            candidate_points = self.simplified_schema[device_type_normalized].get("points", [])
                            if candidate_points:
                                prompt_lines.append("\nReference EnOS Points for this Device Type (prioritize semantic match, list may be incomplete):")
                                prompt_lines.extend(candidate_points[:20]) # Show first 20 as examples
                        else:
                            prompt_lines.append("\nNo specific reference points file provided; rely on standard EnOS points for this device type.")

                        # 4. Final Instruction
                        prompt_lines.append("\nBased on the above, what is the single best semantic EnOS point mapping? Respond ONLY with a JSON object like: {\"enosPoint\": \"TARGET_ENOS_POINT\"} or {\"enosPoint\": \"unknown\"}.")

                        prompt = "\n".join(prompt_lines)
                        # --- End Prompt Enhancement ---
                        
                        # Select strategy (existing logic, might need review)
                        selected_strategy = None 
                        if pattern_analysis_result and pattern_analysis_result.get('recommended_strategy'):
                            selected_strategy = pattern_analysis_result['recommended_strategy']
                            logger.info(f"Using pattern-analysis strategy for {pointName}: {selected_strategy}")
                        else:
                            selected_strategy = "direct_semantic" # Default strategy
                            logger.debug(f"Using default strategy for {pointName}: {selected_strategy}")

                        # --- Existing AI Call Logic ---                        
                        mapping = None # Initialize mapping variable
                        try:
                            # logger.info(f"Attempting AI mapping for point: {pointName} using strategy: {selected_strategy}")
                            # Use the Agent Runner
                            result = Runner.run_sync(self.mapping_agent, prompt)

                            # Extract the final output from the result
                            content = result.final_output
                            if not content or not isinstance(content, str):
                                raise ValueError(f"Agent returned invalid content type: {type(content)}")

                            # Basic check if content looks like JSON, try to extract if noisy
                            if '{' not in content or '}' not in content:
                                try:
                                    json_start = content.index('{')
                                    json_end = content.rindex('}') + 1
                                    content = content[json_start:json_end]
                                    logger.warning(f"Extracted potential JSON from noisy agent response for {pointName}: {content}")
                                except ValueError:
                                     raise ValueError(f"Agent response for {pointName} does not contain valid JSON object markers: {content}")

                            logger.debug(f"Raw Agent SDK response for {pointName}: {content}")

                            # Save response for analysis
                            self._save_api_response({
                                "prompt": prompt,
                                "response": content,
                                "model": self.model,
                                "agent_name": self.mapping_agent.name,
                                "timestamp": datetime.datetime.now().isoformat(),
                                "point_name": pointName # Add point name for easier debugging
                            })
                            
                            # Process AI response with reflection
                            mapping = self.process_ai_response(content, point)
                            
                            logger.info(f"Mapped point {pointName} to {mapping['mapping']['enosPoint']} (Status: {mapping['mapping']['status']})")

                            # Cache successful mappings
                            if mapping['mapping']['status'] == "mapped":
                                cache_key = self._generate_cache_key(pointName, device_type)
                                self._save_to_cache(cache_key, mapping['mapping']['enosPoint'], pointName, device_type)
                                
                            processed_mappings.append(mapping) # Add to list for batch analysis
                            stats["mapped"] += 1

                        except Exception as e:
                            logger.error(f"Error during AI mapping or processing of {pointName}: {str(e)}")
                            stats["errors"] += 1
                            # Create fallback mapping with error
                            fallback_enos_point = "unknown" # Default fallback
                             # Try reflection fallback (existing logic)
                            if self.enable_reflection and hasattr(self, 'reflection_system'):
                                try:
                                    suggestion = self.reflection_system.suggest_mapping(point)
                                    if suggestion.get('success') and suggestion.get('suggested_mapping'):
                                        fallback_enos_point = suggestion.get('suggested_mapping')
                                        logger.info(f"Using reflection-suggested fallback for {pointName}: {fallback_enos_point}")
                                except Exception as reflection_error:
                                    logger.warning(f"Error getting reflection fallback for {pointName}: {str(reflection_error)}")
                            
                            # Create the error mapping structure
                            mapping = {
                                "original": point,
                                "mapping": {
                                    "pointId": point.get("pointId", ""),
                                    "enosPoint": fallback_enos_point, 
                                    "status": "error",
                                    "error": str(e),
                                    "confidence": 0.1, # Low confidence for error/fallback
                                    "source": "error_fallback"
                                },
                                "reflection": {
                                    "logic_used": "error_fallback",
                                    "confidence": 0.1,
                                    "explanation": f"AI mapping failed for {pointName}: {str(e)}. Used fallback '{fallback_enos_point}'."
                                }
                            }
                            processed_mappings.append(mapping) # Add error mapping for analysis
                            
                        # Append the result (either successful mapping or error fallback) to all_mappings
                        if mapping: # Ensure mapping is not None before appending
                            all_mappings.append(mapping)
                        else:
                             logger.error(f"Mapping result was None for point {pointName}, even after error handling. Skipping.")
                             # Optionally create a different kind of error entry if needed


                        # Log progress every N points
                        if stats["total"] % 20 == 0: # Log every 20 points to reduce noise
                            current_success_rate = 0 if stats["total"] == 0 else (stats['mapped']/stats['total']*100)
                            logger.info(f"Processed {stats['mapped']}/{stats['total']} points overall ({current_success_rate:.1f}% success rate)")
                    
                    except Exception as point_error:
                        point_name_safe = point.get('pointName', '[Unknown Name]')
                        logger.error(f"Unhandled error processing point {point_name_safe}: {str(point_error)}")
                        logger.error(traceback.format_exc()) # Log traceback for unhandled errors
                        stats["total"] += 1 # Increment total even if point processing fails
                        stats["errors"] += 1
                        # Create a minimal error entry for this point
                        error_mapping = {
                            "original": point,
                             "mapping": {"pointId": point.get("pointId", ""), "status": "error", "error": f"Unhandled point processing error: {str(point_error)}", "enosPoint": "unknown"},
                             "reflection": {"explanation": f"Critical error processing point {point_name_safe}: {str(point_error)}"}
                        }
                        all_mappings.append(error_mapping)
                        processed_mappings.append(error_mapping) # Also add to processed for analysis
                        # Continue with next point

            # ... (existing batch analysis, logging, and return logic) ...

        except Exception as e:
            logger.error(f"Critical error in map_points: {str(e)}")
            logger.error(traceback.format_exc()) # Log full traceback for critical errors
            return {
                "success": False,
                "error": str(e),
                "mappings": [],
                "stats": {"total": 0, "mapped": 0, "errors": 0},
                "insights": []
            }

    # ... (rest of the class methods like _get_ai_mapping, process_ai_response, etc.) ...

    def _get_ai_mapping(self, prompt: str) -> str:
        """Get mapping from OpenAI using the Agents SDK Runner with retries."""
        for attempt in range(self.max_retries):
            try:
                self.api_calls += 1
                logger.info(f"Attempt {attempt + 1}/{self.max_retries} to get mapping via Agent SDK for prompt snippet: {prompt[:100]}...")

                # Use the Agent Runner
                result = Runner.run_sync(self.mapping_agent, prompt)

                # Extract the final output from the result
                content = result.final_output
                if not content or not isinstance(content, str):
                    raise ValueError(f"Agent returned invalid content type: {type(content)}")

                # Basic check if content looks like JSON
                if '{' not in content or '}' not in content:
                    raise ValueError(f"Agent response does not contain JSON object: {content}")

                logger.debug(f"Raw Agent SDK response: {content}")

                # Save response for analysis
                self._save_api_response({
                    "prompt": prompt,
                    "response": content,
                    "model": self.model,
                    "agent_name": self.mapping_agent.name,
                    "timestamp": datetime.datetime.now().isoformat()
                })

                return content

            except Exception as e: # Catch generic exceptions, including potential SDK errors
                logger.warning(f"Generic error during Agent SDK mapping attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"AI mapping failed after {self.max_retries} attempts (Generic Error).")
                    raise # Re-raise the last exception
                time.sleep(2 ** attempt) # Exponential backoff
                
        # Should not be reached
        raise Exception(f"AI mapping failed definitively after {self.max_retries} attempts.") 