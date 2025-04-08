# Phase 3: Self-Reflection Components for Mapping

## Overview
This phase focuses on implementing self-reflection mechanisms to analyze failed mappings, understand why they failed, and generate improved mapping attempts. Key components include point decomposition analysis, format error reflection, and semantic reflection for unknown mappings.

## Point Decomposition Analysis

### Point Analyzer Class

```python
# app/bms/point_analyzer.py

import re
from typing import Dict, List, Any, Optional, Set, Tuple

class PointAnalyzer:
    """Analyzes BMS points to extract semantic components."""
    
    def __init__(self, abbreviation_dict=None):
        """Initialize the point analyzer.
        
        Args:
            abbreviation_dict: Optional dictionary of abbreviations
        """
        self.abbreviations = abbreviation_dict or self._default_abbreviations()
    
    def _default_abbreviations(self) -> Dict[str, str]:
        """Default abbreviation dictionary.
        
        Returns:
            Dictionary mapping abbreviations to meanings
        """
        return {
            "CWP": "Chilled Water Pump",
            "VSD": "Variable Speed Drive",
            "Hz": "Frequency",
            "AHU": "Air Handling Unit",
            "VAV": "Variable Air Volume",
            "CH": "Chiller",
            "SYS": "System",
            "SPT": "Set Point",
            "TMP": "Temperature",
            "PRS": "Pressure",
            "FLW": "Flow",
            "CTL": "Control",
            "STT": "Status",
            "PWR": "Power",
            "VLV": "Valve",
            "DMP": "Damper"
            # Add more abbreviations as needed
        }
    
    def decompose_point_name(self, point_name: str) -> Dict[str, Any]:
        """Decompose a point name into semantic components.
        
        Args:
            point_name: Name of the point
            
        Returns:
            Dictionary of semantic components
        """
        components = {
            "original": point_name,
            "segments": self._split_into_segments(point_name),
            "abbreviations": {},
            "measurement_type": None,
            "device": None,
            "property": None,
            "location": None
        }
        
        # Identify abbreviations
        for segment in components["segments"]:
            for abbr, meaning in self.abbreviations.items():
                if abbr.lower() == segment.lower() or abbr.lower() in segment.lower():
                    components["abbreviations"][abbr] = meaning
        
        # Determine measurement type
        components["measurement_type"] = self._determine_measurement_type(point_name, components["abbreviations"])
        
        # Identify device
        components["device"] = self._identify_device(point_name, components["abbreviations"])
        
        # Identify property
        components["property"] = self._identify_property(point_name, components["abbreviations"])
        
        # Identify location
        components["location"] = self._identify_location(point_name, components["segments"])
        
        return components
    
    def _split_into_segments(self, point_name: str) -> List[str]:
        """Split a point name into logical segments.
        
        Args:
            point_name: Name of the point
            
        Returns:
            List of segments
        """
        # Split on common delimiters
        segments = re.split(r'[._\-\s]', point_name)
        
        # Filter out empty segments
        return [s for s in segments if s]
    
    def _determine_measurement_type(
        self, 
        point_name: str, 
        abbreviations: Dict[str, str]
    ) -> Optional[str]:
        """Determine the measurement type.
        
        Args:
            point_name: Name of the point
            abbreviations: Detected abbreviations
            
        Returns:
            Measurement type or None
        """
        # Common measurement types and their indicators
        measurement_types = {
            "temperature": ["temp", "tmp", "temperature"],
            "pressure": ["press", "prs", "pressure"],
            "flow": ["flow", "flw"],
            "status": ["status", "state", "stt", "on", "off"],
            "setpoint": ["setpoint", "spt", "set"],
            "frequency": ["hz", "hertz", "freq"],
            "power": ["power", "pwr", "kw", "watt"],
            "position": ["pos", "position", "open", "closed"]
        }
        
        point_name_lower = point_name.lower()
        
        # Check for direct indicators in point name
        for mtype, indicators in measurement_types.items():
            if any(ind in point_name_lower for ind in indicators):
                return mtype
        
        # Check abbreviations
        if "TMP" in abbreviations:
            return "temperature"
        if "PRS" in abbreviations:
            return "pressure"
        if "FLW" in abbreviations:
            return "flow"
        if "STT" in abbreviations:
            return "status"
        if "SPT" in abbreviations:
            return "setpoint"
        if "Hz" in abbreviations:
            return "frequency"
        if "PWR" in abbreviations:
            return "power"
        
        return None
    
    def _identify_device(
        self, 
        point_name: str, 
        abbreviations: Dict[str, str]
    ) -> Optional[str]:
        """Identify the device referenced in the point name.
        
        Args:
            point_name: Name of the point
            abbreviations: Detected abbreviations
            
        Returns:
            Device type or None
        """
        # Common devices and their indicators
        devices = {
            "pump": ["pump", "cwp", "hwp"],
            "valve": ["valve", "vlv"],
            "damper": ["damper", "dmp"],
            "fan": ["fan", "fn"],
            "compressor": ["compressor", "comp"],
            "motor": ["motor", "mtr"],
            "chiller": ["chiller", "ch", "chlr"],
            "boiler": ["boiler", "blr"],
            "vsd": ["vsd", "drive", "vfd"]
        }
        
        point_name_lower = point_name.lower()
        
        # Check for direct indicators in point name
        for device, indicators in devices.items():
            if any(ind in point_name_lower for ind in indicators):
                return device
        
        # Check abbreviations
        if "CWP" in abbreviations or "HWP" in abbreviations:
            return "pump"
        if "VLV" in abbreviations:
            return "valve"
        if "DMP" in abbreviations:
            return "damper"
        if "VSD" in abbreviations:
            return "vsd"
        
        return None
    
    def _identify_property(
        self, 
        point_name: str, 
        abbreviations: Dict[str, str]
    ) -> Optional[str]:
        """Identify the property being measured.
        
        Args:
            point_name: Name of the point
            abbreviations: Detected abbreviations
            
        Returns:
            Property or None
        """
        # Common properties and their indicators
        properties = {
            "supply": ["supply", "sup", "discharge"],
            "return": ["return", "ret", "inlet"],
            "speed": ["speed", "spd"],
            "output": ["output", "out"],
            "input": ["input", "in"],
            "command": ["command", "cmd"],
            "actual": ["actual", "act"],
            "position": ["position", "pos"],
            "raw": ["raw", "direct"]
        }
        
        point_name_lower = point_name.lower()
        
        # Check for direct indicators in point name
        for prop, indicators in properties.items():
            if any(ind in point_name_lower for ind in indicators):
                return prop
        
        return None
    
    def _identify_location(
        self, 
        point_name: str, 
        segments: List[str]
    ) -> Optional[str]:
        """Identify the location referenced in the point name.
        
        Args:
            point_name: Name of the point
            segments: Segments of the point name
            
        Returns:
            Location or None
        """
        # Look for numeric identifiers that might indicate location
        location_pattern = re.search(r'(\d+)[^\d]*$', segments[0] if segments else "")
        if location_pattern:
            return location_pattern.group(1)
        
        return None
```

