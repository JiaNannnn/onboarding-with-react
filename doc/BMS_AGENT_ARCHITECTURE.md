# BMS to EnOS Onboarding Tool - Agent Architecture

## System Overview

The BMS to EnOS Onboarding Tool has been redesigned with a multi-agent architecture to improve specialization, maintainability, and processing efficiency. The system splits the onboarding workflow into three distinct phases, each managed by a specialized agent:

1. **Grouping Agent**: Organizes raw BMS points into logical equipment hierarchies
2. **Tagging Agent**: Applies standardized tags and metadata based on HVAC ontology
3. **Mapping Agent**: Maps tagged BMS points to EnOS model points

This architecture supports the three-stage implementation plan:
- Stage 1: Data Integration & Semantic Transformation
- Stage 2: Asset Modeling & Schema Instantiation
- Stage 3: Hierarchical Topology Generation

## Data Flow

```
Raw BMS Points → Grouping Agent → Grouped Points → Tagging Agent → Tagged Points → Mapping Agent → EnOS Mapped Points
```

## Agent Specifications

### 1. Grouping Agent

#### Responsibilities
- Analyze raw BMS point names and attributes
- Identify equipment types (AHU, FCU, CT, CHPL, etc.)
- Group points by specific equipment instances
- Create hierarchical organization of points
- Handle diverse naming conventions and patterns
- Provide consistent organizational structure for downstream processing

#### Key Methods
- `identify_equipment_type(point_name: str) -> str`: Detect equipment type from point name
- `extract_device_instance(point_name: str, equipment_type: str) -> str`: Extract specific instance identifier
- `group_points_by_equipment(points: List[BMSPoint]) -> Dict[str, Dict[str, List[BMSPoint]]]`: Create hierarchical grouping
- `normalize_equipment_names(equipment_name: str) -> str`: Standardize equipment naming
- `detect_naming_patterns(points: List[BMSPoint]) -> Dict[str, Any]`: Identify common naming patterns
- `validate_grouping(grouping: Dict[str, Any]) -> bool`: Ensure grouping meets quality standards

#### Technical Implementation
```python
class GroupingAgent:
    def __init__(self, equipment_ontology: Dict = None):
        self.equipment_ontology = equipment_ontology or self._load_default_ontology()
        self.equipment_patterns = self._generate_equipment_patterns()
        
    def process_points(self, points: List[BMSPoint]) -> Dict[str, Dict[str, List[BMSPoint]]]:
        """
        Main processing method that takes raw points and returns hierarchical grouping
        """
        # First pass: identify equipment types
        equipment_points = self._identify_equipment_types(points)
        
        # Second pass: group by specific instances
        hierarchical_groups = {}
        for equipment_type, equipment_points in equipment_points.items():
            device_instances = self._extract_device_instances(equipment_type, equipment_points)
            hierarchical_groups[equipment_type] = device_instances
            
        return hierarchical_groups
    
    def _identify_equipment_types(self, points: List[BMSPoint]) -> Dict[str, List[BMSPoint]]:
        """Group points by equipment type"""
        # Implementation details

    def _extract_device_instances(self, equipment_type: str, points: List[BMSPoint]) -> Dict[str, List[BMSPoint]]:
        """Extract device instances for specific equipment type"""
        # Implementation details
        
    def _load_default_ontology(self) -> Dict:
        """Load the HVAC ontology definitions"""
        # Implementation details
```

### 2. Tagging Agent

#### Responsibilities
- Apply standardized tags to points based on HVAC ontology
- Classify points according to component/subcomponent relationships
- Identify point function (sensor, setpoint, command, status)
- Determine engineering units (when missing in raw data)
- Associate metadata (phenomenon, quantity, unit, location)
- Enhance point descriptions with standardized terminology

