# Phase 1: Enhanced Reasoning Architecture - Detailed Design

## API Endpoints Design

### 1. New Endpoints
```python
# app/bms/routes.py

@router.post("/points/map-with-reasoning")
async def map_points_with_reasoning(
    points_data: List[PointData], 
    reasoning_level: Optional[int] = 1,
    request: Request
):
    """Map BMS points to EnOS points with reasoning capabilities.
    
    Args:
        points_data: List of points to map
        reasoning_level: Level of reasoning detail (1-3)
        
    Returns:
        Mapped points with reasoning chains
    """
    mapper = get_mapper(request.app.state)
    result = await mapper.map_points_with_reasoning(points_data, reasoning_level)
    return result

@router.post("/points/reflect-and-remap/{point_id}")
async def reflect_and_remap_point(
    point_id: str,
    point_data: PointData,
    previous_result: MappingResult,
    request: Request
):
    """Reflect on a previous mapping attempt and try remapping.
    
    Args:
        point_id: ID of the point to remap
        point_data: Original point data
        previous_result: Previous mapping result
        
    Returns:
        New mapping result with reflection data
    """
    mapper = get_mapper(request.app.state)
    result = await mapper.reflect_and_remap(point_id, point_data, previous_result)
    return result

@router.post("/points/reflect-and-remap-batch")
async def reflect_and_remap_points_batch(
    points_data: List[PointData],
    previous_results: List[MappingResult],
    batch_size: Optional[int] = 20,
    request: Request
):
    """Reflect on previous mapping attempts and try remapping multiple points at once.
    
    Args:
        points_data: List of original point data
        previous_results: List of previous mapping results
        batch_size: Size of each processing batch (default: 20)
        
    Returns:
        New mapping results with reflection data
    """
    if len(points_data) != len(previous_results):
        raise HTTPException(status_code=400, detail="The number of points and previous results must match")
        
    mapper = get_mapper(request.app.state)
    results = await mapper.reflect_and_remap_batch(points_data, previous_results, batch_size)
    return results
```

## EnOSMapper Class Modifications

