"""
BMS测点到EnOS Schema的LLM驱动映射引擎

这个模块实现了基于大型语言模型(LLM)的BMS测点映射逻辑，
利用语义理解能力处理各种BMS命名约定，同时确保输出格式符合EnOS schema规范。
"""

import os
import json
import time
import logging
import re
import random
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from openai import OpenAI
from agents import Agent, Runner

# 配置日志
logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'llm_mapper'))
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# API响应目录
API_RESPONSES_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'api_responses'))
API_RESPONSES_DIR.mkdir(exist_ok=True, parents=True)

# 增强的映射提示模板
ENHANCED_MAPPING_PROMPT = """
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

Format requirements:
1. DEVICE_TYPE must be "{device_type}" or its standard abbreviation.
2. CATEGORY must be "raw" or "calc" or "write"
3. MEASUREMENT_TYPE must be one of: temp, power, status, speed, pressure, flow, 
   humidity, position, energy, current, voltage, frequency, level, occupancy, 
   setpoint, mode, command, alarm, damper, valve, state, volume, trip
4. POINT can include additional context for the specific point

Specific mapping rules for different device types:
1. For FCU (Fan Coil Unit):
   - Points containing "Trip" or "TripStatus" or "FAIL" should map to "FCU_raw_trip"
   - Points related to valve status should map to "FCU_raw_chw_valve_status" or "FCU_raw_hw_valve_status"
   - Temperature points should map to "FCU_raw_zone_air_temp"
   - Temperature setpoints should map to "FCU_write_sp_zone_air_temp"
   - Fan speed related points should map to "FCU_raw_fan_speed" 
   - Mode related points should map to "FCU_raw_cooling_heating_mode"

2. For AHU (Air Handling Unit):
   - Trip related points should map to "AHU_raw_trip"
   - Supply air temperature should map to "AHU_raw_temp_sa"
   - Return air temperature should map to "AHU_raw_temp_ra"
   - Status points should map to "AHU_raw_status"
   - Damper related points should map to "AHU_raw_ra_damper_position"

3. For Chillers (CH):
   - Supply water temperature points should map to "CH_raw_temp_chws"
   - Return water temperature points should map to "CH_raw_temp_chwr"
   - Trip related points should map to "CH_raw_trip"
   - Status points should map to "CH_raw_status"
   - Load related points should map to "CH_raw_load_ratio"

4. For ENERGY/POWER:
   - Power consumption (kW) points should map to "ENERGY_raw_power_total"
   - Energy consumption (kWh) points should map to "ENERGY_raw_energy_total"
   - Cooling water pump power points should map to "ENERGY_raw_power_cwp"

5. For Header (HEADER):
   - Temperature points containing "st" or "supply" should map to "HEADER_raw_temp_supply"
   - Temperature points containing "rt" or "return" should map to "HEADER_raw_temp_return"
   - Flow points containing "flow" or "gpm" should map to "HEADER_raw_flow"
   - Pressure points should map to "HEADER_raw_pressure"
   - Differential temperature (dt) should map to "HEADER_raw_temp_diff"
   - Valve position points should map to "HEADER_raw_valve_pos"

6. For other device types like MKP:
   - Trip/Fail/Fault points should map to "MKP_raw_trip"
   - Status points should map to "MKP_raw_status"
   - Temperature points should map to "MKP_raw_temp"

BMS naming conventions:
- Temperature points often use "temp", "tmp", "temperature", "st" (supply temp), "rt" (return temp), "dt" (differential temp)
- Status points often use "status", "state", "on", "off"
- Power points may include "kW", "power", "demand"
- Energy points may include "kWh", "energy", "consumption"
- Flow points may include "flow", "cfm", "gpm"
- Trip/fault points often include "trip", "tripstatus", "alarm", "fault", "fail"

IMPORTANT: Always check the point name carefully to identify its function.
- For trip/alarm/fault/fail points, always map to the appropriate _raw_trip point type for the device.
- For temperature points, identify if it's supply (st), return (rt), or zone temperature.
- For flow points, use the appropriate _raw_flow mapping.

Return ONLY a valid JSON object containing the mapped EnOS point with the following structure:
{{
    "enos_point": "DEVICE_TYPE_CATEGORY_MEASUREMENT_TYPE_POINT"
}}
Do not include any other text, explanations, or formatting outside the JSON object.
"""

class LLMMapper:
    """
    基于LLM的BMS测点映射引擎
    
    使用大型语言模型的语义理解能力将BMS测点映射到EnOS schema,
    同时确保输出格式的一致性和正确性。
    """
    
    # 代理指令
    _mapping_agent_instructions = """You are an expert in mapping Building Management System (BMS) points to EnOS schema.
    
    Pay special attention to point types:
    - For FCU (Fan Coil Unit): Points with "Trip", "TripStatus", or "FAIL" should map to "FCU_raw_trip"
    - For AHU (Air Handling Unit): Points with "Trip", "Fault", or "FAIL" should map to "AHU_raw_trip" 
    - For Chillers (CH): Points with "Trip", "Fault", or "FAIL" should map to "CH_raw_trip"
    - For MKP: Points with "FAIL" or "Fault" should map to "MKP_raw_trip" not "MKP_raw_status"
    - For Header (HEADER): 
        - Temperature points with "st" should map to "HEADER_raw_temp_supply"
        - Temperature points with "rt" should map to "HEADER_raw_temp_return"
        - Temperature points with "dt" should map to "HEADER_raw_temp_diff"
        - Flow points with "flow" or "gpm" should map to "HEADER_raw_flow"
    - For all devices: Alarm/fault/fail points typically map to device_raw_trip
    
    IMPORTANT: You must respond with a valid JSON containing ONLY the 'enos_point' field.
    Example: {"enos_point": "AHU_raw_temp_rt"}
    Do not include ANY explanations, markdown formatting, or text outside the JSON object."""