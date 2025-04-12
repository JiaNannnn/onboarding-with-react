"""
Knowledge Base Module.

This module provides access to the knowledge base for the HVAC Model Context Protocol,
containing abbreviations, keywords, units, and contradiction rules.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Default knowledge base as inline constant for initial implementation
DEFAULT_KB = {
    "version": "1.0.0",
    "abbreviations": {
        "AHU": "Air Handling Unit",
        "VAV": "Variable Air Volume",
        "FCU": "Fan Coil Unit",
        "CH": "Chiller",
        "CWP": "Chilled Water Pump",
        "CHWP": "Chilled Water Pump",
        "CDWP": "Condenser Water Pump",
        "CT": "Cooling Tower",
        "BLR": "Boiler",
        "HWP": "Hot Water Pump",
        "EF": "Exhaust Fan",
        "SF": "Supply Fan",
        "RF": "Return Fan",
        "SA": "Supply Air",
        "RA": "Return Air",
        "OA": "Outside Air",
        "EA": "Exhaust Air",
        "MA": "Mixed Air",
        "CC": "Cooling Coil",
        "HC": "Heating Coil",
        "RHC": "Reheat Coil",
        "TEMP": "Temperature",
        "TMP": "Temperature",
        "HUM": "Humidity",
        "PRESS": "Pressure",
        "SPT": "Setpoint",
        "SP": "Setpoint",
        "STAT": "Status",
        "CMD": "Command",
        "POS": "Position",
        "FLW": "Flow",
        "VLV": "Valve",
        "DMPR": "Damper",
        "ZN": "Zone",
        "RM": "Room",
        "VSD": "Variable Speed Drive",
        "CH-SYS": "Chiller System",
        "CHSYS": "Chiller System",
        "MODE": "Mode",
        "RUN": "Run",
        "TRIP": "Trip",
        "FAIL": "Failure",
        "HEAT": "Heating",
        "COOL": "Cooling",
        "SINK": "Heat Sink"
    },
    "keywords": {
        "temp": ["SensorAnalog", "Temperature"],
        "tmp": ["SensorAnalog", "Temperature"],
        "hum": ["SensorAnalog", "Humidity"],
        "press": ["SensorAnalog", "Pressure"],
        "flow": ["SensorAnalog", "Flow"],
        "co2": ["SensorAnalog", "CO2 Level"],
        "cmd": ["SetpointCommand", "Command"],
        "command": ["SetpointCommand", "Command"],
        "spt": ["SetpointCommand", "Setpoint"],
        "sp": ["SetpointCommand", "Setpoint"],
        "pos": ["SetpointCommand", "Position"],
        "status": ["StatusFeedback", "Status"],
        "state": ["StatusFeedback", "State"],
        "on": ["StatusFeedback", "Status"],
        "off": ["StatusFeedback", "Status"],
        "alarm": ["Alarm", "Alarm"],
        "alm": ["Alarm", "Alarm"],
        "fault": ["Alarm", "Fault"],
        "run": ["CalculatedValue", "Runtime"],
        "hours": ["CalculatedValue", "Runtime"],
        "eff": ["CalculatedValue", "Efficiency"],
        "energy": ["CalculatedValue", "Energy"],
        "vsd": ["StatusFeedback", "VariableSpeedDrive"],
        "heatsink": ["SensorAnalog", "Temperature"],
        "trip": ["Alarm", "Trip"],
        "fail": ["Alarm", "Failure"],
        "mode": ["StatusFeedback", "Mode"]
    },
    "units": {
        "Temperature": ["degC", "degF", "K"],
        "Pressure": ["Pa", "kPa", "psi", "inWC", "bar"],
        "Flow": ["m3/s", "m3/h", "l/s", "gpm", "cfm"],
        "Humidity": ["%RH", "%"],
        "CO2 Level": ["ppm"],
        "Position": ["%", "deg"],
        "Energy": ["kWh", "MWh", "J", "BTU"],
        "Power": ["kW", "W", "MW", "HP"],
        "Speed": ["rpm", "Hz"]
    },
    "contradictions": {
        "AHU": ["chiller", "pump", "cooling tower", "boiler", "vav terminal"],
        "VAV": ["chiller", "pump", "cooling tower", "boiler", "supply fan", "return fan"],
        "FCU": ["chiller", "cooling tower", "air handling", "vav terminal"],
        "CH": ["air handling", "vav", "boiler", "terminal unit", "zone"],
        "CT": ["air handling", "vav", "boiler", "terminal unit", "zone"],
        "BLR": ["chiller", "cooling tower", "condenser"],
        "CHWP": ["air handling", "vav", "space temp", "room", "terminal unit"]
    },
    "naming_patterns": {
        "AHU": ["AHU-\\d+", "AH-\\d+", "MAU-\\d+", "A[H|I|U]-\\d+"],
        "VAV": ["VAV-\\d+", "VAV_\\d+", "VA-\\d+", "VV-\\d+", "RM\\d+", "ZN\\d+"],
        "CH": ["CH-\\d+", "CHLR-\\d+", "CH_\\d+"],
        "CWP": ["CWP-\\d+", "CHWP-\\d+", "CHLWP-\\d+", "CHWP_\\d+"],
        "CHWP": ["CHWP[-_]\\d+", "CHWP\\d+", "CWP[-_]\\d+", "CH-SYS[-_.]\\d+\\.CHWP"],
        "CDWP": ["CDWP-\\d+", "CndWP-\\d+", "CNDWP-\\d+"],
        "CT": ["CT-\\d+", "CTW-\\d+", "COOL-TWR-\\d+"],
        "BLR": ["BLR-\\d+", "B-\\d+", "BOIL-\\d+"],
        "FCU": ["FCU[-_.]\\d+", "FCU\\.FCU[-_.]\\d+", "FC[-_.]\\d+"]
    },
    "hierarchical_patterns": {
        "CH-SYS": {
            "pattern": "CH-SYS[-_.](\\d+)",
            "components": ["CH", "CHWP", "CWP", "CDWP", "CT"]
        },
        "AHU": {
            "pattern": "AHU[-_.](\\d+)",
            "components": ["SF", "RF", "CC", "HC", "DMPR"]
        },
        "FCU": {
            "pattern": "FCU[-_.](\\d+)",
            "components": ["FAN", "COIL", "VALVE", "TEMP"]
        },
        "VAV": {
            "pattern": "VAV[-_.](\\d+)",
            "components": ["DMPR", "RHC", "TEMP"]
        }
    },
    "common_function_patterns": {
        "VSD_HeatSinkTemp": ["Variable Speed Drive Heat Sink Temperature", "CHWP"],
        "RoomTemp": ["Room Temperature", "FCU"],
        "ModeStatus": ["Operating Mode Status", "Equipment"],
        "RunStatus": ["Run Status", "Equipment"],
        "TripStatus": ["Trip Status", "Equipment"],
        "FailStatus": ["Failure Status", "Equipment"]
    }
}

def load_knowledge_base(kb_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the HVAC knowledge base from a file or use the default built-in KB.
    
    Args:
        kb_path: Path to a JSON file containing the knowledge base (optional)
        
    Returns:
        Dictionary containing the knowledge base
    """
    if kb_path and os.path.exists(kb_path):
        try:
            with open(kb_path, 'r') as f:
                kb = json.load(f)
            logger.info(f"Loaded knowledge base from {kb_path}")
            return kb
        except Exception as e:
            logger.error(f"Error loading knowledge base from {kb_path}: {e}")
            logger.warning("Falling back to default knowledge base")
    
    logger.info("Using default built-in knowledge base")
    return DEFAULT_KB