### 1. New Methods
```python
# app/bms/mapping.py

class EnOSMapper:
    # ... existing code ...
    
    async def map_points_with_reasoning(
        self, 
        points: List[Dict[str, Any]], 
        reasoning_level: int = 1
    ) -> List[Dict[str, Any]]:
        """Map points with explicit reasoning steps.
        
        Args:
            points: List of points to map
            reasoning_level: Level of reasoning detail (1-3)
            
        Returns:
            Mapped points with reasoning chains
        """
        # Group points based on device type with CoT reasoning
        grouped_points = self._group_points_with_reasoning(points)
        
        # Process each group with CoT mapping
        results = []
        for device_type, device_points in grouped_points.items():
            batch_results = await self._process_batch_with_reasoning(
                device_type, 
                device_points,
                reasoning_level
            )
            results.extend(batch_results)
            
        return results
    
    def _group_points_with_reasoning(
        self,
        points: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group points by device type with reasoning.
        
        Args:
            points: List of points to group
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        # Initialize reasoning engine
        reasoning_engine = ReasoningEngine(self.enos_schema)
        
        # If device type already specified, use that
        predefined_groups = {}
        points_to_group = []
        
        for point in points:
            if "deviceType" in point and point["deviceType"]:
                device_type = point["deviceType"]
                if device_type not in predefined_groups:
                    predefined_groups[device_type] = []
                predefined_groups[device_type].append(point)
            else:
                points_to_group.append(point)
        
        # Use CoT reasoning to determine device types for remaining points
        if points_to_group:
            reasoned_groups = reasoning_engine.chain_of_thought_grouping(points_to_group)
            
            # Merge with predefined groups
            for device_type, group_points in reasoned_groups.items():
                if device_type not in predefined_groups:
                    predefined_groups[device_type] = []
                predefined_groups[device_type].extend(group_points)
        
        return predefined_groups
    
    async def _process_batch_with_reasoning(
        self,
        device_type: str,
        points: List[Dict[str, Any]],
        reasoning_level: int
    ) -> List[Dict[str, Any]]:
        """Process a batch of points with reasoning.
        
        Args:
            device_type: Device type for this batch
            points: List of points to process
            reasoning_level: Level of reasoning detail
            
        Returns:
            List of mapping results with reasoning chains
        """
        # Initialize reasoning engine
        reasoning_engine = ReasoningEngine(self.enos_schema)
        
        results = []
        for point in points:
            # Generate CoT reasoning for this point
            reasoning_chain = reasoning_engine.chain_of_thought_mapping(point, device_type)
            
            # Generate mapping prompt with reasoning instructions
            prompt = self._generate_mapping_prompt_with_reasoning(
                point,
                device_type,
                reasoning_chain,
                reasoning_level
            )
            
            # Run the LLM
            llm_response = await Runner.run_sync(self.mapping_agent, prompt)
            
            # Process and validate result
            mapping_result = self._process_llm_response(llm_response, point, device_type)
            
            # Add reasoning chain to result
            mapping_result["reasoning"] = {
                "chain": reasoning_chain,
                "level": reasoning_level
            }
            
            # Store reasoning data for analysis
            reasoning_engine.store_reasoning_data(
                point.get("pointId", "unknown"),
                reasoning_chain,
                None,  # No reflection yet
                mapping_result
            )
            
            results.append(mapping_result)
            
        return results
    
    async def reflect_and_remap(
        self,
        point_id: str,
        point_data: Dict[str, Any],
        previous_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reflect on a failed mapping and attempt remapping.
        
        Args:
            point_id: ID of the point
            point_data: Original point data
            previous_result: Previous mapping result
            
        Returns:
            New mapping result with reflection
        """
        # Initialize reasoning engine
        reasoning_engine = ReasoningEngine(self.enos_schema)
        
        # Generate reflection
        error_type = previous_result.get("reflection", {}).get("reason", "unknown")
        reflection = reasoning_engine.reflect_on_mapping(
            point_data,
            previous_result,
            error_type
        )
        
        # Get the original reasoning chain if it exists
        original_reasoning = previous_result.get("reasoning", {}).get("chain", [])
        
        # Generate refined prompt with reflection
        device_type = point_data.get("deviceType", "unknown")
        prompt = reasoning_engine.generate_refined_prompt(
            point_data,
            original_reasoning,
            reflection
        )
        
        # Run the LLM again
        llm_response = await Runner.run_sync(self.mapping_agent, prompt)
        
        # Process and validate result
        new_result = self._process_llm_response(llm_response, point_data, device_type)
        
        # Add reflection to result
        new_result["reflection"] = {
            "analysis": reflection,
            "previous_mapping": previous_result.get("mapping", {}).get("enosPoint", "unknown"),
            "success": new_result["mapping"]["enosPoint"] != "unknown"
        }
        
        # Store reasoning and reflection data
        reasoning_engine.store_reasoning_data(
            point_id,
            original_reasoning,
            reflection,
            new_result
        )
        
        return new_result
        
    async def reflect_and_remap_batch(
        self,
        points_data: List[Dict[str, Any]],
        previous_results: List[Dict[str, Any]],
        batch_size: int = 20
    ) -> List[Dict[str, Any]]:
        """Reflect on multiple failed mappings and attempt remapping in batches.
        
        Args:
            points_data: List of original point data
            previous_results: List of previous mapping results
            batch_size: Size of each processing batch
            
        Returns:
            List of new mapping results with reflection data
        """
        # Validate input lists have same length
        if len(points_data) != len(previous_results):
            raise ValueError("Points data and previous results must have the same length")
        
        # Initialize reasoning engine
        reasoning_engine = ReasoningEngine(self.enos_schema)
        
        # Process in batches
        total_points = len(points_data)
        results = []
        
        for i in range(0, total_points, batch_size):
            batch_points = points_data[i:i+batch_size]
            batch_results = previous_results[i:i+batch_size]
            
            # Process each point in the batch
            batch_output = []
            for j, point_data in enumerate(batch_points):
                point_id = point_data.get("pointId", f"unknown_{i+j}")
                previous_result = batch_results[j]
                
                # Process individual point with reflection
                new_result = await self._process_reflection(point_id, point_data, previous_result)
                batch_output.append(new_result)
            
            # Add batch results to overall results
            results.extend(batch_output)
            
            # Optional: Add a small delay between batches to avoid rate limiting
            if i + batch_size < total_points:
                await asyncio.sleep(0.5)
        
        return results

    async def _process_reflection(
        self,
        point_id: str,
        point_data: Dict[str, Any],
        previous_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process reflection and remapping for a single point.
        
        Args:
            point_id: ID of the point
            point_data: Original point data
            previous_result: Previous mapping result
            
        Returns:
            New mapping result with reflection
        """
        # Initialize reasoning engine
        reasoning_engine = ReasoningEngine(self.enos_schema)
        
        # Generate reflection
        error_type = previous_result.get("reflection", {}).get("reason", "unknown")
        reflection = reasoning_engine.reflect_on_mapping(
            point_data,
            previous_result,
            error_type
        )
        
        # Get the original reasoning chain if it exists
        original_reasoning = previous_result.get("reasoning", {}).get("chain", [])
        
        # Generate refined prompt with reflection
        device_type = point_data.get("deviceType", "unknown")
        prompt = reasoning_engine.generate_refined_prompt(
            point_data,
            original_reasoning,
            reflection
        )
        
        # Run the LLM again
        llm_response = await Runner.run_sync(self.mapping_agent, prompt)
        
        # Process and validate result
        new_result = self._process_llm_response(llm_response, point_data, device_type)
        
        # Add reflection to result
        new_result["reflection"] = {
            "analysis": reflection,
            "previous_mapping": previous_result.get("mapping", {}).get("enosPoint", "unknown"),
            "success": new_result["mapping"]["enosPoint"] != "unknown"
        }
        
        # Store reasoning and reflection data
        reasoning_engine.store_reasoning_data(
            point_id,
            original_reasoning,
            reflection,
            new_result
        )
        
        return new_result

    def generate_refined_prompt(
        self,
        point_data: Dict[str, Any],
        reasoning_chain: List[str],
        reflection: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate refined prompt based on reasoning and reflection using OpenAI API.
        
        Args:
            point_data: Point data
            reasoning_chain: Original reasoning chain
            reflection: Optional reflection data
            
        Returns:
            Refined prompt
        """
        # Prepare base context for the model
        base_context = {
            "point_id": point_data.get("pointId", "unknown"),
            "point_name": point_data.get("pointName", ""),
            "device_type": point_data.get("deviceType", ""),
            "unit": point_data.get("unit", ""),
            "description": point_data.get("description", ""),
            "reasoning_chain": reasoning_chain
        }
        
        # Add reflection data if available
        if reflection:
            base_context["reflection"] = {
                "error_type": reflection.get("error_type", "unknown"),
                "analysis": reflection.get("analysis", []),
                "suggestions": reflection.get("suggestions", [])
            }
            
            if "closest_matches" in reflection:
                base_context["reflection"]["closest_matches"] = reflection["closest_matches"]
        
        # Generate optimized prompt using OpenAI
        try:
            # Create input for prompt generation
            prompt_generation_input = self._create_prompt_generation_input(base_context)
            
            # Call OpenAI API to generate optimized prompt
            optimized_prompt = Runner.run_sync(self.mapping_agent, prompt_generation_input)
            
            # Return the optimized prompt
            return optimized_prompt
            
        except Exception as e:
            # Log error
            logger.error(f"Error generating refined prompt with OpenAI: {str(e)}")
            
            # Fall back to template-based prompt generation
            return self._generate_fallback_prompt(base_context)
    
    def _create_prompt_generation_input(self, context: Dict[str, Any]) -> str:
        """Create input for prompt generation with OpenAI.
        
        Args:
            context: Context for prompt generation
            
        Returns:
            Input for prompt generation
        """
        # Create a meta-prompt that asks the model to generate a prompt
        meta_prompt = """You are an expert prompt engineer tasked with creating an optimal prompt for mapping BMS points to EnOS schema points.
Given the context below, create a mapping prompt that will yield the most accurate mapping possible.

Context Information:
"""
        # Add basic point information
        meta_prompt += f"""
Point ID: {context['point_id']}
Point Name: {context['point_name']}
Device Type: {context['device_type']}
Unit: {context['unit']}
Description: {context['description']}

Original reasoning steps:
"""
        
        # Add reasoning chain
        for step in context["reasoning_chain"]:
            meta_prompt += f"- {step}\n"
        
        # Add reflection data if available
        if "reflection" in context:
            reflection = context["reflection"]
            meta_prompt += f"\nReflection on previous mapping attempt (error type: {reflection['error_type']}):\n"
            
            if reflection["analysis"]:
                meta_prompt += "\nAnalysis:\n"
                for analysis in reflection["analysis"]:
                    meta_prompt += f"- {analysis}\n"
            
            if reflection.get("suggestions"):
                meta_prompt += "\nSuggestions:\n"
                for suggestion in reflection["suggestions"]:
                    meta_prompt += f"- {suggestion}\n"
            
            if reflection.get("closest_matches"):
                meta_prompt += "\nPotential matches:\n"
                for match in reflection["closest_matches"]:
                    meta_prompt += f"- {match}\n"
        
        # Add instructions for the prompt format
        meta_prompt += """
Create an optimized prompt for the mapping agent that will result in the most accurate mapping.
The prompt should:
1. Include all relevant point information
2. Incorporate insights from the reasoning chain
3. Address issues identified in the reflection (if available)
4. Provide clear instructions for the expected response format
5. Emphasize the need for accuracy and precision

Your output should be ONLY the prompt itself, with no meta-commentary or explanations.
"""
        
        return meta_prompt
    
    def _generate_fallback_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a fallback prompt if OpenAI API fails.
        
        Args:
            context: Context for prompt generation
            
        Returns:
            Fallback prompt
        """
        # Extract context variables
        point_id = context["point_id"]
        point_name = context["point_name"]
        device_type = context["device_type"]
        unit = context["unit"]
        description = context["description"]
        reasoning_chain = context["reasoning_chain"]
        
        # Create the base prompt
        prompt = f"""Map the following BMS point to the EnOS schema:

Point ID: {point_id}
Point Name: {point_name}
Device Type: {device_type}
Unit: {unit}
Description: {description}

Reasoning steps:
{chr(10).join(reasoning_chain)}
"""

        # Add reflection data if available
        if "reflection" in context:
            reflection = context["reflection"]
            prompt += f"""

Previous mapping attempt failed due to: {reflection["error_type"]}

Analysis:
{chr(10).join(reflection["analysis"])}

"""
            if reflection.get("suggestions"):
                prompt += f"""Suggestions:
{chr(10).join(reflection["suggestions"])}

"""
            
            if reflection.get("closest_matches"):
                prompt += f"""Consider these potential matches:
{chr(10).join(reflection["closest_matches"])}

"""
            
            prompt += """Please provide a more accurate mapping in the format:
{"enosPoint": "TARGET_POINT"}
"""
        else:
            prompt += """

Please provide the mapping in the format:
{"enosPoint": "TARGET_POINT"}

If you cannot determine the mapping, respond with:
{"enosPoint": "unknown"}
"""
        
        return prompt
```

