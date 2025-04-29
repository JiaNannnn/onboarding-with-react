# Enhanced BMS-to-EnOS Mapping Implementation

This document explains how to use the enhanced BMS point mapping implementation that has been added to improve the mapping accuracy for various HVAC device types.

## What's New

A new file `enhancedMapping.ts` has been created that contains an improved implementation of the mapping logic. This enhanced implementation:

1. Supports more device types: FCU, AHU, CHILLER, PUMP, CT (Cooling Tower), and CHPL (Chiller Plant)
2. Handles more point naming patterns with higher accuracy
3. Provides more detailed mapping statistics
4. Better handles setpoints vs actual values
5. Properly maps command points
6. Improves confidence calculation
7. **NEW**: Adds mapping quality analysis to identify points needing improvement
8. **NEW**: Provides a framework for second-round mapping improvements

## How to Use the Enhanced Mapping

To use the enhanced mapping implementation:

1. First, import the enhanced mapping function in your `useBMSClient.ts` file:

```typescript
// Add this import at the top of useBMSClient.ts
import { enhancedMapPointsToEnOS, analyzeMappingQuality } from './enhancedMapping';
```

2. Then, replace the existing `mapPointsToEnOS` function with a simpler version that just calls the enhanced implementation:

```typescript
/**
 * Map points to EnOS schema using enhanced local mapping
 * This implementation uses the enhanced mapping logic from enhancedMapping.ts
 * which provides comprehensive pattern matching for all common HVAC device types
 */
const mapPointsToEnOS = useCallback((
  points: BMSPoint[],
  mappingConfig: MappingConfig = {}
): Promise<MapPointsToEnOSResponse> => {
  // Use the enhanced mapping implementation instead
  return enhancedMapPointsToEnOS(points, mappingConfig);
}, []);
```

## Mapping Quality Analysis

The enhanced implementation now includes an `analyzeMappingQuality` function that evaluates mapping results and identifies points that need improvement:

```typescript
// After getting mapping results
const mappingResults = await mapPointsToEnOS(points);
const qualityAnalysis = analyzeMappingQuality(mappingResults);

console.log(`Mapping quality summary:`, qualityAnalysis.qualitySummary);
console.log(`Points needing improvement:`, qualityAnalysis.pointsWithPoorQuality.length);
```

## Second-Round Mapping Improvements

We've added a new API endpoint for improving mapping results in a second round of processing:

```typescript
// First round mapping
const firstRoundResults = await mapPointsToEnOS(points);
const taskId = firstRoundResults.taskId;

// Check quality
const qualityAnalysis = analyzeMappingQuality(firstRoundResults);
if (qualityAnalysis.qualitySummary.poor + qualityAnalysis.qualitySummary.unacceptable > 0) {
  // Second round mapping with improvements
  const improvedResults = await improveMappingResults(
    taskId,                // Original mapping task ID
    'below_fair',          // Filter quality level: 'poor', 'unacceptable', or 'below_fair'
    {                      // Enhanced configuration for second round
      matchingStrategy: 'ai',
      prioritizeFailedPatterns: true,
      includeReflectionData: true
    }
  );
  
  console.log(`Improved mapping results:`, improvedResults);
}
```

## Benefits

The enhanced mapping implementation:

- Improves mapping accuracy by using more detailed pattern matching
- Adds support for additional point types (CO2, humidity, filter status, etc.)
- Better distinguishes between setpoints and actual values
- Handles command points properly
- Provides more detailed statistics about the mapping results
- Adds source information to help with debugging
- **NEW**: Identifies poor quality mappings that need improvement
- **NEW**: Supports iterative improvement of mapping results

## Testing

The enhanced mapping has been tested with sample point data and shows significant improvements in mapping accuracy. It correctly identifies:

- Zone temperature vs supply temperature points
- Setpoint vs actual value points
- Command points vs status points
- Valve positions for different system types (cooling vs heating)
- Fan speed and frequency points
- Multiple types of sensors (temperature, pressure, flow, etc.)

## Future Improvements

In the future, we could further enhance the mapping by:

1. Adding support for more device types (e.g., VAV, Heat Pumps, etc.)
2. Implementing machine learning to automatically improve mapping accuracy over time
3. Adding ability to save and load custom mapping configurations
4. Adding support for custom point naming conventions specific to different BMS vendors
5. Implementing an automated improvement pipeline that handles multiple rounds of refinement
6. Adding a feedback mechanism to learn from manual corrections