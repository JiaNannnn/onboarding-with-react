"""
Integration Example for HVAC Model Context Protocol.

This example demonstrates how to integrate the protocol with an existing
reasoning engine for analyzing HVAC point names.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional

# Add parent directory to path to import hvac_mcp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hvac_mcp import ProtocolEngine

# Simulated function for calling an LLM API
def call_llm_with_prompt(prompt: str) -> str:
    """
    Simulated function for calling an LLM API.
    
    In a real application, this would call the OpenAI API, Anthropic API, or similar.
    For this example, we just return a predefined response.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response
    """
    print("\n=== SENDING PROMPT TO LLM ===")
    print(f"Prompt length: {len(prompt)} characters")
    print("First 100 characters of prompt:")
    print(prompt[:100] + "...\n")
    
    # In a real application, this would be the API call
    # response = openai.Completion.create(prompt=prompt, model="gpt-4", max_tokens=500)
    
    # For demonstration, return a simulated response
    return """
## Device Type: AHU
## Point Type: SensorAnalog
## Function: Temperature
## Location: Supply Air
## Confidence Score: 0.85

## Steps Followed:
1. Parsed Point Name: Split "AHU-1.SA-TEMP" into components.
2. Extracted Prefix: Identified "AHU-1" as the potential device prefix.
3. Looked up Prefix: Matched "AHU" against the Knowledge Base as "Air Handling Unit".
4. Identified Measurement Function: "TEMP" corresponds to Temperature measurement.
5. Checked for Contradictions: Found no contradicting evidence for an AHU having a temperature point.
6. Evaluated Unit Consistency: The unit "degF" is appropriate for a temperature measurement.
7. Assigned Confidence Score: High confidence (0.85) due to clear matching of all components.
8. Reasoning Summary: This point is a Supply Air Temperature sensor for Air Handling Unit 1.
"""

# Function that would normally use basic LLM reasoning
def original_reason_device_type(point_name: str, unit: Optional[str] = None) -> Dict[str, Any]:
    """
    Original function for reasoning about a point name without protocol context.
    
    Args:
        point_name: The point name to analyze
        unit: Optional unit for the point
        
    Returns:
        Dictionary with classification results
    """
    # Create a basic prompt without the protocol context
    prompt = f"""
Please analyze the following Building Management System (BMS) point name and determine:
1. The most likely device type it belongs to
2. The type of point (sensor, command, etc.)
3. The function of the point
4. Your confidence level (0-1)

Point Name: {point_name}
Unit: {unit if unit else "Not specified"}
"""
    
    # Call the LLM with the basic prompt
    response = call_llm_with_prompt(prompt)
    
    # In a real application, response parsing would be more robust
    # For simplicity, we're just returning the response
    return {
        "point_name": point_name,
        "response": response,
        "protocol_used": False
    }

# Enhanced function using the HVAC Model Context Protocol
def protocol_reason_device_type(point_name: str, unit: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhanced function for reasoning about a point name with protocol context.
    
    Args:
        point_name: The point name to analyze
        unit: Optional unit for the point
        
    Returns:
        Dictionary with classification results and structured reasoning
    """
    # Initialize the protocol engine
    protocol_engine = ProtocolEngine()
    
    # Generate optimized protocol context
    protocol_context = protocol_engine.generate_context(
        [point_name],  # Typically we'd include similar points for better context
        "point_name_analysis"
    )
    
    # Create the enhanced prompt with protocol context
    prompt = f"""{protocol_context}
## USER PROMPT
Analyze the following point name and determine its classification:
Point Name: {point_name}
Unit: {unit if unit else "Not specified"}

Provide your analysis following the reasoning template steps above.
"""
    
    # Call the LLM with the enhanced prompt
    response = call_llm_with_prompt(prompt)
    
    # Extract structured reasoning from the response
    reasoning = protocol_engine.extract_reasoning_from_response(
        response,
        "point_name_analysis"
    )
    
    return {
        "point_name": point_name,
        "structured_reasoning": reasoning,
        "response": response,
        "protocol_used": True
    }

# Example function for verifying a group of points
def protocol_verify_group(points: List[str], proposed_device_type: str) -> Dict[str, Any]:
    """
    Verify that a group of points belongs to the same device type using the protocol.
    
    Args:
        points: List of point names to verify
        proposed_device_type: The proposed device type for the group
        
    Returns:
        Dictionary with verification results
    """
    # Initialize the protocol engine
    protocol_engine = ProtocolEngine()
    
    # Generate optimized protocol context
    protocol_context = protocol_engine.generate_context(
        points,
        "group_verification"
    )
    
    # Create the prompt with protocol context
    prompt = f"""{protocol_context}
## USER PROMPT
Verify if the following points belong to the same device type:
Proposed Device Type: {proposed_device_type}
Points: {", ".join(points)}

Provide your verification following the reasoning template steps above.
"""
    
    # Call the LLM with the enhanced prompt
    response = call_llm_with_prompt(prompt)
    
    # Extract structured reasoning from the response
    reasoning = protocol_engine.extract_reasoning_from_response(
        response,
        "group_verification"
    )
    
    return {
        "points": points,
        "proposed_device_type": proposed_device_type,
        "verification_result": reasoning,
        "response": response
    }

def main():
    """
    Main function to demonstrate the protocol usage.
    """
    print("HVAC Model Context Protocol - Integration Example")
    print("=================================================\n")
    
    # Sample point names for demonstration
    point_names = [
        "AHU-1.SA-TEMP",
        "VAV-3.DMPR-POS",
        "FCU-2.FAN-STAT",
        "CH-SYS.CH-1.COND-TEMP"
    ]
    
    # Compare original and protocol-enhanced reasoning for a point
    print("\n=== COMPARING ORIGINAL VS PROTOCOL-ENHANCED REASONING ===")
    sample_point = point_names[0]
    
    print(f"\nAnalyzing point: {sample_point}")
    print("\nWithout Protocol Context:")
    original_result = original_reason_device_type(sample_point, "degF")
    
    print("\nWith Protocol Context:")
    protocol_result = protocol_reason_device_type(sample_point, "degF")
    
    # Show structured reasoning extracted from the protocol response
    print("\n=== STRUCTURED REASONING EXTRACTED FROM RESPONSE ===")
    print(json.dumps(protocol_result["structured_reasoning"], indent=2))
    
    # Example of group verification
    print("\n=== GROUP VERIFICATION EXAMPLE ===")
    group_points = [
        "AHU-1.SA-TEMP",
        "AHU-1.RA-TEMP",
        "AHU-1.OA-DMPR",
        "AHU-1.SF-STAT",
        "VAV-3.DMPR-POS"  # This is an outlier
    ]
    verification_result = protocol_verify_group(group_points, "AHU")
    
    # Show structured verification result
    print("\n=== STRUCTURED VERIFICATION RESULT ===")
    print(json.dumps(verification_result["verification_result"], indent=2))
    
    print("\n=== EXAMPLE COMPLETE ===")

if __name__ == "__main__":
    main() 