## Format Error Reflection

### Add Format Reflection Methods to ReasoningEngine

```python
def reflect_on_format_error(
    self,
    point_data: Dict[str, Any],
    llm_response: str
) -> Dict[str, Any]:
    """Reflect on a format error in LLM response.
    
    Args:
        point_data: Point data
        llm_response: Raw LLM response that failed validation
        
    Returns:
        Reflection data
    """
    # Initialize reflection
    reflection = {
        "error_type": "format",
        "original_response": llm_response,
        "analysis": [],
        "corrected_format": None
    }
    
    # Check for common format issues
    if not llm_response.strip():
        reflection["analysis"].append("Empty response from LLM")
    elif "{" not in llm_response or "}" not in llm_response:
        reflection["analysis"].append("Response does not contain JSON structure")
        reflection["analysis"].append("Expected format: {\"enosPoint\": \"TARGET_POINT\"}")
        
        # Try to extract a potential mapping
        potential_point = self._extract_point_from_text(llm_response)
        if potential_point:
            reflection["analysis"].append(f"Found potential point name: {potential_point}")
            reflection["corrected_format"] = {
                "enosPoint": potential_point
            }
    elif "enosPoint" not in llm_response:
        reflection["analysis"].append("JSON is missing the required 'enosPoint' field")
        
        # Try to extract potential field names
        field_match = re.search(r'"([^"]+)":', llm_response)
        if field_match:
            wrong_field = field_match.group(1)
            reflection["analysis"].append(f"Found incorrect field name: '{wrong_field}' instead of 'enosPoint'")
    else:
        # More complex parsing issues
        reflection["analysis"].append("Malformed JSON structure")
        
        # Try to extract the intended mapping
        try:
            # Find any quoted string that might be the target point
            matches = re.findall(r'"([^"]+)"', llm_response)
            if len(matches) >= 2:
                # Second quoted string might be the value
                potential_point = matches[1]
                reflection["analysis"].append(f"Found potential point name: {potential_point}")
                reflection["corrected_format"] = {
                    "enosPoint": potential_point
                }
        except:
            pass
    
    return reflection

def _extract_point_from_text(self, text: str) -> Optional[str]:
    """Extract a potential EnOS point name from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Extracted point name or None
    """
    # Try to find patterns like "point is PUMP_raw_frequency" or similar
    patterns = [
        r'point is ([A-Z_]+)',
        r'mapping is ([A-Z_]+)',
        r'mapped to ([A-Z_]+)',
        r'target is ([A-Z_]+)',
        r'point ([A-Z_]+)',
        r'([A-Z_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            potential_point = match.group(1)
            # Validate that this looks like an EnOS point
            if re.match(r'^[A-Z][A-Z_]+$', potential_point):
                return potential_point
    
    return None

def apply_format_correction(
    self,
    reflection: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Apply format correction based on reflection.
    
    Args:
        reflection: Reflection data
        
    Returns:
        Corrected format or None
    """
    if reflection.get("corrected_format"):
        return reflection["corrected_format"]
    
    return None
```

