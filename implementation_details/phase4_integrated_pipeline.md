# Phase 4: Integrated Reasoning Pipeline

## Overview
This phase focuses on creating an integrated pipeline that combines Chain of Thought (CoT) reasoning with self-reflection. The pipeline will provide step-by-step mapping decisions with confidence levels and cross-verification between grouping and mapping.

## Step-by-Step Mapping Decision Tree

### EnOSMapper Integration

```python
async def map_with_integrated_reasoning(
    self,
    points: List[Dict[str, Any]],
    reasoning_level: int = 2
) -> List[Dict[str, Any]]:
    """Map points using the integrated reasoning pipeline.
    
    Args:
        points: List of points to map
        reasoning_level: Detail level for reasoning (1-3)
        
    Returns:
        Mapping results with full reasoning chains
    """
    # Initialize reasoning engine
    reasoning_engine = self.get_reasoning_engine()
    
    # Phase 1: Group points with CoT reasoning
    grouped_points = reasoning_engine.group_points_with_reasoning(points)
    
    # Phase 2: Generate mapping decisions for each group
    results = []
    
    for device_type, group_points in grouped_points.items():
        # Get reference points for this device type
        reference_points = self._get_reference_points(device_type)
        
        # Map each point with detailed reasoning
        for point in group_points:
            # Step 1: Generate detailed CoT reasoning
            reasoning_chain = reasoning_engine.detailed_mapping_reasoning(
                point, 
                device_type,
                reference_points,
                reasoning_level
            )
            
            # Step 2: Make mapping decision with confidence
            mapping_decision = reasoning_engine.make_mapping_decision(
                point,
                reasoning_chain,
                device_type
            )
            
            # If confidence is low, add reflection
            if mapping_decision["confidence"] < 0.7:
                reflection = reasoning_engine.reflect_on_low_confidence(
                    point,
                    mapping_decision,
                    reasoning_chain
                )
                
                # Update decision based on reflection
                refined_decision = reasoning_engine.refine_decision_with_reflection(
                    mapping_decision,
                    reflection
                )
                
                # Use the refined decision
                mapping_decision = refined_decision
            
            # Create result with full reasoning
            result = {
                "original": point,
                "mapping": {
                    "pointId": point.get("pointId", "unknown"),
                    "enosPoint": mapping_decision["enosPoint"],
                    "confidence": mapping_decision["confidence"],
                    "status": "mapped" if mapping_decision["enosPoint"] != "unknown" else "unmapped",
                    "source": "reasoning_pipeline"
                },
                "reasoning": {
                    "chain": reasoning_chain,
                    "level": reasoning_level,
                    "decision_path": mapping_decision["decision_path"],
                    "confidence_factors": mapping_decision["confidence_factors"]
                }
            }
            
            # Add reflection if present
            if "reflection" in locals() and reflection:
                result["reflection"] = reflection
            
            results.append(result)
            
            # Clean up for next iteration
            if "reflection" in locals():
                del reflection
    
    return results

def _get_reference_points(self, device_type: str) -> List[Dict[str, Any]]:
    """Get reference points for a device type.
    
    Args:
        device_type: Device type
        
    Returns:
        List of reference points
    """
    # This would typically come from a database or configuration
    # Simplified implementation for now
    reference_points = []
    
    # Load from mapping_patterns.json
    if hasattr(self, "mapping_patterns") and self.mapping_patterns:
        device_patterns = self.mapping_patterns.get(device_type, [])
        for pattern in device_patterns:
            reference_points.append({
                "pattern": pattern.get("pattern", ""),
                "enosPoint": pattern.get("enos_point", "unknown"),
                "confidence": pattern.get("confidence", 0.0)
            })
    
    return reference_points
```

## Detailed Reasoning Engine Methods

