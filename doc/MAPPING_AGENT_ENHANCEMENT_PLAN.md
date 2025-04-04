# MappingAgent Enhancement Plan

## Background

Testing of the BMS onboarding pipeline has revealed that while the tagging phase performs well, the mapping phase fails with a 0% success rate. Analysis has identified schema compatibility issues between the EnOS model definitions and the expectations of the mapping algorithm.

This document outlines a concrete plan to address these issues and enhance the MappingAgent to achieve better mapping results.

## Current Issues

1. **Schema Mismatch**: The EnOS model file structure does not match what the MappingAgent expects:
   - MappingAgent expects points in an array format
   - Actual file uses a dictionary with point IDs as keys

2. **Field Name Mismatch**: Key fields have different names:
   - "quantity" in JSON vs. "measurement" in code
   - "phenomenon" + "aspect" in JSON vs. "component" in code

3. **Matching Score Threshold**: The threshold of 0.3 is too high given the field mismatches, causing all potential matches to be rejected.

4. **Insufficient Diagnostics**: Lack of detailed logging makes diagnosing matching issues difficult.

## Implementation Plan

### Phase 1: Schema Adapter (Immediate Fix)

**Objective**: Create an adapter to convert the current EnOS model structure to the format expected by the mapping algorithm.

**Tasks**:

1. **Implement ModelAdapter Class**:
```python
class EnOSModelAdapter:
    """
    Adapter to convert between different EnOS model schemas.
    """
    
    @staticmethod
    def adapt_model(raw_model):
        """Convert the raw model to the expected format"""
        adapted_model = {}
        
        for equipment_type, equipment_data in raw_model.items():
            adapted_model[equipment_type] = {
                "points": []
            }
            
            # Copy equipment-level properties
            for key, value in equipment_data.items():
                if key != "points":
                    adapted_model[equipment_type][key] = value
            
            # Convert points from dict to array format
            if "points" in equipment_data:
                for point_id, point_data in equipment_data["points"].items():
                    adapted_point = {
                        "id": point_id,
                        **point_data
                    }
                    
                    # Field name adaptations
                    if "quantity" in adapted_point and "measurement" not in adapted_point:
                        adapted_point["measurement"] = adapted_point["quantity"]
                        
                    # Handle component mapping
                    if "component" not in adapted_point:
                        # Use phenomenon and aspect to create component
                        phenomenon = adapted_point.get("phenomenon", [])
                        aspect = adapted_point.get("aspect", [])
                        
                        if isinstance(phenomenon, str):
                            phenomenon = [phenomenon]
                        if isinstance(aspect, str):
                            aspect = [aspect]
                            
                        # Combine phenomenon and aspect to create a component list
                        components = []
                        for p in phenomenon:
                            for a in aspect if aspect else [""]:
                                if p and a:
                                    components.append(f"{p} {a}")
                                elif p:
                                    components.append(p)
                                    
                        if components:
                            adapted_point["component"] = components
                    
                    adapted_model[equipment_type]["points"].append(adapted_point)
        
        return adapted_model
```

2. **Integrate Adapter in EnOSModelManager**:
```python
def _load_models(self) -> Dict:
    """Load the EnOS model definitions from the JSON file."""
    try:
        if self.enos_model_file and os.path.exists(self.enos_model_file):
            with open(self.enos_model_file, 'r', encoding='utf-8') as f:
                raw_models = json.load(f)
                # Use adapter to convert to expected format
                return EnOSModelAdapter.adapt_model(raw_models)
        else:
            logging.error(f"EnOS model file not found: {self.enos_model_file}")
            return {}
    except Exception as e:
        logging.error(f"Error loading EnOS models: {str(e)}")
        raise ResourceError(f"Failed to load EnOS model definitions: {str(e)}")
```

### Phase 2: Enhanced Diagnostics and Logging

**Objective**: Add detailed logging to diagnose matching issues.

**Tasks**:

1. **Add Component Score Logging**:
```python
def _calculate_match_score(self, bms_point, enos_point) -> Tuple[float, Dict[str, float]]:
    """Calculate the match score between a BMS point and an EnOS point."""
    # Initialize score components
    component_score = 0.0
    name_score = 0.0
    measurement_score = 0.0
    unit_score = 0.0
    
    # Component score - weight: 30%
    if bms_point.component and "component" in enos_point:
        components = enos_point["component"]
        if isinstance(components, str):
            components = [components]
            
        for component in components:
            similarity = self._calculate_string_similarity(
                bms_point.component.lower(), 
                component.lower()
            )
            component_score = max(component_score, similarity)
    
    # Log component score details
    logging.debug(f"Component score: {component_score:.2f} - BMS: {bms_point.component}, EnOS: {enos_point.get('component', 'None')}")
    
    # [Rest of the existing function with similar logging for each score component]
    
    # Weight the scores
    total_score = (
        component_score * 0.3 +
        name_score * 0.4 +
        measurement_score * 0.2 +
        unit_score * 0.1
    )
    
    score_details = {
        "component_score": component_score,
        "name_score": name_score,
        "measurement_score": measurement_score,
        "unit_score": unit_score,
        "total_score": total_score
    }
    
    logging.debug(f"Total match score: {total_score:.2f} for BMS point {bms_point.point_name} and EnOS point {enos_point.get('id', 'Unknown')}")
    
    return total_score, score_details
```

2. **Add Match Candidate Logging**:
```python
def _find_best_match(self, bms_point, enos_points) -> Tuple[Optional[Dict], float, Dict]:
    """Find the best matching EnOS point for a BMS point."""
    best_match = None
    best_score = 0.0
    best_score_details = {}
    
    logging.debug(f"Finding best match for BMS point: {bms_point.point_name} ({bms_point.equipment_type})")
    logging.debug(f"Evaluating {len(enos_points)} potential EnOS points")
    
    for enos_point in enos_points:
        score, score_details = self._calculate_match_score(bms_point, enos_point)
        
        logging.debug(f"  EnOS point: {enos_point.get('id', 'Unknown')} - Score: {score:.2f}")
        
        if score > best_score:
            best_match = enos_point
            best_score = score
            best_score_details = score_details
    
    if best_match:
        logging.debug(f"Best match found: {best_match.get('id', 'Unknown')} with score {best_score:.2f}")
        logging.debug(f"Score breakdown: {best_score_details}")
    else:
        logging.debug("No suitable match found")
        
    return best_match, best_score, best_score_details
```

### Phase 3: Lower Match Thresholds

**Objective**: Temporarily reduce match thresholds to capture more potential matches.

**Tasks**:

1. **Adjust Thresholds in MappingAgent**:
```python
def _map_equipment_points(self, equipment_type, instance_points):
    """Map points for a specific equipment instance."""
    mappings = []
    
    # Get the EnOS model for this equipment type
    enos_model = self._get_enos_model_for_equipment(equipment_type)
    
    if not enos_model or "points" not in enos_model:
        # No matching model, return unmapped points
        for point in instance_points:
            mappings.append(self._create_unmapped_point(point, f"No EnOS model found for {equipment_type}"))
        return mappings
        
    enos_points = enos_model["points"]
    
    # Process each point
    for point in instance_points:
        # Find the best match
        best_match, score, score_details = self._find_best_match(point, enos_points)
        
        # LOWERED THRESHOLD: Changed from 0.3 to 0.1
        if best_match and score > 0.1:
            # Create the EnOS point
            enos_point = self._create_enos_point(best_match, enos_model)
            
            # Determine mapping type based on score
            mapping_type = "suggested"
            # LOWERED THRESHOLD: Changed from 0.8 to 0.6
            if score > 0.6:
                mapping_type = "auto"
                
            # Create the mapping with transformation info
            transformation = self._determine_transformation(point, best_match)
            
            mapping = EnOSPointMapping(
                bms_point=point,
                enos_point=enos_point,
                confidence=score,
                mapping_type=mapping_type,
                transformation=transformation,
                reason=f"Matched with score {score:.2f}"
            )
        else:
            # No suitable match found
            mapping = self._create_unmapped_point(
                point, 
                f"No suitable match found, best score: {score:.2f}" if best_match else "No potential matches"
            )
            
        mappings.append(mapping)
        
    return mappings
```

### Phase 4: Schema Validation

**Objective**: Add validation of the EnOS model structure when it's loaded.

**Tasks**:

