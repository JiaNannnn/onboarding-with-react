# AI/LLM Engineering Documentation

## Overview

This document details the AI and LLM integration aspects of the BMS to EnOS Onboarding Tool. The AI system is designed as a multi-agent architecture that specializes in different phases of the onboarding process, leveraging large language models for intelligent processing and analysis.

## Architecture

### Agent-Based Pipeline

The AI system follows a multi-agent architecture with three specialized components:

```
Raw BMS Points → Grouping Agent → Tagged Points → Mapping Agent → EnOS Mapped Points
```

1. **Grouping Agent**: Organizes raw BMS points into logical equipment hierarchies
2. **Tagging Agent**: Applies standardized tags based on HVAC ontology
3. **Mapping Agent**: Maps tagged points to EnOS model points with confidence scores

### Core Components

```
ai_llm/
├── agents/                # Agent implementations
│   ├── grouping_agent/    # Pattern recognition and grouping
│   ├── tagging_agent/     # Ontology-based tagging
│   └── mapping_agent/     # Mapping suggestion and confidence scoring
├── models/                # Data models and transformations
├── ontology/              # HVAC and BMS ontology definitions
├── prompts/               # LLM prompt templates
└── service.py             # Orchestration service
```

## Agent Implementations

### Grouping Agent

The Grouping Agent analyzes point names to organize them into equipment hierarchies:

```python
class GroupingAgent:
    """Agent for analyzing and grouping BMS points"""
    
    def __init__(self, equipment_ontology=None):
        self.equipment_ontology = equipment_ontology or self._load_default_ontology()
        self.equipment_patterns = self._generate_equipment_patterns()
        
    def process_points(self, points):
        """Process points and create hierarchical grouping"""
        # First pass: identify equipment types
        equipment_points = self._identify_equipment_types(points)
        
        # Second pass: group by specific instances
        hierarchical_groups = {}
        for equipment_type, points in equipment_points.items():
            device_instances = self._extract_device_instances(equipment_type, points)
            hierarchical_groups[equipment_type] = device_instances
            
        return hierarchical_groups
        
    def _identify_equipment_types(self, points):
        """Identify equipment types based on point names"""
        equipment_points = defaultdict(list)
        
        # Apply various identification strategies
        for point in points:
            equipment_type = None
            
            # Strategy 1: Direct pattern matching
            for eq_type, patterns in self.equipment_patterns.items():
                if any(re.search(pattern, point.point_name, re.IGNORECASE) for pattern in patterns):
                    equipment_type = eq_type
                    break
            
            # Strategy 2: LLM-based analysis for complex names
            if not equipment_type and point.description:
                equipment_type = self._identify_with_llm(point)
            
            # Default to "Unknown" if no type identified
            equipment_type = equipment_type or "Unknown"
            equipment_points[equipment_type].append(point)
            
        return dict(equipment_points)
        
    def _extract_device_instances(self, equipment_type, points):
        """Extract device instances for a specific equipment type"""
        # Implementation details
```

### Tagging Agent

The Tagging Agent applies metadata and tags based on HVAC ontology:

```python
class TaggingAgent:
    """Agent for tagging and enhancing BMS points with metadata"""
    
    def __init__(self, hvac_ontology=None):
        self.hvac_ontology = hvac_ontology or self._load_hvac_ontology()
        self.component_patterns = self._generate_component_patterns()
        self.function_patterns = self._generate_function_patterns()
        
    def process_grouped_points(self, grouped_points):
        """Process grouped points and add tags/metadata"""
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
        
    def _tag_point(self, point, equipment_type, instance_id):
        """Tag an individual point with metadata"""
        # Get standards for this equipment type
        std_points = self.hvac_ontology.get('STANDARD_POINTS', {}).get(equipment_type, [])
        
        # Identify component and subcomponent
        component, subcomponent = self._identify_component(point, equipment_type)
        
        # Determine point function
        function = self._determine_function(point)
        
        # Identify phenomenon and quantity
        phenomenon, quantity = self._identify_phenomenon_quantity(point)
        
        # Create tags based on gathered information
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

### Mapping Agent

The Mapping Agent suggests EnOS point mappings with confidence scores:

```python
class MappingAgent:
    """Agent for mapping BMS points to EnOS model points"""
    
    def __init__(self, enos_model_definitions=None):
        self.enos_model_defs = enos_model_definitions or self._load_enos_models()
        self.mapping_rules = self._load_mapping_rules()
        self.transformation_rules = self._load_transformation_rules()
        
    def process_tagged_points(self, tagged_grouped_points):
        """Process tagged points and generate EnOS mappings"""
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
        
    def _suggest_mappings(self, point):
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

