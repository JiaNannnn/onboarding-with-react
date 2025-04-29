# Memory Testing CI Integration

This document describes how memory testing is integrated into the CI/CD pipeline for the BMS Onboarding Tool. Memory testing helps ensure that the application maintains good performance and doesn't introduce memory leaks or excessive memory usage.

## Overview

The memory testing framework consists of several components:

1. **Memory profiling tools** - Classes and utilities for measuring and recording memory usage
2. **Test cases** - Unit and integration tests that profile memory usage during execution
3. **Visualization tools** - Scripts to generate charts and reports from memory data
4. **GitHub Actions workflow** - Automated pipeline that runs memory tests on each PR and scheduled intervals

## How It Works

### Memory Profiler

The `MemoryProfiler` class in `tests/test_memory_usage.py` provides a context manager that can track memory usage throughout a code block's execution. It supports:

- Tracking peak memory usage
- Recording memory usage timelines
- Marking processing phases for granular analysis
- Generating memory usage reports

Example usage:

```python
from tests.test_memory_usage import MemoryProfiler

with MemoryProfiler() as profiler:
    # Mark the start of a phase
    profiler.mark_phase_start("data_loading")
    
    # Load data
    data = load_large_dataset()
    
    # Mark the end of the phase
    profiler.mark_phase_end("data_loading")
    
    # Mark the start of another phase
    profiler.mark_phase_start("processing")
    
    # Process data
    result = process_data(data)
    
    # Mark the end of the phase
    profiler.mark_phase_end("processing")
    
    # Get memory statistics
    peak_memory = profiler.peak_memory
    memory_timeline = profiler.get_memory_timeline()
    phase_stats = profiler.get_phase_stats()
```

### Test Suite

The memory test suite includes:

1. **Standard memory tests** (`test_memory_usage.py`) - Tests that measure memory usage with various dataset sizes
2. **Batch processing tests** (`test_batch_processing_memory.py`) - Tests focused on batch processing efficiency
3. **Agent component tests** - Tests for each agent component that include memory profiling
   - `test_grouping_agent.py`
   - `test_tagging_agent.py`
   - `test_mapping_agent.py`
4. **Integration tests** (`test_agent_integration.py`) - Tests that measure memory usage across the full pipeline

### Memory Benchmarking

The framework includes benchmark functionality that:

1. Runs multiple iterations to get statistically significant results
2. Records memory usage, processing time, and throughput metrics
3. Compares results against previous benchmarks to detect regressions
4. Generates reports and visualizations for easier analysis

To run a benchmark:

```bash
python -m tests.test_memory_usage benchmark --iterations=3
```

### CI/CD Integration

The memory testing workflow (`.github/workflows/memory-testing.yml`) is configured to:

1. Run on pull requests to main/develop branches
2. Run on direct pushes to main/develop branches
3. Run weekly scheduled tests (Sunday at midnight)

The workflow:

1. Sets up the Python environment
2. Installs dependencies including `psutil`, `matplotlib`, and `seaborn`
3. Runs the memory test suite
4. Runs benchmarks to generate performance metrics
5. Generates a memory usage dashboard
6. Uploads test results as artifacts
7. Analyzes memory trends and flags regressions
8. Reports significant changes in memory usage

## Performance Dashboard

The `scripts/track_performance.py` script generates a performance dashboard that includes:

1. Memory usage trends over time
2. Processing time trends
3. Processing rate (throughput) trends
4. Tables showing significant performance changes
5. Benchmark history

To generate the dashboard manually:

```bash
python scripts/track_performance.py --reports-dir=test_output --output-dir=performance_dashboard
```

## Thresholds and Alerts

The memory testing framework includes configurable thresholds for alerting:

1. **Memory regression threshold** - Default 15% increase triggers a warning in CI
2. **Maximum allowed memory usage** - Each test has a specific threshold that fails the test if exceeded
3. **Minimum processing rate** - Performance tests ensure throughput remains above minimum levels

## Test Output and Artifacts

The CI workflow saves several artifacts:

1. **Memory timeline plots** - PNG files showing memory usage over time
2. **Benchmark reports** - Text files with detailed benchmark results
3. **Performance dashboard** - HTML file with visualizations and metrics
4. **Comparison reports** - Analysis of changes compared to previous runs
5. **Performance history** - JSON file with historical benchmark data

## Adding New Memory Tests

To add a new memory test:

1. Import the `MemoryProfiler` from `tests/test_memory_usage.py`
2. Create a test method that uses the profiler to track memory usage
3. Add memory assertions to verify memory usage is within acceptable limits

Example:

```python
def test_new_memory_feature(self):
    """Test memory usage for a new feature."""
    with MemoryProfiler() as profiler:
        # Mark the start of processing
        profiler.mark_phase_start("processing")
        
        # Run the code under test
        result = my_feature_function()
        
        # Mark the end of processing
        profiler.mark_phase_end("processing")
        
        # Get memory usage and add to test result
        self.memory_profiler = profiler
        
        # Verify memory usage is within limits
        final_memory = profiler.memory_usage
        self.assertLessEqual(
            final_memory, 
            100,  # MB threshold
            f"Memory usage ({final_memory:.2f} MB) exceeds threshold (100 MB)"
        )
```

## Configuring Memory Test Thresholds

Memory thresholds can be configured in several places:

1. **Individual tests** - Each test can specify its own memory threshold
2. **CI workflow** - The workflow file can specify global thresholds
3. **Performance tracking** - The tracking script accepts a `--threshold` parameter

## Best Practices

1. Run memory tests locally before submitting PRs
2. Review memory usage trends regularly to identify gradual increases
3. Address memory regressions promptly
4. Use batch processing for large datasets to control memory usage
5. Implement proper garbage collection in long-running tests

## Troubleshooting

### Common Issues

1. **Test timeouts** - Set appropriate timeouts for large dataset tests
2. **Inconsistent results** - Run multiple iterations for more reliable benchmarks
3. **Memory visualization issues** - Ensure matplotlib and seaborn are installed
4. **False positives** - Check if threshold is too strict for the task

### Debugging Memory Issues

1. Use the phase tracking to identify which component is using excessive memory
2. Compare memory timelines before and after changes
3. Check for objects not being properly garbage collected
4. Look for memory spikes in the timeline visualization

## References

- [Python psutil documentation](https://psutil.readthedocs.io/en/latest/)
- [Understanding memory profiling](https://pythonspeed.com/articles/python-memory-profiling/)
- [GitHub Actions documentation](https://docs.github.com/en/actions)