```python
def detailed_mapping_reasoning(
    self,
    point: Dict[str, Any],
    device_type: str,
    reference_points: List[Dict[str, Any]],
    detail_level: int
) -> List[Dict[str, Any]]:
    """Generate detailed step-by-step reasoning for mapping.
    
    Args:
        point: Point data
        device_type: Device type
        reference_points: Reference points for this device type
        detail_level: Level of detail (1-3)
        
    Returns:
        List of reasoning steps with metadata
    """
    # Extract point information
    point_name = point.get("pointName", "")
    point_description = point.get("description", "")
    point_unit = point.get("unit", "")
    
    # Get point analyzer
    point_analyzer = PointAnalyzer(self.abbreviations)
    
    # Decompose point name
    decomposition = point_analyzer.decompose_point_name(point_name)
    
    # Initialize reasoning chain
    reasoning_chain = []
    
    # Step 1: Analyze point name
    reasoning_chain.append({
        "step": 1,
        "type": "analysis",
        "description": f"Analyzing point name: {point_name}",
        "detail": f"Point name has {len(decomposition['segments'])} segments: {', '.join(decomposition['segments'])}"
    })
    
    # Step 2: Identify abbreviations and components
    reasoning_chain.append({
        "step": 2,
        "type": "identification",
        "description": "Identifying abbreviations and components",
        "detail": f"Detected abbreviations: {decomposition['abbreviations']}",
        "components": {
            "measurement_type": decomposition["measurement_type"],
            "device": decomposition["device"],
            "property": decomposition["property"]
        }
    })
    
    # Step 3: Consider unit information
    reasoning_chain.append({
        "step": 3,
        "type": "analysis",
        "description": f"Considering unit information: {point_unit}",
        "detail": self._unit_analysis(point_unit, decomposition)
    })
    
    # Step 4: Check for pattern matches
    pattern_matches = self._find_pattern_matches(point_name, reference_points)
    reasoning_chain.append({
        "step": 4,
        "type": "matching",
        "description": "Checking for pattern matches",
        "detail": f"Found {len(pattern_matches)} potential pattern matches",
        "matches": pattern_matches[:3]  # Top 3 matches
    })
    
    # Step 5: Semantic analysis of matches
    if pattern_matches:
        semantic_analysis = self._analyze_matches_semantically(
            pattern_matches, 
            decomposition,
            point_unit
        )
        reasoning_chain.append({
            "step": 5,
            "type": "analysis",
            "description": "Performing semantic analysis of matches",
            "detail": semantic_analysis["description"],
            "ratings": semantic_analysis["ratings"]
        })
    
    # Step 6: Consider alternatives if needed
    if not pattern_matches or max(m["confidence"] for m in pattern_matches) < 0.7:
        alternatives = self._generate_alternatives(decomposition, device_type, point_unit)
        reasoning_chain.append({
            "step": 6,
            "type": "generation",
            "description": "Considering alternative mappings",
            "detail": f"Generated {len(alternatives)} alternatives based on point characteristics",
            "alternatives": alternatives
        })
    
    # Add extra details based on detail level
    if detail_level >= 2:
        # Add schema analysis
        schema_analysis = self._analyze_schema_compatibility(
            decomposition, 
            pattern_matches or [],
            self.enos_schema
        )
        reasoning_chain.append({
            "step": len(reasoning_chain) + 1,
            "type": "schema_analysis",
            "description": "Analyzing compatibility with EnOS schema",
            "detail": schema_analysis["description"],
            "compatibility": schema_analysis["compatibility"]
        })
    
    if detail_level >= 3:
        # Add analogous point analysis
        analogous = self._find_analogous_points(point, decomposition, device_type)
        reasoning_chain.append({
            "step": len(reasoning_chain) + 1,
            "type": "analogy",
            "description": "Finding analogous points in other systems",
            "detail": f"Found {len(analogous)} analogous points in different systems",
            "analogous_points": analogous
        })
    
    return reasoning_chain

def make_mapping_decision(
    self,
    point: Dict[str, Any],
    reasoning_chain: List[Dict[str, Any]],
    device_type: str
) -> Dict[str, Any]:
    """Make a mapping decision based on the reasoning chain.
    
    Args:
        point: Point data
        reasoning_chain: Reasoning chain
        device_type: Device type
        
    Returns:
        Mapping decision with confidence and rationale
    """
    # Extract relevant information from reasoning chain
    pattern_matches = []
    alternatives = []
    components = {}
    
    for step in reasoning_chain:
        if step["type"] == "matching" and "matches" in step:
            pattern_matches = step["matches"]
        if step["type"] == "generation" and "alternatives" in step:
            alternatives = step["alternatives"]
        if step["type"] == "identification" and "components" in step:
            components = step["components"]
    
    # Combine matches and alternatives
    all_candidates = []
    
    # Add pattern matches
    for match in pattern_matches:
        all_candidates.append({
            "enosPoint": match["enosPoint"],
            "confidence": match["confidence"],
            "source": "pattern_match",
            "rationale": f"Matched pattern '{match['pattern']}'"
        })
    
    # Add alternatives
    for alt in alternatives:
        # Check if already in candidates
        if not any(c["enosPoint"] == alt["enosPoint"] for c in all_candidates):
            all_candidates.append({
                "enosPoint": alt["enosPoint"],
                "confidence": alt["confidence"],
                "source": "alternative",
                "rationale": alt["rationale"]
            })
    
    # If no candidates, return unknown
    if not all_candidates:
        return {
            "enosPoint": "unknown",
            "confidence": 0.0,
            "decision_path": ["No matching patterns or alternatives found"],
            "confidence_factors": {
                "pattern_matches": 0.0,
                "semantic_relevance": 0.0,
                "unit_compatibility": 0.0
            }
        }
    
    # Sort candidates by confidence
    all_candidates.sort(key=lambda c: c["confidence"], reverse=True)
    top_candidate = all_candidates[0]
    
    # Calculate additional confidence factors
    unit_compatibility = self._calculate_unit_compatibility(
        point.get("unit", ""),
        top_candidate["enosPoint"]
    )
    
    semantic_relevance = self._calculate_semantic_relevance(
        components,
        top_candidate["enosPoint"]
    )
    
    # Calculate overall confidence
    confidence_factors = {
        "pattern_matches": top_candidate["confidence"],
        "semantic_relevance": semantic_relevance,
        "unit_compatibility": unit_compatibility
    }
    
    # Weighted average of confidence factors
    weights = {
        "pattern_matches": 0.5,
        "semantic_relevance": 0.3,
        "unit_compatibility": 0.2
    }
    
    overall_confidence = sum(
        factor * weights[factor_name]
        for factor_name, factor in confidence_factors.items()
    )
    
    # Create decision path
    decision_path = [
        f"Selected '{top_candidate['enosPoint']}' with confidence {overall_confidence:.2f}",
        f"Primary basis: {top_candidate['rationale']}",
        f"Semantic relevance: {semantic_relevance:.2f}",
        f"Unit compatibility: {unit_compatibility:.2f}"
    ]
    
    # Make final decision
    if overall_confidence >= 0.5:
        return {
            "enosPoint": top_candidate["enosPoint"],
            "confidence": overall_confidence,
            "decision_path": decision_path,
            "confidence_factors": confidence_factors
        }
    else:
        return {
            "enosPoint": "unknown",
            "confidence": overall_confidence,
            "decision_path": decision_path + ["Confidence below threshold (0.5), marking as unknown"],
            "confidence_factors": confidence_factors
        }
```

