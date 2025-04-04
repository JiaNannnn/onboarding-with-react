# Reflection Layer API Documentation

This document describes the API endpoints for the Reflection Layer, which provides advanced capabilities for mapping analysis, pattern recognition, and quality assessment.

## Overview

The Reflection Layer API enables:

1. Analyzing patterns in mapping data
2. Assessing mapping quality across multiple dimensions
3. Suggesting optimal mappings based on historical data
4. Extracting insights from mapping batches
5. Retrieving reflection system statistics

## API Endpoints

### Get Reflection Statistics

Retrieves statistics about the reflection system, including pattern counts, quality distributions, and learning metrics.

```
GET /api/bms/reflection/stats
```

**Response:**

```json
{
  "success": true,
  "stats": {
    "total_reflections": 128,
    "quality_distribution": {
      "excellent": 45,
      "good": 63,
      "fair": 12,
      "poor": 8,
      "unacceptable": 0
    },
    "strategy_success_rates": {
      "direct_pattern": 0.92,
      "semantic_inference": 0.85,
      "device_context": 0.78
    },
    "memory_stats": {
      "total_patterns": 87,
      "device_types": {
        "AHU": 42,
        "FCU": 15,
        "CHILLER": 12,
        "PUMP": 18
      },
      "avg_quality_score": 0.78,
      "cache_stats": {
        "hits": 65,
        "misses": 22,
        "hit_rate": 0.75
      }
    }
  }
}
```

### Analyze Mappings

Analyzes a batch of mappings to extract patterns, identify pattern families, calculate quality statistics, and generate insights.

```
POST /api/bms/reflection/analyze
```

**Request Body:**

```json
{
  "mappings": [
    {
      "original": {
        "pointName": "AHU-1.ReturnAirTemp",
        "deviceType": "AHU",
        "deviceId": "AHU-1",
        "pointType": "AI",
        "unit": "degF"
      },
      "mapping": {
        "pointId": "AHU-1:1",
        "enosPoint": "AHU_raw_temp_rat",
        "status": "mapped"
      },
      "reflection": {
        "quality_score": 0.85,
        "reason": "semantic_match",
        "explanation": "Semantic match based on temperature keywords",
        "success": true
      }
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "analysis": {
    "patterns": {
      "common_prefixes": [["AHU", 42], ["FCU", 15], ["CT", 8]],
      "common_suffixes": [["Temp", 36], ["Status", 22], ["Pressure", 14]],
      "device_patterns": {
        "AHU": {
          "patterns": {
            "ngrams": {
              "all": [["return_air_temp", 18], ["supply_air_temp", 15], ["fan_status", 9]]
            },
            "point_count": 42
          }
        }
      }
    },
    "pattern_families": {
      "AHU": {
        "target_groups": {
          "temp_rat": [
            {
              "source": "AHU-1.ReturnAirTemp",
              "target": "AHU_raw_temp_rat",
              "source_pattern": "returnairtemp",
              "target_pattern": "temp_rat"
            }
          ]
        }
      }
    },
    "quality_stats": {
      "counts": {
        "excellent": 45,
        "good": 63,
        "fair": 12,
        "poor": 8,
        "unacceptable": 0
      },
      "percentages": {
        "excellent": 35.2,
        "good": 49.2,
        "fair": 9.4,
        "poor": 6.2,
        "unacceptable": 0
      }
    },
    "insights": [
      "Common point name prefixes: AHU, FCU, CT",
      "AHU devices have the highest mapping quality.",
      "Most effective strategies: Direct Pattern Matching, Semantic Inference"
    ]
  }
}
```

### Suggest Mapping

Suggests an optimal mapping for a given point based on historical data and pattern matching.

```
POST /api/bms/reflection/suggest
```

**Request Body:**

```json
{
  "point": {
    "pointName": "AHU-2.ReturnAirTemp",
    "deviceType": "AHU",
    "deviceId": "AHU-2",
    "pointType": "AI",
    "unit": "degF"
  }
}
```

**Response:**

```json
{
  "success": true,
  "suggestion": {
    "success": true,
    "suggested_mapping": "AHU_raw_temp_rat",
    "confidence": 0.92,
    "reason": "Pattern match: returnairtemp → temp_rat",
    "strategy": "direct_pattern",
    "source": "memory"
  }
}
```

