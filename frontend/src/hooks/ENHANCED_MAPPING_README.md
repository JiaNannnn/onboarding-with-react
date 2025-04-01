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

## How to Use the Enhanced Mapping

To use the enhanced mapping implementation:

1. First, import the enhanced mapping function in your `useBMSClient.ts` file:

```typescript
// Add this import at the top of useBMSClient.ts
import { enhancedMapPointsToEnOS } from './enhancedMapping';
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

## Benefits

The enhanced mapping implementation:

- Improves mapping accuracy by using more detailed pattern matching
- Adds support for additional point types (CO2, humidity, filter status, etc.)
- Better distinguishes between setpoints and actual values
- Handles command points properly
- Provides more detailed statistics about the mapping results
- Adds source information to help with debugging

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