## Reflection for Low Confidence Mappings

```python
def reflect_on_low_confidence(
    self,
    point: Dict[str, Any],
    mapping_decision: Dict[str, Any],
    reasoning_chain: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Reflect on a low-confidence mapping decision.
    
    Args:
        point: Point data
        mapping_decision: Initial mapping decision
        reasoning_chain: Reasoning chain
        
    Returns:
        Reflection data
    """
    # Initialize reflection
    reflection = {
        "type": "low_confidence",
        "original_decision": mapping_decision,
        "analysis": [],
        "improvement_suggestions": [],
        "confidence_improvements": {}
    }
    
    # Analyze confidence factors
    factors = mapping_decision["confidence_factors"]
    
    # Identify weakest factor
    weakest_factor = min(factors.items(), key=lambda x: x[1])
    reflection["weakest_factor"] = weakest_factor[0]
    
    # Analyze based on weakest factor
    if weakest_factor[0] == "pattern_matches":
        reflection["analysis"].append("Pattern matching confidence is low")
        reflection["analysis"].append("Point name may not match existing patterns")
        reflection["improvement_suggestions"].append("Consider adding a new pattern for this point type")
        
        # Suggest pattern improvements
        point_analyzer = PointAnalyzer(self.abbreviations)
        decomposition = point_analyzer.decompose_point_name(point.get("pointName", ""))
        
        # Generate potential pattern
        pattern = self._generate_pattern_from_point(point.get("pointName", ""), decomposition)
        reflection["improvement_suggestions"].append(f"Potential new pattern: {pattern}")
        
        # Estimate confidence improvement
        reflection["confidence_improvements"]["pattern_matches"] = 0.8  # Estimated improvement
        
    elif weakest_factor[0] == "semantic_relevance":
        reflection["analysis"].append("Semantic relevance is low")
        reflection["analysis"].append("Point components don't align well with EnOS schema")
        
        # Suggest alternative interpretations
        alternatives = self._generate_semantic_alternatives(point, reasoning_chain)
        
        if alternatives:
            reflection["improvement_suggestions"].append("Consider these semantic interpretations:")
            for alt in alternatives:
                reflection["improvement_suggestions"].append(f"- {alt['interpretation']}: maps to {alt['enosPoint']}")
            
            # Estimate confidence improvement
            reflection["confidence_improvements"]["semantic_relevance"] = 0.7  # Estimated improvement
        
    elif weakest_factor[0] == "unit_compatibility":
        reflection["analysis"].append("Unit compatibility is low")
        reflection["analysis"].append(f"Unit '{point.get('unit', '')}' may not match expected unit for the EnOS point")
        
        # Suggest unit reconciliation
        unit_options = self._suggest_unit_reconciliation(
            point.get("unit", ""),
            mapping_decision["enosPoint"]
        )
        
        if unit_options:
            reflection["improvement_suggestions"].append("Consider these unit interpretations:")
            for option in unit_options:
                reflection["improvement_suggestions"].append(f"- {option['explanation']}")
            
            # Estimate confidence improvement
            reflection["confidence_improvements"]["unit_compatibility"] = 0.8  # Estimated improvement
    
    # Calculate potential overall improvement
    current_confidence = mapping_decision["confidence"]
    potential_improvements = {}
    
    # Copy original factors
    for factor, value in factors.items():
        potential_improvements[factor] = value
    
    # Apply estimated improvements
    for factor, improvement in reflection["confidence_improvements"].items():
        potential_improvements[factor] = improvement
    
    # Calculate new potential confidence
    weights = {
        "pattern_matches": 0.5,
        "semantic_relevance": 0.3,
        "unit_compatibility": 0.2
    }
    
    potential_confidence = sum(
        factor * weights[factor_name]
        for factor_name, factor in potential_improvements.items()
    )
    
    reflection["potential_confidence"] = potential_confidence
    reflection["confidence_improvement"] = potential_confidence - current_confidence
    
    return reflection

def refine_decision_with_reflection(
    self,
    original_decision: Dict[str, Any],
    reflection: Dict[str, Any]
) -> Dict[str, Any]:
    """Refine a mapping decision based on reflection.
    
    Args:
        original_decision: Original mapping decision
        reflection: Reflection data
        
    Returns:
        Refined mapping decision
    """
    # Start with a copy of the original decision
    refined_decision = original_decision.copy()
    refined_decision["confidence_factors"] = original_decision["confidence_factors"].copy()
    
    # If potential confidence is high enough, apply improvements
    if reflection.get("potential_confidence", 0.0) >= 0.7:
        # Apply confidence improvements
        for factor, improvement in reflection.get("confidence_improvements", {}).items():
            refined_decision["confidence_factors"][factor] = improvement
        
        # Recalculate overall confidence
        weights = {
            "pattern_matches": 0.5,
            "semantic_relevance": 0.3,
            "unit_compatibility": 0.2
        }
        
        new_confidence = sum(
            factor * weights[factor_name]
            for factor_name, factor in refined_decision["confidence_factors"].items()
        )
        
        refined_decision["confidence"] = new_confidence
        
        # Update decision path
        refined_decision["decision_path"] = original_decision["decision_path"] + [
            f"Applied reflection: confidence improved from {original_decision['confidence']:.2f} to {new_confidence:.2f}"
        ]
        
        # If confidence is now high enough, update enosPoint if it was unknown
        if new_confidence >= 0.7 and original_decision["enosPoint"] == "unknown":
            # Look for suggested mapping in reflection
            for suggestion in reflection.get("improvement_suggestions", []):
                if "maps to " in suggestion:
                    # Extract suggested mapping
                    match = re.search(r"maps to ([A-Z_]+)", suggestion)
                    if match:
                        refined_decision["enosPoint"] = match.group(1)
                        refined_decision["decision_path"].append(
                            f"Reflection suggested mapping: {refined_decision['enosPoint']}"
                        )
                        break
    else:
        # Not enough improvement, keep original decision
        refined_decision["decision_path"].append(
            "Reflection did not provide sufficient confidence improvement"
        )
    
    return refined_decision
```