def get_abbreviation(kb: Dict[str, Any], abbr: str) -> Optional[str]:
    """
    Get the full form of an abbreviation.
    
    Args:
        kb: The knowledge base dictionary
        abbr: The abbreviation to look up
        
    Returns:
        The full form of the abbreviation or None if not found
    """
    return kb.get("abbreviations", {}).get(abbr.upper())

def get_keyword_classification(kb: Dict[str, Any], keyword: str) -> Optional[List[str]]:
    """
    Get the classification of a keyword.
    
    Args:
        kb: The knowledge base dictionary
        keyword: The keyword to look up
        
    Returns:
        List containing [PointType, Function] or None if not found
    """
    return kb.get("keywords", {}).get(keyword.lower())

def get_units_for_measurement(kb: Dict[str, Any], measurement_type: str) -> Optional[List[str]]:
    """
    Get the valid units for a measurement type.
    
    Args:
        kb: The knowledge base dictionary
        measurement_type: The type of measurement (e.g., "Temperature")
        
    Returns:
        List of valid units or None if not found
    """
    return kb.get("units", {}).get(measurement_type)

def get_contradictions(kb: Dict[str, Any], device_type: str) -> Optional[List[str]]:
    """
    Get the contradictions for a device type.
    
    Args:
        kb: The knowledge base dictionary
        device_type: The device type to look up contradictions for
        
    Returns:
        List of contradicting terms or None if not found
    """
    return kb.get("contradictions", {}).get(device_type)

