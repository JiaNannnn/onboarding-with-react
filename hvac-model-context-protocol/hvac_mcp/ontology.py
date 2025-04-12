"""
Ontology Module.

This module defines the ontology loader and manager for the HVAC Model Context Protocol.
It provides access to the hierarchical representation of HVAC systems, components, and relationships.
"""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default ontology as inline constant for initial implementation
DEFAULT_ONTOLOGY = {
    "version": "1.0.0",
    "systems": {
        "chiller_plant": {
            "id": "CH-SYS",
            "name": "Chiller Plant",
            "components": {
                "chiller": {"id": "CH", "name": "Chiller"},
                "chilled_water_pump": {"id": "CWP", "name": "Chilled Water Pump"},
                "condenser_water_pump": {"id": "CDWP", "name": "Condenser Water Pump"},
                "cooling_tower": {"id": "CT", "name": "Cooling Tower"}
            }
        },
        "boiler_plant": {
            "id": "BLR-SYS",
            "name": "Boiler Plant",
            "components": {
                "boiler": {"id": "BLR", "name": "Boiler"},
                "hot_water_pump": {"id": "HWP", "name": "Hot Water Pump"}
            }
        },
        "air_handling_unit": {
            "id": "AHU",
            "name": "Air Handling Unit",
            "components": {
                "supply_fan": {"id": "SF", "name": "Supply Fan"},
                "return_fan": {"id": "RF", "name": "Return Fan"},
                "cooling_coil": {"id": "CC", "name": "Cooling Coil"},
                "heating_coil": {"id": "HC", "name": "Heating Coil"},
                "filter": {"id": "FLTR", "name": "Filter"},
                "mixed_air_damper": {"id": "MAD", "name": "Mixed Air Damper"},
                "outside_air_damper": {"id": "OAD", "name": "Outside Air Damper"}
            }
        },
        "exhaust_system": {
            "id": "EF",
            "name": "Exhaust Fan",
            "components": {}
        },
        "variable_air_volume": {
            "id": "VAV",
            "name": "Variable Air Volume",
            "components": {
                "zone_damper": {"id": "ZD", "name": "Zone Damper"},
                "reheat_coil": {"id": "RHC", "name": "Reheat Coil"}
            }
        },
        "fan_coil_unit": {
            "id": "FCU",
            "name": "Fan Coil Unit",
            "components": {
                "fan": {"id": "FAN", "name": "Fan"},
                "coil": {"id": "COIL", "name": "Coil"}
            }
        },
        "zone_controls": {
            "id": "ZC",
            "name": "Zone Controls",
            "components": {}
        }
    },
    "relationships": {
        "upstream_downstream": [
            {"upstream": "CH-SYS", "downstream": "AHU.CC"},
            {"upstream": "BLR-SYS", "downstream": "AHU.HC"},
            {"upstream": "BLR-SYS", "downstream": "VAV.RHC"},
            {"upstream": "AHU", "downstream": "VAV"}
        ],
        "cross_system": [
            {"system": "HVAC", "related_system": "Electrical", "interface": "VFD control, power monitoring"},
            {"system": "HVAC", "related_system": "Lighting", "interface": "Occupancy sharing, schedule coordination"},
            {"system": "HVAC", "related_system": "Security", "interface": "Door position status, occupancy integration"},
            {"system": "HVAC", "related_system": "Fire Safety", "interface": "Smoke control dampers, emergency mode"}
        ]
    },
    "point_types": {
        "sensor_analog": {
            "id": "SA",
            "name": "Sensor Analog",
            "examples": ["Temperature", "Pressure", "Flow", "Humidity", "CO2 Level"]
        },
        "sensor_binary": {
            "id": "SB",
            "name": "Sensor Binary",
            "examples": ["Status On/Off", "Occupancy Detected/Undetected", "Filter Dirty/Clean"]
        },
        "setpoint_command": {
            "id": "CMD",
            "name": "Setpoint Command",
            "examples": ["Temperature Setpoint", "Damper Position Command"]
        },
        "status_feedback": {
            "id": "STAT",
            "name": "Status Feedback",
            "examples": ["Pump Running/Stopped", "Valve Open/Closed"]
        },
        "alarm": {
            "id": "ALM",
            "name": "Alarm",
            "examples": ["High Temp Alarm", "Low Pressure Alarm", "Communication Failure"]
        },
        "calculated_value": {
            "id": "CALC",
            "name": "Calculated Value",
            "examples": ["Efficiency", "Runtime Hours", "Energy Consumption"]
        }
    }
}

