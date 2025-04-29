# Mapping Feedback and Persistence System

## Overview

This document outlines the design and implementation plan for the Mapping Feedback and Persistence System in the BMS to EnOS mapping platform. This system enables the platform to store, analyze, and learn from mapping outcomes, creating a continuous improvement cycle for mapping quality.

## Current Limitations

The current mapping system faces several persistence-related challenges:

1. Limited storage of mapping decisions and their rationale
2. No systematic feedback collection from successful and failed mappings
3. Inability to transfer knowledge between similar mapping tasks
4. Lack of detailed quality metrics and improvement analytics
5. No historical comparison to track mapping improvements over time

## System Components

### 1. Mapping Knowledge Repository

**Purpose**: Centralized storage for mapping decisions, patterns, and outcomes.

**Implementation**:
- Create a structured database schema for mapping knowledge
- Implement versioning for evolving mapping patterns
- Develop efficient indexing for pattern retrieval
- Build automated cleanup and archiving mechanisms

**Schema Design**:
```
Mapping Patterns:
- pattern_id: UUID
- device_type: String
- point_category: String
- source_pattern: String
- target_pattern: String
- confidence: Float
- creation_date: Timestamp
- last_modified: Timestamp
- version: Integer
- usage_count: Integer
- success_rate: Float

Mapping Examples:
- example_id: UUID
- pattern_id: FK -> Mapping Patterns
- bms_point: String
- enos_point: String
- result: Enum(success, failure)
- quality_score: Float
- feedback: Text
- context: JSON
- timestamp: Timestamp

Quality Metrics:
- metric_id: UUID
- mapping_task_id: String
- total_points: Integer
- success_count: Integer
- excellent_count: Integer
- good_count: Integer
- fair_count: Integer
- poor_count: Integer
- unacceptable_count: Integer
- average_quality: Float
- timestamp: Timestamp
```

### 2. Feedback Collection System

**Purpose**: Capture and process feedback on mapping quality and correctness.

**Implementation**:
- Create automated quality assessment
- Implement user feedback collection interfaces
- Develop domain expert review workflows
- Build anomaly detection for unusual mappings

**Feedback Types**:
- Automated quality scoring
- User corrections and approvals
- Expert reviews and annotations
- System-detected anomalies
- Cross-validation results

### 3. Analytics Engine

**Purpose**: Analyze mapping patterns and quality trends to identify improvement opportunities.

**Implementation**:
- Create mapping quality dashboards
- Implement trend analysis for quality metrics
- Develop pattern effectiveness evaluation
- Build comparative analysis between mapping runs

**Key Metrics**:
- Quality score distribution
- Success rate by device type
- Pattern efficacy ratings
- Most problematic point types
- Quality improvement over time

### 4. Knowledge Transfer System

**Purpose**: Apply learned mapping patterns across different buildings and systems.

**Implementation**:
- Create mapping pattern export/import
- Implement cross-project pattern recommendation
- Develop context-aware pattern matching
- Build domain adaptation for different building types

**Transfer Scenarios**:
- New building with similar device types
- New project with different naming conventions
- Expansion with new device types
- Cross-vendor system integration

### 5. Continuous Improvement Framework

**Purpose**: Systematically enhance mapping quality based on feedback and analysis.

**Implementation**:
- Create automated pattern refinement
- Implement A/B testing for pattern improvements
- Develop quality goal setting and tracking
- Build systematic review schedules

**Improvement Loop**:
```
┌─────────────────┐
│ Collect Feedback│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analyze Patterns│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Refine Patterns │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Test Changes  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deploy Updates  │
└────────┬────────┘
         │
         ▼
    Improved Quality
```

## Implementation Plan

### Phase 1: Knowledge Repository Development

1. Design and implement the database schema
2. Create the API layer for repository access
3. Develop the initial data models
4. Implement basic persistence functionality

### Phase 2: Feedback Collection Implementation

1. Design the feedback collection interfaces
2. Implement automated quality assessment
3. Create the feedback processing pipeline
4. Develop the annotation system for expert input

### Phase 3: Analytics Engine Creation

1. Design the analytics dashboard
2. Implement the core metrics calculations
3. Create trend analysis components
4. Develop comparative analysis tools

### Phase 4: Knowledge Transfer System

1. Design the pattern export/import functionality
2. Implement cross-project recommendations
3. Create the context adaptation system
4. Develop validation for transferred patterns

### Phase 5: Continuous Improvement Framework

1. Design the improvement workflow
2. Implement pattern refinement algorithms
3. Create A/B testing infrastructure
4. Develop quality tracking and reporting

## Technical Implementation

### Repository API