## Logging System

### 1. Reasoning Logger
```python
# app/bms/logging.py

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ReasoningLogger:
    """Logger for reasoning and reflection data."""
    
    def __init__(self, log_dir: str = "logs/reasoning"):
        """Initialize the reasoning logger.
        
        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure standard logger
        self.logger = logging.getLogger("reasoning")
        self.logger.setLevel(logging.INFO)
        
        # File handler for all reasoning logs
        file_handler = logging.FileHandler(f"{log_dir}/reasoning_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)
    
    def log_reasoning_chain(
        self,
        point_id: str,
        reasoning_chain: List[str],
        result: Dict[str, Any]
    ):
        """Log a reasoning chain.
        
        Args:
            point_id: ID of the point
            reasoning_chain: Chain of reasoning steps
            result: Final mapping result
        """
        # Log to standard logger
        self.logger.info(f"Reasoning for point {point_id}: {len(reasoning_chain)} steps, result: {result['mapping']['enosPoint']}")
        
        # Create detailed log file for this reasoning chain
        chain_dir = f"{self.log_dir}/chains"
        os.makedirs(chain_dir, exist_ok=True)
        
        with open(f"{chain_dir}/{point_id}.json", "w") as f:
            json.dump({
                "point_id": point_id,
                "timestamp": datetime.now().isoformat(),
                "reasoning_chain": reasoning_chain,
                "result": result
            }, f, indent=2)
    
    def log_reflection(
        self,
        point_id: str,
        reflection: Dict[str, Any],
        original_result: Dict[str, Any],
        new_result: Dict[str, Any]
    ):
        """Log a reflection.
        
        Args:
            point_id: ID of the point
            reflection: Reflection data
            original_result: Original mapping result
            new_result: New mapping result after reflection
        """
        # Log to standard logger
        self.logger.info(f"Reflection for point {point_id}: original={original_result['mapping']['enosPoint']}, new={new_result['mapping']['enosPoint']}")
        
        # Create detailed log file for this reflection
        reflection_dir = f"{self.log_dir}/reflections"
        os.makedirs(reflection_dir, exist_ok=True)
        
        with open(f"{reflection_dir}/{point_id}.json", "w") as f:
            json.dump({
                "point_id": point_id,
                "timestamp": datetime.now().isoformat(),
                "reflection": reflection,
                "original_result": original_result,
                "new_result": new_result
            }, f, indent=2)
```