### Extract Patterns

Extracts patterns from a list of points without requiring mapping data.

```
POST /api/bms/reflection/patterns
```

**Request Body:**

```json
{
  "points": [
    {
      "pointName": "AHU-1.ReturnAirTemp",
      "deviceType": "AHU",
      "deviceId": "AHU-1",
      "pointType": "AI",
      "unit": "degF"
    },
    {
      "pointName": "AHU-1.SupplyAirTemp",
      "deviceType": "AHU",
      "deviceId": "AHU-1",
      "pointType": "AI",
      "unit": "degF"
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "patterns": {
    "common_prefixes": [["AHU", 2]],
    "common_suffixes": [["Temp", 2]],
    "common_words": [["Air", 2], ["Temp", 2]],
    "device_patterns": {
      "AHU": {
        "points": ["AHU-1.ReturnAirTemp", "AHU-1.SupplyAirTemp"],
        "patterns": {
          "ngrams": {
            "all": [["air_temp", 2]],
            "threshold": 2,
            "total_unique": 3
          }
        }
      }
    }
  }
}
```

### Assess Mapping Quality

Assesses the quality of a mapping across multiple dimensions.

```
POST /api/bms/reflection/quality
```

**Request Body:**

```json
{
  "mapping": {
    "original": {
      "pointName": "AHU-1.ReturnAirTemp",
      "deviceType": "AHU",
      "deviceId": "AHU-1",
      "pointType": "AI",
      "unit": "degF"
    },
    "mapping": {
      "pointId": "AHU-1:1",
      "enosPoint": "AHU_raw_temp_rat",
      "status": "mapped"
    }
  },
  "reference_mappings": []
}
```

**Response:**

```json
{
  "success": true,
  "quality_assessment": {
    "dimension_scores": {
      "semantic_correctness": 0.9,
      "convention_adherence": 1.0,
      "consistency": 0.8,
      "device_context": 0.9,
      "schema_completeness": 1.0
    },
    "overall_score": 0.92,
    "quality_level": "excellent",
    "suggestions": []
  }
}
```

## Using the API from Frontend

### Example: Analyzing Mapping Results

```typescript
// Function to analyze mapping results
async function analyzeMappingResults(mappings: MappingResult[]): Promise<AnalysisResult> {
  try {
    const response = await fetch('/api/bms/reflection/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ mappings })
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.analysis;
    } else {
      throw new Error(data.error || 'Analysis failed');
    }
  } catch (error) {
    console.error('Error analyzing mappings:', error);
    throw error;
  }
}

// Example usage
const analysis = await analyzeMappingResults(mappingResults);
console.log('Mapping insights:', analysis.insights);
```

### Example: Suggesting Mappings

```typescript
// Function to get mapping suggestion
async function getSuggestion(point: BmsPoint): Promise<SuggestionResult> {
  try {
    const response = await fetch('/api/bms/reflection/suggest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ point })
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.suggestion;
    } else {
      throw new Error(data.error || 'Suggestion failed');
    }
  } catch (error) {
    console.error('Error getting suggestion:', error);
    throw error;
  }
}

// Example usage
const suggestion = await getSuggestion({
  pointName: 'AHU-2.ReturnAirTemp',
  deviceType: 'AHU',
  deviceId: 'AHU-2'
});

if (suggestion.suggested_mapping) {
  console.log(`Suggested mapping: ${suggestion.suggested_mapping} (confidence: ${suggestion.confidence})`);
} else {
  console.log('No confident suggestion available');
}
```

## Error Handling

All endpoints return a `success` property indicating whether the operation was successful. In case of an error, an `error` property contains the error message:

```json
{
  "success": false,
  "error": "Invalid or missing point data"
}
```

The HTTP status code will also indicate the type of error:
- 400: Bad Request (missing or invalid parameters)
- 500: Server Error (internal processing error)

## Rate Limiting

The reflection layer API endpoints may perform intensive computational operations. As a result, they have rate limiting applied:

- Maximum 60 requests per minute for statistics and suggestion endpoints
- Maximum 20 requests per minute for analysis and pattern extraction endpoints

Exceeding these limits will result in a 429 (Too Many Requests) response.