#### Key Methods
- `identify_point_type(point: BMSPoint) -> str`: Determine the type of measurement
- `classify_point_component(point: BMSPoint, equipment_type: str) -> str`: Identify which equipment component the point belongs to
- `determine_point_function(point: BMSPoint) -> str`: Classify point as sensor, setpoint, command, or status
- `infer_engineering_units(point: BMSPoint) -> str`: Suggest appropriate units if missing
- `generate_point_tags(point: BMSPoint) -> List[str]`: Create standardized tags
- `enhance_description(point: BMSPoint) -> str`: Generate improved descriptive text

#### Technical Implementation
```python
class TaggingAgent:
    def __init__(self, hvac_ontology=None, resource_definitions=None):
        self.hvac_ontology = hvac_ontology or self._load_hvac_ontology()
        self.resource_defs = resource_definitions or self._load_resource_definitions()
        
    def process_grouped_points(self, grouped_points: Dict[str, Dict[str, List[BMSPoint]]]) -> Dict[str, Dict[str, List[TaggedBMSPoint]]]:
        """
        Process already grouped points and return the same structure with tagged points
        """
        tagged_grouped_points = {}
        
        for equipment_type, instances in grouped_points.items():
            tagged_grouped_points[equipment_type] = {}
            
            for instance_id, points in instances.items():
                tagged_points = []
                
                for point in points:
                    tagged_point = self._tag_point(point, equipment_type, instance_id)
                    tagged_points.append(tagged_point)
                    
                tagged_grouped_points[equipment_type][instance_id] = tagged_points
                
        return tagged_grouped_points
    
    def _tag_point(self, point: BMSPoint, equipment_type: str, instance_id: str) -> TaggedBMSPoint:
        """Tag an individual point with metadata"""
        # Implementation details
        
        # Get standard points for this equipment type
        std_points = self.hvac_ontology.get('STANDARD_POINTS', {}).get(equipment_type, [])
        
        # Identify component and subcomponent
        component, subcomponent = self._identify_component(point, equipment_type)
        
        # Determine point function
        function = self._determine_function(point)
        
        # Identify phenomenon and quantity from resource definitions
        phenomenon, quantity = self._identify_phenomenon_quantity(point)
        
        # Create tags based on all gathered information
        tags = self._generate_tags(
            point, 
            equipment_type, 
            instance_id, 
            component, 
            subcomponent,
            function,
            phenomenon,
            quantity
        )
        
        # Create enhanced description
        description = self._enhance_description(point, equipment_type, instance_id, component)
        
        # Create tagged point with all metadata
        tagged_point = TaggedBMSPoint.from_bms_point(
            point,
            tags=tags,
            component=component,
            subcomponent=subcomponent,
            function=function,
            phenomenon=phenomenon, 
            quantity=quantity,
            enhanced_description=description
        )
        
        return tagged_point
```

### 3. Mapping Agent

#### Responsibilities
- Map tagged BMS points to EnOS model points
- Suggest appropriate mappings based on tag metadata
- Validate mappings against EnOS model specifications
- Handle point transformation rules when needed
- Generate mapping configurations for export
- Provide mapping quality/confidence scores

#### Key Methods
- `suggest_mappings(tagged_point: TaggedBMSPoint) -> List[EnOSPointMapping]`: Generate mapping suggestions
- `rank_mapping_suggestions(suggestions: List[EnOSPointMapping]) -> List[EnOSPointMapping]`: Order by confidence
- `validate_mapping(mapping: EnOSPointMapping) -> bool`: Check mapping validity
- `apply_transformation_rule(mapping: EnOSPointMapping) -> EnOSPointMapping`: Apply data transformations
- `generate_mapping_config(mappings: List[EnOSPointMapping]) -> Dict`: Create exportable configuration
- `calculate_confidence_score(mapping: EnOSPointMapping) -> float`: Determine mapping confidence