## Reasoning Engine

### 1. Initial Implementation
```python
# app/bms/reasoning.py

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

class ReasoningEngine:
    """Engine for generating reasoning chains and reflections."""
    
    def __init__(self, enos_schema: Dict[str, Any], logger=None):
        """Initialize the reasoning engine.
        
        Args:
            enos_schema: EnOS schema
            logger: Optional reasoning logger
        """
        self.enos_schema = enos_schema
        
        # Initialize logger if not provided
        if logger is None:
            from app.bms.logging import ReasoningLogger
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
            # Add more abbreviations as needed
        }
    
    def chain_of_thought_grouping(self, points: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate step-by-step reasoning for device type grouping.
        
        Args:
            points: List of points to group
            
        Returns:
            Dictionary mapping device types to lists of points
        """
        # Implement basic heuristic grouping for now
        # This will be replaced with LLM-based CoT in Phase 2
        grouped_points = {}
        
        for point in points:
            point_name = point.get("pointName", "")
            
            # Extract potential device type from point name
            device_type = "unknown"
            
            # Check for common device type prefixes
            if point_name.startswith("CH") or "CH-" in point_name:
                device_type = "CH-SYS"
            elif point_name.startswith("AHU") or "AHU-" in point_name:
                device_type = "AHU"
            elif point_name.startswith("VAV") or "VAV-" in point_name:
                device_type = "VAV"
            # Add more device type detection rules
            
            # Add reasoning steps (placeholder for now)
            point["grouping_reasoning"] = [
                f"Point name '{point_name}' analysis:",
                f"Detected potential device type '{device_type}' based on prefix pattern"
            ]
            
            # Add to grouped points
            if device_type not in grouped_points:
                grouped_points[device_type] = []
            grouped_points[device_type].append(point)
        
        return grouped_points
    
    def chain_of_thought_mapping(
        self,
        point_data: Dict[str, Any],
        device_type: str
    ) -> List[str]:
        """Generate step-by-step reasoning for point mapping.
        
        Args:
            point_data: Point data
            device_type: Device type
            
        Returns:
            List of reasoning steps
        """
        # Extract point information
        point_name = point_data.get("pointName", "")
        point_description = point_data.get("description", "")
        point_unit = point_data.get("unit", "")
        
        # Initialize reasoning chain
        reasoning_chain = [
            f"Analyzing point '{point_name}' of device type '{device_type}':"
        ]
        
        # Decompose point name into components
        components = point_name.split(".")
        reasoning_chain.append(f"Point name components: {components}")
        
        # Identify abbreviations
        detected_abbrs = []
        for component in components:
            for abbr, meaning in self.abbreviations.items():
                if abbr in component:
                    detected_abbrs.append(f"{abbr} ({meaning})")
        
        if detected_abbrs:
            reasoning_chain.append(f"Detected abbreviations: {', '.join(detected_abbrs)}")
        
        # Consider unit information
        if point_unit:
            reasoning_chain.append(f"Point unit: {point_unit}")
            
            # Add unit-specific reasoning
            if point_unit.lower() in ["hz", "hertz"]:
                reasoning_chain.append("Unit 'Hz' indicates a frequency measurement")
                
                if "pump" in point_name.lower() or "cwp" in point_name.lower():
                    reasoning_chain.append("Frequency measurement for a pump suggests a PUMP_raw_frequency or similar EnOS point")
        
        # Consider description
        if point_description:
            reasoning_chain.append(f"Point description: '{point_description}'")
        
        # Return the reasoning chain
        return reasoning_chain
    
    def reflect_on_mapping(
        self,
        point_data: Dict[str, Any],
        failed_result: Dict[str, Any],
        error_type: str
    ) -> Dict[str, Any]:
        """Generate reflection on why mapping failed.
        
        Args:
            point_data: Point data
            failed_result: Failed mapping result
            error_type: Type of error
            
        Returns:
            Reflection data
        """
        # Extract point information
        point_id = point_data.get("pointId", "unknown")
        point_name = point_data.get("pointName", "")
        
        # Initialize reflection
        reflection = {
            "point_id": point_id,
            "point_name": point_name,
            "error_type": error_type,
            "analysis": [],
            "suggestions": []
        }
        
        # Analyze based on error type
        if error_type == "format":
            reflection["analysis"].append("The LLM response failed format validation")
            reflection["analysis"].append("This may be due to incorrect JSON formatting or missing required fields")
            reflection["suggestions"].append("Provide clearer formatting instructions in the prompt")
            
        elif error_type == "unknown_mapping":
            reflection["analysis"].append("The LLM could not determine a suitable EnOS point")
            reflection["analysis"].append("This may be due to ambiguous point name or missing context")
            
            # Suggest potential EnOS points based on point characteristics
            point_characteristics = self._extract_point_characteristics(point_data)
            potential_matches = self._find_potential_matches(point_characteristics)
            
            if potential_matches:
                reflection["suggestions"].append(f"Consider these potential EnOS points: {', '.join(potential_matches)}")
        
        # Return the reflection
        return reflection
    
    def _extract_point_characteristics(self, point_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant characteristics from a point.
        
        Args:
            point_data: Point data
            
        Returns:
            Dictionary of characteristics
        """
        # Extract basic information
        characteristics = {
            "name": point_data.get("pointName", ""),
            "device_type": point_data.get("deviceType", ""),
            "unit": point_data.get("unit", ""),
            "description": point_data.get("description", "")
        }
        
        # Extract abbreviations
        detected_abbrs = []
        for abbr, meaning in self.abbreviations.items():
            if abbr in characteristics["name"]:
                detected_abbrs.append(abbr)
        
        characteristics["abbreviations"] = detected_abbrs
        
        return characteristics
    
    def _find_potential_matches(self, characteristics: Dict[str, Any]) -> List[str]:
        """Find potential EnOS points matching the characteristics using OpenAI's API.
        
        Args:
            characteristics: Point characteristics
            
        Returns:
            List of potential EnOS points
        """
        # Extract relevant information for the prompt
        point_name = characteristics["name"]
        device_type = characteristics["device_type"]
        unit = characteristics["unit"]
        description = characteristics["description"]
        abbreviations = characteristics["abbreviations"]
        
        # Create a prompt for the OpenAI API
        prompt = f"""Analyze this BMS point and suggest the most appropriate EnOS point mappings:

Point Name: {point_name}
Device Type: {device_type}
Unit: {unit}
Description: {description}
Detected Abbreviations: {', '.join(abbreviations)}

Based on these characteristics, what are the most likely EnOS point types this could map to?
Return your answer as a JSON array of strings, containing the top 3 most likely EnOS point types.
Example format: ["PUMP_raw_frequency", "PUMP_status", "PUMP_command"]
"""
        
        try:
            # Call the OpenAI API using the existing mapping agent
            llm_response = Runner.run_sync(self.mapping_agent, prompt)
            
            # Parse the response to extract the suggested mappings
            # This handles various response formats the API might return
            matches = self._parse_potential_matches_response(llm_response)
            
            # Return the top 3 matches
            return matches[:3]
        
        except Exception as e:
            # Log the error
            logger.error(f"Error using OpenAI API for potential matches: {str(e)}")
            
            # Fall back to simple rule-based matching
            fallback_matches = []
            name = point_name.lower()
            
            # Simple rule-based fallback logic
            if "pump" in name or "cwp" in abbreviations:
                if unit.lower() in ["hz", "hertz"]:
                    fallback_matches.append("PUMP_raw_frequency")
                
                if "status" in name:
                    fallback_matches.append("PUMP_status")
                    
                if "command" in name or "cmd" in name:
                    fallback_matches.append("PUMP_command")
            
            # Return fallback matches
            return fallback_matches[:3]
    
    def _parse_potential_matches_response(self, response: str) -> List[str]:
        """Parse the OpenAI API response to extract potential matches.
        
        Args:
            response: The response from the OpenAI API
            
        Returns:
            List of potential EnOS points
        """
        try:
            # Try to parse as JSON
            matches = json.loads(response)
            if isinstance(matches, list):
                return matches
            
            # If the response is a dict with an array field, extract that
            if isinstance(matches, dict):
                for key, value in matches.items():
                    if isinstance(value, list) and all(isinstance(item, str) for item in value):
                        return value
            
            # Fall back to regex pattern matching
            pattern = r'["\']([\w_]+)["\']'
            regex_matches = re.findall(pattern, response)
            if regex_matches:
                # Filter to only keep things that look like EnOS points (uppercase with underscores)
                enos_points = [m for m in regex_matches if re.match(r'^[A-Z][A-Z_]+$', m)]
                return enos_points
            
        except json.JSONDecodeError:
            # Not valid JSON, try regex
            pattern = r'["\']([\w_]+)["\']'
            regex_matches = re.findall(pattern, response)
            if regex_matches:
                # Filter to only keep things that look like EnOS points (uppercase with underscores)
                enos_points = [m for m in regex_matches if re.match(r'^[A-Z][A-Z_]+$', m)]
                return enos_points
        
        except Exception as e:
            logger.error(f"Error parsing potential matches response: {str(e)}")
        
        # If all parsing attempts fail, return empty list
        return []
    
    def store_reasoning_data(
        self,
        point_id: str,
        reasoning_chain: List[str],
        reflection: Optional[Dict[str, Any]],
        outcome: Dict[str, Any]
    ):
        """Store reasoning data for analysis.
        
        Args:
            point_id: Point ID
            reasoning_chain: Reasoning chain
            reflection: Optional reflection data
            outcome: Mapping outcome
        """
        # Log reasoning chain
        self.logger.log_reasoning_chain(point_id, reasoning_chain, outcome)
        
        # Log reflection if available
        if reflection:
            # Assuming original result is stored in reflection
            original_result = reflection.get("original_result", {})
            self.logger.log_reflection(point_id, reflection, original_result, outcome)
```

