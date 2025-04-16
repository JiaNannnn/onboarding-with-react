from typing import Dict, List, Any, Optional, Tuple, Set
import json
import os
import re
from datetime import datetime
from agents import Runner

# Import logging system
from .app_logging import ReasoningLogger

class ReasoningEngine:
    """Engine for generating reasoning chains and reflections."""
    
    def __init__(self, enos_schema: Dict[str, Any], logger=None, mapping_agent=None):
        """Initialize the reasoning engine.
        
        Args:
            enos_schema: EnOS schema
            logger: Optional reasoning logger
            mapping_agent: Optional mapping agent for API calls
        """
        self.enos_schema = enos_schema
        self.mapping_agent = mapping_agent
        
        # Initialize logger if not provided
        if logger is None:
            self.logger = ReasoningLogger()
        else:
            self.logger = logger
        
        # Load abbreviation dictionary
        self.abbreviations = self._load_abbreviations()
    
    def _load_abbreviations(self) -> Dict[str, str]:
        """Load abbreviation dictionary.
        
        Returns:
            Dictionary mapping abbreviations to meanings
        """
        # Load from file or use hardcoded dictionary
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
            "DMP": "Damper",
            "TEMP": "Temperature",
            "RH": "Relative Humidity",
            "CO2": "Carbon Dioxide",
            "ZN": "Zone",
            "RT": "Return",
            "SP": "Setpoint",
            "SA": "Supply Air",
            "RA": "Return Air",
            "OA": "Outside Air",
            "FCU": "Fan Coil Unit",
            "VAV": "Variable Air Volume",
            "CH": "Chiller",
            "METER": "Meter",
            "LIGHTING": "Lighting",
            "CHPL": "Chiller Plant",
        }
    
    def chain_of_thought_grouping(self, points: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate step-by-step reasoning for device type grouping.
        
        Args:
            points: List of points to group
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        # Using enhanced grouping with reasoning from Phase 2
        return self._group_points_with_reasoning(points)
    
    def _group_points_with_reasoning(
        self,
        points: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group points by device type with chain of thought reasoning.
        
        Args:
            points: List of points to group
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        # First pass: Use explicit device types and extract prefixes
        initial_groups = {}
        points_to_analyze = []
        
        for point in points:
            if "deviceType" in point and point["deviceType"]:
                # Use explicit device type
                device_type = point["deviceType"]
                if device_type not in initial_groups:
                    initial_groups[device_type] = []
                initial_groups[device_type].append(point)
            else:
                # Extract potential device type from name prefix
                point_name = point.get("pointName", "")
                prefix = self.extract_device_prefix(point_name)
                
                if prefix:
                    # Store prefix for later analysis
                    point["extracted_prefix"] = prefix
                    
                # Add to points needing further analysis
                points_to_analyze.append(point)
        
        # Second pass: Group points with similar prefixes
        prefix_groups = {}
        points_without_prefix = []
        
        for point in points_to_analyze:
            if "extracted_prefix" in point:
                prefix = point["extracted_prefix"]
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(point)
            else:
                points_without_prefix.append(point)
        
        # Third pass: Use CoT reasoning to map prefixes to device types
        for prefix, prefix_points in prefix_groups.items():
            # Use reasoning to determine device type from prefix
            reasoning_chain, device_type = self.reason_device_type_from_prefix(
                prefix, prefix_points
            )
            
            # Store reasoning chain in points
            for point in prefix_points:
                point["grouping_reasoning"] = reasoning_chain
            
            # Add to initial groups or create new group
            if device_type not in initial_groups:
                initial_groups[device_type] = []
            initial_groups[device_type].extend(prefix_points)
        
        # Fourth pass: Handle remaining points without prefixes
        if points_without_prefix:
            # Use batch reasoning for remaining points
            reasoned_groups = self.batch_reason_device_types(points_without_prefix)
            
            # Merge with initial groups
            for device_type, device_points in reasoned_groups.items():
                if device_type not in initial_groups:
                    initial_groups[device_type] = []
                initial_groups[device_type].extend(device_points)
        
        # Final pass: Verify group assignments
        verified_groups = {}
        
        for device_type, device_points in initial_groups.items():
            # Verify group assignment and potentially reassign points
            verification_result = self.verify_group_assignment(
                device_type, device_points
            )
            
            # Process the verification result
            for verified_type, verified_points in verification_result.items():
                if verified_type not in verified_groups:
                    verified_groups[verified_type] = []
                verified_groups[verified_type].extend(verified_points)
        
        return verified_groups
    
    def extract_device_prefix(self, point_name: str) -> Optional[str]:
        """Extract potential device type prefix from point name with enhanced pattern recognition.
        
        Args:
            point_name: Name of the point
            
        Returns:
            Extracted prefix or None
        """
        if not point_name:
            return None
        
        # Strategy 1: Hierarchical notation (CH-SYS-1.CHWP)
        if '.' in point_name:
            parts = point_name.split('.')
            if len(parts) >= 2:
                # If first part has system identifier, return it
                if any(sys_id in parts[0].upper() for sys_id in ["CH-SYS", "AHU", "VAV", "FCU"]):
                    return parts[0]
                # For cases like FCU.FCU_05_01_8, return the most specific component
                if parts[0] == parts[1].split('_')[0]:
                    return parts[1].split('_')[0]
                # Return both parent and child for component identification
                return f"{parts[0]}.{parts[1]}"
        
        # Strategy 2: Standard delimiters (AHU-1, FCU-2)
        delimiter_match = re.search(r'^([A-Za-z\-]+)[\-_\.](\d+)', point_name)
        if delimiter_match:
            return delimiter_match.group(1)
        
        # Strategy 3: Equipment with number separator (CHWP_1, CHWP-1)
        equipment_match = re.search(r'^([A-Za-z]+)[_\-\.]?(\d+)', point_name)
        if equipment_match:
            return equipment_match.group(1)
        
        # Strategy 4: Equipment identifier at start (CHWP_1_VSD_HeatSinkTemp)
        if '_' in point_name:
            parts = point_name.split('_')
            # Check if first part is a known equipment type
            if parts[0] in ["CHWP", "CWP", "FCU", "AHU", "VAV", "CH", "CT"]:
                # If second part is numeric, include it in the prefix
                if len(parts) > 1 and parts[1].isdigit():
                    return f"{parts[0]}_{parts[1]}"
                return parts[0]
        
        # Strategy 5: Generic pattern for detecting device prefixes
        components = re.split(r'[._\-]', point_name)
        if components and components[0]:
            # Check if first component matches known equipment type patterns
            if any(eq_type in components[0].upper() for eq_type in 
                  ["CHWP", "CWP", "FCU", "AHU", "VAV", "CH", "CT", "VSD"]):
                return components[0]
        
        return None

    def reason_device_type_from_prefix(
        self,
        prefix: str,
        points: List[Dict[str, Any]]
    ) -> Tuple[List[str], str]:
        """Reason the likely device type from a prefix with enhanced hierarchical awareness.
        
        Args:
            prefix: The prefix to analyze
            points: Points with this prefix (for additional context)
            
        Returns:
            Tuple of (reasoning_chain, device_type)
        """
        # Start reasoning chain
        reasoning = [f"Analyzing prefix '{prefix}' to determine device type"]
        
        # Handle hierarchical prefixes (CH-SYS-1.CHWP)
        if '.' in prefix:
            parent, child = prefix.split('.', 1)
            reasoning.append(f"Detected hierarchical structure: '{parent}' (parent) and '{child}' (component)")
            
            # Check if parent is a known system
            parent_clean = re.sub(r'[-_]\d+', '', parent).upper()
            if parent_clean == "CH-SYS" or parent_clean == "CHSYS":
                reasoning.append(f"Parent '{parent}' identified as Chiller System")
                
                # Determine component type
                if child.upper().startswith("CHWP") or child.upper().startswith("CWP"):
                    reasoning.append(f"Component '{child}' identified as Chilled Water Pump")
                    return reasoning, "CHWP"
                elif child.upper().startswith("CH"):
                    reasoning.append(f"Component '{child}' identified as Chiller")
                    return reasoning, "CH"
                elif child.upper().startswith("CT"):
                    reasoning.append(f"Component '{child}' identified as Cooling Tower")
                    return reasoning, "CT"
            
            # Check for AHU components
            elif parent_clean.startswith("AHU"):
                reasoning.append(f"Parent '{parent}' identified as Air Handling Unit")
                
                # Handle common AHU components
                if child.upper().startswith("SF") or "SUPPLY" in child.upper():
                    reasoning.append(f"Component '{child}' identified as Supply Fan")
                    return reasoning, "AHU-SF"
                elif child.upper().startswith("RF") or "RETURN" in child.upper():
                    reasoning.append(f"Component '{child}' identified as Return Fan")
                    return reasoning, "AHU-RF"
                
                # Default to parent if component can't be specifically identified
                return reasoning, "AHU"
        
        # Handle compound equipment identifiers (CHWP_1, FCU_05_01)
        if '_' in prefix:
            base_equipment = prefix.split('_')[0].upper()
            reasoning.append(f"Identified equipment base type: '{base_equipment}'")
            
            if base_equipment == "CHWP" or base_equipment == "CWP":
                reasoning.append("Recognized as Chilled Water Pump")
                return reasoning, "CHWP"
            elif base_equipment == "FCU":
                reasoning.append("Recognized as Fan Coil Unit")
                return reasoning, "FCU"
            elif base_equipment == "AHU":
                reasoning.append("Recognized as Air Handling Unit")
                return reasoning, "AHU"
            elif base_equipment == "VAV":
                reasoning.append("Recognized as Variable Air Volume box")
                return reasoning, "VAV"
        
        # Handle direct equipment references
        if prefix.upper().startswith("CH-SYS") or prefix.upper().startswith("CHSYS"):
            reasoning.append("Prefix pattern matches Chiller System")
            return reasoning, "CH-SYS"
        elif prefix.upper().startswith("CHWP") or prefix.upper().startswith("CWP"):
            reasoning.append("Prefix pattern matches Chilled Water Pump")
            return reasoning, "CHWP"
        elif prefix.upper().startswith("CH") and not (prefix.upper().startswith("CHWP") or prefix.upper().startswith("CH-SYS")):
            reasoning.append("Prefix pattern matches Chiller")
            return reasoning, "CH"
        elif prefix.upper().startswith("FCU"):
            reasoning.append("Prefix pattern matches Fan Coil Unit")
            return reasoning, "FCU"
        elif prefix.upper().startswith("AHU"):
            reasoning.append("Prefix pattern matches Air Handling Unit")
            return reasoning, "AHU"
        elif prefix.upper().startswith("VAV"):
            reasoning.append("Prefix pattern matches Variable Air Volume box")
            return reasoning, "VAV"
        elif prefix.upper().startswith("CT"):
            reasoning.append("Prefix pattern matches Cooling Tower")
            return reasoning, "CT"
        
        # If no pattern matches, analyze point names for common keywords
        if not reasoning or len(reasoning) <= 2:
            reasoning.append("No clear pattern match for prefix, analyzing point details")
            
            # Extract common words from point names
            common_words = self._extract_common_keywords(points)
            reasoning.append(f"Found common keywords in points: {', '.join(common_words)}")
            
            # Look for equipment indicators in the common words
            if any(kw in common_words for kw in ["VSD", "PUMP", "FLOW"]):
                reasoning.append("Keywords suggest a pump-related equipment")
                if "CHILL" in common_words or "CHW" in common_words:
                    reasoning.append("Keywords suggest Chilled Water Pump")
                    return reasoning, "CHWP"
            elif any(kw in common_words for kw in ["TEMP", "ROOM", "SPACE", "ZONE"]):
                if "FCU" in common_words:
                    reasoning.append("Keywords suggest Fan Coil Unit")
                    return reasoning, "FCU"
                else:
                    reasoning.append("Temperature-related keywords suggest a terminal unit")
                    return reasoning, "TU"
        
        # Default fallback
        reasoning.append("Unable to determine specific type, defaulting to UNKNOWN")
        return reasoning, "UNKNOWN"

    def _extract_common_keywords(self, points: List[Dict[str, Any]]) -> List[str]:
        """Extract common keywords from point names to aid in classification.
        
        Args:
            points: List of points to analyze
            
        Returns:
            List of common keywords found
        """
        # List of keywords to look for
        keywords = [
            "TEMP", "TEMPERATURE", "FLOW", "PRESSURE", "VALVE", "PUMP", 
            "FAN", "SPEED", "STATUS", "COMMAND", "VSD", "CHILLER", "CHILL",
            "COOLING", "HEATING", "ROOM", "SPACE", "ZONE", "SUPPLY", "RETURN",
            "FCU", "AHU", "VAV", "CHW", "HW", "CW", "CT", "SETPOINT", "SPT"
        ]
        
        # Count occurrences of each keyword
        keyword_counts = {kw: 0 for kw in keywords}
        
        for point in points:
            point_name = point.get("pointName", "").upper()
            for kw in keywords:
                if kw in point_name:
                    keyword_counts[kw] += 1
        
        # Return keywords that appear in at least 30% of points
        threshold = max(1, len(points) * 0.3)
        common_words = [kw for kw, count in keyword_counts.items() if count >= threshold]
        
        return common_words

    def batch_reason_device_types(
        self,
        points: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Use batch reasoning to determine device types for points without clear prefixes.
        
        Args:
            points: Points without clear device type indicators
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        if not points:
            return {}
        
        # Check if we can use the LLM agent for better reasoning
        if self.mapping_agent:
            return self._llm_batch_reasoning(points)
        
        # Fallback to rule-based reasoning if no LLM agent is available
        return self._rule_based_batch_reasoning(points)

    def _llm_batch_reasoning(self, points: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Use LLM to batch reason device types for points.
        
        Args:
            points: Points to analyze
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        # Extract point names for analysis
        point_names = []
        for i, point in enumerate(points):
            point_name = point.get("pointName", f"Unknown-{i}")
            units = point.get("unit", "")
            description = point.get("description", "")
            
            # Include contextual information
            point_info = f"{point_name}"
            if units:
                point_info += f" (Unit: {units})"
            if description:
                point_info += f" - {description}"
            
            point_names.append(point_info)
        
        # Construct prompt for LLM reasoning
        prompt = f"""Analyze these Building Management System (BMS) point names and group them by device type.
Determine the most probable device type for each point from these categories:
- CH-SYS: Chiller System
- AHU: Air Handling Unit
- VAV: Variable Air Volume unit
- FCU: Fan Coil Unit
- METER: Metering device
- LIGHTING: Lighting control system
- ZONE: Generic zone sensors or controls
- MISC: Miscellaneous device

Explain your reasoning for each point classification, then output a JSON structure with device types 
as keys, and lists of point indices (0-based) as values, along with reasoning for each group.

Point list:
{chr(10).join([f"{i}: {name}" for i, name in enumerate(point_names)])}

Output format:
{{
  "device_type1": {{
    "point_indices": [list of indices],
    "reasoning": "detailed explanation for this classification"
  }},
  "device_type2": {{
    "point_indices": [list of indices],
    "reasoning": "detailed explanation for this classification"
  }}
}}
"""
        
        # Call LLM to analyze points
        try:
            self.logger.log_reasoning_step("batch_reason_device_types", "Sending point batch to LLM for analysis")
            result = self.mapping_agent.run(prompt)
            
            # Try to parse the response as JSON
            try:
                import json
                import re
                
                # Extract JSON if it's embedded in a larger response
                json_match = re.search(r'({[\s\S]*})', result)
                if json_match:
                    result_json = json.loads(json_match.group(1))
                else:
                    result_json = json.loads(result)
                    
                # Process the LLM reasoning results
                device_groups = {}
                
                for device_type, group_data in result_json.items():
                    # Clean up device type (trim whitespace, convert to uppercase)
                    clean_device_type = device_type.strip().upper()
                    
                    # Skip if the device type is invalid
                    if not clean_device_type:
                        continue
                    
                    # Get point indices and reasoning
                    point_indices = group_data.get("point_indices", [])
                    reasoning = group_data.get("reasoning", "")
                    
                    # Initialize group if needed
                    if clean_device_type not in device_groups:
                        device_groups[clean_device_type] = []
                    
                    # Add points to group with reasoning
                    for idx in point_indices:
                        if 0 <= idx < len(points):
                            # Create a copy of the point to avoid modifying the original
                            point_copy = dict(points[idx])
                            
                            # Add reasoning chain
                            point_copy["grouping_reasoning"] = [
                                f"LLM analysis of point without clear prefix:",
                                reasoning
                            ]
                            
                            device_groups[clean_device_type].append(point_copy)
                
                self.logger.log_reasoning_step("batch_reason_device_types", 
                    f"LLM successfully classified {len(points)} points into {len(device_groups)} device types")
                    
                return device_groups
                
            except Exception as json_error:
                self.logger.log_reasoning_step("batch_reason_device_types", 
                    f"Failed to parse LLM response as JSON: {str(json_error)}")
                # Fallback to rule-based reasoning
                return self._rule_based_batch_reasoning(points)
                
        except Exception as llm_error:
            self.logger.log_reasoning_step("batch_reason_device_types", 
                f"LLM reasoning failed: {str(llm_error)}")
            # Fallback to rule-based reasoning
            return self._rule_based_batch_reasoning(points)

    def _rule_based_batch_reasoning(self, points: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Use rule-based reasoning to determine device types for points without clear prefixes.
        
        Args:
            points: Points to analyze
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        device_groups = {
            "CH-SYS": [],
            "AHU": [],
            "VAV": [],
            "FCU": [],
            "METER": [],
            "ZONE": [],
            "MISC": []
        }
        
        for point in points:
            point_name = point.get("pointName", "").lower()
            unit = point.get("unit", "").lower()
            description = point.get("description", "").lower()
            
            # Add reasoning chain
            reasoning = [
                f"Analyzing point without clear prefix: {point.get('pointName', '')}",
                "Using rule-based classification since LLM is not available"
            ]
            
            # Create a copy to avoid modifying the original
            point_copy = dict(point)
            
            # Check for keywords in point name and description
            if any(term in point_name or term in description for term in 
                   ["chiller", "chw", "condenser", "cooling tower", "evaporator"]):
                reasoning.append("Contains chiller-related terms, categorizing as CH-SYS")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["CH-SYS"].append(point_copy)
                
            elif any(term in point_name or term in description for term in 
                    ["ahu", "air handler", "air handling", "supply fan", "return fan"]):
                reasoning.append("Contains air handler terms, categorizing as AHU")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["AHU"].append(point_copy)
                
            elif any(term in point_name or term in description for term in 
                    ["vav", "variable air", "terminal unit", "zone damper"]):
                reasoning.append("Contains VAV terms, categorizing as VAV")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["VAV"].append(point_copy)
                
            elif any(term in point_name or term in description for term in 
                    ["fcu", "fan coil"]):
                reasoning.append("Contains fan coil terms, categorizing as FCU")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["FCU"].append(point_copy)
                
            elif any(term in point_name or term in description for term in 
                    ["meter", "energy", "power", "kwh", "kw", "consumption"]):
                reasoning.append("Contains metering terms, categorizing as METER")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["METER"].append(point_copy)
                
            elif any(term in point_name or term in description for term in 
                    ["zone", "room", "space", "area"]) and any(term in point_name or term in description or term in unit for term in 
                    ["temp", "humidity", "co2", "occupancy"]):
                reasoning.append("Contains zone sensor terms, categorizing as ZONE")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["ZONE"].append(point_copy)
                
            else:
                reasoning.append("No clear device type indicators, categorizing as MISC")
                point_copy["grouping_reasoning"] = reasoning
                device_groups["MISC"].append(point_copy)
        
        # Remove empty groups
        return {k: v for k, v in device_groups.items() if v}

    def verify_group_assignment(
        self,
        device_type: str,
        points: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Verify group assignments with enhanced semantic contradictions and equipment-specific checks.
        
        Args:
            device_type: Proposed device type
            points: Points in this group
            
        Returns:
            Dictionary of verified device types and their points
        """
        # Initialize result with original group as default
        result = {device_type: []}
        
        # If there are no points to verify, return empty group
        if not points:
            return result
        
        # Log verification start
        self.logger.log_reasoning_step("verify_group_assignment", 
            f"Verifying {len(points)} points assigned to device type '{device_type}'")
        
        # Equipment-specific contradiction rules
        contradiction_rules = {
            "VAV": {
                "terms": ["chiller", "compressor", "condenser", "cooling tower", "ch-sys", "chw", "pump", "boiler"],
                "functions": ["central supply", "return fan", "mixed air", "outdoor air damper"],
                "system": "terminal unit"
            },
            "CH-SYS": {
                "terms": ["airflow", "damper", "duct", "vav", "terminal unit", "space temp", "room"],
                "functions": ["zone control", "reheat", "discharge air"],
                "system": "central plant"
            },
            "CHWP": {
                "terms": ["airflow", "damper", "duct", "vav", "space temp", "mixing", "filter"],
                "functions": ["zone control", "economizer", "filter", "damper position"],
                "system": "pumping equipment"
            },
            "AHU": {
                "terms": ["chiller", "compressor", "condenser", "cooling tower", "chwp", "pump status", "boiler"],
                "functions": ["condenser", "chilled water", "refrigerant", "hot water pressure"],
                "system": "air handling"
            },
            "FCU": {
                "terms": ["chiller", "cooling tower", "chwp", "air handling", "vav terminal", "chw", "compressor"],
                "functions": ["economizer", "static pressure", "mixed air", "system-level"],
                "system": "terminal unit"
            }
        }
        
        # Device type specific point type expectations
        expected_point_types = {
            "VAV": ["AI", "AO", "BI", "BO"],
            "CH-SYS": ["AI", "AO", "BI", "BO"],
            "CHWP": ["AI", "BI", "BO"],
            "AHU": ["AI", "AO", "BI", "BO"],
            "FCU": ["AI", "AO", "BI", "BO"]
        }
        
        # Device type specific function expectations
        expected_functions = {
            "VAV": ["temp", "flow", "damper", "setpoint", "status"],
            "CH-SYS": ["temp", "pressure", "flow", "status", "power"],
            "CHWP": ["status", "speed", "pressure", "flow", "power"],
            "AHU": ["temp", "humidity", "pressure", "flow", "fan", "damper", "status"],
            "FCU": ["temp", "fan", "valve", "setpoint", "status"]
        }
        
        # Analyze each point in the group
        for point in points:
            point_name = point.get("pointName", "").lower()
            unit = point.get("unit", "").lower()
            description = point.get("description", "").lower()
            
            # Start verification reasoning
            verification = [
                f"Verifying '{point_name}' as device type '{device_type}'"
            ]
            
            # Get contradiction rules for this device type
            rules = contradiction_rules.get(device_type, {"terms": [], "functions": [], "system": "unknown"})
            
            # Check for contradicting evidence based on device type
            contradictions = []
            
            # Check for contradicting terms
            for term in rules["terms"]:
                if term in point_name or term in description:
                    contradictions.append(f"Point contains '{term}', inconsistent with {device_type} classification")
            
            # Check for contradicting functions
            for function in rules["functions"]:
                if function in point_name or function in description:
                    contradictions.append(f"Point function '{function}' is inconsistent with {device_type} classification")
            
            # Check for point type consistency
            if device_type in expected_point_types:
                point_type = point.get("pointType", "")
                if point_type and point_type not in expected_point_types[device_type]:
                    contradictions.append(f"Point type '{point_type}' is uncommon for {device_type}")
            
            # Check for functional consistency
            if device_type in expected_functions:
                point_functions = expected_functions[device_type]
                if not any(func in point_name.lower() for func in point_functions):
                    contradictions.append(f"Point function doesn't match common {device_type} functions")
            
            # Special case checks for particular device types
            if device_type == "CHWP":
                # CHWP points should have pump-related terms
                if not any(term in point_name.lower() or term in description.lower() 
                           for term in ["pump", "flow", "pressure", "vsd", "speed", "status"]):
                    contradictions.append("Point lacks typical pump-related terms")
                    
                # If clearly labeled with another component type, it's a contradiction
                for component in ["cooling tower", "condenser", "chiller", "boiler"]:
                    if component in point_name.lower() or component in description.lower():
                        contradictions.append(f"Point specifically mentions '{component}', not a pump component")
            
            elif device_type == "CH-SYS":
                # CH-SYS points should have chiller system related terms
                if not any(term in point_name.lower() or term in description.lower()
                          for term in ["chiller", "chw", "cooling", "condenser", "ctwr", "ch-sys"]):
                    contradictions.append("Point lacks typical chiller system terms")
                    
                # If clearly a terminal unit, it's a contradiction
                for terminal in ["zone", "room", "space temp", "vav", "fcu"]:
                    if terminal in point_name.lower() or terminal in description.lower():
                        contradictions.append(f"Point specifically mentions '{terminal}', which is a terminal unit concept")
            
            # If contradictions exist, reassign point
            if contradictions:
                # Determine correct device type
                correct_type = self._determine_correct_device_type(point, contradictions)
                
                # Add reasoning
                verification.append("Contradictions found:")
                verification.extend([f"- {c}" for c in contradictions])
                verification.append(f"Reassigning to device type: {correct_type}")
                
                # Add point to correct group with verification reasoning
                point_copy = dict(point)
                
                # Merge existing reasoning with verification
                if "grouping_reasoning" in point_copy:
                    point_copy["verification_reasoning"] = [
                        *verification,
                        "Original grouping reasoning:",
                        *point_copy["grouping_reasoning"]
                    ]
                else:
                    point_copy["verification_reasoning"] = verification
                
                # Remove grouping_reasoning to avoid duplication
                if "grouping_reasoning" in point_copy:
                    del point_copy["grouping_reasoning"]
                
                # Add to correct group
                if correct_type not in result:
                    result[correct_type] = []
                
                result[correct_type].append(point_copy)
                
            else:
                # No contradictions, keep in original group
                verification.append("No contradictions found, assignment verified")
                
                # Create a copy to avoid modifying the original
                point_copy = dict(point)
                
                # Store verification reasoning
                if "grouping_reasoning" in point_copy:
                    point_copy["verification_reasoning"] = [
                        *verification,
                        "Original grouping reasoning:",
                        *point_copy["grouping_reasoning"]
                    ]
                    # Remove grouping_reasoning to avoid duplication
                    del point_copy["grouping_reasoning"]
                else:
                    point_copy["verification_reasoning"] = verification
                
                # Keep in original group
                result[device_type].append(point_copy)
        
        # Log verification results
        reassignment_count = sum(len(points) for dev_type, points in result.items() if dev_type != device_type)
        self.logger.log_reasoning_step("verify_group_assignment", 
            f"Verification complete: {reassignment_count} points reassigned from '{device_type}'")
        
        # Remove empty groups
        return {k: v for k, v in result.items() if v}

    def _determine_correct_device_type(
        self,
        point: Dict[str, Any],
        contradictions: List[str]
    ) -> str:
        """Determine the correct device type for a point with contradictions.
        
        Args:
            point: The point to reassign
            contradictions: List of contradiction reasons
            
        Returns:
            The corrected device type
        """
        point_name = point.get("pointName", "").lower()
        description = point.get("description", "").lower()
        
        # Extract key terms for classification
        key_terms = []
        for text in [point_name, description]:
            key_terms.extend(re.findall(r'[a-z]+', text.lower()))
        
        # Check for hierarchical naming patterns
        if '.' in point_name:
            parts = point_name.split('.')
            # If we have a clear parent.child structure, use the parent
            if len(parts) >= 2 and any(sys_id in parts[0].upper() for sys_id in 
                                      ["CH-SYS", "AHU", "VAV", "FCU"]):
                system_id = parts[0]
                
                # Extract system type from hierarchical name
                if "CH-SYS" in system_id.upper():
                    # For CH-SYS, also check the component
                    if len(parts) >= 2:
                        component = parts[1].upper()
                        if "CHWP" in component or "CWP" in component:
                            return "CHWP"
                        elif "CH" in component and "CHWP" not in component:
                            return "CH"
                        elif "CT" in component:
                            return "CT"
                    return "CH-SYS"
                elif "AHU" in system_id.upper():
                    return "AHU"
                elif "VAV" in system_id.upper():
                    return "VAV"
                elif "FCU" in system_id.upper():
                    return "FCU"
        
        # Heuristic patterns for specific device types
        if any(term in point_name for term in ["chwp", "chw pump", "chilled water pump"]):
            return "CHWP"
        elif any(term in point_name for term in ["vav", "box", "terminal", "zone"]) and "temp" in point_name:
            return "VAV"
        elif any(term in point_name for term in ["ahu", "air handler", "air handling"]):
            return "AHU"
        elif any(term in point_name for term in ["fcu", "fan coil"]):
            return "FCU"
        elif any(term in point_name for term in ["ch-sys", "chiller", "chilled water"]) and not any(term in point_name for term in ["pump", "chwp"]):
            return "CH-SYS"
        
        # If point clearly contains VSD and pump terms, it's likely a pump
        if ("vsd" in point_name or "variable speed" in point_name) and "pump" in point_name:
            if "chilled" in point_name or "chw" in point_name:
                return "CHWP"
            else:
                return "PUMP"
        
        # Analyze contradiction messages for clues
        for contradiction in contradictions:
            # If moving from VAV but contains AHU terms, assign to AHU
            if "VAV" in contradiction and any(term in contradiction for term in ["ahu", "air handling", "central"]):
                return "AHU"
            # If moving from AHU but contains VAV terms, assign to VAV
            elif "AHU" in contradiction and any(term in contradiction for term in ["vav", "terminal", "zone"]):
                return "VAV"
            # If moving from CH-SYS but contains air terms, assign to AHU
            elif "CH-SYS" in contradiction and any(term in contradiction for term in ["airflow", "damper", "duct"]):
                return "AHU"
            # If moving from CHWP but contains other CH-SYS terms, assign to CH-SYS
            elif "CHWP" in contradiction and any(term in contradiction for term in ["cooling tower", "condenser", "chiller"]):
                # Check specific component mentioned
                if "cooling tower" in contradiction or "ct" in point_name:
                    return "CT"
                elif "chiller" in contradiction:
                    return "CH"
                else:
                    return "CH-SYS"
        
        # Analyze point functions for terminal vs central system classification
        if any(term in point_name for term in ["room", "space", "zone"]) and "temp" in point_name:
            return "TU"  # Terminal Unit
        elif any(term in point_name for term in ["setpoint", "spt", "cmd", "command"]):
            if "temp" in point_name:
                if any(term in point_name for term in ["room", "space", "zone"]):
                    return "VAV"
                else:
                    return "AHU"
            elif "flow" in point_name:
                return "CHWP"
        
        # Use simple keyword matching as last resort
        if "pump" in point_name:
            if "chilled" in point_name or "chw" in point_name:
                return "CHWP"
            else:
                return "PUMP"
        elif "fan" in point_name:
            if "coil" in point_name:
                return "FCU"
            else:
                return "AHU"
        elif "temp" in point_name:
            if "room" in point_name or "space" in point_name:
                return "TU"
            else:
                return "SENSOR"
        
        # Default fallback
        return "MISC"
        
    def calculate_group_confidence(
        self,
        device_type: str,
        points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate confidence scores for group assignment.
        
        Args:
            device_type: Device type
            points: Points in this group
            
        Returns:
            Dictionary with confidence scores
        """
        # Initialize scores
        scores = {
            "overall": 0.0,
            "details": {
                "naming_pattern": 0.0,
                "point_types": 0.0,
                "units": 0.0,
                "coherence": 0.0
            }
        }
        
        # Check naming pattern consistency
        prefix_patterns = self._analyze_naming_patterns(points)
        pattern_score = self._score_naming_patterns(prefix_patterns, device_type)
        scores["details"]["naming_pattern"] = pattern_score
        
        # Check point type consistency
        point_types = [p.get("pointType", "") for p in points]
        expected_types = self._get_expected_point_types(device_type)
        type_score = self._score_point_types(point_types, expected_types)
        scores["details"]["point_types"] = type_score
        
        # Check unit consistency
        units = [p.get("unit", "") for p in points]
        expected_units = self._get_expected_units(device_type)
        unit_score = self._score_units(units, expected_units)
        scores["details"]["units"] = unit_score
        
        # Check overall coherence
        coherence_score = self._calculate_coherence(points, device_type)
        scores["details"]["coherence"] = coherence_score
        
        # Calculate overall score (weighted average)
        weights = {
            "naming_pattern": 0.4,
            "point_types": 0.2,
            "units": 0.2,
            "coherence": 0.2
        }
        
        overall_score = sum(
            scores["details"][key] * weight 
            for key, weight in weights.items()
        )
        
        scores["overall"] = overall_score
        
        return scores

    def _analyze_naming_patterns(
        self,
        points: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Analyze naming patterns in a group of points.
        
        Args:
            points: List of points to analyze
            
        Returns:
            Dictionary mapping prefixes to their frequency
        """
        prefixes = {}
        
        for point in points:
            point_name = point.get("pointName", "")
            
            # Extract potential prefix (first part of name before separator)
            for separator in [".", "_", "-", " "]:
                if separator in point_name:
                    prefix = point_name.split(separator)[0]
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                    break
            else:
                # No separator found, use first 3 characters as prefix
                if len(point_name) >= 3:
                    prefix = point_name[:3]
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
        
        return prefixes

    def _score_naming_patterns(
        self,
        prefix_patterns: Dict[str, int],
        device_type: str
    ) -> float:
        """Score naming pattern consistency.
        
        Args:
            prefix_patterns: Dictionary mapping prefixes to their frequency
            device_type: Expected device type
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not prefix_patterns:
            return 0.0
        
        # Get total number of points
        total_points = sum(prefix_patterns.values())
        
        # Get most common prefix
        most_common_prefix = max(prefix_patterns.items(), key=lambda x: x[1])
        most_common_count = most_common_prefix[1]
        
        # Calculate dominance ratio of most common prefix
        dominance_ratio = most_common_count / total_points if total_points > 0 else 0
        
        # Check if most common prefix matches expected device type
        prefix_matches_type = False
        device_type_lower = device_type.lower()
        most_common_prefix_lower = most_common_prefix[0].lower()
        
        if device_type_lower in most_common_prefix_lower or most_common_prefix_lower in device_type_lower:
            prefix_matches_type = True
        
        # Calculate final score
        base_score = dominance_ratio * 0.8  # Base score from dominance ratio
        type_match_bonus = 0.2 if prefix_matches_type else 0.0  # Bonus for matching device type
        
        return base_score + type_match_bonus

    def _get_expected_point_types(
        self,
        device_type: str
    ) -> List[str]:
        """Get expected point types for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            List of expected point types
        """
        # Define expected point types for common device types
        expected_types = {
            "AHU": ["AI", "AO", "BI", "BO"],
            "VAV": ["AI", "AO", "BI", "BO"],
            "FCU": ["AI", "AO", "BI", "BO"],
            "Chiller": ["AI", "AO", "BI", "BO"],
            "Boiler": ["AI", "AO", "BI", "BO"],
            "Pump": ["AI", "BI", "BO"],
            "Fan": ["AI", "BI", "BO"],
            "Lighting": ["BI", "BO"],
            "Meter": ["AI"],
            "Sensor": ["AI", "BI"]
        }
        
        return expected_types.get(device_type, [])

    def _score_point_types(
        self,
        point_types: List[str],
        expected_types: List[str]
    ) -> float:
        """Score point type consistency.
        
        Args:
            point_types: List of point types
            expected_types: List of expected point types
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not point_types or not expected_types:
            return 0.5  # Neutral score if no data available
        
        # Count points with expected types
        matching_count = sum(1 for pt in point_types if pt in expected_types)
        
        # Calculate ratio of matching points
        matching_ratio = matching_count / len(point_types) if point_types else 0
        
        return matching_ratio

    def _get_expected_units(
        self,
        device_type: str
    ) -> Dict[str, List[str]]:
        """Get expected units for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            Dictionary mapping point functions to expected units
        """
        # Define expected units for common point functions
        common_units = {
            "temperature": ["°C", "°F", "C", "F", "deg C", "deg F"],
            "pressure": ["Pa", "kPa", "psi", "inH2O", "bar"],
            "flow": ["m3/h", "l/s", "gpm", "cfm"],
            "humidity": ["%", "%RH", "percent", "% RH"],
            "power": ["kW", "W", "kWh", "MW"],
            "status": ["", "on/off", "open/closed"]
        }
        
        # Define expected units for device types by function
        expected_units = {
            "AHU": {
                "temperature": common_units["temperature"],
                "pressure": common_units["pressure"],
                "flow": common_units["flow"],
                "humidity": common_units["humidity"],
                "status": common_units["status"]
            },
            "VAV": {
                "temperature": common_units["temperature"],
                "flow": common_units["flow"],
                "pressure": common_units["pressure"],
                "status": common_units["status"]
            },
            "FCU": {
                "temperature": common_units["temperature"],
                "flow": common_units["flow"],
                "status": common_units["status"]
            },
            "Chiller": {
                "temperature": common_units["temperature"],
                "flow": common_units["flow"],
                "power": common_units["power"],
                "status": common_units["status"]
            },
            "Boiler": {
                "temperature": common_units["temperature"],
                "flow": common_units["flow"],
                "pressure": common_units["pressure"],
                "status": common_units["status"]
            },
            "Pump": {
                "flow": common_units["flow"],
                "pressure": common_units["pressure"],
                "status": common_units["status"]
            },
            "Fan": {
                "flow": common_units["flow"],
                "pressure": common_units["pressure"],
                "status": common_units["status"]
            },
            "Meter": {
                "power": common_units["power"],
                "flow": common_units["flow"]
            }
        }
        
        return expected_units.get(device_type, {})

    def _score_units(
        self,
        units: List[str],
        expected_units: Dict[str, List[str]]
    ) -> float:
        """Score unit consistency.
        
        Args:
            units: List of units
            expected_units: Dictionary mapping point functions to expected units
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not units or not expected_units:
            return 0.5  # Neutral score if no data available
        
        # Flatten expected units into a single list
        all_expected_units = []
        for function_units in expected_units.values():
            all_expected_units.extend(function_units)
        
        # Count points with expected units
        matching_count = sum(1 for unit in units if unit in all_expected_units)
        
        # Calculate ratio of matching units
        matching_ratio = matching_count / len(units) if units else 0
        
        return matching_ratio

    def _calculate_coherence(
        self,
        points: List[Dict[str, Any]],
        device_type: str
    ) -> float:
        """Calculate overall coherence of the group.
        
        Args:
            points: List of points
            device_type: Device type
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not points:
            return 0.0
        
        # Get expected point functions for this device type
        expected_functions = self._get_expected_functions(device_type)
        
        # Count how many expected functions are present
        function_coverage = 0
        for function in expected_functions:
            if any(function.lower() in p.get("pointName", "").lower() for p in points):
                function_coverage += 1
        
        # Calculate function coverage ratio
        function_ratio = function_coverage / len(expected_functions) if expected_functions else 0
        
        # Check for minimum expected number of points for this device type
        min_expected_points = self._get_min_expected_points(device_type)
        size_factor = min(1.0, len(points) / min_expected_points) if min_expected_points > 0 else 0.5
        
        # Combine factors
        coherence_score = (function_ratio * 0.7) + (size_factor * 0.3)
        
        return coherence_score

    def _get_expected_functions(
        self,
        device_type: str
    ) -> List[str]:
        """Get expected point functions for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            List of expected point functions
        """
        # Define expected functions for common device types
        expected_functions = {
            "AHU": ["temp", "temperature", "humidity", "pressure", "flow", "fan", "damper", "valve", "status"],
            "VAV": ["temp", "temperature", "flow", "damper", "valve", "setpoint", "status"],
            "FCU": ["temp", "temperature", "fan", "valve", "setpoint", "status"],
            "Chiller": ["temp", "temperature", "flow", "power", "status"],
            "Boiler": ["temp", "temperature", "pressure", "flow", "status"],
            "Pump": ["flow", "pressure", "speed", "status"],
            "Fan": ["flow", "pressure", "speed", "status"],
            "Lighting": ["level", "status"],
            "Meter": ["power", "energy", "flow"],
            "Sensor": ["temp", "temperature", "humidity", "co2", "occupancy"]
        }
        
        return expected_functions.get(device_type, [])

    def _get_min_expected_points(
        self,
        device_type: str
    ) -> int:
        """Get minimum expected number of points for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            Minimum expected number of points
        """
        # Define minimum expected points for common device types
        min_points = {
            "AHU": 8,
            "VAV": 5,
            "FCU": 4,
            "Chiller": 6,
            "Boiler": 5,
            "Pump": 3,
            "Fan": 3,
            "Lighting": 2,
            "Meter": 1,
            "Sensor": 1
        }
        
        return min_points.get(device_type, 3) 