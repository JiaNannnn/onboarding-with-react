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
import re # Import re for regular expressions
import uuid
import io

logger = logging.getLogger(__name__)

# Directory for API responses
API_RESPONSES_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'api_responses'))
API_RESPONSES_DIR.mkdir(exist_ok=True, parents=True)

# Cache directory
CACHE_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'mapper'))
CACHE_DIR.mkdir(exist_ok=True, parents=True)

MAPPING_PROMPT = """
You are an expert in mapping Building Management System (BMS) points to EnOS schema.
Below is the EnOS schema:
{
    "Chiller": {
        "shortName": "CH",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CH",
        "points": [
            "CH_raw_status",
            "CH_raw_trip",
            "CH_raw_temp_chws",
            "CH_raw_temp_chwr",
            "CH_raw_temp_evap",
            "CH_raw_power_active_total", 
            "CH_raw_energy_active_total",
            "CH_raw_sp_temp_chws",
            "CH_raw_chilled_valve_status",
            "CH_raw_cooling_valve_status",
            "CH_raw_chilled_water_flow",
            "CH_raw_cooling_water_flow",
            "CH_raw_fla",
            "CH_raw_flow_chws",
            "CH_raw_temp_cwr",
            "CH_raw_temp_cws",
            "CH_raw_temp_cond",
            "CH_raw_load_chiller"
        ]
    },
    "Chilled Water Pump":{
        "shortName": "CHWP",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CHWP",
        "points": [
            "PUMP_raw_status",
            "PUMP_raw_trip",
            "PUMP_raw_power_active_total",
            "PUMP_raw_energy_active_total",
            "PUMP_raw_flow",
            "PUMP_raw_pressure",
            "PUMP_raw_head",
            "PUMP_raw_water_flow",
            "PUMP_raw_on_off_command",
            "PUMP_raw_delta_pressure",
            "PUMP_raw_sp_delta_pressure",
            "PUMP_raw_frequency_command"
        ]
    },
    "Condenser Water Pump":{
        "shortName": "CWP",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CWP",
        "points": [
            "PUMP_raw_status",
            "PUMP_raw_trip",
            "PUMP_raw_power_active_total",
            "PUMP_raw_energy_active_total",
            "PUMP_raw_flow",
            "PUMP_raw_pressure",
            "PUMP_raw_head",
            "PUMP_raw_water_flow",
            "PUMP_raw_on_off_command",
            "PUMP_raw_delta_pressure",
            "PUMP_raw_sp_delta_pressure",
            "PUMP_raw_frequency_command",
            "PUMP_raw_power_active_total",
            "PUMP_raw_frequency"
        ]
    },
    "Cooling Tower": {
        "shortName": "CT",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CT",
        "points": [
            "CT_raw_status",
            "CT_raw_on_off_command",
            "CT_raw_trip",
            "CT_raw_temp_cwe",
            "CT_raw_temp_cwl",
            "CT_raw_valve_status_cwe",
            "CT_raw_valve_status_cwl",
            "CT_raw_power_active_total",
            "CT_raw_energy_active_total",
            "CT_raw_valve_status_cwe_command",
            "CT_raw_sp_temp_cwl",
            "CT_raw_valve_status_cwl_command"
        ]
    },
    "Chiller Plant": {
        "shortName": "CHPL",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CHPL",
        "points": [
            "CHPL_raw_load_building",
            "CHPL_raw_temp_chws_header",
            "CHPL_raw_temp_chwr_header",
            "CHPL_raw_flow_chws_header",
            "CHPL_raw_chws_pressure",
            "CHPL_raw_chwr_pressure",
            "CHPL_raw_flow_chwr_header",
            "CHPL_raw_power_active_total",
            "CHPL_raw_energy_active_total"
        ]
    },
    "Air Handing Unit": {
        "shortName": "AHU",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_AHU",
        "points": [
            "AHU_raw_status",
            "AHU_raw_trip",
            "AHU_raw_cooling_heating_mode_command",
            "AHU_raw_energy_active_total",
            "AHU_raw_ra_damper_position",
            "AHU_raw_return_air_co2",
            "AHU_raw_return_air_humidity",
            "AHU_raw_sp_ra_damper_position",
            "AHU_raw_static_pressure",
            "AHU_raw_sp_supply_air_temp",
            "AHU_raw_supply_air_fan_frequency",
            "AHU_raw_temp_chwr",
            "AHU_raw_temp_chws",
            "AHU_raw_sp_return_air_co2",
            "AHU_raw_filter_status",
            "AHU_raw_operation_mode",
            "AHU_raw_sp_return_air_temp",
            "AHU_raw_supply_air_fan_speed_command",
            "AHU_raw_valve_position",
            "AHU_raw_oa_damper_position",
            "AHU_raw_sp_static_pressure",
            "AHU_raw_return_air_temp",
            "AHU_raw_supply_air_fan_frequency_command",
            "AHU_raw_cooling_demand",
            "AHU_raw_sp_oa_damper_position",
            "AHU_raw_hw_valve_position",
            "AHU_raw_supply_air_temp",
            "AHU_raw_supply_air_fan_speed",
            "AHU_raw_return_air_fan_frequency",
            "AHU_opt_sp_supply_air_temp",
            "AHU_write_sp_return_air_temp",
            "AHU_raw_on_off_command",
            "AHU_write_sp_static_pressure",
            "AHU_opt_sp_return_air_temp",
            "AHU_stat_device_on_off",
            "AHU_write_ra_damper_position",
            "AHU_write_on_off_command",
            "AHU_write_sp_oa_damper_position",
            "AHU_opt_sp_static_pressure",
            "AHU_write_sp_return_air_co2",
            "AHU_raw_air_flow",
            "AHU_write_sp_supply_air_temp",
            "AHU_raw_mix_air_velocity2",
            "AHU_raw_mix_air_velocity1",
            "AHU_raw_mix_air_velocity4",
            "AHU_raw_mix_air_velocity3",
            "AHU_raw_power_active_total",
            "AHU_raw_outside_air_temp",
            "AHU_write_sp_supply_air_co2",
            "AHU_write_cooling_heating_mode_command",
            "AHU_raw_filter_delta_pressure",
            "AHU_raw_sp_supply_air_co2",
            "AHU_write_fan_speed",
            "AHU_ai_opt_auto_ctrl",
            "AHU_raw_sp_offcoil_temp",
            "AHU_write_sp_offcoil_temp",
            "AHU_raw_room_temp",
            "AHU_raw_return_air_temp_humidity",
            "AHU_raw_supply_air_humidity",
            "AHU_raw_off_coil_temp",
            "AHU_raw_sp_off_coil_temp",
            "AHU_ai_opt_sp_static_pressure",
            "AHU_ai_opt_sp_supply_air_temp",
            "AHU_write_sp_off_coil_temp",
            "AHU_raw_sp_room_air_temp"
        ]
    },
    "Fan Coil Unit": {
        "shortName": "FCU",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_FCU",
        "points": [
            "FCU_raw_chw_valve_status",
            "FCU_raw_cooling_heating_mode",
            "FCU_raw_cooling_heating_mode_command",
            "FCU_raw_energy_active_total",
            "FCU_raw_fan_speed",
            "FCU_raw_fan_speed_command",
            "FCU_raw_hw_valve_status", 
            "FCU_raw_local_mode",
            "FCU_raw_local_mode_command",
            "FCU_raw_on_off_command",
            "FCU_raw_power_active_total",
            "FCU_raw_sp_supply_air_co2",
            "FCU_raw_sp_zone_air_temp",
            "FCU_raw_status",
            "FCU_raw_trip",
            "FCU_raw_valve_status",
            "FCU_raw_zone_air_temp",
            "FCU_raw_zone_occupancy",
            "FCU_write_cooling_heating_mode_command",
            "FCU_write_fan_speed",
            "FCU_write_fan_speed_command",
            "FCU_write_local_mode_command",
            "FCU_write_on_off_command",
            "FCU_write_sp_supply_air_co2",
            "FCU_write_sp_zone_air_temp",
            "FCU_write_sp_zone_air_temp_command"
        ]
        
    },
    "Power Meter": {
        "shortName": "PMT",
        "enos_model": "EnOS_CITY_PMT",
        "points": [
            "PMT_raw_power_active_total",
            "PMT_raw_energy_active_total"
        ]
    },
    "Weather Station": {
        "shortName": "WST",
        "enos_model": "EnOS_CITY_WST",
        "points": [
            "WST_raw_outside_air_temp",
            "WST_raw_outside_air_humidity"
        ]
    }
}
"""