#### Technical Implementation
```python
class MappingAgent:
    def __init__(self, enos_model_definitions=None):
        self.enos_model_defs = enos_model_definitions or self._load_enos_models()
        self.mapping_rules = self._load_mapping_rules()
        self.transformation_rules = self._load_transformation_rules()
        
    def process_tagged_points(self, tagged_grouped_points: Dict[str, Dict[str, List[TaggedBMSPoint]]]) -> Dict[str, Dict[str, List[EnOSPointMapping]]]:
        """
        Process tagged points and generate EnOS mappings
        """
        mapped_points = {}
        
        for equipment_type, instances in tagged_grouped_points.items():
            mapped_points[equipment_type] = {}
            
            for instance_id, points in instances.items():
                mappings = []
                
                for point in points:
                    mapping_suggestions = self._suggest_mappings(point)
                    if mapping_suggestions:
                        # Use the highest confidence mapping
                        best_mapping = mapping_suggestions[0]
                        mappings.append(best_mapping)
                    else:
                        # Create unmapped record
                        unmapped = EnOSPointMapping(
                            bms_point=point,
                            enos_point=None,
                            confidence=0,
                            mapping_type="unmapped",
                            reason="No suitable mapping found"
                        )
                        mappings.append(unmapped)
                
                mapped_points[equipment_type][instance_id] = mappings
                
        return mapped_points
    
    def _suggest_mappings(self, point: TaggedBMSPoint) -> List[EnOSPointMapping]:
        """Generate and rank mapping suggestions"""
        suggestions = []
        
        # Find candidate EnOS points based on metadata
        candidates = self._find_enos_candidates(point)
        
        for candidate in candidates:
            confidence = self._calculate_confidence(point, candidate)
            transformation = self._determine_transformation(point, candidate)
            
            mapping = EnOSPointMapping(
                bms_point=point,
                enos_point=candidate,
                confidence=confidence,
                mapping_type="auto" if confidence > 0.8 else "suggested", 
                transformation=transformation
            )
            
            suggestions.append(mapping)
            
        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return suggestions
```

## Integration Between Agents

The three agents are designed to work sequentially in a pipeline, but should be loosely coupled for maintainability:

### Interface Contracts

1. **Grouping Agent Output** → **Tagging Agent Input**:
   ```python
   # Structure: Dict[equipment_type: str, Dict[instance_id: str, List[BMSPoint]]]
   grouped_points = {
       "AHU": {
           "AHU-1": [BMSPoint1, BMSPoint2, ...],
           "AHU-2": [BMSPoint3, BMSPoint4, ...]
       },
       "FCU": {
           "FCU-101": [BMSPoint5, BMSPoint6, ...]
       }
   }
   ```

2. **Tagging Agent Output** → **Mapping Agent Input**:
   ```python
   # Structure: Dict[equipment_type: str, Dict[instance_id: str, List[TaggedBMSPoint]]]
   tagged_points = {
       "AHU": {
           "AHU-1": [TaggedBMSPoint1, TaggedBMSPoint2, ...],
           "AHU-2": [TaggedBMSPoint3, TaggedBMSPoint4, ...]
       },
       "FCU": {
           "FCU-101": [TaggedBMSPoint5, TaggedBMSPoint6, ...]
       }
   }
   ```

3. **Mapping Agent Output**:
   ```python
   # Structure: Dict[equipment_type: str, Dict[instance_id: str, List[EnOSPointMapping]]]
   mapped_points = {
       "AHU": {
           "AHU-1": [EnOSPointMapping1, EnOSPointMapping2, ...],
           "AHU-2": [EnOSPointMapping3, EnOSPointMapping4, ...]
       },
       "FCU": {
           "FCU-101": [EnOSPointMapping5, EnOSPointMapping6, ...]
       }
   }
   ```

### Service Orchestration

