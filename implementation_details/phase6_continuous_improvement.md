# Phase 6: Continuous Improvement System

## Overview
This phase establishes a feedback loop system that extracts patterns from successful reasoning chains, automatically updates mapping patterns, and evaluates different reasoning strategies through A/B testing.

## Pattern Extraction System

```python
# app/bms/pattern_extractor.py

import re
import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class PatternExtractor:
    """Extracts and manages patterns from successful reasoning chains."""
    
    def __init__(self, patterns_file: str = "mapping_patterns.json"):
        """Initialize the pattern extractor.
        
        Args:
            patterns_file: Path to patterns file
        """
        self.patterns_file = patterns_file
        self.logger = logging.getLogger("pattern_extractor")
        
        # Load existing patterns
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load existing patterns from file.
        
        Returns:
            Dictionary mapping device types to patterns
        """
        try:
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def extract_patterns_from_results(
        self,
        results: List[Dict[str, Any]],
        min_confidence: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Extract patterns from successful mapping results.
        
        Args:
            results: List of mapping results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of extracted patterns
        """
        extracted_patterns = []
        
        # Filter for high-confidence successful mappings
        successful_mappings = [
            r for r in results
            if r["mapping"]["enosPoint"] != "unknown" 
            and r["mapping"]["confidence"] >= min_confidence
        ]
        
        for result in successful_mappings:
            original = result.get("original", {})
            point_name = original.get("pointName", "")
            device_type = original.get("deviceType", "unknown")
            enos_point = result["mapping"]["enosPoint"]
            
            # Skip if no point name or enos point
            if not point_name or not enos_point:
                continue
            
            # Create pattern template from point name
            pattern_template = self._create_pattern_template(point_name)
            
            # Create new pattern
            new_pattern = {
                "pattern": pattern_template,
                "enos_point": enos_point,
                "confidence": result["mapping"]["confidence"],
                "created_at": datetime.now().isoformat(),
                "source": "auto_extracted",
                "examples": [point_name]
            }
            
            # Add to extracted patterns
            extracted_patterns.append({
                "device_type": device_type,
                "pattern": new_pattern
            })
        
        return extracted_patterns
    
    def _create_pattern_template(self, point_name: str) -> str:
        """Create a regex pattern template from a point name.
        
        Args:
            point_name: Point name
            
        Returns:
            Regex pattern template
        """
        # Replace digits with number placeholders
        pattern = re.sub(r'\d+', r'\\d+', point_name)
        
        # Escape dots and other special characters
        pattern = re.sub(r'\.', r'\\.', pattern)
        
        # Add anchors
        pattern = f"^{pattern}$"
        
        return pattern
    
    def update_patterns(
        self,
        extracted_patterns: List[Dict[str, Any]],
        min_similarity: float = 0.8
    ) -> Dict[str, Any]:
        """Update patterns file with extracted patterns.
        
        Args:
            extracted_patterns: List of extracted patterns
            min_similarity: Minimum similarity threshold for merging
            
        Returns:
            Dictionary with update statistics
        """
        # Statistics
        stats = {
            "new_patterns": 0,
            "merged_patterns": 0,
            "unchanged": 0
        }
        
        # Group by device type
        by_device_type = {}
        for item in extracted_patterns:
            device_type = item["device_type"]
            if device_type not in by_device_type:
                by_device_type[device_type] = []
            by_device_type[device_type].append(item["pattern"])
        
        # Process each device type
        for device_type, new_patterns in by_device_type.items():
            # Create device type in patterns if not exists
            if device_type not in self.patterns:
                self.patterns[device_type] = []
            
            # Process each new pattern
            for new_pattern in new_patterns:
                # Check if similar pattern exists
                similar_pattern = self._find_similar_pattern(
                    new_pattern,
                    self.patterns[device_type],
                    min_similarity
                )
                
                if similar_pattern:
                    # Merge with existing pattern
                    self._merge_patterns(similar_pattern, new_pattern)
                    stats["merged_patterns"] += 1
                else:
                    # Add as new pattern
                    self.patterns[device_type].append(new_pattern)
                    stats["new_patterns"] += 1
        
        # Save updated patterns
        self._save_patterns()
        
        return stats
    
    def _find_similar_pattern(
        self,
        new_pattern: Dict[str, Any],
        existing_patterns: List[Dict[str, Any]],
        min_similarity: float
    ) -> Optional[Dict[str, Any]]:
        """Find similar pattern in existing patterns.
        
        Args:
            new_pattern: New pattern
            existing_patterns: List of existing patterns
            min_similarity: Minimum similarity threshold
            
        Returns:
            Similar pattern or None
        """
        for pattern in existing_patterns:
            # Same EnOS point
            if pattern["enos_point"] == new_pattern["enos_point"]:
                # Check pattern similarity
                similarity = self._calculate_pattern_similarity(
                    pattern["pattern"],
                    new_pattern["pattern"]
                )
                
                if similarity >= min_similarity:
                    return pattern
        
        return None
    
    def _calculate_pattern_similarity(
        self,
        pattern1: str,
        pattern2: str
    ) -> float:
        """Calculate similarity between two patterns.
        
        Args:
            pattern1: First pattern
            pattern2: Second pattern
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple similarity metric based on character overlap
        # In a real implementation, this would be more sophisticated
        chars1 = set(pattern1)
        chars2 = set(pattern2)
        
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_patterns(
        self,
        existing_pattern: Dict[str, Any],
        new_pattern: Dict[str, Any]
    ):
        """Merge new pattern into existing pattern.
        
        Args:
            existing_pattern: Existing pattern
            new_pattern: New pattern
        """
        # Update confidence (weighted average)
        existing_examples = len(existing_pattern.get("examples", []))
        new_examples = len(new_pattern.get("examples", []))
        total_examples = existing_examples + new_examples
        
        existing_pattern["confidence"] = (
            existing_pattern["confidence"] * existing_examples +
            new_pattern["confidence"] * new_examples
        ) / total_examples
        
        # Add new examples
        if "examples" not in existing_pattern:
            existing_pattern["examples"] = []
        
        existing_pattern["examples"].extend(new_pattern.get("examples", []))
        
        # Update last modified
        existing_pattern["last_modified"] = datetime.now().isoformat()
    
    def _save_patterns(self):
        """Save patterns to file."""
        # Create backup
        backup_file = f"{self.patterns_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            with open(self.patterns_file, 'r') as src:
                with open(backup_file, 'w') as dst:
                    dst.write(src.read())
        except FileNotFoundError:
            pass
        
        # Save updated patterns
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
            
        self.logger.info(f"Updated patterns saved to {self.patterns_file}")
```