class EnOSMapper:
    # Enhance the mapping agent instructions
    _mapping_agent_instructions = """
    Map the raw BMS points to the EnOS points according to the following rules:

    1. Each BMS point must be mapped to a valid EnOS point name
    The EnOS points schema is defined in:
    {
    "Chiller": {
        "shortName": "CH",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CH",
        "points": [
            "CH_raw_status",
            "CH_raw_trip",
            "CH_raw_temp_chws",
            "CH_raw_temp_chwr",
            "CH_raw_temp_evap",
            "CH_raw_power_active_total", 
            "CH_raw_energy_active_total",
            "CH_raw_sp_temp_chws",
            "CH_raw_chilled_valve_status",
            "CH_raw_cooling_valve_status",
            "CH_raw_chilled_water_flow",
            "CH_raw_cooling_water_flow",
            "CH_raw_fla",
            "CH_raw_flow_chws",
            "CH_raw_temp_cwr",
            "CH_raw_temp_cws",
            "CH_raw_temp_cond",
            "CH_raw_load_chiller"
        ]
    },
    "Chilled Water Pump":{
        "shortName": "CHWP",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CHWP",
        "points": [
            "PUMP_raw_status",
            "PUMP_raw_trip",
            "PUMP_raw_power_active_total",
            "PUMP_raw_energy_active_total",
            "PUMP_raw_flow",
            "PUMP_raw_pressure",
            "PUMP_raw_head",
            "PUMP_raw_water_flow",
            "PUMP_raw_on_off_command",
            "PUMP_raw_delta_pressure",
            "PUMP_raw_sp_delta_pressure",
            "PUMP_raw_frequency_command"
        ]
    },
    "Condenser Water Pump":{
        "shortName": "CWP",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CWP",
        "points": [
            "PUMP_raw_status",
            "PUMP_raw_trip",
            "PUMP_raw_power_active_total",
            "PUMP_raw_energy_active_total",
            "PUMP_raw_flow",
            "PUMP_raw_pressure",
            "PUMP_raw_head",
            "PUMP_raw_water_flow",
            "PUMP_raw_on_off_command",
            "PUMP_raw_delta_pressure",
            "PUMP_raw_sp_delta_pressure",
            "PUMP_raw_frequency_command",
            "PUMP_raw_power_active_total",
            "PUMP_raw_frequency"
        ]
    },
    "Cooling Tower": {
        "shortName": "CT",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CT",
        "points": [
            "CT_raw_status",
            "CT_raw_on_off_command",
            "CT_raw_trip",
            "CT_raw_temp_cwe",
            "CT_raw_temp_cwl",
            "CT_raw_valve_status_cwe",
            "CT_raw_valve_status_cwl",
            "CT_raw_power_active_total",
            "CT_raw_energy_active_total",
            "CT_raw_valve_status_cwe_command",
            "CT_raw_sp_temp_cwl",
            "CT_raw_valve_status_cwl_command"
        ]
    },
    "Chiller Plant": {
        "shortName": "CHPL",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_CHPL",
        "points": [
            "CHPL_raw_load_building",
            "CHPL_raw_temp_chws_header",
            "CHPL_raw_temp_chwr_header",
            "CHPL_raw_flow_chws_header",
            "CHPL_raw_chws_pressure",
            "CHPL_raw_chwr_pressure",
            "CHPL_raw_flow_chwr_header",
            "CHPL_raw_power_active_total",
            "CHPL_raw_energy_active_total"
        ]
    },
    "Air Handing Unit": {
        "shortName": "AHU",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_AHU",
        "points": [
            "AHU_raw_status",
            "AHU_raw_trip",
            "AHU_raw_cooling_heating_mode_command",
            "AHU_raw_energy_active_total",
            "AHU_raw_ra_damper_position",
            "AHU_raw_return_air_co2",
            "AHU_raw_return_air_humidity",
            "AHU_raw_sp_ra_damper_position",
            "AHU_raw_static_pressure",
            "AHU_raw_sp_supply_air_temp",
            "AHU_raw_supply_air_fan_frequency",
            "AHU_raw_temp_chwr",
            "AHU_raw_temp_chws",
            "AHU_raw_sp_return_air_co2",
            "AHU_raw_filter_status",
            "AHU_raw_operation_mode",
            "AHU_raw_sp_return_air_temp",
            "AHU_raw_supply_air_fan_speed_command",
            "AHU_raw_valve_position",
            "AHU_raw_oa_damper_position",
            "AHU_raw_sp_static_pressure",
            "AHU_raw_return_air_temp",
            "AHU_raw_supply_air_fan_frequency_command",
            "AHU_raw_cooling_demand",
            "AHU_raw_sp_oa_damper_position",
            "AHU_raw_hw_valve_position",
            "AHU_raw_supply_air_temp",
            "AHU_raw_supply_air_fan_speed",
            "AHU_raw_return_air_fan_frequency",
            "AHU_opt_step",
            "AHU_opt_sp_supply_air_temp",
            "AHU_high_sap_energy_waste_5min",
            "AHU_write_sp_return_air_temp",
            "AHU_raw_on_off_command",
            "AHU_write_sp_static_pressure",
            "AHU_opt_sp_return_air_temp",
            "AHU_stat_device_on_off",
            "AHU_write_ra_damper_position",
            "AHU_write_on_off_command",
            "AHU_write_sp_oa_damper_position",
            "AHU_opt_sp_static_pressure",
            "AHU_write_sp_return_air_co2",
            "AHU_raw_air_flow",
            "AHU_write_sp_supply_air_temp",
            "AHU_raw_mix_air_velocity2",
            "AHU_raw_mix_air_velocity1",
            "AHU_raw_mix_air_velocity4",
            "AHU_raw_mix_air_velocity3",
            "AHU_raw_power_active_total",
            "AHU_raw_outside_air_temp",
            "AHU_write_sp_supply_air_co2",
            "AHU_write_cooling_heating_mode_command",
            "AHU_raw_filter_delta_pressure",
            "AHU_schedule_output",
            "AHU_raw_sp_supply_air_co2",
            "AHU_write_fan_speed",
            "AHU_ai_opt_auto_ctrl",
            "AHU_raw_sp_offcoil_temp",
            "AHU_write_sp_offcoil_temp",
            "AHU_raw_room_temp",
            "AHU_raw_return_air_temp_humidity",
            "AHU_raw_supply_air_humidity",
            "AHU_raw_off_coil_temp",
            "AHU_raw_sp_off_coil_temp",
            "AHU_ai_opt_sp_static_pressure",
            "AHU_ai_opt_sp_supply_air_temp",
            "AHU_write_sp_off_coil_temp",
            "AHU_raw_sp_room_air_temp"
        ]
    },
    "Fan Coil Unit": {
        "shortName": "FCU",
        "parent": "HVAC",
        "enos_model": "EnOS_HVAC_FCU",
        "points": [
            "FCU_raw_chw_valve_status",
            "FCU_raw_cooling_heating_mode",
            "FCU_raw_cooling_heating_mode_command",
            "FCU_raw_energy_active_total",
            "FCU_raw_fan_speed",
            "FCU_raw_fan_speed_command",
            "FCU_raw_hw_valve_status", 
            "FCU_raw_local_mode",
            "FCU_raw_local_mode_command",
            "FCU_raw_on_off_command",
            "FCU_raw_power_active_total",
            "FCU_raw_sp_supply_air_co2",
            "FCU_raw_sp_zone_air_temp",
            "FCU_raw_status",
            "FCU_raw_trip",
            "FCU_raw_valve_status",
            "FCU_raw_zone_air_temp",
            "FCU_raw_zone_occupancy",
            "FCU_write_cooling_heating_mode_command",
            "FCU_write_fan_speed",
            "FCU_write_fan_speed_command",
            "FCU_write_local_mode_command",
            "FCU_write_on_off_command",
            "FCU_write_sp_supply_air_co2",
            "FCU_write_sp_zone_air_temp",
            "FCU_write_sp_zone_air_temp_command"
        ]
        
    }
}
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

    # Revise the mapping with clearer naming
    CANONICAL_TO_PREFIX_MAP = {
        'FCU': 'FCU',
        'AHU': 'AHU',
        'VAV': 'VAV',
        'CHILLER': 'CH',
        'BOILER': 'BOIL',
        'CONDENSER WATER PUMP': 'PUMP',
        'CHILLED WATER PUMP': 'PUMP',  # Note: CHWP should map to PUMP prefix
        'HEATER WATER PUMP': 'PUMP',
        'PUMP': 'PUMP',
        'COOLING TOWER': 'CT',
        'RTU': 'RTU',
        'METER': 'METER',
        'EXHAUST_FAN': 'EF',
        'OTHER': 'UNKNOWN',
        'UNKNOWN': 'UNKNOWN'
    }

    def _get_expected_prefix_for_type(self, canonical_device_type: str) -> str:
        """Gets the expected EnOS prefix for a normalized/canonical device type."""
        if not canonical_device_type:
            logger.warning("Empty canonical device type passed to _get_expected_prefix_for_type")
            return 'UNKNOWN'
            
        # Ensure canonical_device_type is uppercase for lookup consistency
        canonical_upper = canonical_device_type.upper()
        
        # Debug log the lookup attempt
        logger.debug(f"Looking up prefix for canonical device type: '{canonical_upper}'")
        
        # Direct lookup in the map
        prefix = self.CANONICAL_TO_PREFIX_MAP.get(canonical_upper)
        
        if prefix:
            logger.debug(f"Found prefix '{prefix}' for canonical type '{canonical_upper}'")
            return prefix
        
        # Special case handling for pumps
        if 'PUMP' in canonical_upper or 'CWP' in canonical_upper or 'CHWP' in canonical_upper or 'HWP' in canonical_upper:
            logger.debug(f"Special case: '{canonical_upper}' contains pump identifier, mapping to 'PUMP'")
            return 'PUMP'
            
        # If we can't find a match, log and return UNKNOWN
        logger.warning(f"No prefix mapping found for canonical device type: '{canonical_upper}'")
        return 'UNKNOWN'

    def __init__(self):
        # Initialize OpenAI client with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1")
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
                                "type": "string"
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
    
    def _load_simplified_schema(self) -> Dict:
        """Load the simplified EnOS schema for device types and points"""
        try:
            logger.info("Loading simplified schema for device types and points")
            
            # First try the existing schema if already loaded (optimization)
            if hasattr(self, 'enos_schema') and self.enos_schema:
                logger.info("Using existing schema as simplified schema")
                self.simplified_schema = self.enos_schema
                return self.enos_schema
            
            # Try loading from simplified schema files
            possible_paths = [
                Path(__file__).parent / 'enos_simplified.json',
                Path(__file__).parent / 'enos_simlified.json',  # Handle possible typo
                Path(__file__).parent.parent.parent / 'enos_simplified.json',
                Path(__file__).parent.parent.parent / 'enos_simlified.json',
                Path(__file__).parent / 'enos.json'
            ]
            
            # Log all paths being checked
            for path in possible_paths:
                logger.info(f"Checking for simplified schema at: {path} (exists: {path.exists()})")
            
            for schema_path in possible_paths:
                if schema_path.exists():
                    try:
                        with open(schema_path, 'r', encoding='utf-8') as f:
                            raw_schema = json.load(f)
                            
                            # Process schema based on expected format
                            if isinstance(raw_schema, dict):
                                if "deviceTypes" in raw_schema:
                                    # Handle nested format
                                    schema = self._convert_schema_format(raw_schema.get("deviceTypes", {}))
                                else:
                                    # Handle direct format
                                    schema = self._convert_schema_format(raw_schema)
                                    
                                logger.info(f"Successfully loaded simplified schema with {len(schema)} device types from {schema_path}")
                                self.simplified_schema = schema
                                return schema
                    except Exception as e:
                        logger.error(f"Error loading simplified schema from {schema_path}: {str(e)}")
            
            # If no simplified schema was found, try using _load_enos_schema as fallback
            logger.info("No simplified schema found, attempting to use full EnOS schema")
            schema = self._load_enos_schema()
            
            # Store the result as simplified schema
            self.simplified_schema = schema
            return schema
            
        except Exception as e:
            logger.error(f"Failed to load simplified schema: {str(e)}")
            # Create empty simplified schema to prevent further loading attempts
            self.simplified_schema = {}
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
        """Normalize device type to match expected EnOS schema keys."""
        if not device_type:
            return 'UNKNOWN'

        # Cleaning and normalization
        device_type_clean = device_type.upper().strip()
        
        # Debug log
        logger.debug(f"Normalizing device type: '{device_type}' -> '{device_type_clean}'")
        
        # Direct mapping for common device types - exact matches first
        # Map of common abbreviations/variations to their canonical names
        type_mapping = {
            # Air handlers
            'AHU': 'AHU',
            'AIR HANDLING UNIT': 'AHU',
            
            # Fan coil units
            'FCU': 'FCU',
            'FAN COIL UNIT': 'FCU',
            
            # Chillers
            'CHILLER': 'CHILLER',
            
            # Boilers
            'BOILER': 'BOILER',
            'BOIL': 'BOILER',
            
            # Pumps - critical for prefix mapping
            'PUMP': 'PUMP',
            'CWP': 'CONDENSER WATER PUMP',
            'CONDENSER WATER PUMP': 'CONDENSER WATER PUMP',
            'CHWP': 'CHILLED WATER PUMP',  # This is the critical mapping
            'CHILLED WATER PUMP': 'CHILLED WATER PUMP',
            'HWP': 'HEATER WATER PUMP',
            'HEATER WATER PUMP': 'HEATER WATER PUMP',
            
            # Cooling towers
            'CT': 'COOLING TOWER',
            'COOLING TOWER': 'COOLING TOWER',
            
            # Other common types
            'RTU': 'RTU',
            'METER': 'METER',
            'DPM': 'METER',
            'EF': 'EXHAUST_FAN',
            'EXHAUST_FAN': 'EXHAUST_FAN',
        }
        
        # 1. Exact match lookup - most reliable
        if device_type_clean in type_mapping:
            result = type_mapping[device_type_clean]
            logger.debug(f"Exact match found for '{device_type_clean}' -> '{result}'")
            return result
            
        # 2. Handle important special cases to prevent mismatches
        # Explicitly check for pump types to avoid confusion with other types
        if device_type_clean.startswith('CHWP'):
            logger.debug(f"CHWP special case for '{device_type_clean}' -> 'CHILLED WATER PUMP'")
            return 'CHILLED WATER PUMP'
            
        if device_type_clean.startswith('CWP'):
            logger.debug(f"CWP special case for '{device_type_clean}' -> 'CONDENSER WATER PUMP'")
            return 'CONDENSER WATER PUMP'
            
        if device_type_clean.startswith('HWP'):
            logger.debug(f"HWP special case for '{device_type_clean}' -> 'HEATER WATER PUMP'")
            return 'HEATER WATER PUMP'
            
        # Critical to prevent AHU from matching CH
        if device_type_clean == 'CH' or device_type_clean.startswith('CH-'):
            logger.debug(f"CH special case for '{device_type_clean}' -> 'CHILLER'")
            return 'CHILLER'

        # 3. Pattern matching for the rest - now with more careful containment checks
        # This is potentially less reliable, so we log clearly
        for pattern, canonical in [
            ('PUMP', 'PUMP'),
            ('COOLING TOWER', 'COOLING TOWER'),
            ('CT', 'COOLING TOWER'),
            ('CHILLER', 'CHILLER'),
            ('BOILER', 'BOILER'),
            ('AHU', 'AHU'),
            ('FCU', 'FCU'),
            ('VAV', 'VAV'),
        ]:
            # Word boundary would be better, but simple containment for now
            if pattern in device_type_clean:
                logger.debug(f"Pattern match '{pattern}' in '{device_type_clean}' -> '{canonical}'")
                return canonical
        
        # No match found - return as is but normalized
        logger.warning(f"No pattern match for device type '{device_type}' -> returning '{device_type_clean}'")
        return device_type_clean
        
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
                if "pump" in point_lowercase or "cwp" in point_lowercase or "chwp" in point_lowercase or "hwp" in point_lowercase:
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
                elif "pump" in point_lowercase or "cwp" in point_lowercase or "chwp" in point_lowercase or "hwp" in point_lowercase:
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
        """Get the expected EnOS prefix for a device type"""
        if not device_type:
            return 'UNKNOWN'
            
        # Special explicit handling for CHWP to guarantee correct mapping
        if device_type.upper().strip() == 'CHWP' or 'CHWP' in device_type.upper().strip():
            logger.debug(f"Direct CHWP handling in _get_expected_enos_prefix for '{device_type}' -> 'PUMP'")
            return 'PUMP'
            
        # First normalize the device type to its canonical form
        normalized_type = self._normalize_device_type(device_type)
        logger.debug(f"Normalized '{device_type}' to '{normalized_type}'")
        
        # Then use the mapping to get the correct prefix
        prefix = self._get_expected_prefix_for_type(normalized_type)
        logger.debug(f"Final prefix for '{device_type}' via '{normalized_type}' -> '{prefix}'")
        
        return prefix
        
    def _validate_enos_format(self, enos_point: str, device_type: str = None) -> bool:
        """Validate that the EnOS point name follows the correct format and matches device type."""
        if not enos_point:
            logger.warning("Empty EnOS point name")
            return False
            
        # Special case: 'unknown' is always valid
        if enos_point == 'unknown':
            return True
            
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
        if parts[1] not in {'raw', 'calc', 'write', 'opt', 'stat', 'high', 'ai'}:
            logger.warning(f"Invalid EnOS point category: {parts[1]}")
            return False
            
        # Check if the enos_point exists in the schema for the given device type
        if hasattr(self, 'enos_schema') and self.enos_schema and device_type:
            # Normalize device type for schema lookup
            device_type_normalized = self._normalize_device_type(device_type)
            
            if device_type_normalized in self.enos_schema:
                device_points = self.enos_schema[device_type_normalized].get('points', {})
                
                # Direct check if the entire point name exists in schema
                if enos_point in device_points:
                    return True
                
                # If the point is not found directly in the schema, log a warning
                logger.warning(f"EnOS point '{enos_point}' not found in schema for device type '{device_type_normalized}'")
                
                # Even if not in schema, we'll still do basic validation below for backward compatibility
            
        # Fallback validation using measurement types
        # This is backward compatible with the old method but less restrictive
        valid_measurements = {
            'temp', 'power', 'status', 'speed', 'pressure', 'flow', 'humidity', 'position',
            'energy', 'current', 'voltage', 'frequency', 'level', 'occupancy', 'setpoint',
            'mode', 'command', 'alarm', 'damper', 'valve', 'state', 'volume', 'co2',
            'trip', 'sp', 'head', 'load', 'air', 'water', 'delta', 'offcoil', 'off_coil',
            'step', 'waste', 'demand', 'velocity', 'cooling', 'chilled', 'room', 'fan',
            'filter', 'hw', 'ra', 'oa', 'chwr', 'chws', 'cwr', 'cws', 'cwe', 'cwl',
            'evap', 'cond', 'fla', 'ctrl', 'auto', 'header', 'building', 'zone'
        }
        
        # For point names with multiple parts after the category (e.g., return_air_co2),
        # we need a more flexible approach
        measurement_valid = False
        
        # Check the third part directly
        if parts[2] in valid_measurements:
            measurement_valid = True
        # If it's a compound measurement, it might contain valid sub-parts
        elif '_' in parts[2]:
            sub_parts = parts[2].split('_')
            # Check if at least one sub-part is valid
            if any(sub_part in valid_measurements for sub_part in sub_parts):
                measurement_valid = True
                
        if not measurement_valid:
            logger.warning(f"Invalid EnOS point measurement type: {parts[2]}")
            return False
            
        return True

    def _clean_json_response(self, response: str) -> str:
        """
        Enhanced cleaning and normalizing of JSON responses from AI to handle various formatting issues.
        This method tries multiple approaches to extract valid JSON from potentially malformed responses.
        """
        if not response:
            return '{"fallback_mapping": {}}'  # Return empty object for empty responses
            
        # First, check if this is an error response that already has a valid JSON structure
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                # If it's already valid JSON with error or status fields, just return it
                if "error" in parsed or "status" in parsed:
                    # Ensure it has the fallback_mapping field for consistency
                    if "fallback_mapping" not in parsed:
                        parsed["fallback_mapping"] = {}
                    return json.dumps(parsed)
                
                # If it's a valid dictionary with mappings, return as is
                return response
        except json.JSONDecodeError:
            # Not valid JSON, proceed with cleaning
            pass
            
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
            
            # 6. Check for "Connection error" text and create a structured error
            if "connection error" in response.lower() or "network error" in response.lower():
                logger.warning(f"Detected connection error in response: {response}")
                error_resp = {
                    "error": "Connection error detected in response",
                    "status": "connection_error",
                    "fallback_mapping": {}
                }
                return json.dumps(error_resp)
            
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
            
            # When all else fails, create a fallback error response the system can handle
            logger.error(f"Unable to parse or extract valid JSON from response: {response}")
            return json.dumps({
                "error": "Failed to extract valid JSON from response",
                "status": "parsing_error",
                "fallback_mapping": {},
                "original_response": response[:200]  # Include part of the original for debugging
            })
    
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
            # Check if point is a dictionary or a string
            if not isinstance(point, dict):
                logger.warning(f"Non-dictionary point provided to process_ai_response: {type(point)}")
                # Convert string to minimal dictionary for processing
                if isinstance(point, str):
                    point_name = point
                    point = {
                        "pointName": point_name,
                        "deviceType": self._infer_device_type_from_name(point_name) or "UNKNOWN",
                        "pointId": ""
                    }
                else:
                    # If it's neither a dict nor a string, create a dummy point
                    point = {
                        "pointName": "unknown",
                        "deviceType": "UNKNOWN",
                        "pointId": ""
                    }
                reason = self.REASON_FALLBACK
                explanation = "Invalid point data format"
            
            # Get point name for logging (safely)
            point_name = point.get('pointName', 'unknown')
            
            # Print raw response for debugging
            logger.info(f"Raw AI response for point '{point_name}': {response}")
            
            # Check for missing device type and try to infer it
            if not point.get('deviceType'):
                # Extract device type from point name
                inferred_device_type = self._infer_device_type_from_name(point_name)
                point['deviceType'] = inferred_device_type
                logger.info(f"Inferred deviceType '{inferred_device_type}' from pointName '{point_name}'")
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
        """Map points with device context awareness, batch processing, and reflection capabilities."""
        stats = {"total": 0, "mapped": 0, "unmapped": 0, "errors": 0} # Added unmapped
        all_mappings_results = [] # Changed name for clarity
        pattern_insights = [] # Renamed for clarity
        BATCH_SIZE_LIMIT = 100 # Define a max number of points per LLM call

        # Ensure schema is loaded once before processing points
        if not hasattr(self, 'enos_schema') or not self.enos_schema: # Corrected check
            logger.info("Schema not loaded in instance, attempting to load...")
            self.enos_schema = self._load_enos_schema() # Corrected assignment
            if not self.enos_schema:
                logger.error("Failed to load EnOS schema. Cannot proceed with mapping.")
                return {
                     "success": False,
                     "error": "EnOS Schema not loaded",
                    "mappings": [],
                     "stats": stats,
                    "insights": []
                }

        try:
            # Group points by a composite key of deviceType and deviceId for uniqueness context
            points_by_device = {}
            for point in points:
                if not isinstance(point, dict):
                     logger.warning(f"Skipping invalid point data (not a dict): {point}")
                     stats["errors"] += 1
                     continue

                device_type = point.get('deviceType')
                point_name = point.get('pointName', '')
                point_id = point.get('pointId', point_name)
                device_id = point.get('deviceId', 'UNKNOWN_DEVICE_ID') # Use a default if missing

                if not point_id:
                     logger.warning(f"Skipping point missing 'pointId' or 'pointName': {point}")
                     stats["errors"] += 1
                     continue

                if not device_type:
                    device_type = self._infer_device_type_from_name(point_name)
                if not device_type or device_type == 'UNKNOWN':
                    device_type = self._fallback_device_type_extraction(point_name) or 'UNKNOWN'
                
                device_type_upper = str(device_type).upper()
                device_key = f"{device_type_upper}_{device_id}" # Composite key

                # Standardize point structure before grouping
                standardized_point = {
                    "pointId": point_id,
                    "pointName": point_name,
                    "deviceType": device_type_upper,
                    "deviceId": device_id,
                    "pointType": point.get('pointType', 'unknown'),
                    "unit": point.get('unit'),
                    "description": point.get('description'),
                    "presentValue": point.get('value', point.get('presentValue'))
                }

                if device_key not in points_by_device:
                    points_by_device[device_key] = []
                points_by_device[device_key].append(standardized_point)

            # Process points group by group (device instance)
            for device_key, device_points in points_by_device.items():
                device_type = device_points[0]['deviceType'] # Get type from first point in group
                device_id_val = device_points[0]['deviceId'] # Get ID from first point
                logger.info(f"Processing mapping for device: {device_key} ({len(device_points)} points)")
                
                # --- Batching for large devices --- 
                for i in range(0, len(device_points), BATCH_SIZE_LIMIT):
                    batch_points = device_points[i:i+BATCH_SIZE_LIMIT]
                    batch_number = (i // BATCH_SIZE_LIMIT) + 1
                    logger.info(f"  Processing batch {batch_number} for device {device_key} ({len(batch_points)} points)")
                    stats["total"] += len(batch_points) # Increment total stat here per batch
                    
                    # Get device type from the first point for consistency within the batch
                    # Ensure device_type is treated as string
                    device_type = str(batch_points[0]['deviceType']) if batch_points else 'UNKNOWN'
                    device_id_val = str(batch_points[0]['deviceId']) if batch_points else 'UNKNOWN_DEVICE_ID'
                    
                    # Normalize device type for schema lookup and prompt context
                    device_type_normalized = self._normalize_device_type(device_type)
                    logger.debug(f"Normalized device type for batch {device_key}-{batch_number}: '{device_type}' -> '{device_type_normalized}'")

                    # --- Construct Batch Prompt ---
                    prompt_lines = [
                        f"Device Type: {device_type_normalized}", # Use normalized type
                        f"Device ID: {device_id_val}"
                    ]

                    # Add Reference EnOS Points section - Get the correct prefix for this type
                    expected_prefix = self._get_expected_prefix_for_type(device_type_normalized)
                    reference_points_added = False
                    candidate_points_list = []

                    # Find the schema entry matching the normalized type OR the expected prefix
                    # This helps find points even if normalization isn't perfect
                    schema_device_entry = None
                    if self.enos_schema:
                         if device_type_normalized in self.enos_schema:
                             schema_device_entry = self.enos_schema[device_type_normalized]
                         else:
                             # Fallback: Try finding a schema entry by expected prefix if direct normalized match fails
                             # (e.g., if normalized type is 'CHILLED WATER PUMP' but schema only has 'PUMP')
                             # This part might need refinement based on exact schema structure
                             for name, entry in self.enos_schema.items():
                                  # Check if canonical name or shortName matches expected prefix logic
                                  canonical_prefix = self._get_expected_prefix_for_type(name)
                                  short_name = entry.get("shortName", "").upper()
                                  short_name_prefix = self._get_expected_prefix_for_type(short_name) if short_name else 'UNKNOWN'

                                  if canonical_prefix == expected_prefix or short_name_prefix == expected_prefix:
                                      logger.debug(f"Using schema entry '{name}' as reference for prefix '{expected_prefix}'")
                                      schema_device_entry = entry
                                      break # Use the first match based on prefix

                    if schema_device_entry:
                        candidate_points_dict = schema_device_entry.get("points", {})
                        candidate_points_list = list(candidate_points_dict.keys())
                        if candidate_points_list:
                            prompt_lines.append(f"\\nReference EnOS Points for {device_type_normalized} (prefix: {expected_prefix}):")
                            prompt_lines.append("(Map relevant BMS points to ONE of these standard points OR 'unknown'. Multiple BMS points CAN map to the same reference point if appropriate.)") # Relaxed uniqueness
                            prompt_lines.extend([f"- {p}" for p in candidate_points_list])
                            reference_points_added = True
                        else:
                            logger.warning(f"Schema entry found for '{device_type_normalized}', but it has no 'points'.")

                    if not reference_points_added:
                         prompt_lines.append(f"\\nNo relevant Reference EnOS Points found in schema for Device Type '{device_type_normalized}' (Expected Prefix: '{expected_prefix}'). Map all points to 'unknown'.")


                    # Add BMS Points section with more context
                    prompt_lines.append("\\nBMS Points to Map:")
                    bms_points_for_prompt = []
                    for p in batch_points:
                         # Skip None values
                         if p is None:
                             logger.warning("Skipping None point in batch_points")
                             continue
                             
                         # Include relevant details for better semantic matching
                         point_info = {
                             "pointId": p.get("pointId"),
                             "pointName": p.get("pointName"),
                             "pointType": p.get("pointType"),
                             "unit": p.get("unit"),
                             "description": p.get("description", "")[:100] if p.get("description") is not None else "", # Limit description length
                             # Optional: Include presentValue if it helps semantic meaning (e.g., for binary status)
                             # "presentValue": str(p.get("presentValue"))[:50]
                         }
                         # Filter out None values explicitly
                         bms_points_for_prompt.append({k: v for k, v in point_info.items() if v is not None})
                    prompt_lines.append(json.dumps(bms_points_for_prompt, indent=2)) # Add points as JSON list

                    # Final Instruction - emphasize mapping to reference points or unknown
                    prompt_lines.append("\\nBased on the BMS Point details and the Reference EnOS Points, provide the mapping. Respond ONLY with a single JSON object where keys are input 'pointId's and values are the mapped Reference EnOS points (or 'unknown' if no suitable reference point exists).")

                    prompt = "\\n".join(prompt_lines)
                    # --- End Batch Prompt Construction ---
                    
                    # --- AI Call for Batch --- 
                    batch_mappings = {} # To store results like {"pointId1": "enosPoint1", "pointId2": "unknown", ...}
                    ai_call_failed = False
                    error_message = "Unknown AI call error"
                    content = None # Initialize content
                    
                    try:
                        logger.debug(f"Running Agent for batch: {device_key}, batch {batch_number}")
                        result = Runner.run_sync(self.mapping_agent, prompt)
                        content = result.final_output

                        if not isinstance(content, str):
                            raise ValueError(f"Agent returned non-string content type: {type(content)}")
                        
                        logger.debug(f"Raw Agent SDK response for batch {device_key}-{batch_number}: {content}")
                        self._save_api_response({ # Log response before processing
                            "prompt": prompt, "response": content, "model": self.model,
                            "agent_name": self.mapping_agent.name, "timestamp": datetime.datetime.now().isoformat(),
                            "device_key": device_key, "batch_number": batch_number
                        })
                        
                        # Check if response contains a connection error
                        try:
                            parsed_response = json.loads(content)
                            if isinstance(parsed_response, dict) and parsed_response.get("status") == "connection_error":
                                logger.warning(f"Connection error detected in agent response: {parsed_response.get('error')}")
                                ai_call_failed = True
                                error_message = f"Connection error: {parsed_response.get('error', 'Unknown connection issue')}"
                                batch_mappings = {p['pointId']: "unknown" for p in batch_points}
                                # Skip further processing since we detected a connection error
                                raise ValueError(error_message)
                        except json.JSONDecodeError:
                            # Not a JSON error response, continue normal processing
                            pass
                        
                        # Clean and parse the batch response (expects a dict)
                        cleaned_content = self._clean_json_response(content)
                        try:
                            parsed_content = json.loads(cleaned_content)
                            
                            # Check if this is an error response with fallback_mapping
                            if isinstance(parsed_content, dict) and "status" in parsed_content:
                                if parsed_content.get("status") in ["connection_error", "parsing_error"]:
                                    logger.warning(f"Error status in response: {parsed_content.get('status')} - {parsed_content.get('error')}")
                                    ai_call_failed = True
                                    error_message = parsed_content.get('error', 'Unknown error in response')
                                    
                                    # Check if there's a fallback mapping we can use
                                    if "fallback_mapping" in parsed_content and isinstance(parsed_content["fallback_mapping"], dict):
                                        batch_mappings = parsed_content["fallback_mapping"]
                                        # If empty, create default unknown mappings for all points
                                        if not batch_mappings:
                                            batch_mappings = {p['pointId']: "unknown" for p in batch_points}
                                    else:
                                        # Default to unknown for all points
                                        batch_mappings = {p['pointId']: "unknown" for p in batch_points}
                                    
                                    # Skip further processing for this batch
                                    raise ValueError(error_message)
                                # If it's a valid mapping response, use it directly
                                else:
                                    batch_mappings = parsed_content
                            else:
                                # Normal case - parsed content is the mappings
                                batch_mappings = parsed_content
                                
                            if not isinstance(batch_mappings, dict):
                                raise ValueError("LLM response was not a dictionary as expected.")
                        except json.JSONDecodeError as je:
                            logger.error(f"JSON decoding error in batch {device_key}-{batch_number}: {str(je)}")
                            ai_call_failed = True
                            error_message = f"JSON parsing failed: {str(je)}"
                            batch_mappings = {p['pointId']: "unknown" for p in batch_points}

                    except Exception as ai_call_error:
                        logger.error(f"Error during AI call or initial parsing for batch {device_key}-{batch_number}: {str(ai_call_error)}\n{traceback.format_exc()}")
                        ai_call_failed = True
                        error_message = f"AI call/parsing failed: {str(ai_call_error)}" # Store error message
                        # For a failed batch, all points in it will be marked as error
                        batch_mappings = {p['pointId']: "error_state" for p in batch_points} # Use a placeholder

                    # --- Process Results for Each Point in Batch --- 
                    used_enos_points_in_batch = set() # Track usage within this batch response
                    for point in batch_points:
                        point_id = point['pointId']
                        enos_point_result = "unknown" # Default
                        mapping_status = "error" # Default status
                        final_explanation = error_message if ai_call_failed else "Processing error"
                        final_reason = self.REASON_FALLBACK
                        mapping_success = False
                        quality_score = 0.0
                        source = "ai_call_error" if ai_call_failed else "processing_error"

                        if not ai_call_failed:
                            try:
                                # Get the mapping from the LLM's batch response dict
                                enos_point_llm = batch_mappings.get(point_id)
                                
                                if enos_point_llm is None:
                                    logger.warning(f"LLM response missing mapping for pointId {point_id} in batch {device_key}-{batch_number}. Treating as unknown.")
                                    enos_point_result = "unknown"
                                    final_explanation = "Mapping missing in LLM batch response."
                                elif not isinstance(enos_point_llm, str) or not enos_point_llm.strip():
                                    logger.warning(f"LLM returned invalid/empty mapping for pointId {point_id}: '{enos_point_llm}'. Treating as unknown.")
                                    enos_point_result = "unknown"
                                    final_explanation = "Invalid/empty mapping from LLM."
                                else:
                                    enos_point_llm = enos_point_llm.strip()
                                    
                                    # Validate the format from LLM
                                    if self._validate_enos_format(enos_point_llm, device_type):
                                        # Check uniqueness constraint within this batch response
                                        if enos_point_llm != "unknown":
                                            if enos_point_llm in used_enos_points_in_batch:
                                                 logger.warning(f"Duplicate EnOS point '{enos_point_llm}' detected for point {point_id} (used by another point in this batch). Mapping to unknown.")
                                                 enos_point_result = "unknown"
                                                 final_explanation = f"Duplicate assignment of '{enos_point_llm}' by LLM within batch."
                                            else:
                                                 # Valid, unique mapping found
                                                 enos_point_result = enos_point_llm
                                                 used_enos_points_in_batch.add(enos_point_llm)
                                                 mapping_success = True
                                                 source = "llm_agent"
                                                 # Evaluate quality if mapping is not unknown
                                                 quality_score, final_reason, final_explanation = self._evaluate_mapping_quality(enos_point_result, point)
                                        else:
                                            # LLM explicitly returned unknown
                                            enos_point_result = "unknown"
                                            mapping_success = False # Explicit unknown is not an error, but not mapped
                                            source = "llm_agent"
                                            quality_score, final_reason, final_explanation = self._evaluate_mapping_quality(enos_point_result, point)
                                            
                                    else:
                                        logger.warning(f"Invalid format '{enos_point_llm}' from LLM for point {point_id}. Treating as unknown.")
                                        enos_point_result = "unknown"
                                        final_explanation = f"Invalid format '{enos_point_llm}' from LLM."
                            
                            except Exception as process_err:
                                 logger.error(f"Error processing LLM result for point {point_id}: {str(process_err)}\n{traceback.format_exc()}")
                                 enos_point_result = "unknown"
                                 final_explanation = f"Error processing LLM result: {str(process_err)}" 
                        
                        # Determine final status based on result
                        if enos_point_result == "unknown":
                            mapping_status = "unmapped"
                            stats["unmapped"] += 1
                        elif mapping_success:
                             mapping_status = "mapped"
                             stats["mapped"] += 1
                        else:
                             # Errors that result in unknown are counted here
                            mapping_status = "error"
                            stats["errors"] += 1

                        # Construct the final mapping dictionary for this point
                        mapping_dict = {
                            "original": point,
                                    "mapping": {
                                "pointId": point_id,
                                "enosPoint": enos_point_result,
                                "status": mapping_status,
                                "confidence": quality_score,
                                "source": source,
                                "error": final_explanation if mapping_status == 'error' else None
                                    },
                                    "reflection": {
                                "quality_score": quality_score,
                                "reason": final_reason,
                                "explanation": final_explanation,
                                "success": mapping_success and enos_point_result != "unknown"
                            }
                        }
                        
                        all_mappings_results.append(mapping_dict)
                        self._log_mapping_reflection(point, enos_point_result, quality_score, final_reason, final_explanation, mapping_dict["reflection"]["success"])

                    # --- End Point Processing in Batch --- 

                    # --- Add Delay Between Batches --- 
                    # Introduce a small delay to avoid hitting API rate limits
                    logger.debug(f"Finished processing batch {batch_number} for {device_key}. Pausing briefly...")
                    time.sleep(1.1) # Sleep for 1.1 seconds to stay under ~60 reqs/min limit

                # --- End Batch Loop --- 

            # --- End Device Group Loop --- 

            # --- Final Return --- 
            logger.info(f"Mapping finished. Final Stats: Total={stats['total']}, Mapped={stats['mapped']}, Unmapped={stats['unmapped']}, Errors={stats['errors']}")
            final_success_status = stats["errors"] == 0 and stats["total"] > 0 # Consider success if points processed and no errors
            return {
                "success": final_success_status,
                "mappings": all_mappings_results,
                "stats": stats,
                "insights": pattern_insights # Include collected insights
            }

        except Exception as critical_error:
            logger.error(f"Critical error in map_points execution: {str(critical_error)}\n{traceback.format_exc()}")
            # Ensure total count reflects input if crash happens early
            if stats["total"] == 0: stats["total"] = len(points)
            stats["errors"] = stats["total"] - stats["mapped"] - stats["unmapped"] # Assign remaining as errors
            return {
                "success": False,
                "error": f"Critical mapping failure: {str(critical_error)}",
                "mappings": all_mappings_results, # Return any partial mappings
                "stats": stats,
                "insights": pattern_insights
            }

    def _fallback_device_type_extraction(self, point_name: str) -> Optional[str]:
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

    def _fallback_device_type_extraction(self, point_name: str) -> str:
        """Fallback method to extract device type from point name when other methods fail."""
        # Try to infer device type from the point name
        if not point_name:
            return "UNKNOWN"
        
        # Common device prefixes in BMS systems
        device_prefixes = {
            "AHU": "AHU",
            "VAV": "VAV",
            "CH": "CH-SYS",
            "CHPL": "CHILLER PLANT",
            "CHILLER": "CH-SYS",
            "FCU": "FCU",
            "HX": "HEATEXCHANGER",
            "CWP": "CONDENSER WATER PUMP",
            "HWP": "HEATER WATER PUMP",
            "CHWP": "CHILLED WATER PUMP",
            "CT": "COOLING TOWER",
            "COOLING-TOWER": "CT",
            "BLR": "BOILER",
            "BOILER": "BOILER",
            "FAN": "FAN",
            "METER": "METER",
            "PMT": "POWER METER"
        }
        
        # Check for prefixes in the point name
        point_upper = point_name.upper()
        for prefix, device_type in device_prefixes.items():
            if point_upper.startswith(prefix) or f".{prefix}" in point_upper or f"-{prefix}" in point_upper:
                return device_type
        
        # If no matching prefix, try more general inference
        if "TEMP" in point_upper or "TMP" in point_upper:
            return "SENSOR" 
        if "PRESS" in point_upper or "PRS" in point_upper:
            return "SENSOR"
        if "FLOW" in point_upper or "FLW" in point_upper:
            return "SENSOR"
        if "PWR" in point_upper or "POWER" in point_upper or "KW" in point_upper:
            return "METER"
        if "ENERGY" in point_upper or "KWH" in point_upper:
            return "METER"
        
        # Default to unknown if no pattern matches
        return "UNKNOWN"
        
    def _extract_device_type_from_name(self, point_name: str) -> str:
        """Extract device type from a point name."""
        if not point_name:
            return ""
            
        # Try to extract device type from common patterns
        # Pattern: DeviceType-Number (e.g., AHU-1, VAV-305)
        pattern1 = re.match(r'^([A-Za-z\-]+)[\-\.]?(\d+)', point_name)
        if pattern1:
            device_prefix = pattern1.group(1).upper()
            # Map common prefixes to standardized device types
            device_map = {
                "AHU": "AHU",
                "VAV": "VAV",
                "FCU": "FCU",
                "CHILLER": "CH-SYS",
                "CH": "CH-SYS",
                "CWP": "CONDENSER WATER PUMP",
                "HWP": "HEATER WATER PUMP",
                "CHWP": "CHILLED WATER PUMP",
                "CT": "COOLING TOWER",
                "PMT": "POWER METER"
            }
            
            for prefix, device_type in device_map.items():
                if device_prefix == prefix:
                    return device_type
            
            # If not in map but looks like a valid device type, return the prefix
            if re.match(r'^[A-Z]{2,}$', device_prefix):
                return device_prefix
                
        # Pattern: Device.Point (e.g., AHU.SupplyTemp)
        pattern2 = re.match(r'^([A-Za-z\-]+)\.', point_name)
        if pattern2:
            device_prefix = pattern2.group(1).upper()
            # Use the same mapping as above
            device_map = {
                "AHU": "AHU",
                "VAV": "VAV",
                "FCU": "FCU",
                "CHILLER": "CH-SYS",
                "CH": "CH-SYS",
                "CWP": "CONDENSER WATER PUMP",
                "HWP": "HEATER WATER PUMP",
                "CHWP": "CHILLED WATER PUMP",
                "CT": "COOLING TOWER"
            }
            
            for prefix, device_type in device_map.items():
                if device_prefix == prefix:
                    return device_type
                    
            # Return prefix if it looks like a valid device type
            if re.match(r'^[A-Z]{2,}$', device_prefix):
                return device_prefix
        
        # If no pattern matches, return empty string
        return ""
        
    def export_mappings(self, mappings_data: List[Dict], include_unmapped: bool = True) -> List[Dict]:
        """
        Export mappings to a standard format for EnOS, including unmapped points with fallback names.
        
        This method processes both mapped and unmapped points for export. For unmapped points,
        it creates standardized fallback names based on device type and point name patterns.
        
        Args:
            mappings_data: List of mapping entries from map_points output
            include_unmapped: Whether to include unmapped points in the export
            
        Returns:
            List of export-ready mapping records
        """
        if not mappings_data:
            return []
            
        # Format for EnOS export
        export_data = []
        unmapped_export_data = []
        
        # Process each mapping entry
        for entry in mappings_data:
            try:
                # Skip invalid entries
                if not isinstance(entry, dict) or "original" not in entry or "mapping" not in entry:
                    logger.warning(f"Skipping invalid mapping entry: {entry}")
                    continue
                    
                original = entry.get("original", {})
                mapping = entry.get("mapping", {})
                status = mapping.get("status", "unmapped")
                
                # Basic validation
                if not original.get("pointId") or not original.get("pointName"):
                    logger.warning(f"Skipping entry with missing pointId or pointName: {original}")
                    continue
                
                # Create export record
                export_record = {
                    "pointId": original.get("pointId", ""),
                    "pointName": original.get("pointName", ""),
                    "deviceId": original.get("deviceId", ""),
                    "deviceType": original.get("deviceType", "UNKNOWN"),
                    "pointType": original.get("pointType", ""),
                    "unit": original.get("unit", ""),
                    "enosPoint": mapping.get("enosPoint", ""),
                    "status": status,
                    "confidence": mapping.get("confidence", 0)
                }
                
                # Add to appropriate list
                if status == "mapped" and export_record["enosPoint"]:
                    export_data.append(export_record)
                elif include_unmapped:
                    # For unmapped points, set a default EnOS point name if empty
                    if not export_record["enosPoint"]:
                        # Get device type prefix
                        device_type = original.get("deviceType", "").upper()
                        prefix = self._get_expected_enos_prefix(device_type)
                        
                        if not prefix or prefix == "UNKNOWN":
                            # Try to extract from point name if device type is unknown
                            extracted_type = self._extract_device_type_from_name(original.get("pointName", ""))
                            if extracted_type:
                                prefix = self._get_expected_enos_prefix(extracted_type)
                        
                        # Final fallback to UNKNOWN
                        if not prefix:
                            prefix = "UNKNOWN"
                            
                        # Create a fallback mapping based on point name and device type
                        point_name = original.get("pointName", "")
                        
                        # Clean up the point name
                        # First remove device prefix if present (e.g., "AHU1." from "AHU1.SupplyTemp")
                        point_suffix = point_name
                        pattern = re.match(r'^[A-Za-z]+-?\d+\.(.+)$', point_name)
                        if pattern:
                            point_suffix = pattern.group(1)
                        
                        # Then normalize the remaining point name
                        point_suffix = point_suffix.replace(" ", "_").replace(".", "_").replace("-", "_").lower()
                        
                        # Limit length and ensure valid characters
                        point_suffix = re.sub(r'[^a-z0-9_]', '', point_suffix)
                        if len(point_suffix) > 30:
                            point_suffix = point_suffix[:30]
                        
                        # Create the fallback mapping
                        export_record["enosPoint"] = f"{prefix}_raw_{point_suffix}"
                        export_record["status"] = "unmapped_exported"
                        export_record["confidence"] = 0.1  # Low confidence for fallback mappings
                        
                    unmapped_export_data.append(export_record)
            except Exception as entry_error:
                logger.warning(f"Error processing export entry: {str(entry_error)}\n{traceback.format_exc()}")
                continue
        
        # Combine mapped and unmapped data
        if include_unmapped:
            all_export_data = export_data + unmapped_export_data
        else:
            all_export_data = export_data
            
        # Log export stats
        logger.info(f"Export complete. Total: {len(all_export_data)}, Mapped: {len(export_data)}, Unmapped: {len(unmapped_export_data)}")
            
        return all_export_data