## Trigger Conditions

### 1. Implementation in EnOSMapper
```python
def _should_trigger_reflection(self, result: Dict[str, Any]) -> bool:
    """Determine if reflection should be triggered.
    
    Args:
        result: Mapping result
        
    Returns:
        True if reflection should be triggered
    """
    # Trigger reflection if mapping failed
    if result["mapping"]["enosPoint"] == "unknown":
        return True
    
    # Trigger reflection if confidence is low
    if result["mapping"]["confidence"] < 0.5:
        return True
    
    # Don't trigger reflection for high-confidence mappings
    return False
```

## Batch Reflection Processing

### 1. New Endpoint and Implementation
For processing large datasets with over 100 points that need reflection, a batch processing approach has been implemented. This allows for efficient reflection and remapping of multiple points at once, rather than requiring individual API calls for each point.

```python
@router.post("/points/reflect-and-remap-batch")
async def reflect_and_remap_points_batch(
    points_data: List[PointData],
    previous_results: List[MappingResult],
    batch_size: Optional[int] = 20,
    request: Request
):
    """Reflect on previous mapping attempts and try remapping multiple points at once.
    
    Args:
        points_data: List of original point data
        previous_results: List of previous mapping results
        batch_size: Size of each processing batch (default: 20)
        
    Returns:
        New mapping results with reflection data
    """
    if len(points_data) != len(previous_results):
        raise HTTPException(status_code=400, detail="The number of points and previous results must match")
        
    mapper = get_mapper(request.app.state)
    results = await mapper.reflect_and_remap_batch(points_data, previous_results, batch_size)
    return results
```