## Semantic Reflection for Unknown Mappings

### Add Semantic Reflection Methods to ReasoningEngine

```python
def reflect_on_unknown_mapping(
    self,
    point_data: Dict[str, Any],
    device_type: str
) -> Dict[str, Any]:
    """Reflect on an unknown mapping result.
    
    Args:
        point_data: Point data
        device_type: Device type
        
    Returns:
        Reflection data
    """
    # Initialize reflection
    reflection = {
        "error_type": "unknown_mapping",
        "analysis": [],
        "suggestions": [],
        "closest_matches": []
    }
    
    # Get point analyzer
    point_analyzer = PointAnalyzer(self.abbreviations)
    
    # Decompose point name
    decomposition = point_analyzer.decompose_point_name(point_data.get("pointName", ""))
    
    # Add decomposition to reflection
    reflection["decomposition"] = decomposition
    reflection["analysis"].append(f"Point name decomposed into: {decomposition['segments']}")
    
    if decomposition["abbreviations"]:
        reflection["analysis"].append(f"Detected abbreviations: {decomposition['abbreviations']}")
    
    if decomposition["measurement_type"]:
        reflection["analysis"].append(f"Likely measurement type: {decomposition['measurement_type']}")
    
    if decomposition["device"]:
        reflection["analysis"].append(f"Likely device: {decomposition['device']}")
    
    # Find similar points in EnOS schema
    similar_points = self._find_similar_enos_points(
        decomposition, 
        device_type,
        point_data.get("unit", "")
    )
    
    # Add similar points to reflection
    if similar_points:
        reflection["closest_matches"] = similar_points[:5]  # Top 5 matches
        reflection["analysis"].append(f"Found {len(similar_points)} potential matches in EnOS schema")
        reflection["suggestions"].append(f"Consider these EnOS points: {', '.join(similar_points[:3])}")
    else:
        reflection["analysis"].append("No close matches found in EnOS schema")
        reflection["suggestions"].append("This may require a custom mapping or schema extension")
    
    # Generate additional suggestions based on point characteristics
    if decomposition["measurement_type"] == "frequency" and decomposition["device"] == "pump":
        reflection["suggestions"].append("This appears to be a pump frequency measurement, should map to PUMP_raw_frequency")
    elif decomposition["measurement_type"] == "temperature" and "supply" in decomposition.get("property", ""):
        reflection["suggestions"].append("This appears to be a supply temperature, should map to TEMP_supply or similar")
    
    return reflection

def _find_similar_enos_points(
    self,
    decomposition: Dict[str, Any],
    device_type: str,
    unit: str
) -> List[str]:
    """Find similar points in EnOS schema.
    
    Args:
        decomposition: Point name decomposition
        device_type: Device type
        unit: Unit of measurement
        
    Returns:
        List of similar EnOS points
    """
    # This is a simplified version
    # In the real implementation, this would search the EnOS schema more thoroughly
    similar_points = []
    
    # Filter by measurement type
    if decomposition["measurement_type"] == "temperature":
        similar_points.extend(["TEMP_supply", "TEMP_return", "TEMP_ambient", "TEMP_zone"])
    elif decomposition["measurement_type"] == "pressure":
        similar_points.extend(["PRESSURE_supply", "PRESSURE_return", "PRESSURE_differential"])
    elif decomposition["measurement_type"] == "flow":
        similar_points.extend(["FLOW_water", "FLOW_air"])
    elif decomposition["measurement_type"] == "status":
        similar_points.extend(["STATUS_on_off", "STATUS_alarm"])
    elif decomposition["measurement_type"] == "frequency":
        similar_points.extend(["PUMP_raw_frequency", "FAN_raw_frequency"])
    elif decomposition["measurement_type"] == "power":
        similar_points.extend(["POWER_kW", "POWER_consumption"])
    
    # Further filter by device
    if decomposition["device"] == "pump":
        pump_points = ["PUMP_raw_frequency", "PUMP_status", "PUMP_command", "PUMP_speed"]
        similar_points.extend([p for p in pump_points if p not in similar_points])
    elif decomposition["device"] == "valve":
        valve_points = ["VALVE_position", "VALVE_command", "VALVE_feedback"]
        similar_points.extend([p for p in valve_points if p not in similar_points])
    elif decomposition["device"] == "damper":
        damper_points = ["DAMPER_position", "DAMPER_command", "DAMPER_feedback"]
        similar_points.extend([p for p in damper_points if p not in similar_points])
    
    # Consider unit
    if unit.lower() in ["hz", "hertz"]:
        frequency_points = ["PUMP_raw_frequency", "FAN_raw_frequency", "MOTOR_frequency"]
        similar_points.extend([p for p in frequency_points if p not in similar_points])
    
    # Sort by relevance (simplified implementation)
    # In practice, this would calculate similarity scores
    
    return similar_points
```