## A/B Testing Framework

```python
# app/bms/ab_testing.py

import random
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class ABTestingFramework:
    """Framework for A/B testing different reasoning strategies."""
    
    def __init__(self, results_file: str = "ab_testing_results.json"):
        """Initialize the A/B testing framework.
        
        Args:
            results_file: Path to results file
        """
        self.results_file = results_file
        self.logger = logging.getLogger("ab_testing")
        
        # Load existing results
        self.results = self._load_results()
        
        # Test variants
        self.variants = {
            "baseline": {
                "description": "Standard mapping without reasoning",
                "weight": 0.2
            },
            "cot_only": {
                "description": "Chain of Thought reasoning only",
                "weight": 0.2
            },
            "reflection_only": {
                "description": "Reflection only for failed mappings",
                "weight": 0.2
            },
            "integrated": {
                "description": "Integrated CoT and reflection pipeline",
                "weight": 0.4
            }
        }
    
    def _load_results(self) -> Dict[str, Any]:
        """Load existing results from file.
        
        Returns:
            Dictionary with test results
        """
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "tests": [],
                "stats": {}
            }
    
    def select_variant(self, session_id: str) -> str:
        """Select a test variant for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Selected variant name
        """
        # Check if session already has a variant
        for test in self.results["tests"]:
            if test["session_id"] == session_id:
                return test["variant"]
        
        # Select variant based on weights
        weights = [v["weight"] for v in self.variants.values()]
        variant_names = list(self.variants.keys())
        
        selected = random.choices(variant_names, weights=weights, k=1)[0]
        
        # Record new test
        self.results["tests"].append({
            "session_id": session_id,
            "variant": selected,
            "start_time": datetime.now().isoformat(),
            "points_processed": 0,
            "successful_mappings": 0,
            "average_confidence": 0.0,
            "completed": False
        })
        
        # Save results
        self._save_results()
        
        return selected
    
    def record_test_results(
        self,
        session_id: str,
        points_processed: int,
        successful_mappings: int,
        average_confidence: float
    ):
        """Record test results for a session.
        
        Args:
            session_id: Session ID
            points_processed: Number of points processed
            successful_mappings: Number of successful mappings
            average_confidence: Average confidence score
        """
        # Find test record
        for test in self.results["tests"]:
            if test["session_id"] == session_id:
                test["points_processed"] = points_processed
                test["successful_mappings"] = successful_mappings
                test["average_confidence"] = average_confidence
                test["completed"] = True
                test["end_time"] = datetime.now().isoformat()
                break
        
        # Update variant stats
        self._update_variant_stats()
        
        # Save results
        self._save_results()
    
    def _update_variant_stats(self):
        """Update variant statistics."""
        stats = {}
        
        # Group tests by variant
        for variant in self.variants.keys():
            variant_tests = [
                t for t in self.results["tests"]
                if t["variant"] == variant and t["completed"]
            ]
            
            # Skip if no tests
            if not variant_tests:
                continue
            
            # Calculate statistics
            total_points = sum(t["points_processed"] for t in variant_tests)
            total_success = sum(t["successful_mappings"] for t in variant_tests)
            avg_confidence = sum(t["average_confidence"] * t["points_processed"] for t in variant_tests) / total_points if total_points > 0 else 0.0
            
            stats[variant] = {
                "test_count": len(variant_tests),
                "total_points": total_points,
                "success_rate": total_success / total_points if total_points > 0 else 0.0,
                "average_confidence": avg_confidence
            }
        
        self.results["stats"] = stats
    
    def _save_results(self):
        """Save results to file."""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
```

