from typing import Dict, List, Any, Optional, Tuple
import json
import os
import re
from datetime import datetime
from agents import Runner

# Import logging system
from app.bms.logging import ReasoningLogger

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
            "OA": "Outside Air"
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
        """Extract potential device type prefix from point name.
        
        Args:
            point_name: Name of the point
            
        Returns:
            Extracted prefix or None
        """
        # Common patterns for device type prefixes
        patterns = [
            r"^([A-Z]+-[A-Z]+)-\d+",  # e.g., "CH-SYS-1"
            r"^([A-Z]+)-\d+",         # e.g., "AHU-1"
            r"^([A-Z]+\d+)",          # e.g., "VAV12"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, point_name)
            if match:
                return match.group(1)
        
        # Try a more generic pattern for detecting device prefixes
        components = point_name.split(".")
        if components and components[0]:
            # Return first component as potential prefix
            return components[0]
        
        return None

    def reason_device_type_from_prefix(
        self,
        prefix: str,
        points: List[Dict[str, Any]]
    ) -> Tuple[List[str], str]:
        """Reason about device type from prefix with CoT.
        
        Args:
            prefix: Extracted prefix
            points: Points with this prefix
            
        Returns:
            Tuple of (reasoning chain, determined device type)
        """
        # Initialize reasoning chain
        reasoning_chain = [
            f"Analyzing prefix '{prefix}' for {len(points)} points:"
        ]
        
        # Analyze prefix components
        components = re.split(r'[-_.]', prefix)
        reasoning_chain.append(f"Prefix components: {components}")
        
        # Interpret abbreviations in prefix
        abbr_meanings = []
        for component in components:
            if component in self.abbreviations:
                abbr_meanings.append(f"{component} = {self.abbreviations[component]}")
        
        if abbr_meanings:
            reasoning_chain.append(f"Abbreviation meanings: {', '.join(abbr_meanings)}")
        
        # Analyze point names to find common patterns
        suffixes = []
        units = set()
        
        for point in points:
            point_name = point.get("pointName", "")
            if point_name.startswith(prefix):
                suffix = point_name[len(prefix):].lstrip(".-_")
                suffixes.append(suffix)
            
            unit = point.get("unit", "").lower()
            if unit:
                units.add(unit)
        
        reasoning_chain.append(f"Common suffixes: {suffixes[:5]}{' (truncated)' if len(suffixes) > 5 else ''}")
        
        if units:
            reasoning_chain.append(f"Units in group: {', '.join(units)}")
        
        # Apply heuristic rules for device type identification
        device_type = "unknown"
        
        # Check for common device types
        prefix_lower = prefix.lower()
        if "ch" in prefix_lower and "sys" in prefix_lower:
            device_type = "CH-SYS"
            reasoning_chain.append("Prefix contains 'CH' and 'SYS', indicating a Chiller System")
        elif "ahu" in prefix_lower:
            device_type = "AHU"
            reasoning_chain.append("Prefix contains 'AHU', indicating an Air Handling Unit")
        elif "vav" in prefix_lower:
            device_type = "VAV"
            reasoning_chain.append("Prefix contains 'VAV', indicating a Variable Air Volume unit")
        elif "fcu" in prefix_lower:
            device_type = "FCU"
            reasoning_chain.append("Prefix contains 'FCU', indicating a Fan Coil Unit")
        elif "cwp" in prefix_lower or ("pump" in prefix_lower and "chw" in prefix_lower):
            device_type = "PUMP"
            reasoning_chain.append("Prefix contains pump-related terms, indicating a Pump")
        elif "ct" in prefix_lower or "tower" in prefix_lower:
            device_type = "CT"
            reasoning_chain.append("Prefix contains cooling tower terms, indicating a Cooling Tower")
        elif "blr" in prefix_lower or "boiler" in prefix_lower:
            device_type = "BOILER"
            reasoning_chain.append("Prefix contains boiler terms, indicating a Boiler")
        
        # Analyze suffixes for additional clues
        has_temp = any("temp" in suffix.lower() for suffix in suffixes)
        has_flow = any("flow" in suffix.lower() for suffix in suffixes)
        has_pressure = any("pressure" in suffix.lower() or "press" in suffix.lower() for suffix in suffixes)
        
        # Use suffix patterns to refine device type
        if device_type == "unknown":
            if has_temp and has_flow:
                device_type = "AHU"
                reasoning_chain.append("Points include temperature and flow measurements, likely an Air Handling Unit")
            elif has_pressure:
                device_type = "CH-SYS"
                reasoning_chain.append("Points include pressure measurements, likely a Chiller System")
        
        reasoning_chain.append(f"Determined device type: {device_type}")
        
        return reasoning_chain, device_type

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
        # Prepare LLM prompt for batch reasoning
        point_names = [point.get("pointName", "") for point in points]
        
        prompt = f"""Analyze these Building Management System (BMS) point names and group them by likely device type.
For each point, determine the most probable device type from these categories:
- CH-SYS: Chiller System
- AHU: Air Handling Unit
- VAV: Variable Air Volume unit
- FCU: Fan Coil Unit
- METER: Metering device
- MISC: Miscellaneous device

Point names:
{chr(10).join(point_names)}

Explain your reasoning for each group, then output each group in JSON format:
{{
  "device_type": (determined device type),
  "points": [(indices of points in this group, 0-based)],
  "reasoning": [(reasoning steps)]
}}
"""
        
        # Execute LLM reasoning (this could use self.mapping_agent with an appropriate wrapper)
        # For now, we'll implement a simpler rule-based grouping as a fallback
        
        # Mock response parsing
        groups = self._mock_batch_grouping(points)
        
        return groups

    def verify_group_assignment(
        self,
        device_type: str,
        points: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Verify group assignments and resolve potential conflicts.
        
        Args:
            device_type: Proposed device type
            points: Points in this group
            
        Returns:
            Dictionary of verified device types and their points
        """
        # Initialize result with original group
        result = {device_type: []}
        
        # Analyze each point in the group
        for point in points:
            point_name = point.get("pointName", "")
            
            # Start verification reasoning
            verification = [
                f"Verifying '{point_name}' as device type '{device_type}':"
            ]
            
            # Check for contradicting evidence
            contradictions = []
            
            # Example: VAV points shouldn't have chiller-specific terms
            if device_type == "VAV" and any(term in point_name.lower() for term in ["chiller", "compressor", "condenser"]):
                contradictions.append(f"Point name contains chiller-specific terms, inconsistent with VAV classification")
            
            # Example: CH-SYS points shouldn't have airflow-specific terms
            if device_type == "CH-SYS" and any(term in point_name.lower() for term in ["airflow", "damper", "duct"]):
                contradictions.append(f"Point name contains airflow-specific terms, inconsistent with CH-SYS classification")
            
            # Add more device-specific contradiction rules
            if device_type == "AHU" and any(term in point_name.lower() for term in ["zone", "room", "space", "vav"]):
                contradictions.append(f"Point name contains zone-specific terms, may be a VAV or FCU instead of AHU")
                
            if device_type == "FCU" and any(term in point_name.lower() for term in ["chw", "chiller", "cooling tower"]):
                contradictions.append(f"Point name contains chiller system terms, inconsistent with FCU classification")
            
            # If contradictions exist, reassign point
            if contradictions:
                # Determine correct device type
                correct_type = self._determine_correct_device_type(point, contradictions)
                
                # Add reasoning
                verification.append("Contradictions found:")
                verification.extend([f"- {c}" for c in contradictions])
                verification.append(f"Reassigning to device type: {correct_type}")
                
                # Add point to correct group
                if correct_type not in result:
                    result[correct_type] = []
                
                # Store verification reasoning
                point["verification_reasoning"] = verification
                
                # Add to correct group
                result[correct_type].append(point)
            else:
                # No contradictions, keep in original group
                verification.append("No contradictions found, assignment verified")
                
                # Store verification reasoning
                point["verification_reasoning"] = verification
                
                # Keep in original group
                result[device_type].append(point)
        
        return result

    def _determine_correct_device_type(
        self,
        point: Dict[str, Any],
        contradictions: List[str]
    ) -> str:
        """Determine correct device type based on contradictions.
        
        Args:
            point: Point data
            contradictions: List of contradiction explanations
            
        Returns:
            Corrected device type
        """
        # This is a simplified version, real implementation would use more sophisticated rules
        point_name = point.get("pointName", "").lower()
        
        if any(term in point_name for term in ["chiller", "compressor", "condenser", "cooling", "ch-", "ch."]):
            return "CH-SYS"
        elif any(term in point_name for term in ["ahu", "air", "handling", "airflow", "damper"]):
            return "AHU"
        elif any(term in point_name for term in ["vav", "variable", "air", "volume", "zone"]):
            return "VAV"
        elif any(term in point_name for term in ["fcu", "fan", "coil"]):
            return "FCU"
        elif any(term in point_name for term in ["meter", "consumption", "energy", "power"]):
            return "METER"
        else:
            return "MISC"

    def _mock_batch_grouping(
        self, 
        points: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Mock implementation of batch grouping (for development only).
        
        Args:
            points: Points to group
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        # Simple rule-based grouping
        groups = {
            "CH-SYS": [],
            "AHU": [],
            "VAV": [],
            "MISC": []
        }
        
        for point in points:
            point_name = point.get("pointName", "").lower()
            
            # Add mock reasoning chains
            reasoning = [
                f"Analyzing point name: {point.get('pointName', '')}",
                "Looking for device type indicators in the name"
            ]
            
            # Simple keyword matching
            if any(term in point_name for term in ["chiller", "ch-", "cooling", "condenser"]):
                reasoning.append("Found chiller-related terms, categorizing as CH-SYS")
                point["grouping_reasoning"] = reasoning
                groups["CH-SYS"].append(point)
            elif any(term in point_name for term in ["ahu", "air", "handling"]):
                reasoning.append("Found air handling unit terms, categorizing as AHU")
                point["grouping_reasoning"] = reasoning
                groups["AHU"].append(point)
            elif any(term in point_name for term in ["vav", "variable", "zone"]):
                reasoning.append("Found variable air volume terms, categorizing as VAV")
                point["grouping_reasoning"] = reasoning
                groups["VAV"].append(point)
            else:
                reasoning.append("No clear device type indicators, categorizing as MISC")
                point["grouping_reasoning"] = reasoning
                groups["MISC"].append(point)
        
        # Filter out empty groups
        return {k: v for k, v in groups.items() if v}
        
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