## Integration with Mapping Process

### Update the EnOSMapper Class

```python
async def map_points_with_reflection(
    self,
    points: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Map points with reflection for failed mappings.
    
    Args:
        points: List of points to map
        
    Returns:
        Mapped points with reflection data where needed
    """
    # First pass: Normal mapping
    results = await self.map_points(points)
    
    # Initialize reasoning engine
    reasoning_engine = self.get_reasoning_engine()
    
    # Second pass: Apply reflection to failed mappings
    for i, result in enumerate(results):
        # Check if reflection is needed
        if self._should_trigger_reflection(result):
            # Get original point data
            point_data = points[i]
            device_type = point_data.get("deviceType", "unknown")
            
            # Check if format error or unknown mapping
            if "error" in result and result["error"] and "format" in result["error"].lower():
                # Reflect on format error
                reflection = reasoning_engine.reflect_on_format_error(
                    point_data,
                    result.get("raw_response", "")
                )
                
                # Try to apply format correction
                corrected_format = reasoning_engine.apply_format_correction(reflection)
                if corrected_format:
                    # Update mapping with corrected format
                    result["mapping"]["enosPoint"] = corrected_format.get("enosPoint", "unknown")
                    result["reflection"] = {
                        "type": "format_correction",
                        "analysis": reflection["analysis"],
                        "success": result["mapping"]["enosPoint"] != "unknown"
                    }
                else:
                    # Format correction failed, perform remapping
                    new_result = await self._remap_with_reflection(point_data, device_type, reflection)
                    results[i] = new_result
            else:
                # Unknown mapping, perform semantic reflection
                reflection = reasoning_engine.reflect_on_unknown_mapping(
                    point_data,
                    device_type
                )
                
                # Try remapping with reflection
                new_result = await self._remap_with_reflection(point_data, device_type, reflection)
                results[i] = new_result
    
    return results

async def _remap_with_reflection(
    self,
    point_data: Dict[str, Any],
    device_type: str,
    reflection: Dict[str, Any]
) -> Dict[str, Any]:
    """Remap a point using reflection data.
    
    Args:
        point_data: Point data
        device_type: Device type
        reflection: Reflection data
        
    Returns:
        New mapping result
    """
    # Get reasoning engine
    reasoning_engine = self.get_reasoning_engine()
    
    # Generate refined prompt with reflection
    prompt = reasoning_engine.generate_refined_prompt_with_reflection(
        point_data,
        device_type,
        reflection
    )
    
    # Run the LLM again
    llm_response = await Runner.run_sync(self.mapping_agent, prompt)
    
    # Process and validate result
    new_result = self._process_llm_response(llm_response, point_data, device_type)
    
    # Add reflection to result
    new_result["reflection"] = {
        "type": reflection["error_type"],
        "analysis": reflection["analysis"],
        "suggestions": reflection.get("suggestions", []),
        "success": new_result["mapping"]["enosPoint"] != "unknown"
    }
    
    return new_result
```