def get_naming_patterns(kb: Dict[str, Any], device_type: str) -> Optional[List[str]]:
    """
    Get the naming patterns for a device type.
    
    Args:
        kb: The knowledge base dictionary
        device_type: The device type to look up patterns for
        
    Returns:
        List of regex patterns or None if not found
    """
    return kb.get("naming_patterns", {}).get(device_type)

def kb_to_markdown(kb: Dict[str, Any], relevance_filter: Optional[List[str]] = None) -> str:
    """
    Convert the knowledge base to a Markdown string for inclusion in LLM prompts.
    Optionally filter to only include relevant sections based on keywords.
    
    Args:
        kb: The knowledge base dictionary
        relevance_filter: Optional list of keywords to filter by
        
    Returns:
        Markdown representation of the knowledge base
    """
    md = f"## HVAC KNOWLEDGE BASE v{kb.get('version', '1.0.0')}\n\n"
    
    # Abbreviations
    md += "### Abbreviations\n"
    abbreviations = kb.get("abbreviations", {})
    if relevance_filter:
        filtered_abbrs = {k: v for k, v in abbreviations.items() 
                         if any(keyword.lower() in k.lower() or keyword.lower() in v.lower() 
                                for keyword in relevance_filter)}
        for abbr, full_form in filtered_abbrs.items():
            md += f"- {abbr}: {full_form}\n"
    else:
        for abbr, full_form in abbreviations.items():
            md += f"- {abbr}: {full_form}\n"
    
    # Keywords
    md += "\n### Keywords\n"
    keywords = kb.get("keywords", {})
    if relevance_filter:
        filtered_keywords = {k: v for k, v in keywords.items() 
                           if any(keyword.lower() in k.lower() for keyword in relevance_filter)}
        for keyword, classification in filtered_keywords.items():
            md += f"- {keyword}: {' / '.join(classification)}\n"
    else:
        for keyword, classification in keywords.items():
            md += f"- {keyword}: {' / '.join(classification)}\n"
    
    # Units
    md += "\n### Units\n"
    units = kb.get("units", {})
    if relevance_filter:
        filtered_units = {k: v for k, v in units.items() 
                         if any(keyword.lower() in k.lower() for keyword in relevance_filter)}
        for measurement, valid_units in filtered_units.items():
            md += f"- {measurement}: {', '.join(valid_units)}\n"
    else:
        for measurement, valid_units in units.items():
            md += f"- {measurement}: {', '.join(valid_units)}\n"
    
    # Contradictions
    md += "\n### Contradictions\n"
    contradictions = kb.get("contradictions", {})
    if relevance_filter:
        filtered_contradictions = {k: v for k, v in contradictions.items() 
                                 if any(keyword.lower() in k.lower() for keyword in relevance_filter)}
        for device_type, contradicting_terms in filtered_contradictions.items():
            md += f"- {device_type}: {', '.join(contradicting_terms)}\n"
    else:
        for device_type, contradicting_terms in contradictions.items():
            md += f"- {device_type}: {', '.join(contradicting_terms)}\n"
    
    # Naming Patterns
    md += "\n### Naming Patterns\n"
    patterns = kb.get("naming_patterns", {})
    if relevance_filter:
        filtered_patterns = {k: v for k, v in patterns.items() 
                           if any(keyword.lower() in k.lower() for keyword in relevance_filter)}
        for device_type, regex_patterns in filtered_patterns.items():
            md += f"- {device_type}: {', '.join(regex_patterns)}\n"
    else:
        for device_type, regex_patterns in patterns.items():
            md += f"- {device_type}: {', '.join(regex_patterns)}\n"
    
    return md

