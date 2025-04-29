# Memory Testing Framework

This document describes the comprehensive memory testing framework implemented for the BMS Onboarding Tool.

## Overview

The memory testing framework provides tools for:

1. Monitoring memory usage during processing
2. Visualizing memory consumption over time
3. Detecting memory leaks and inefficiencies
4. Benchmarking memory performance
5. Comparing results between runs
6. Stress testing under extreme conditions

## Usage

The memory testing framework can be accessed through the `test_memory_usage.py` module, which provides a CLI interface:

```bash
# Run standard memory tests
python -m tests.test_memory_usage test

# Run stress tests (high memory load)
python -m tests.test_memory_usage test --stress

# Run specific test
python -m tests.test_memory_usage test --test test_memory_usage_with_large_dataset

# Run memory benchmark with iterations
python -m tests.test_memory_usage benchmark --iterations 3

# Compare memory usage reports
python -m tests.test_memory_usage compare report1.txt report2.txt
```

## Components

### MemoryProfiler

```python
with MemoryProfiler(sample_interval_sec=0.2) as profiler:
    # Mark phases
    profiler.mark_phase_start("data_generation")
    
    # Generate data
    # ...
    
    profiler.mark_phase_end("data_generation")
    
    # Periodically check memory
    profiler.check_memory(force_sample=True)
    
    # Get memory timeline
    memory_timeline = profiler.get_memory_timeline()
    
    # Get phase statistics
    phase_stats = profiler.get_phase_stats()
```

The `MemoryProfiler` is a context manager that monitors memory usage with the following capabilities:
- Sampling memory usage at specified intervals
- Marking processing phases for detailed analysis
- Providing memory timelines for visualization
- Calculating peak memory and memory change

### Memory Visualization

The framework includes visualization tools for memory usage data:

```python
# Create and save memory usage visualization
visualize_memory_timeline(
    memory_timeline,
    "Memory Usage for 500 Points",
    "memory_usage_plot.png"
)
```

Visualizations include:
- Memory usage over time
- Memory change rate
- Phase markers
- Peak memory indicators

### Reporting

The framework generates detailed reports of memory usage:

```
================================================================================
MEMORY USAGE REPORT
================================================================================
Generated: 2023-05-15 14:35:12
Iterations: 3
--------------------------------------------------------------------------------

SUMMARY:
Average processing time: 6.14 seconds
Average memory usage: 0.39 MB
Average processing rate: 47.61 points/second

ITERATION DETAILS:
Iteration 1:
  Processing time: 6.25 seconds
  Memory usage: 0.52 MB
  Points processed: 294
  Processing rate: 47.05 points/second
```

### Benchmarking

The benchmarking functionality allows for consistent performance testing:

```python
# Run benchmark with 3 iterations
benchmark_report = run_memory_benchmark(iterations=3)
```

Benchmarks collect:
- Processing time
- Memory usage
- Processing rate (points/second)
- Statistical aggregates across iterations

### Comparison Tools

The framework includes tools to compare memory usage between runs:

```python
# Compare two memory reports
comparison_report = compare_memory_reports(report1_path, report2_path)
```

Comparisons highlight:
- Differences in processing time
- Memory usage changes
- Performance improvements or regressions
- Phase-by-phase analysis

## Implementation Details

### Memory Sampling

Memory is sampled using the `psutil` library to get accurate RSS (Resident Set Size) measurements.

### Phase Tracking

Processing phases are tracked with timestamps and memory snapshots at phase boundaries.

### Garbage Collection Integration

The framework integrates with Python's garbage collector to:
- Force collection at strategic points
- Detect memory leaks after processing
- Ensure clean memory state between tests

### Test Data Generation

The framework includes optimized test data generation:
- Cached configuration with `lru_cache`
- Batched generation through generators
- Configurable data size and characteristics
- Pattern-based point naming for realistic testing

### Extensibility

The framework is designed to be extensible:
- Modular components for easy enhancement
- Configurable parameters
- Well-documented interfaces
- Clear separation of concerns

## Best Practices

1. **Use Phases**: Mark distinct processing phases to identify memory-intensive operations.
2. **Regular Sampling**: Set appropriate sampling intervals based on processing duration.
3. **Benchmark Iterations**: Use multiple benchmark iterations for statistical reliability.
4. **Controlled Environment**: Run benchmarks in stable environments for consistent results.
5. **Compare Thoughtfully**: When comparing reports, consider system variables that might affect results.

## Future Enhancements

Planned enhancements to the memory testing framework include:
1. Integration with CI/CD pipelines for automated memory testing
2. Memory usage thresholds for automated pass/fail criteria
3. Machine learning for anomaly detection in memory patterns
4. Extended visualization options (3D plots, interactive dashboards)
5. Integration with APM (Application Performance Monitoring) tools