## Scheduled Effectiveness Reports

```python
# app/bms/reporting.py

import json
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class EffectivenessReporter:
    """Generates reports on reasoning effectiveness."""
    
    def __init__(
        self,
        reasoning_logs_dir: str = "logs/reasoning",
        report_dir: str = "reports"
    ):
        """Initialize the effectiveness reporter.
        
        Args:
            reasoning_logs_dir: Directory with reasoning logs
            report_dir: Directory for reports
        """
        self.reasoning_logs_dir = reasoning_logs_dir
        self.report_dir = report_dir
        self.logger = logging.getLogger("effectiveness_reporter")
        
        # Create report directory if not exists
        os.makedirs(report_dir, exist_ok=True)
    
    def generate_weekly_report(self):
        """Generate weekly effectiveness report."""
        # Get current date
        now = datetime.now()
        
        # Start and end dates for report
        end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=7)
        
        # Generate report
        report = self._generate_report(start_date, end_date)
        
        # Save report
        report_file = f"{self.report_dir}/weekly_report_{end_date.strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate visualizations
        self._generate_visualizations(report, report_file.replace('.json', ''))
        
        self.logger.info(f"Weekly report generated: {report_file}")
        
        return report
    
    def _generate_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate report for date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Report data
        """
        # Initialize report
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "overall": {
                "total_points": 0,
                "successful_mappings": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
                "reflection_count": 0,
                "reflection_success_rate": 0.0
            },
            "by_device_type": {},
            "by_reasoning_type": {},
            "error_analysis": {
                "common_errors": [],
                "error_counts": {}
            }
        }
        
        # Get reasoning logs
        reasoning_logs = self._load_reasoning_logs(start_date, end_date)
        
        # Process logs
        self._process_logs(reasoning_logs, report)
        
        return report
    
    def _load_reasoning_logs(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Load reasoning logs for date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of reasoning logs
        """
        logs = []
        
        # Chain logs
        chain_dir = f"{self.reasoning_logs_dir}/chains"
        if os.path.exists(chain_dir):
            for filename in os.listdir(chain_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = f"{chain_dir}/{filename}"
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        
                        # Check timestamp
                        timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                        if start_date <= timestamp < end_date:
                            logs.append(data)
                except (json.JSONDecodeError, ValueError, FileNotFoundError):
                    self.logger.warning(f"Error loading log file: {filepath}")
        
        # Reflection logs
        reflection_dir = f"{self.reasoning_logs_dir}/reflections"
        if os.path.exists(reflection_dir):
            for filename in os.listdir(reflection_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = f"{reflection_dir}/{filename}"
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        
                        # Check timestamp
                        timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                        if start_date <= timestamp < end_date:
                            logs.append(data)
                except (json.JSONDecodeError, ValueError, FileNotFoundError):
                    self.logger.warning(f"Error loading log file: {filepath}")
        
        return logs
    
    def _process_logs(
        self,
        logs: List[Dict[str, Any]],
        report: Dict[str, Any]
    ):
        """Process logs and update report.
        
        Args:
            logs: List of logs
            report: Report to update
        """
        # Extract relevant data
        points_data = []
        
        for log in logs:
            result = log.get("result", {})
            original = result.get("original", {})
            mapping = result.get("mapping", {})
            
            # Skip if no mapping
            if not mapping:
                continue
            
            # Create point data
            point_data = {
                "point_id": mapping.get("pointId", "unknown"),
                "device_type": original.get("deviceType", "unknown"),
                "enos_point": mapping.get("enosPoint", "unknown"),
                "confidence": mapping.get("confidence", 0.0),
                "success": mapping.get("enosPoint", "unknown") != "unknown",
                "has_reflection": "reflection" in result,
                "reflection_success": False
            }
            
            # Check reflection success
            if "reflection" in result:
                report["overall"]["reflection_count"] += 1
                
                reflection = result["reflection"]
                if reflection.get("success", False):
                    point_data["reflection_success"] = True
                    report["overall"]["reflection_success_rate"] += 1
            
            points_data.append(point_data)
        
        # Update overall stats
        total_points = len(points_data)
        report["overall"]["total_points"] = total_points
        
        if total_points > 0:
            successful = sum(1 for p in points_data if p["success"])
            report["overall"]["successful_mappings"] = successful
            report["overall"]["success_rate"] = successful / total_points
            
            avg_confidence = sum(p["confidence"] for p in points_data) / total_points
            report["overall"]["average_confidence"] = avg_confidence
            
            if report["overall"]["reflection_count"] > 0:
                report["overall"]["reflection_success_rate"] /= report["overall"]["reflection_count"]
        
        # Group by device type
        device_types = {}
        for point in points_data:
            device_type = point["device_type"]
            if device_type not in device_types:
                device_types[device_type] = []
            device_types[device_type].append(point)
        
        # Calculate device type stats
        for device_type, device_points in device_types.items():
            count = len(device_points)
            successful = sum(1 for p in device_points if p["success"])
            
            report["by_device_type"][device_type] = {
                "count": count,
                "success_count": successful,
                "success_rate": successful / count if count > 0 else 0.0,
                "average_confidence": sum(p["confidence"] for p in device_points) / count if count > 0 else 0.0
            }
        
        # Error analysis
        errors = [p for p in points_data if not p["success"]]
        error_count = len(errors)
        
        # Count errors by device type
        error_by_device = {}
        for error in errors:
            device_type = error["device_type"]
            if device_type not in error_by_device:
                error_by_device[device_type] = 0
            error_by_device[device_type] += 1
        
        # Add to report
        report["error_analysis"]["error_counts"] = {
            device_type: {
                "count": count,
                "percentage": count / error_count if error_count > 0 else 0.0
            }
            for device_type, count in error_by_device.items()
        }
    
    def _generate_visualizations(
        self,
        report: Dict[str, Any],
        base_filename: str
    ):
        """Generate visualizations for report.
        
        Args:
            report: Report data
            base_filename: Base filename for visualizations
        """
        # Success rate by device type
        self._plot_success_by_device_type(report, f"{base_filename}_success_by_device.png")
        
        # Confidence distribution
        self._plot_confidence_distribution(report, f"{base_filename}_confidence_distribution.png")
        
        # Reflection effectiveness
        self._plot_reflection_effectiveness(report, f"{base_filename}_reflection_effectiveness.png")
    
    def _plot_success_by_device_type(
        self,
        report: Dict[str, Any],
        filename: str
    ):
        """Plot success rate by device type.
        
        Args:
            report: Report data
            filename: Output filename
        """
        device_data = report["by_device_type"]
        
        if not device_data:
            return
        
        # Create dataframe
        data = {
            "Device Type": [],
            "Success Rate": [],
            "Count": []
        }
        
        for device_type, stats in device_data.items():
            data["Device Type"].append(device_type)
            data["Success Rate"].append(stats["success_rate"] * 100)
            data["Count"].append(stats["count"])
        
        df = pd.DataFrame(data)
        
        # Create plot
        plt.figure(figsize=(10, 6))
        
        ax = df.plot.bar(x="Device Type", y="Success Rate", color="skyblue")
        
        # Customize plot
        plt.title("Mapping Success Rate by Device Type")
        plt.xlabel("Device Type")
        plt.ylabel("Success Rate (%)")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        
        # Add count labels
        for i, count in enumerate(df["Count"]):
            plt.text(i, 5, f"n={count}", ha="center")
        
        # Save plot
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
```