def load_ontology(ontology_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the HVAC ontology from a file or use the default built-in ontology.
    
    Args:
        ontology_path: Path to a JSON file containing the ontology (optional)
        
    Returns:
        Dictionary containing the ontology
    """
    if ontology_path and os.path.exists(ontology_path):
        try:
            with open(ontology_path, 'r') as f:
                ontology = json.load(f)
            logger.info(f"Loaded ontology from {ontology_path}")
            return ontology
        except Exception as e:
            logger.error(f"Error loading ontology from {ontology_path}: {e}")
            logger.warning("Falling back to default ontology")
    
    logger.info("Using default built-in ontology")
    return DEFAULT_ONTOLOGY

def get_system_by_id(ontology: Dict[str, Any], system_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a system from the ontology by its ID.
    
    Args:
        ontology: The ontology dictionary
        system_id: The ID of the system to find
        
    Returns:
        The system dictionary or None if not found
    """
    for system_key, system in ontology.get("systems", {}).items():
        if system.get("id") == system_id:
            return system
    return None

def get_component_by_id(ontology: Dict[str, Any], system_id: str, component_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a component from a system by its ID.
    
    Args:
        ontology: The ontology dictionary
        system_id: The ID of the system containing the component
        component_id: The ID of the component to find
        
    Returns:
        The component dictionary or None if not found
    """
    system = get_system_by_id(ontology, system_id)
    if not system:
        return None
    
    for component_key, component in system.get("components", {}).items():
        if component.get("id") == component_id:
            return component
    return None

def get_downstream_systems(ontology: Dict[str, Any], system_id: str) -> list:
    """
    Get all systems that are downstream from the specified system.
    
    Args:
        ontology: The ontology dictionary
        system_id: The ID of the upstream system
        
    Returns:
        List of downstream system IDs
    """
    downstream_systems = []
    for relationship in ontology.get("relationships", {}).get("upstream_downstream", []):
        if relationship.get("upstream") == system_id:
            downstream_id = relationship.get("downstream")
            if "." in downstream_id:  # System.Component format
                downstream_systems.append(downstream_id.split(".")[0])
            else:
                downstream_systems.append(downstream_id)
    
    return list(set(downstream_systems))  # Remove duplicates

def get_point_type_by_id(ontology: Dict[str, Any], point_type_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a point type from the ontology by its ID.
    
    Args:
        ontology: The ontology dictionary
        point_type_id: The ID of the point type to find
        
    Returns:
        The point type dictionary or None if not found
    """
    for type_key, point_type in ontology.get("point_types", {}).items():
        if point_type.get("id") == point_type_id:
            return point_type
    return None

def ontology_to_markdown(ontology: Dict[str, Any]) -> str:
    """
    Convert the ontology to a Markdown string for inclusion in LLM prompts.
    
    Args:
        ontology: The ontology dictionary
        
    Returns:
        Markdown representation of the ontology
    """
    md = f"## HVAC ONTOLOGY v{ontology.get('version', '1.0.0')}\n\n"
    
    # Systems and components
    md += "### Systems and Components\n"
    for system_key, system in ontology.get("systems", {}).items():
        md += f"- {system['name']} ({system['id']})\n"
        for component_key, component in system.get("components", {}).items():
            md += f"  - {component['name']} ({component['id']})\n"
    
    md += "\n### System Relationships\n"
    for relationship in ontology.get("relationships", {}).get("upstream_downstream", []):
        md += f"- {relationship['upstream']} → {relationship['downstream']}\n"
    
    md += "\n### Point Types\n"
    for type_key, point_type in ontology.get("point_types", {}).items():
        md += f"- {point_type['name']} ({point_type['id']}): {', '.join(point_type['examples'])}\n"
    
    return md 