### 2. EnOSMapper Batch Method
The EnOSMapper class has been extended with a new method to handle batch reflection and remapping:

```python
async def reflect_and_remap_batch(
    self,
    points_data: List[Dict[str, Any]],
    previous_results: List[Dict[str, Any]],
    batch_size: int = 20
) -> List[Dict[str, Any]]:
    """Reflect on multiple failed mappings and attempt remapping in batches.
    
    Args:
        points_data: List of original point data
        previous_results: List of previous mapping results
        batch_size: Size of each processing batch
        
    Returns:
        List of new mapping results with reflection data
    """
    # Process in batches with rate limiting
    total_points = len(points_data)
    results = []
    
    for i in range(0, total_points, batch_size):
        batch_points = points_data[i:i+batch_size]
        batch_results = previous_results[i:i+batch_size]
        
        # Process batch
        batch_output = []
        for j, point_data in enumerate(batch_points):
            # Process individual point with reflection
            point_id = point_data.get("pointId", f"unknown_{i+j}")
            previous_result = batch_results[j]
            new_result = await self._process_reflection(point_id, point_data, previous_result)
            batch_output.append(new_result)
        
        # Add batch results to overall results
        results.extend(batch_output)
        
        # Add delay between batches to avoid rate limiting
        if i + batch_size < total_points:
            await asyncio.sleep(0.5)
    
    return results
```