## Cross-Verification Between Grouping and Mapping

```python
def verify_consistency(
    self,
    grouped_points: Dict[str, List[Dict[str, Any]]],
    mapping_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Verify consistency between grouping and mapping decisions.
    
    Args:
        grouped_points: Points grouped by device type
        mapping_results: Mapping results for all points
        
    Returns:
        Verification results
    """
    # Initialize verification results
    verification = {
        "inconsistencies": [],
        "patterns": {},
        "suggestions": []
    }
    
    # Build result lookup by point ID
    result_by_id = {
        r["mapping"]["pointId"]: r
        for r in mapping_results
    }
    
    # Analyze each device group
    for device_type, points in grouped_points.items():
        # Collect mappings for this group
        mappings = {}
        
        for point in points:
            point_id = point.get("pointId", "unknown")
            if point_id in result_by_id:
                result = result_by_id[point_id]
                enos_point = result["mapping"]["enosPoint"]
                
                # Count mappings
                if enos_point not in mappings:
                    mappings[enos_point] = []
                mappings[enos_point].append(point_id)
        
        # Find expected patterns for this device type
        expected_patterns = self._get_expected_patterns(device_type)
        
        # Check for unexpected mappings
        for enos_point, point_ids in mappings.items():
            if enos_point != "unknown" and enos_point not in expected_patterns:
                verification["inconsistencies"].append({
                    "type": "unexpected_mapping",
                    "device_type": device_type,
                    "enos_point": enos_point,
                    "point_count": len(point_ids),
                    "point_ids": point_ids[:5]  # First 5 for brevity
                })
        
        # Check for missing expected mappings
        missing_patterns = []
        for expected in expected_patterns:
            if expected not in mappings:
                missing_patterns.append(expected)
        
        if missing_patterns:
            verification["inconsistencies"].append({
                "type": "missing_mappings",
                "device_type": device_type,
                "missing_patterns": missing_patterns
            })
        
        # Record mapping patterns for this device type
        verification["patterns"][device_type] = {
            "total_points": len(points),
            "mapped_points": sum(len(ids) for ids in mappings.values()) - len(mappings.get("unknown", [])),
            "unmapped_points": len(mappings.get("unknown", [])),
            "mapping_distribution": {
                enos_point: len(point_ids)
                for enos_point, point_ids in mappings.items()
                if enos_point != "unknown"
            }
        }
    
    # Generate suggestions
    if verification["inconsistencies"]:
        verification["suggestions"].append(
            f"Found {len(verification['inconsistencies'])} inconsistencies between grouping and mapping"
        )
        
        # Suggest device type corrections
        unexpected_mappings = [
            inc for inc in verification["inconsistencies"]
            if inc["type"] == "unexpected_mapping"
        ]
        
        if unexpected_mappings:
            for inc in unexpected_mappings:
                # Find more appropriate device type for this mapping
                better_device = self._find_better_device_type(
                    inc["enos_point"],
                    inc["device_type"]
                )
                
                if better_device:
                    verification["suggestions"].append(
                        f"Points mapped to {inc['enos_point']} might belong to device type {better_device} rather than {inc['device_type']}"
                    )
    
    return verification

def _get_expected_patterns(self, device_type: str) -> List[str]:
    """Get expected EnOS points for a device type.
    
    Args:
        device_type: Device type
        
    Returns:
        List of expected EnOS points
    """
    # This would come from configuration or be derived from patterns
    # Simplified implementation
    expected = {
        "CH-SYS": [
            "TEMP_supply", "TEMP_return", "PRESSURE_supply", 
            "PRESSURE_return", "PUMP_raw_frequency", "PUMP_status"
        ],
        "AHU": [
            "TEMP_supply", "TEMP_return", "TEMP_mixed", 
            "DAMPER_position", "FAN_speed", "FAN_status"
        ],
        "VAV": [
            "TEMP_zone", "DAMPER_position", "FLOW_air", 
            "TEMP_setpoint", "VALVE_position"
        ]
    }
    
    return expected.get(device_type, [])

def _find_better_device_type(self, enos_point: str, current_device: str) -> Optional[str]:
    """Find a better device type for an EnOS point.
    
    Args:
        enos_point: EnOS point
        current_device: Current device type
        
    Returns:
        Better device type or None
    """
    # This would be a more sophisticated lookup
    # Simplified implementation
    point_to_devices = {
        "PUMP_raw_frequency": ["CH-SYS"],
        "PUMP_status": ["CH-SYS"],
        "FAN_speed": ["AHU"],
        "FAN_status": ["AHU"],
        "DAMPER_position": ["AHU", "VAV"],
        "FLOW_air": ["AHU", "VAV"],
        "VALVE_position": ["VAV", "FCU"]
    }
    
    # If point is associated with specific devices
    if enos_point in point_to_devices:
        devices = point_to_devices[enos_point]
        
        # If current device is not in the list
        if current_device not in devices and devices:
            return devices[0]  # Suggest first device
    
    return None
``` 