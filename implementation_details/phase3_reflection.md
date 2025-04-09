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
    """Find similar points in EnOS schema using semantic matching with OpenAI API.
    
    Args:
        decomposition: Point name decomposition
        device_type: Device type
        unit: Unit of measurement
        
    Returns:
        List of similar EnOS points
    """
    # Get available points for this device type from schema
    available_points = self._get_available_points_for_device(device_type)
    
    # If no points available in schema, return empty list
    if not available_points:
        return []
    
    # Prepare point description for semantic matching
    point_description = self._create_point_description(decomposition, unit)
    
    # Use OpenAI API to find semantically similar points
    prompt = self._create_semantic_matching_prompt(point_description, available_points)
    
    # Call OpenAI API
    response = self._call_openai_api(prompt)
    
    # Parse response to get ranked matches
    matches = self._parse_semantic_matches(response)
    
    return matches

def _get_available_points_for_device(self, device_type: str) -> List[str]:
    """Get available points for a device type from the EnOS schema.
    
    Args:
        device_type: Device type
        
    Returns:
        List of available points
    """
    # Try to get points from schema
    points = []
    
    # Check if device type exists in schema
    if device_type in self.enos_schema:
        # Get points from schema
        device_schema = self.enos_schema[device_type]
        if "points" in device_schema:
            points = list(device_schema["points"].keys())
    
    # If no points in schema, use fallback list based on common patterns
    if not points:
        # Fallback common points by device category
        if device_type.startswith("AHU"):
            points = ["AHU_temp_supply", "AHU_temp_return", "AHU_fan_status", "AHU_damper_position"]
        elif device_type.startswith("CH") or device_type.startswith("CHILLER"):
            points = ["CHILLER_status", "CHILLER_temp_supply", "CHILLER_temp_return", "CHILLER_power"]
        elif device_type.startswith("PUMP"):
            points = ["PUMP_status", "PUMP_speed", "PUMP_raw_frequency", "PUMP_power"]
        elif device_type.startswith("VAV"):
            points = ["VAV_flow", "VAV_temp", "VAV_damper_position", "VAV_setpoint"]
        else:
            # Generic points
            points = [
                "TEMP_supply", "TEMP_return", "TEMP_zone",
                "PRESSURE_supply", "PRESSURE_return",
                "FLOW_water", "FLOW_air",
                "STATUS_on_off", "STATUS_alarm",
                "POWER_kW", "HUMIDITY_relative"
            ]
    
    return points

def _create_point_description(self, decomposition: Dict[str, Any], unit: str) -> str:
    """Create a description of the point for semantic matching.
    
    Args:
        decomposition: Point name decomposition
        unit: Unit of measurement
        
    Returns:
        Point description
    """
    description_parts = []
    
    # Add device info if available
    if decomposition["device"]:
        description_parts.append(f"Device: {decomposition['device']}")
    
    # Add measurement type if available
    if decomposition["measurement_type"]:
        description_parts.append(f"Measurement type: {decomposition['measurement_type']}")
    
    # Add property if available
    if decomposition["property"]:
        description_parts.append(f"Property: {decomposition['property']}")
    
    # Add unit information
    if unit:
        description_parts.append(f"Unit: {unit}")
    
    # Add raw segments
    segments_str = ", ".join(decomposition["segments"])
    description_parts.append(f"Name components: {segments_str}")
    
    # Add abbreviations
    if decomposition["abbreviations"]:
        abbrs_str = ", ".join([f"{a} ({m})" for a, m in decomposition["abbreviations"].items()])
        description_parts.append(f"Abbreviations: {abbrs_str}")
    
    return "; ".join(description_parts)

def _create_semantic_matching_prompt(self, point_description: str, available_points: List[str]) -> str:
    """Create a prompt for semantic matching using OpenAI API.
    
    Args:
        point_description: Description of the point
        available_points: Available EnOS points
        
    Returns:
        Prompt for OpenAI API
    """
    points_str = "\n".join([f"- {point}" for point in available_points])
    
    prompt = f"""Given a BMS point description, find the most semantically similar points from the EnOS schema.

Point description:
{point_description}

Available EnOS points:
{points_str}

Analyze the BMS point description and find the top 5 most semantically matching EnOS points from the available list.
Consider the measurement type, device, property, and other characteristics.
Provide your ranking in JSON format:
{{
  "matches": [
    "FIRST_BEST_MATCH",
    "SECOND_BEST_MATCH",
    "THIRD_BEST_MATCH",
    "FOURTH_BEST_MATCH",
    "FIFTH_BEST_MATCH"
  ],
  "reasoning": "Your reasoning for the rankings"
}}

Only include points from the available list. Rank them by semantic similarity."""

    return prompt

def _call_openai_api(self, prompt: str) -> str:
    """Call OpenAI API for semantic matching.
    
    Args:
        prompt: Prompt for OpenAI API
        
    Returns:
        API response
    """
    # In a real implementation, this would use the OpenAI client
    # For now, we'll use Runner.run_sync with the LLM agent
    try:
        response = Runner.run_sync(self.mapping_agent, prompt)
        return response
    except Exception as e:
        # Log error
        logger.error(f"Error calling OpenAI API: {str(e)}")
        # Return empty response
        return '{}'

def _parse_semantic_matches(self, response: str) -> List[str]:
    """Parse OpenAI API response to get ranked matches.
    
    Args:
        response: API response
        
    Returns:
        List of ranked matches
    """
    try:
        # Try to parse JSON response
        match_data = json.loads(response)
        
        # Extract matches
        if "matches" in match_data and isinstance(match_data["matches"], list):
            # Return matches
            return match_data["matches"]
        
        # Handle case where response isn't in expected format
        logger.warning(f"Unexpected response format: {response}")
        
        # Try to extract any list of strings
        if isinstance(match_data, dict):
            for key, value in match_data.items():
                if isinstance(value, list) and all(isinstance(item, str) for item in value):
                    return value
        
        # Fallback: try regex to extract anything that looks like an EnOS point
        matches = re.findall(r'([A-Z][A-Z_]+)', response)
        if matches:
            # Deduplicate while preserving order
            unique_matches = []
            for match in matches:
                if match not in unique_matches:
                    unique_matches.append(match)
            return unique_matches
        
    except Exception as e:
        # Log error
        logger.error(f"Error parsing semantic matches: {str(e)}")
    
    # If all else fails, return empty list
    return []
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