## LLM Integration

### Prompt Engineering

The system uses specialized prompts for different tasks:

#### Grouping Prompt Template

```python
GROUPING_PROMPT_TEMPLATE = """
You are an expert in Building Management Systems (BMS). Your task is to analyze the
following list of BMS points and identify the equipment type and instance for each point.

Points:
{points_text}

Instructions:
1. Identify the equipment type for each point (AHU, FCU, VAV, CHILLER, BOILER, etc.)
2. For each equipment type, identify specific instances/units
3. Return the points organized by equipment type and instance

Example patterns:
- AHU-1.ZN-T → Air Handling Unit 1, Zone Temperature
- FCU_3B_PUMP_STAT → Fan Coil Unit 3B, Pump Status
- CHILLER-02.COND-PRESS → Chiller 2, Condenser Pressure

Format your response as a JSON object with the following structure:
{{
  "equipment_type": {{
    "instance_id": [
      {{
        "point_id": "id",
        "point_name": "name",
        ...
      }}
    ]
  }}
}}

Think step by step and be as accurate as possible.
"""
```

#### Tagging Prompt Template

```python
TAGGING_PROMPT_TEMPLATE = """
You are an expert in HVAC systems and building automation. Your task is to analyze
these BMS points that have already been grouped by equipment type and instance.
For each point, determine its component, function, and add appropriate tags.

Grouped Points:
{grouped_points_json}

HVAC Component Types:
- Fan: Supply, Return, Exhaust
- Damper: Outside Air, Return Air, Supply Air
- Valve: Heating, Cooling, Mixed
- Sensor: Temperature, Pressure, Humidity, Flow
- Filter: Air, Water
- Coil: Heating, Cooling, Mixed
- Pump: Primary, Secondary, Condenser

Point Functions:
- Sensor: Measures a physical value
- Command: Controls equipment operation
- Setpoint: Desired value for operation
- Status: Indicates operational state

For each point, provide:
1. Component and subcomponent classification
2. Function determination
3. Tags that identify the point's purpose
4. Enhanced description

Format your response as a JSON with the same structure as the input, but with
added metadata for each point.

Think step by step and use your knowledge of HVAC terminology.
"""
```

#### Mapping Prompt Template

```python
MAPPING_PROMPT_TEMPLATE = """
You are an expert in mapping BMS points to standardized EnOS model points.
Your task is to analyze these tagged BMS points and suggest appropriate
mappings to EnOS model points.

Tagged BMS Points:
{tagged_points_json}

Available EnOS Model Points:
{enos_model_points_json}

For each BMS point, determine:
1. The most appropriate EnOS model point to map to
2. A confidence score (0-1) for the mapping
3. Any required data transformations
4. The mapping type: "auto" (>0.8 confidence), "suggested" (0.5-0.8), "manual" (<0.5)

Consider these factors when mapping:
- Point function (sensor, command, setpoint, status)
- Physical quantity measured or controlled
- Engineering units and potential conversions
- Equipment component relationships
- Tag and metadata similarity

Format your response as a JSON with mappings for each point, including confidence
scores and reasoning.

Think step by step and prioritize accuracy over quantity of mappings.
"""
```

### LLM Service Implementation

```python
class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self, model="gpt-4o"):
        self.model = model
        self.system_prompt = "You are an expert HVAC and building automation assistant specializing in BMS to EnOS mapping."
        self.service_ready = self._check_service_ready()
        
    def _check_service_ready(self):
        """Check if the OpenAI service is available"""
        try:
            # Simple API test call
            openai.api_key = os.getenv("OPENAI_API_KEY")
            return True
        except Exception as e:
            openai_logger.error(f"OpenAI service initialization error: {str(e)}")
            return False
            
    def group_points(self, points):
        """Use LLM to group points by equipment and instance"""
        if not self.service_ready:
            raise ServiceError("OpenAI service is not available")
            
        # Prepare points text for prompt
        points_text = self._format_points_for_prompt(points)
        
        # Create prompt with template
        prompt = GROUPING_PROMPT_TEMPLATE.format(points_text=points_text)
        
        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Parse response
            result_text = response['choices'][0]['message']['content']
            
            # Extract JSON from response
            grouped_points = self._extract_json_from_response(result_text)
            
            return grouped_points
            
        except Exception as e:
            openai_logger.error(f"Error in OpenAI grouping call: {str(e)}")
            raise ProcessingError("Failed to process points with OpenAI", 
                                  phase="grouping", 
                                  original_error=e)
```

## Confidence Scoring

The system implements a sophisticated confidence scoring algorithm:

```python
def _calculate_confidence(self, bms_point, enos_point):
    """Calculate confidence score for a potential mapping"""
    # Base score
    score = 0.0
    
    # Feature weights
    weights = {
        'name_similarity': 0.3,
        'function_match': 0.2,
        'component_match': 0.15,
        'phenomenon_match': 0.15,
        'unit_compatibility': 0.1,
        'tag_overlap': 0.1
    }
    
    # Name similarity (using fuzzy matching)
    name_similarity = self._calculate_name_similarity(bms_point.point_name, enos_point.point_name)
    score += weights['name_similarity'] * name_similarity
    
    # Function match
    if bms_point.function == enos_point.function:
        score += weights['function_match']
    
    # Component match
    component_match = self._calculate_component_match(bms_point.component, enos_point.component)
    score += weights['component_match'] * component_match
    
    # Phenomenon match
    if bms_point.phenomenon == enos_point.phenomenon:
        score += weights['phenomenon_match']
    
    # Unit compatibility
    unit_compatibility = self._check_unit_compatibility(bms_point.unit, enos_point.unit)
    score += weights['unit_compatibility'] * unit_compatibility
    
    # Tag overlap
    tag_overlap = self._calculate_tag_overlap(bms_point.tags, enos_point.tags)
    score += weights['tag_overlap'] * tag_overlap
    
    return round(score, 2)
```

## Token Optimization

The system implements strategies to optimize token usage:

```python
def _optimize_points_for_prompt(self, points, max_tokens=4000):
    """Optimize points for prompt to stay within token limits"""
    # Estimate tokens for each point
    estimated_tokens_per_point = 50  # Average estimate
    max_points = max_tokens // estimated_tokens_per_point
    
    if len(points) <= max_points:
        return self._format_points_for_prompt(points)
    
    # If too many points, use batching
    return self._batch_process_points(points, batch_size=max_points)
    
def _batch_process_points(self, points, batch_size):
    """Process points in batches to handle token limits"""
    results = {}
    
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        batch_results = self._process_point_batch(batch)
        
        # Merge batch results
        for equipment_type, instances in batch_results.items():
            if equipment_type not in results:
                results[equipment_type] = {}
                
            for instance_id, instance_points in instances.items():
                if instance_id not in results[equipment_type]:
                    results[equipment_type][instance_id] = []
                
                results[equipment_type][instance_id].extend(instance_points)
    
    return results
```

## Work In Progress & Roadmap

### Current Development

- Implementing core agent architecture
- Creating specialized LLM prompts
- Developing confidence scoring algorithm
- Implementing token optimization

### Planned Enhancements

1. **Pattern Recognition Improvements**
   - Enhance Grouping Agent with better pattern detection
   - Implement learning from user corrections
   - Add support for custom naming conventions

2. **Ontology Integration**
   - Develop versioned ontology management
   - Create dynamic ontology loading
   - Implement fallback mechanisms

3. **Confidence Score Refinement**
   - Fine-tune scoring algorithm based on feedback
   - Add explainability for confidence scores
   - Implement threshold adjustment based on data quality

## Technical Decisions

### Technology Selection

- **GPT-4o** - Primary LLM for intelligent processing
- **Multi-agent Architecture** - Specialization for different tasks
- **Domain-specific Prompts** - Tailored to specific processing needs
- **Confidence Scoring** - Quantitative assessment of mapping quality

### Architectural Decisions

1. **Agent Specialization**
   - Grouping, Tagging, and Mapping as separate concerns
   - Clear interfaces between agents
   - Independent development and optimization

2. **Prompt Engineering Approach**
   - Task-specific prompt templates
   - Structured output formats (JSON)
   - Example-driven prompting

3. **Memory Management Strategy**
   - Batch processing for token optimization
   - Caching of LLM responses
   - Incremental processing pipeline

## Best Practices & Coding Standards

1. **Prompt Design**
   - Clear instructions and constraints
   - Structured output format specification
   - Example-based guidance
   - Step-by-step reasoning instructions

2. **Error Handling**
   - Graceful fallback mechanisms
   - Comprehensive error context
   - Response validation

3. **Performance Optimization**
   - Cache frequent LLM responses
   - Batch similar requests
   - Optimize token usage

## Performance Considerations

1. **Token Management**
   - Monitor and optimize token usage
   - Implement batching for large datasets
   - Use token-efficient data formats

2. **Response Time Optimization**
   - Implement parallel processing where possible
   - Cache common responses
   - Pre-compute expensive operations

3. **Error Resilience**
   - Handle API failures gracefully
   - Implement exponential backoff for retries
   - Provide fallback mechanisms

---

*This documentation is maintained by the AI/LLM Engineer and should be updated as the implementation evolves.*