### Add Reflection-Enhanced Prompt Generation

```python
def generate_refined_prompt_with_reflection(
    self,
    point_data: Dict[str, Any],
    device_type: str,
    reflection: Dict[str, Any]
) -> str:
    """Generate a refined prompt using reflection data.
    
    Args:
        point_data: Point data
        device_type: Device type
        reflection: Reflection data
        
    Returns:
        Refined prompt
    """
    # Base prompt
    prompt = f"""Map the following BMS point to the EnOS schema:

Point ID: {point_data.get('pointId', 'unknown')}
Point Name: {point_data.get('pointName', '')}
Device Type: {device_type}
Unit: {point_data.get('unit', '')}
Description: {point_data.get('description', '')}

"""
    
    # Add reflection analysis
    prompt += "Based on reflection analysis:\n"
    for analysis in reflection["analysis"]:
        prompt += f"- {analysis}\n"
    
    # Add suggestions if available
    if "suggestions" in reflection and reflection["suggestions"]:
        prompt += "\nSuggestions:\n"
        for suggestion in reflection["suggestions"]:
            prompt += f"- {suggestion}\n"
    
    # Add closest matches if available
    if "closest_matches" in reflection and reflection["closest_matches"]:
        prompt += "\nPotential EnOS points to consider:\n"
        for match in reflection["closest_matches"]:
            prompt += f"- {match}\n"
    
    # Add decomposition if available
    if "decomposition" in reflection:
        decomp = reflection["decomposition"]
        prompt += "\nPoint name decomposition:\n"
        prompt += f"- Segments: {', '.join(decomp['segments'])}\n"
        if decomp["measurement_type"]:
            prompt += f"- Measurement type: {decomp['measurement_type']}\n"
        if decomp["device"]:
            prompt += f"- Device: {decomp['device']}\n"
        if decomp["property"]:
            prompt += f"- Property: {decomp['property']}\n"
    
    # Clear instructions for the format
    prompt += """
Please provide the mapping in the EXACT format:
{"enosPoint": "TARGET_POINT"}

If you cannot determine the mapping, respond with:
{"enosPoint": "unknown"}

Important: Respond ONLY with the JSON object, nothing else.
"""
    
    return prompt
``` 