```python
class BMSOnboardingService:
    def __init__(self):
        self.grouping_agent = GroupingAgent()
        self.tagging_agent = TaggingAgent()
        self.mapping_agent = MappingAgent()
        
    def process_bms_points(self, points: List[BMSPoint]) -> Dict[str, Dict[str, List[EnOSPointMapping]]]:
        """
        Process BMS points through the complete pipeline
        """
        with DiagnosticLogger() as diag_log:
            grouped = self.grouping_agent.process_points(points)
            diag_log.log_stage("grouping", metadata={
                "group_counts": {k: len(v) for k,v in grouped.items()}
            })
            tagged = self.tagging_agent.process_grouped_points(grouped)
            mapped = self.mapping_agent.process_tagged_points(tagged)
            return mapped
    
    def get_mapping_summary(self, mapped_points) -> Dict[str, Any]:
        """
        Generate a summary of the mapping results
        """
        # Implementation details
        
    def export_mapping_config(self, mapped_points) -> str:
        """
        Generate exportable mapping configuration
        """
        # Implementation details
```

## Data Models

### BMSPoint Model
```python
class BMSPoint:
    def __init__(
        self,
        point_id: str,
        point_name: str,
        point_type: str,
        description: str = "",
        device_id: str = "",
        value_type: str = "",
        unit: str = "",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        raw_data: Dict[str, Any] = None
    ):
        self.point_id = point_id
        self.point_name = point_name
        self.point_type = point_type
        self.description = description
        self.device_id = device_id
        self.value_type = value_type
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.raw_data = raw_data or {}
```

### TaggedBMSPoint Model
```python
class TaggedBMSPoint(BMSPoint):
    def __init__(
        self,
        point_id: str,
        point_name: str,
        point_type: str,
        description: str = "",
        device_id: str = "",
        value_type: str = "",
        unit: str = "",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        raw_data: Dict[str, Any] = None,
        tags: List[str] = None,
        component: str = "",
        subcomponent: str = "",
        function: str = "",
        phenomenon: str = "",
        quantity: str = "",
        enhanced_description: str = ""
    ):
        super().__init__(
            point_id, point_name, point_type, description, device_id,
            value_type, unit, min_value, max_value, raw_data
        )
        self.tags = tags or []
        self.component = component
        self.subcomponent = subcomponent
        self.function = function
        self.phenomenon = phenomenon
        self.quantity = quantity
        self.enhanced_description = enhanced_description or description
        
    @classmethod
    def from_bms_point(cls, point: BMSPoint, **kwargs) -> 'TaggedBMSPoint':
        """Create a TaggedBMSPoint from a BMSPoint with additional attributes"""
        tagged_point = cls(
            point_id=point.point_id,
            point_name=point.point_name,
            point_type=point.point_type,
            description=point.description,
            device_id=point.device_id,
            value_type=point.value_type,
            unit=point.unit,
            min_value=point.min_value,
            max_value=point.max_value,
            raw_data=point.raw_data,
            **kwargs
        )
        return tagged_point
```

### EnOSPointMapping Model
```python
class EnOSPoint:
    def __init__(
        self,
        point_id: str,
        point_name: str,
        model_id: str,
        point_type: str = "",
        description: str = "",
        unit: str = "",
        data_type: str = ""
    ):
        self.point_id = point_id
        self.point_name = point_name
        self.model_id = model_id
        self.point_type = point_type
        self.description = description
        self.unit = unit
        self.data_type = data_type

class EnOSPointMapping:
    def __init__(
        self,
        bms_point: TaggedBMSPoint,
        enos_point: Optional[EnOSPoint],
        confidence: float = 0.0,
        mapping_type: str = "suggested",  # "auto", "suggested", "manual", "unmapped"
        transformation: Optional[Dict[str, Any]] = None,
        reason: str = ""
    ):
        self.bms_point = bms_point
        self.enos_point = enos_point
        self.confidence = confidence
        self.mapping_type = mapping_type
        self.transformation = transformation
        self.reason = reason
```

## Error Handling

Each agent should implement comprehensive error handling:

1. **Validation Errors**: Issues with input data format or content
2. **Processing Errors**: Failures during the processing pipeline
3. **Resource Errors**: Problems accessing required resources (ontology, definitions)

Example implementation:

```python
class AgentError(Exception):
    """Base class for agent exceptions"""
    pass

class ValidationError(AgentError):
    """Error for invalid input data"""
    pass

class ProcessingError(AgentError):
    """Error during data processing"""
    pass

class ResourceError(AgentError):
    """Error accessing required resources"""
    pass

# Usage example
def process_points(self, points: List[BMSPoint]) -> Dict:
    if not points:
        raise ValidationError("Empty points list provided")
    
    try:
        # Processing logic
        return result
    except KeyError as e:
        raise ProcessingError(f"Missing key in processing: {str(e)}")
    except Exception as e:
        raise ProcessingError(
            f"Grouping failure in {equipment_type}",
            original_error=e,
            context={
                "point_count": len(points),
                "equipment_type": equipment_type,
                "phase": "grouping"
            }
        ) from e
```

## Testing Strategy

### Unit Tests

Each agent should have comprehensive unit tests:

1. **GroupingAgent Tests**:
   - Test equipment type identification with various naming patterns
   - Test device instance extraction with edge cases
   - Test hierarchical grouping structure
   - Test handling of malformed point names

2. **TaggingAgent Tests**:
   - Test component/subcomponent classification
   - Test point function determination
   - Test tag generation logic
   - Test description enhancement

3. **MappingAgent Tests**:
   - Test mapping suggestions for various point types
   - Test confidence scoring algorithm
   - Test transformation rule application
   - Test mapping validation logic

### Integration Tests

Test the interaction between agents:

1. **GroupingAgent → TaggingAgent**:
   - Verify that grouped points are correctly processed by the tagging agent
   - Check preservation of hierarchical structure

2. **TaggingAgent → MappingAgent**:
   - Verify that tagged points are correctly processed by the mapping agent
   - Check that metadata influences mapping suggestions

3. **End-to-End Pipeline**:
   - Test complete processing from raw points to final mappings
   - Verify hierarchical structure preservation throughout the pipeline

### Test Data Sets

Create comprehensive test data sets:

1. **Synthetic Test Data**:
   - Generate points with predictable patterns for unit testing
   - Create edge cases and corner cases deliberately

2. **Real-world Test Data**:
   - Use anonymized data from actual BMS systems
   - Include diverse equipment types and naming conventions

## Implementation Plan

1. **Phase 1: Core Infrastructure**
   - Implement data models (BMSPoint, TaggedBMSPoint, EnOSPointMapping)
   - Build service orchestration framework
   - Create base agent classes with common utilities

2. **Phase 2: Grouping Agent**
   - Implement equipment type identification
   - Develop device instance extraction
   - Build hierarchical grouping logic
   - Add pattern detection capabilities

3. **Phase 3: Tagging Agent**
   - Integrate HVAC ontology
   - Implement component classification
   - Develop tag generation logic
   - Create description enhancement features

4. **Phase 4: Mapping Agent**
   - Implement mapping suggestion algorithms
   - Develop confidence scoring
   - Build transformation rule engine
   - Create mapping validation logic

5. **Phase 5: Integration & Testing**
   - Connect all agents into unified pipeline
   - Develop comprehensive tests
   - Optimize performance
   - Document API and usage

## Conclusion

This agent-based architecture improves the BMS to EnOS onboarding process by:

1. **Specialization**: Each agent focuses on a specific aspect of the workflow
2. **Maintainability**: Clear boundaries between components
3. **Extensibility**: Easy to enhance individual agents without affecting others
4. **Quality**: Better results through specialized processing at each stage
5. **Performance**: Optimized processing for each specific task

This design supports the staged implementation approach while providing a clear path for future enhancements and optimizations. 

def test_memory_usage():
    # Generate 100,000 sample points
    points = generate_large_dataset() 
    service = BMSOnboardingService()
    
    with memory_profiler.profile() as profiler:
        service.process_bms_points(points)
    
    assert profiler.memory_usage < 500  # MB 

def test_pipeline_state_preservation():
    input_points = [...]  # Points with known issues
    service = BMSOnboardingService()
    
    with pytest.raises(ProcessingError) as e:
        service.process_bms_points(input_points)
    
    assert "Grouping" in e.value.context['phase']
    assert e.value.context['batch_index'] == 3 