### 3. Benefits of Batch Processing
- **Scalability**: Efficiently handles large datasets with hundreds of points
- **Resource Optimization**: Processes points in manageable batches to avoid overwhelming the system
- **Rate Limiting**: Includes optional delays between batches to prevent API rate limits
- **Progress Tracking**: Can be extended to include progress tracking for long-running jobs
- **Error Handling**: Maintains individual point processing to isolate errors

## Integration Into Existing Code

### 1. Dependency Injection
```python
# app/dependencies.py

from app.bms.reasoning import ReasoningEngine
from app.bms.logging import ReasoningLogger

async def get_reasoning_engine(state):
    """Get or create a reasoning engine.
    
    Args:
        state: Application state
        
    Returns:
        ReasoningEngine instance
    """
    if not hasattr(state, "reasoning_engine"):
        # Create logger
        reasoning_logger = ReasoningLogger()
        
        # Get EnOS schema
        enos_schema = state.mapper.enos_schema
        
        # Create reasoning engine
        state.reasoning_engine = ReasoningEngine(enos_schema, reasoning_logger)
    
    return state.reasoning_engine
```

### 2. Application Startup
```python
# app/main.py

from app.bms.reasoning import ReasoningEngine
from app.bms.logging import ReasoningLogger

# ... existing code ...

@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Initialize reasoning logger
    app.state.reasoning_logger = ReasoningLogger()
    
    # Initialize reasoning engine with EnOS schema
    app.state.reasoning_engine = ReasoningEngine(
        app.state.mapper.enos_schema,
        app.state.reasoning_logger
    )
``` 