def update_kb_with_feedback(kb: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the knowledge base with feedback from users.
    
    Args:
        kb: The current knowledge base dictionary
        feedback: Dictionary containing feedback information
        
    Returns:
        Updated knowledge base dictionary
    """
    # Create a copy of the KB to avoid modifying the original
    updated_kb = {k: v.copy() if isinstance(v, dict) else v for k, v in kb.items()}
    
    # Process new abbreviations
    if "new_abbreviations" in feedback:
        for abbr, full_form in feedback["new_abbreviations"].items():
            if abbr not in updated_kb["abbreviations"]:
                updated_kb["abbreviations"][abbr] = full_form
                logger.info(f"Added new abbreviation: {abbr} = {full_form}")
    
    # Process new keywords
    if "new_keywords" in feedback:
        for keyword, classification in feedback["new_keywords"].items():
            if keyword not in updated_kb["keywords"]:
                updated_kb["keywords"][keyword] = classification
                logger.info(f"Added new keyword: {keyword} = {classification}")
    
    # Process new contradictions
    if "new_contradictions" in feedback:
        for device_type, contradictions in feedback["new_contradictions"].items():
            if device_type in updated_kb["contradictions"]:
                # Add only new contradictions
                existing = set(updated_kb["contradictions"][device_type])
                updated_kb["contradictions"][device_type] = list(existing.union(set(contradictions)))
                logger.info(f"Updated contradictions for {device_type}")
            else:
                updated_kb["contradictions"][device_type] = contradictions
                logger.info(f"Added new contradictions for {device_type}")
    
    # Process new naming patterns
    if "new_naming_patterns" in feedback:
        for device_type, patterns in feedback["new_naming_patterns"].items():
            if device_type in updated_kb["naming_patterns"]:
                # Add only new patterns
                existing = set(updated_kb["naming_patterns"][device_type])
                updated_kb["naming_patterns"][device_type] = list(existing.union(set(patterns)))
                logger.info(f"Updated naming patterns for {device_type}")
            else:
                updated_kb["naming_patterns"][device_type] = patterns
                logger.info(f"Added new naming patterns for {device_type}")
    
    # Increment version number (assuming semantic versioning with PATCH update)
    version_parts = kb.get("version", "1.0.0").split(".")
    version_parts[2] = str(int(version_parts[2]) + 1)
    updated_kb["version"] = ".".join(version_parts)
    
    return updated_kb

def save_knowledge_base(kb: Dict[str, Any], kb_path: str) -> bool:
    """
    Save the knowledge base to a file.
    
    Args:
        kb: The knowledge base dictionary to save
        kb_path: Path to save the knowledge base to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(kb_path), exist_ok=True)
        
        # Save KB to file
        with open(kb_path, 'w') as f:
            json.dump(kb, f, indent=2)
            
        logger.info(f"Saved knowledge base to {kb_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving knowledge base to {kb_path}: {e}")
        return False 