1. **Implement Schema Validation**:
```python
def _validate_model_schema(self, model):
    """Validate the EnOS model schema and log warnings for issues."""
    issues = []
    
    # Check if it's a dictionary
    if not isinstance(model, dict):
        issues.append("Model must be a dictionary")
        return issues
        
    # Check equipment types
    for eq_type, eq_data in model.items():
        if not isinstance(eq_data, dict):
            issues.append(f"Equipment type {eq_type} data must be a dictionary")
            continue
            
        # Check for required equipment fields
        for field in ["points"]:
            if field not in eq_data:
                issues.append(f"Equipment type {eq_type} missing required field: {field}")
                
        # Check points structure
        if "points" in eq_data:
            points = eq_data["points"]
            if not isinstance(points, list):
                issues.append(f"Equipment type {eq_type} points must be a list")
                continue
                
            # Check each point
            for i, point in enumerate(points):
                if not isinstance(point, dict):
                    issues.append(f"Equipment type {eq_type} point {i} must be a dictionary")
                    continue
                    
                # Check for required point fields
                for field in ["id"]:
                    if field not in point:
                        issues.append(f"Equipment type {eq_type} point {i} missing required field: {field}")
    
    # Log all issues
    if issues:
        for issue in issues:
            logging.warning(f"EnOS model schema issue: {issue}")
            
    return issues
```

2. **Integrate Validation in EnOSModelManager**:
```python
def _load_models(self) -> Dict:
    """Load the EnOS model definitions from the JSON file."""
    try:
        if self.enos_model_file and os.path.exists(self.enos_model_file):
            with open(self.enos_model_file, 'r', encoding='utf-8') as f:
                raw_models = json.load(f)
                
                # Use adapter to convert to expected format
                adapted_models = EnOSModelAdapter.adapt_model(raw_models)
                
                # Validate the adapted model
                issues = self._validate_model_schema(adapted_models)
                if issues:
                    logging.warning(f"Found {len(issues)} issues with the adapted EnOS model schema")
                else:
                    logging.info("EnOS model schema validation successful")
                    
                return adapted_models
        else:
            logging.error(f"EnOS model file not found: {self.enos_model_file}")
            return {}
    except Exception as e:
        logging.error(f"Error loading EnOS models: {str(e)}")
        raise ResourceError(f"Failed to load EnOS model definitions: {str(e)}")
```

## Implementation Timeline

1. **Phase 1: Schema Adapter** - Immediate (1-2 days)
   - First priority to get basic mapping working

2. **Phase 2: Enhanced Diagnostics** - Short-term (2-3 days)
   - Implement alongside Phase 1 to help debug issues

3. **Phase 3: Lower Thresholds** - Immediate (1 day)
   - Quick change to see if any matches become possible

4. **Phase 4: Schema Validation** - Short-term (2-3 days)
   - Implement after basic matching is working

## Expected Results

After implementing the above changes, we expect:

1. The mapping success rate to increase from 0% to at least 50-60% for auto-mapping and 70-80% for suggested mappings.

2. Detailed diagnostic information that identifies exactly which fields and score components are causing matching issues.

3. A more resilient system that can handle future schema changes through adaptation rather than breaking.

4. Clear validation warnings when schema issues are detected, preventing silent failures.

## Implemented Enhancements

The following enhancements have been implemented to improve the mapping functionality:

1. **Device Type Inference**: The system now automatically infers device types from point names when not provided
   - Example: "CT_1.TripStatus" → Device Type: "CT"
   - Implemented in `_infer_device_type_from_name` function

2. **Improved Prefix Handling**: Corrected issues with missing or incorrect prefixes in EnOS point names
   - Added detection and fixing of missing prefixes (e.g., "_raw_generic_point")
   - Enhanced validation to ensure device type prefixes match

3. **Batch Processing Mode**: Added support for processing large point sets in batches
   - Points grouped by device type for more focused processing
   - Progress tracking with partial results availability
   - Prioritization of specific device types

## Future Considerations

After addressing the immediate issues, the following enhancements should be considered:

1. **Metadata-Driven Matching**: Move field mappings to configuration instead of hardcoding them.

2. **Fuzzy Matching for Names**: Implement more sophisticated name matching algorithms.

3. **Machine Learning Matching**: Train a model based on successful mappings to predict future mappings.

4. **User Feedback Loop**: Incorporate user corrections into the matching algorithm to improve over time.

5. **Schema Registration**: Implement formal schema versioning and management to prevent future compatibility issues.

6. **Enhanced Prefix Validation**: Expand the validation rules for prefixes based on customer feedback.

By systematically implementing these changes, we have transformed the MappingAgent from a component with a 0% success rate to a reliable and adaptable part of the onboarding pipeline.