```python
class MappingRepository:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def store_mapping_pattern(self, pattern):
        """Store a new mapping pattern or update existing one"""
        existing = self.find_similar_pattern(pattern)
        if existing:
            return self.update_pattern(existing.id, pattern)
        return self.create_pattern(pattern)
    
    def find_patterns_for_point(self, point, device_type, context=None):
        """Find applicable patterns for a given point"""
        # Implementation details...
    
    def record_mapping_result(self, pattern_id, bms_point, enos_point, result, quality_score):
        """Record the outcome of applying a pattern"""
        # Implementation details...
    
    def get_quality_metrics(self, filters=None):
        """Retrieve quality metrics based on filters"""
        # Implementation details...
```

### Feedback Collection

```python
class FeedbackCollector:
    def __init__(self, repository):
        self.repository = repository
    
    def collect_automated_feedback(self, mapping_task_id, mappings):
        """Collect automated feedback from mapping results"""
        quality_metrics = self.assess_quality(mappings)
        self.repository.store_quality_metrics(mapping_task_id, quality_metrics)
        
        for mapping in mappings:
            pattern_id = mapping.get('pattern_id')
            if pattern_id:
                result = 'success' if mapping.get('status') == 'mapped' else 'failure'
                quality_score = self.calculate_quality_score(mapping)
                self.repository.record_mapping_result(
                    pattern_id,
                    mapping['original']['pointName'],
                    mapping['mapping']['enosPoint'],
                    result,
                    quality_score
                )
    
    def collect_user_feedback(self, mapping_id, user_feedback):
        """Collect feedback provided by users"""
        # Implementation details...
```

### Analytics Implementation

```python
class MappingAnalytics:
    def __init__(self, repository):
        self.repository = repository
    
    def analyze_quality_trends(self, time_period=None, device_type=None):
        """Analyze quality trends over time"""
        metrics = self.repository.get_quality_metrics({
            'time_period': time_period,
            'device_type': device_type
        })
        
        return {
            'average_quality': self.calculate_average(metrics, 'average_quality'),
            'success_rate': self.calculate_average(metrics, 'success_rate'),
            'trend': self.calculate_trend(metrics, 'average_quality'),
            'by_device_type': self.group_by_device_type(metrics),
            'improvement': self.calculate_improvement(metrics)
        }
    
    def identify_problematic_patterns(self, threshold=0.5):
        """Identify patterns with low success rates"""
        # Implementation details...
```

## API Endpoints

```
# Store mapping patterns
POST /api/v1/repository/patterns
{
    "device_type": "AHU",
    "point_category": "temperature",
    "source_pattern": ".*temp.*supply.*",
    "target_pattern": "AHU_raw_temp_sa"
}

# Record mapping results
POST /api/v1/repository/results
{
    "pattern_id": "pattern-uuid",
    "bms_point": "AHU_1.SAT",
    "enos_point": "AHU_raw_temp_sa",
    "result": "success",
    "quality_score": 0.85
}

# Get quality metrics
GET /api/v1/analytics/quality?device_type=AHU&time_period=last_30_days

# Export patterns for knowledge transfer
GET /api/v1/repository/patterns/export?device_types=AHU,FCU

# Submit user feedback
POST /api/v1/feedback
{
    "mapping_id": "mapping-uuid",
    "correct": false,
    "suggested_mapping": "AHU_raw_temp_sa",
    "notes": "This is a supply air temperature, not return air"
}
```

## Expected Benefits

1. **Institutional Knowledge**: Preservation of mapping decisions and rationale
2. **Continuous Quality Improvement**: Systematic enhancement based on feedback
3. **Knowledge Transfer**: Ability to apply learnings across different projects
4. **Quality Analytics**: Deep insights into mapping performance and trends
5. **Expert Input Integration**: Structured collection of domain expert knowledge

## Success Metrics

The Mapping Feedback and Persistence System will be successful if it achieves:

1. 30% improvement in knowledge reuse across mapping tasks
2. 25% reduction in repetitive mapping errors
3. 40% increase in visibility of mapping quality metrics
4. 35% improvement in mapping quality over time through pattern refinement
5. 20% reduction in expert review time through better targeting of problematic mappings

## Next Steps

After implementing the basic Feedback and Persistence System, future enhancements should focus on:

1. **Machine Learning Integration**: Apply ML to pattern refinement and quality prediction
2. **Natural Language Feedback**: Enable free-text feedback processing
3. **Expert Collaboration**: Develop tools for collaborative review and annotation
4. **Historical Pattern Analysis**: Deep analysis of pattern evolution over time
5. **Quality Prediction**: Predictive analytics for mapping quality issues