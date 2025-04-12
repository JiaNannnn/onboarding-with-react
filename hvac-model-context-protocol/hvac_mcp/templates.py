"""
Templates Module.

This module provides reasoning templates for the HVAC Model Context Protocol,
defining structured steps for tasks like point name analysis and group verification.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Define the reasoning templates
REASONING_TEMPLATES = {
    "point_name_analysis": {
        "title": "Point Name Analysis",
        "description": "Systematic breakdown of a point name to identify device type, function, and measurement",
        "steps": [
            "Parse Point Name: Break down the point name into components using common delimiters ('.', '-', '_').",
            "Extract Prefix: Identify the potential device/system prefix (e.g., 'AHU-1', 'CH-SYS-1.CWP').",
            "Lookup Prefix in Ontology/KB: Match prefix against known system types and abbreviations defined in the Knowledge Base.",
            "Identify Measurement/Control Function: Analyze suffix components and keywords (e.g., 'Temp', 'Status', 'Cmd', 'Hz', 'SPT') using KB definitions to determine the point's purpose.",
            "Check Contradictory Evidence: Based on the potential system type identified in step 3, check if the function identified in step 4 is consistent.",
            "Evaluate Unit Consistency: Check if the provided 'Unit' aligns with the inferred point function (using KB unit mappings).",
            "Assign Confidence Score: Calculate a score based on the strength of prefix match, function identification clarity, and absence of contradictions.",
            "Generate Reasoning Summary: Construct a human-readable explanation following the steps above."
        ],
        "expected_output": {
            "device_type": "The identified primary device or system type (e.g., 'AHU', 'VAV', 'CH')",
            "point_type": "The type of point (e.g., 'SensorAnalog', 'SetpointCommand')",
            "function": "The specific function of the point (e.g., 'Temperature', 'Status', 'Command')",
            "location": "Optional: The specific location or medium (e.g., 'Supply Air', 'Return Air')",
            "confidence_score": "A value between 0 and 1 indicating confidence in the classification",
            "steps_followed": "Array of reasoning steps used to reach this conclusion"
        },
        "versioning": {
            "created": "1.0.0",
            "last_updated": "1.0.0"
        }
    },
    "group_verification": {
        "title": "Group Verification",
        "description": "Verification that a group of points belongs to the same device type",
        "steps": [
            "Identify Expected Point Characteristics: Based on the proposed Device Type, retrieve expected point functions, keywords, and units from the Ontology and KB.",
            "Validate Naming Consistency: Analyze prefixes and suffixes across points in the group. Calculate the dominance of the most common naming pattern.",
            "Check for Outliers: For each point, compare its inferred function and characteristics against the group's expected characteristics. Flag points with significant deviations or contradictions.",
            "Evaluate Cross-System Integration: Identify points that might link systems (e.g., a VAV reporting AHU supply temperature).",
            "Calculate Group Confidence: Score the group based on naming consistency, the proportion of points matching expected characteristics, and the number of unexplained outliers.",
            "Propose Reassignments: Suggest moving outlier points to more appropriate groups based on their individual characteristics."
        ],
        "expected_output": {
            "verified": "Boolean indicating if the group is verified as consistent",
            "confidence_score": "A value between 0 and 1 indicating confidence in the verification",
            "outliers": "Array of points that don't seem to fit with the group",
            "suggested_reassignments": "Map of outlier points to their suggested device types",
            "steps_followed": "Array of reasoning steps used to reach this conclusion"
        },
        "versioning": {
            "created": "1.0.0",
            "last_updated": "1.0.0"
        }
    },
    "ambiguity_resolution": {
        "title": "Ambiguity Resolution",
        "description": "Protocol for resolving points with multiple potential classifications or low confidence",
        "steps": [
            "Apply Classification Confidence Threshold: Determine if the point needs additional review based on confidence score.",
            "Analyze Multiple Matches Strategy: For points with multiple potential matches, check system relationships and naming conventions.",
            "Examine Temporal and Functional Patterns: Look for correlations with known system operations and match point function to system function.",
            "Apply System Prevalence Weighting: Consider facility-specific context like prevalent system types and typical point ratios.",
            "Handle Truly Ambiguous Points: For points that remain ambiguous, create a ranked list of possible classifications with explanations."
        ],
        "expected_output": {
            "final_classification": "The best classification or 'AMBIGUOUS'",
            "possible_classifications": "Ranked list of potential classifications with confidence scores",
            "ambiguity_sources": "Description of what makes this point ambiguous",
            "resolution_approach": "The specific rules or logic used to resolve or flag the ambiguity",
            "additional_info_needed": "Specific information that would help resolve the ambiguity"
        },
        "versioning": {
            "created": "1.0.0",
            "last_updated": "1.0.0"
        }
    },
    "time_based_reasoning": {
        "title": "Time-Based Reasoning",
        "description": "Using historical data patterns to enhance point classification",
        "steps": [
            "Retrieve Historical Data: Pull time-series data for the point and related points (if available).",
            "Extract Operational Patterns: Identify on/off cycles, setpoint changes, and operational correlations.",
            "Validate Point Function: Confirm that sensor values and behaviors match expected ranges and patterns.",
            "Generate Temporal Evidence: Document correlations that support the classification.",
            "Apply Temporal Confidence Boost: Adjust confidence score based on strength of temporal evidence."
        ],
        "expected_output": {
            "enhanced_classification": "The potentially revised classification based on temporal data",
            "confidence_adjustment": "How much the confidence score changed based on temporal evidence",
            "supporting_correlations": "Key temporal correlations that support the classification",
            "contradicting_patterns": "Any operational patterns that contradict the classification"
        },
        "versioning": {
            "created": "1.0.0",
            "last_updated": "1.0.0"
        }
    }
}

def get_reasoning_template(template_type: str) -> Optional[Dict[str, Any]]:
    """
    Get a reasoning template by type.
    
    Args:
        template_type: The type of template to retrieve
        
    Returns:
        The template dictionary or None if not found
    """
    return REASONING_TEMPLATES.get(template_type)

def get_protocol_steps(template_type: str) -> List[str]:
    """
    Get just the protocol steps for a template type.
    
    Args:
        template_type: The type of template to get steps for
        
    Returns:
        List of protocol steps
    """
    template = get_reasoning_template(template_type)
    if template:
        return template.get("steps", [])
    return []

def format_protocol_context(
    template_type: str,
    ontology_snippet: str,
    kb_snippet: str,
    protocol_version: str = "1.0.0"
) -> str:
    """
    Format the protocol context as a Markdown string for inclusion in LLM prompts.
    
    Args:
        template_type: The type of reasoning template to use
        ontology_snippet: Markdown string of relevant ontology sections
        kb_snippet: Markdown string of relevant knowledge base sections
        protocol_version: Version of the protocol
        
    Returns:
        Formatted protocol context
    """
    template = get_reasoning_template(template_type)
    if not template:
        logger.error(f"Unknown template type: {template_type}")
        return ""
    
    context = f"## PROTOCOL CONTEXT V{protocol_version}\n"
    context += f"### TASK: {template['title']}\n\n"
    
    # Add ontology snippet
    context += "### ONTOLOGY_SNIPPET\n"
    context += ontology_snippet + "\n\n"
    
    # Add knowledge base snippet
    context += "### KNOWLEDGE_BASE_SNIPPET\n"
    context += kb_snippet + "\n\n"
    
    # Add reasoning template
    context += "### REASONING_TEMPLATE\n"
    for i, step in enumerate(template["steps"], 1):
        context += f"{i}. {step}\n"
    
    context += "\n---\n"
    
    return context

def parse_llm_response(response: str, template_type: str) -> Dict[str, Any]:
    """
    Parse an LLM response to extract structured reasoning according to the template.
    
    Args:
        response: The LLM response text
        template_type: The type of reasoning template used
        
    Returns:
        Dictionary with extracted reasoning elements
    """
    template = get_reasoning_template(template_type)
    if not template:
        logger.error(f"Unknown template type: {template_type}")
        return {"error": f"Unknown template type: {template_type}"}
    
    # Initialize results with default values
    results = {key: None for key in template.get("expected_output", {}).keys()}
    results["steps_followed"] = []
    
    # Point Name Analysis parsing
    if template_type == "point_name_analysis":
        # Extract device type
        device_type_match = re.search(r"device[_\s]type[\s:]+([A-Za-z0-9-]+)", response, re.IGNORECASE)
        if device_type_match:
            results["device_type"] = device_type_match.group(1).strip()
        
        # Extract point type
        point_type_match = re.search(r"point[_\s]type[\s:]+([A-Za-z]+)", response, re.IGNORECASE)
        if point_type_match:
            results["point_type"] = point_type_match.group(1).strip()
        
        # Extract function
        function_match = re.search(r"function[\s:]+([A-Za-z ]+)", response, re.IGNORECASE)
        if function_match:
            results["function"] = function_match.group(1).strip()
        
        # Extract location (optional)
        location_match = re.search(r"location[\s:]+([A-Za-z ]+)", response, re.IGNORECASE)
        if location_match:
            results["location"] = location_match.group(1).strip()
        
        # Extract confidence score
        confidence_match = re.search(r"confidence[\s:]+(\d+(\.\d+)?)", response, re.IGNORECASE)
        if confidence_match:
            try:
                results["confidence_score"] = float(confidence_match.group(1))
            except ValueError:
                results["confidence_score"] = 0.0
        
    # Group Verification parsing
    elif template_type == "group_verification":
        # Extract verified status
        verified_match = re.search(r"verified[\s:]+(\w+)", response, re.IGNORECASE)
        if verified_match:
            results["verified"] = verified_match.group(1).lower() == "true"
        
        # Extract confidence score
        confidence_match = re.search(r"confidence[\s:]+(\d+(\.\d+)?)", response, re.IGNORECASE)
        if confidence_match:
            try:
                results["confidence_score"] = float(confidence_match.group(1))
            except ValueError:
                results["confidence_score"] = 0.0
        
        # Extract outliers
        outliers_section = re.search(r"outliers[\s:]+(.+?)(?=suggested|$)", response, re.IGNORECASE | re.DOTALL)
        if outliers_section:
            outlier_text = outliers_section.group(1).strip()
            # Process list format: "- item1\n- item2" or "1. item1\n2. item2" or comma-separated
            if "-" in outlier_text or re.search(r"\d+\.", outlier_text):
                results["outliers"] = [item.strip() for item in re.split(r"[-\d+\.]\s+", outlier_text) if item.strip()]
            else:
                results["outliers"] = [item.strip() for item in outlier_text.split(",") if item.strip()]
        
        # Extract suggested reassignments
        reassignment_section = re.search(r"suggested[_\s]reassignments[\s:]+(.+?)(?=steps|$)", response, re.IGNORECASE | re.DOTALL)
        if reassignment_section:
            reassignment_text = reassignment_section.group(1).strip()
            reassignments = {}
            
            # Process lines like "point1 -> deviceType1", "point2: deviceType2"
            for line in reassignment_text.split("\n"):
                if "->" in line:
                    point, device_type = line.split("->", 1)
                    reassignments[point.strip()] = device_type.strip()
                elif ":" in line:
                    point, device_type = line.split(":", 1)
                    reassignments[point.strip()] = device_type.strip()
            
            results["suggested_reassignments"] = reassignments
    
    # Ambiguity Resolution parsing
    elif template_type == "ambiguity_resolution":
        # Extract final classification
        final_match = re.search(r"final[_\s]classification[\s:]+([A-Za-z0-9_-]+)", response, re.IGNORECASE)
        if final_match:
            results["final_classification"] = final_match.group(1).strip()
        
        # Extract possible classifications
        possible_section = re.search(r"possible[_\s]classifications[\s:]+(.+?)(?=ambiguity|$)", response, re.IGNORECASE | re.DOTALL)
        if possible_section:
            possible_text = possible_section.group(1).strip()
            possible_classifications = []
            
            # Process lines like "1. AHU (0.8)", "- VAV (0.6)"
            for line in possible_text.split("\n"):
                if "(" in line and ")" in line:
                    class_match = re.search(r"[^a-zA-Z0-9]([A-Za-z0-9_-]+)\s*\((\d+(\.\d+)?)\)", line)
                    if class_match:
                        class_name = class_match.group(1).strip()
                        try:
                            confidence = float(class_match.group(2))
                            possible_classifications.append({"class": class_name, "confidence": confidence})
                        except ValueError:
                            possible_classifications.append({"class": class_name, "confidence": 0.0})
            
            results["possible_classifications"] = possible_classifications
    
    # Extract steps followed (common to all templates)
    steps_section = re.search(r"steps[_\s]followed[\s:]+(.+?)(?=\n\n|$)", response, re.IGNORECASE | re.DOTALL)
    if steps_section:
        steps_text = steps_section.group(1).strip()
        # Process list format: "- step1\n- step2" or "1. step1\n2. step2"
        if "-" in steps_text or re.search(r"\d+\.", steps_text):
            results["steps_followed"] = [step.strip() for step in re.split(r"[-\d+\.]\s+", steps_text) if step.strip()]
        else:
            results["steps_followed"] = [steps_text]
    
    return results

def extract_reasoning_from_sections(response_sections: Dict[str, str], template_type: str) -> Dict[str, Any]:
    """
    Extract reasoning from structured response sections.
    
    Args:
        response_sections: Dictionary of section names to section content
        template_type: The type of reasoning template used
        
    Returns:
        Dictionary with extracted reasoning elements
    """
    template = get_reasoning_template(template_type)
    if not template:
        logger.error(f"Unknown template type: {template_type}")
        return {"error": f"Unknown template type: {template_type}"}
    
    # Initialize results with default values
    results = {key: None for key in template.get("expected_output", {}).keys()}
    
    # Extract values from relevant sections
    for section, content in response_sections.items():
        section_key = section.lower().replace(" ", "_")
        if section_key in results:
            results[section_key] = content
    
    return results

def find_response_sections(response: str) -> Dict[str, str]:
    """
    Find and extract structured sections from an LLM response.
    
    Args:
        response: The LLM response text
        
    Returns:
        Dictionary mapping section names to their content
    """
    sections = {}
    
    # Look for section headers (e.g., "## Device Type:", "Device Type:", "DEVICE TYPE:")
    section_pattern = re.compile(r"(?:^|\n)(?:#{1,3}\s*)?([A-Za-z_\s]+):\s*(.+?)(?=(?:\n(?:#{1,3}\s*)?[A-Za-z_\s]+:|\Z))", re.DOTALL)
    
    for match in section_pattern.finditer(response):
        section_name = match.group(1).strip()
        section_content = match.group(2).strip()
        sections[section_name] = section_content
    
    return sections 