## Integration with Main Application

```python
# app/bms/routes.py

@router.get("/patterns/suggest-updates")
async def suggest_pattern_updates(
    min_confidence: float = 0.8,
    request: Request
):
    """Suggest updates to mapping patterns.
    
    Args:
        min_confidence: Minimum confidence threshold
        
    Returns:
        Suggested pattern updates
    """
    # Get recent mapping results
    results = request.app.state.recent_results
    
    # Initialize pattern extractor
    from app.bms.pattern_extractor import PatternExtractor
    extractor = PatternExtractor()
    
    # Extract patterns
    extracted_patterns = extractor.extract_patterns_from_results(
        results, min_confidence=min_confidence
    )
    
    return {
        "extracted_patterns": extracted_patterns,
        "count": len(extracted_patterns)
    }

@router.post("/patterns/apply-updates")
async def apply_pattern_updates(
    extracted_patterns: List[Dict[str, Any]],
    min_similarity: float = 0.8,
    request: Request
):
    """Apply updates to mapping patterns.
    
    Args:
        extracted_patterns: List of extracted patterns
        min_similarity: Minimum similarity threshold
        
    Returns:
        Update statistics
    """
    # Initialize pattern extractor
    from app.bms.pattern_extractor import PatternExtractor
    extractor = PatternExtractor()
    
    # Update patterns
    stats = extractor.update_patterns(
        extracted_patterns, min_similarity=min_similarity
    )
    
    # Reload mapper patterns
    request.app.state.mapper.load_mapping_patterns()
    
    return {
        "status": "success",
        "stats": stats
    }

@router.get("/reports/effectiveness")
async def get_effectiveness_report(
    days: int = 7,
    request: Request
):
    """Get effectiveness report.
    
    Args:
        days: Number of days to include
        
    Returns:
        Effectiveness report
    """
    # Initialize reporter
    from app.bms.reporting import EffectivenessReporter
    reporter = EffectivenessReporter()
    
    # Get current date
    now = datetime.now()
    
    # Start and end dates
    end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days)
    
    # Generate report
    report = reporter._generate_report(start_date, end_date)
    
    return report
``` 