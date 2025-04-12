"""
Validation utilities for HVAC point names and reasoning results.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

def is_valid_point_name(point_name: str) -> bool:
    """
    Check if a point name follows expected formatting conventions.
    
    Args:
        point_name: Point name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not point_name or not isinstance(point_name, str):
        return False
    
    # Points should not be excessively long
    if len(point_name) > 100:
        return False
    
    # Points should not contain certain special characters
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', ';', '=']
    if any(char in point_name for char in invalid_chars):
        return False
    
    # Common patterns that indicate valid points
    valid_patterns = [
        # AHU-1.SA-TEMP
        r'^[A-Za-z]+-\d+[A-Za-z]*\.[A-Za-z]+-[A-Za-z]+$',
        # AHU-1.SA_TEMP
        r'^[A-Za-z]+-\d+[A-Za-z]*\.[A-Za-z]+_[A-Za-z]+$',
        # AHU-1_SA-TEMP
        r'^[A-Za-z]+-\d+[A-Za-z]*_[A-Za-z]+-[A-Za-z]+$',
        # AHU1.SATEMP
        r'^[A-Za-z]+\d+[A-Za-z]*\.[A-Za-z]+$',
        # AHU.1.SA.TEMP
        r'^[A-Za-z]+\.\d+\.[A-Za-z]+\.[A-Za-z]+$',
        # AHU.SA.TEMP
        r'^[A-Za-z]+\.[A-Za-z]+\.[A-Za-z]+$',
        # Generic patterns with common delimiters
        r'^[A-Za-z0-9]+([-_.][A-Za-z0-9]+)+$'
    ]
    
    # Check against patterns
    for pattern in valid_patterns:
        if re.match(pattern, point_name, re.IGNORECASE):
            return True
    
    return False

def validate_reasoning(reasoning: Dict[str, Any], template_type: str) -> Tuple[bool, List[str]]:
    """
    Validate that a reasoning result meets expected criteria.
    
    Args:
        reasoning: Reasoning result dictionary
        template_type: Type of reasoning template used
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Common validation for all template types
    if "steps_followed" not in reasoning or not reasoning["steps_followed"]:
        issues.append("Missing reasoning steps")
    
    # Point Name Analysis validation
    if template_type == "point_name_analysis":
        if "device_type" not in reasoning or not reasoning["device_type"]:
            issues.append("Missing device type classification")
        
        if "point_type" not in reasoning or not reasoning["point_type"]:
            issues.append("Missing point type classification")
        
        if "confidence_score" not in reasoning or reasoning["confidence_score"] is None:
            issues.append("Missing confidence score")
        elif reasoning["confidence_score"] < 0 or reasoning["confidence_score"] > 1:
            issues.append(f"Invalid confidence score: {reasoning['confidence_score']} (must be between 0 and 1)")
    
    # Group Verification validation
    elif template_type == "group_verification":
        if "verified" not in reasoning or reasoning["verified"] is None:
            issues.append("Missing verification status")
        
        if "confidence_score" not in reasoning or reasoning["confidence_score"] is None:
            issues.append("Missing confidence score")
        elif reasoning["confidence_score"] < 0 or reasoning["confidence_score"] > 1:
            issues.append(f"Invalid confidence score: {reasoning['confidence_score']} (must be between 0 and 1)")
        
        if "outliers" not in reasoning:
            issues.append("Missing outliers information")
    
    # Ambiguity Resolution validation
    elif template_type == "ambiguity_resolution":
        if "final_classification" not in reasoning or not reasoning["final_classification"]:
            issues.append("Missing final classification")
        
        if "possible_classifications" not in reasoning or not reasoning["possible_classifications"]:
            issues.append("Missing possible classifications")
    
    return len(issues) == 0, issues

def validate_protocol_context(context: str) -> Tuple[bool, List[str]]:
    """
    Validate that a protocol context includes all required sections.
    
    Args:
        context: Protocol context string
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check for required sections
    required_sections = [
        "PROTOCOL CONTEXT",
        "TASK",
        "ONTOLOGY_SNIPPET",
        "KNOWLEDGE_BASE_SNIPPET",
        "REASONING_TEMPLATE"
    ]
    
    for section in required_sections:
        if section not in context:
            issues.append(f"Missing required section: {section}")
    
    # Check for reasoning steps (numbered list)
    if not re.search(r'\d+\.\s+[A-Za-z]', context):
        issues.append("Reasoning template should include numbered steps")
    
    return len(issues) == 0, issues

def validate_expected_device_components(device_type: str, points: List[str]) -> Tuple[bool, float, List[str]]:
    """
    Validate that a list of points contains expected components for a device type.
    
    Args:
        device_type: Device type to validate against
        points: List of point names
        
    Returns:
        Tuple of (has_minimum_components, coverage_score, missing_critical_components)
    """
    # Define expected critical components by device type
    critical_components = {
        "AHU": ["SA", "TEMP", "FAN", "STAT"],
        "VAV": ["FLOW", "TEMP", "DMPR", "ZN"],
        "FCU": ["FAN", "TEMP", "STAT"],
        "CH": ["STAT", "TEMP", "COND", "FLOW"],
        "CWP": ["STAT", "FLOW", "PRESS"],
        "CT": ["STAT", "TEMP", "FAN"],
        "BLR": ["STAT", "TEMP", "PRESS"]
    }
    
    # If device type is not in our list, can't validate
    if device_type not in critical_components:
        return False, 0.0, ["Unknown device type"]
    
    # Get the critical components for this device type
    expected = critical_components[device_type]
    
    # Check which components are present in the point names
    components_present = []
    for component in expected:
        if any(component in point.upper() for point in points):
            components_present.append(component)
    
    # Calculate coverage score
    coverage_score = len(components_present) / len(expected) if expected else 0.0
    
    # Determine missing critical components
    missing = [comp for comp in expected if comp not in components_present]
    
    # A device should have at least 50% of its critical components to be valid
    has_minimum = coverage_score >= 0.5
    
    return has_minimum, coverage_score, missing 