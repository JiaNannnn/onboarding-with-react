# Phase 1: Enhanced Reasoning Architecture

This README provides instructions for testing the Phase 1 implementation of the Enhanced Reasoning Architecture.

## Overview

Phase 1 implements the following features:
- Chain of Thought (CoT) reasoning for point mapping
- Reflection on failed mappings
- Batch processing for large datasets
- Progress tracking

## New Endpoints

The following endpoints have been added:

1. `/bms/points/map-with-reasoning` - Maps BMS points to EnOS points with reasoning capabilities
2. `/bms/points/reflect-and-remap/{point_id}` - Reflects on a failed mapping and attempts to improve it
3. `/bms/points/reflect-and-remap-batch` - Batch version of reflection and remapping
4. `/bms/progress/{operation_id}` - Tracks progress of long-running operations
5. `/bms/progress-dashboard` - Serves the progress tracking dashboard UI

## New Components

The implementation adds the following components:

1. `ReasoningLogger` - Logs reasoning chains and reflection data
2. `ReasoningEngine` - Generates reasoning chains and reflections
3. Progress tracking system for monitoring long-running operations
4. Progress tracking dashboard UI for visualizing operation progress

## Testing

### Prerequisites

1. Make sure you have Python 3.8+ installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure the server is running:
   ```
   python run.py
   ```

### Running Tests

We provide a test script (`test_phase1.py`) to verify the implementation. The script supports three test modes:

1. **Reasoning test** - Tests the mapping with reasoning endpoint
   ```
   python test_phase1.py --test reasoning
   ```

2. **Reflection test** - Tests the reflection and remapping endpoint
   ```
   python test_phase1.py --test reflection
   ```

3. **Batch test** - Tests the batch reflection and remapping endpoint
   ```
   python test_phase1.py --test batch
   ```

By default, the script tests with 5 points. You can change this with the `--points` parameter:

```
python test_phase1.py --test reasoning --points 10
```

To test against a different server, use the `--server` parameter:

```
python test_phase1.py --server http://localhost:8000
```

### Test Sequence

For a complete test, run the following commands in sequence:

1. First, test the reasoning endpoint:
   ```
   python test_phase1.py --test reasoning
   ```

2. Next, test the reflection endpoint (uses results from step 1):
   ```
   python test_phase1.py --test reflection
   ```

3. Finally, test the batch endpoint (also uses results from step 1):
   ```
   python test_phase1.py --test batch
   ```

### Progress Dashboard

The implementation includes a web-based progress tracking dashboard that allows you to monitor operations in real-time. To access the dashboard:

1. Start the server:
   ```
   python run.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000/bms/progress-dashboard
   ```

3. Enter an operation ID in the dashboard to monitor its progress. When running the test script, look for the operation ID in the console output.

![Progress Dashboard](dashboard_screenshot.png)

The dashboard provides:
- Real-time progress updates
- Visual progress bar and chart
- Operation details and status
- Time elapsed and completion estimates

### Examining Results

The test script saves the results to JSON files:
- `test_reasoning_results.json` - Results from the reasoning test
- `test_reflection_results.json` - Results from the reflection test
- `test_batch_results.json` - Results from the batch test

Additionally, reasoning chains and reflection data are logged to the `logs/reasoning` directory:
- `chains/` - Contains reasoning chains for each point
- `reflections/` - Contains reflection data for remapped points
- `progress/` - Contains progress tracking data for each operation

## Expected Results

When running the tests, you should observe the following:

1. **Reasoning test**: 
   - Each point should have a reasoning chain that explains the mapping logic
   - Most points should map successfully to EnOS points

2. **Reflection test**:
   - For points that failed to map initially, the reflection should identify potential issues
   - Some failed mappings should be successfully remapped

3. **Batch test**:
   - Should process points in batches with progress tracking
   - Results should be similar to individual reflection tests

## Troubleshooting

If you encounter issues:

1. Check the server logs for errors
2. Verify that the server is running and accessible
3. Ensure the OpenAI API key is properly configured
4. Check the reasoning logs for detailed information about each operation

## Next Steps

After verifying Phase 1, proceed to Phase 2 implementation which will enhance the Chain of Thought grouping with LLM-based reasoning. 