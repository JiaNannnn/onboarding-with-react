import os
import json
import logging
import hashlib
import datetime
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Directory for storing mapping patterns and reflection data
REFLECTION_DIR = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'reflection'))
REFLECTION_DIR.mkdir(exist_ok=True, parents=True)

class MappingMemorySystem:
    """
    A system for storing and retrieving historical mapping decisions and patterns.
    
    This class provides storage, retrieval, and analysis of mapping patterns to enable
    learning from past mapping decisions and improving future mapping quality.
    """
    
    def __init__(self, cache_expiration: int = 604800):
        """
        Initialize the mapping memory system.
        
        Args:
            cache_expiration: Time in seconds before cache entries expire (default: 7 days)
        """
        self.patterns = {}
        self.memory_file = REFLECTION_DIR / "mapping_patterns.json"
        self.cache_expiration = cache_expiration
        self.mem_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Statistics
        self.pattern_count = 0
        self.device_type_stats = {}
        self.quality_scores = []
        
        # Load patterns from file if available
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load mapping patterns from file storage."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = data.get("patterns", {})
                    logger.info(f"Loaded {len(self.patterns)} mapping patterns from {self.memory_file}")
                    
                    # Initialize statistics
                    self.pattern_count = len(self.patterns)
                    
                    # Calculate device type statistics
                    for pattern_id, pattern in self.patterns.items():
                        device_type = pattern.get("device_type", "unknown")
                        if device_type not in self.device_type_stats:
                            self.device_type_stats[device_type] = 0
                        self.device_type_stats[device_type] += 1
            except Exception as e:
                logger.error(f"Error loading mapping patterns: {str(e)}")
                self.patterns = {}
    
    def _save_patterns(self) -> None:
        """Save mapping patterns to file storage."""
        try:
            data = {
                "last_updated": datetime.datetime.now().isoformat(),
                "patterns": self.patterns,
                "stats": {
                    "pattern_count": self.pattern_count,
                    "device_type_stats": self.device_type_stats,
                    "avg_quality": np.mean(self.quality_scores) if self.quality_scores else 0.0,
                    "success_rate": sum(1 for pid, p in self.patterns.items() 
                                      if p.get("success_count", 0) > p.get("failure_count", 0)) / max(1, len(self.patterns))
                }
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.patterns)} mapping patterns to {self.memory_file}")
        except Exception as e:
            logger.error(f"Error saving mapping patterns: {str(e)}")
    
    def _generate_pattern_id(self, source_pattern: str, device_type: str) -> str:
        """Generate a unique ID for a mapping pattern."""
        key_str = f"{source_pattern}|{device_type}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def store_mapping_result(self, 
                            source_point: str, 
                            target_point: str, 
                            device_type: str,
                            confidence: float,
                            success: bool,
                            quality_score: float = None,
                            context: Dict = None) -> str:
        """
        Store a mapping result in the memory system.
        
        Args:
            source_point: Original BMS point name
            target_point: Mapped EnOS point name
            device_type: Type of device (e.g., 'AHU', 'CHILLER')
            confidence: Confidence score for the mapping (0.0-1.0)
            success: Whether the mapping was successful
            quality_score: Quality score for the mapping (0.0-1.0)
            context: Additional context information
            
        Returns:
            pattern_id: ID of the stored pattern
        """
        # Extract source pattern from point name (simplified for now)
        source_pattern = self._extract_pattern(source_point)
        target_pattern = self._extract_pattern(target_point) if target_point else None
        
        pattern_id = self._generate_pattern_id(source_pattern, device_type)
        
        # Update existing pattern or create new one
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern["confidence"] = (pattern["confidence"] * pattern["total_occurrences"] + confidence) / (pattern["total_occurrences"] + 1)
            
            if success:
                pattern["success_count"] += 1
            else:
                pattern["failure_count"] += 1
                
            pattern["total_occurrences"] += 1
            pattern["last_updated"] = datetime.datetime.now().isoformat()
            
            # Update quality metrics
            if quality_score is not None:
                current_quality = pattern.get("quality_score", 0.0)
                count = pattern.get("quality_count", 0)
                pattern["quality_score"] = (current_quality * count + quality_score) / (count + 1)
                pattern["quality_count"] = count + 1
                
            # Add example (limiting to 10 examples)
            example = {
                "bms_point": source_point,
                "enos_point": target_point,
                "result": "success" if success else "failure",
                "context": context or {}
            }
            
            # Ensure examples don't exceed 10 entries
            if len(pattern["examples"]) >= 10:
                # Remove oldest example (first one) to make room for the new one
                pattern["examples"] = pattern["examples"][1:] + [example]
            else:
                pattern["examples"].append(example)
                
        else:
            # Create new pattern
            self.patterns[pattern_id] = {
                "pattern_id": pattern_id,
                "source_pattern": source_pattern,
                "target_pattern": target_pattern,
                "device_type": device_type,
                "confidence": confidence,
                "success_count": 1 if success else 0,
                "failure_count": 0 if success else 1,
                "total_occurrences": 1,
                "quality_score": quality_score if quality_score is not None else 0.0,
                "quality_count": 1 if quality_score is not None else 0,
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat(),
                "examples": [
                    {
                        "bms_point": source_point,
                        "enos_point": target_point,
                        "result": "success" if success else "failure",
                        "context": context or {}
                    }
                ]
            }
            
            # Update statistics
            self.pattern_count += 1
            device_type_key = device_type or "unknown"
            self.device_type_stats[device_type_key] = self.device_type_stats.get(device_type_key, 0) + 1
        
        # Add to quality scores history
        if quality_score is not None:
            self.quality_scores.append(quality_score)
        
        # Save patterns periodically (every 10 updates)
        if self.pattern_count % 10 == 0:
            self._save_patterns()
            
        return pattern_id
    
    def retrieve_similar_patterns(self, 
                                 point_name: str, 
                                 device_type: str,
                                 threshold: float = 0.6,
                                 limit: int = 5) -> List[Dict]:
        """
        Retrieve patterns similar to the given point name and device type.
        
        Args:
            point_name: The BMS point name to find patterns for
            device_type: The device type
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum number of patterns to return
            
        Returns:
            List of similar patterns
        """
        source_pattern = self._extract_pattern(point_name)
        
        # Query cache first
        cache_key = f"{source_pattern}|{device_type}"
        
        if cache_key in self.mem_cache:
            cache_entry = self.mem_cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - cache_entry["timestamp"] < self.cache_expiration:
                self.cache_hits += 1
                return cache_entry["patterns"]
        
        self.cache_misses += 1
        
        # Find similar patterns
        similar_patterns = []
        for pattern_id, pattern in self.patterns.items():
            # Only consider patterns of the same device type
            if pattern["device_type"] == device_type:
                similarity = self._calculate_similarity(source_pattern, pattern["source_pattern"])
                if similarity >= threshold:
                    # Add similarity score to pattern for sorting
                    result = pattern.copy()
                    result["similarity"] = similarity
                    similar_patterns.append(result)
        
        # Sort by similarity and limit results
        similar_patterns.sort(key=lambda x: x["similarity"], reverse=True)
        result = similar_patterns[:limit]
        
        # Cache the result
        self.mem_cache[cache_key] = {
            "patterns": result,
            "timestamp": time.time()
        }
        
        return result
    
    def get_best_mapping(self, 
                        point_name: str, 
                        device_type: str,
                        confidence_threshold: float = 0.7) -> Tuple[Optional[str], float, str]:
        """
        Get the best EnOS point mapping for a given BMS point based on historical patterns.
        
        Args:
            point_name: The BMS point name to map
            device_type: The device type
            confidence_threshold: Minimum confidence required to use a mapping
            
        Returns:
            tuple: (enos_point, confidence, reason)
                - enos_point: The mapped EnOS point name or None if no confident mapping found
                - confidence: Confidence score for the mapping (0.0-1.0)
                - reason: Reason for the mapping decision
        """
        # Get similar patterns
        similar_patterns = self.retrieve_similar_patterns(point_name, device_type)
        
        if not similar_patterns:
            return None, 0.0, "No similar patterns found"
        
        # Find the best pattern based on confidence and success rate
        best_pattern = None
        best_score = 0.0
        
        for pattern in similar_patterns:
            total = pattern["success_count"] + pattern["failure_count"]
            if total == 0:
                continue
                
            success_rate = pattern["success_count"] / total
            confidence = pattern["confidence"]
            
            # Combined score based on success rate and confidence
            score = 0.7 * success_rate + 0.3 * confidence
            
            if score > best_score:
                best_score = score
                best_pattern = pattern
        
        if best_pattern and best_score >= confidence_threshold:
            # Use example with successful mapping
            for example in best_pattern["examples"]:
                if example["result"] == "success":
                    return (
                        example["enos_point"],
                        best_score,
                        f"Pattern match: {best_pattern['source_pattern']} → {best_pattern['target_pattern']}"
                    )
        
        return None, best_score, "No confident mapping found"
    
    def get_pattern_statistics(self, device_type: Optional[str] = None) -> Dict:
        """
        Get statistics about the mapping patterns.
        
        Args:
            device_type: Optional filter for specific device type
            
        Returns:
            Dictionary of pattern statistics
        """
        stats = {
            "total_patterns": self.pattern_count,
            "device_types": self.device_type_stats,
            "avg_quality_score": np.mean(self.quality_scores) if self.quality_scores else 0.0,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses)
            }
        }
        
        # Calculate success rates by device type
        success_by_device = {}
        for pattern_id, pattern in self.patterns.items():
            dt = pattern["device_type"]
            if device_type and dt != device_type:
                continue
                
            if dt not in success_by_device:
                success_by_device[dt] = {"success": 0, "failure": 0}
                
            success_by_device[dt]["success"] += pattern["success_count"]
            success_by_device[dt]["failure"] += pattern["failure_count"]
        
        # Calculate rates
        device_success_rates = {}
        for dt, counts in success_by_device.items():
            total = counts["success"] + counts["failure"]
            if total > 0:
                device_success_rates[dt] = counts["success"] / total
            else:
                device_success_rates[dt] = 0.0
                
        stats["success_rates_by_device"] = device_success_rates
        
        return stats
    
    def _extract_pattern(self, point_name: str) -> str:
        """
        Extract a standardized pattern from a point name.
        This is a simplified implementation - future versions will use more
        sophisticated pattern extraction algorithms.
        
        Args:
            point_name: The point name to extract a pattern from
            
        Returns:
            A standardized pattern representation
        """
        if not point_name:
            return ""
            
        # Convert to lowercase for standardization
        name = point_name.lower()
        
        # Replace common separators with a standard one
        name = name.replace('-', '_').replace('.', '_').replace(' ', '_')
        
        # Remove numeric parts (they're usually instance-specific)
        import re
        name = re.sub(r'_?\d+', '', name)
        
        # Special handling for energy meter points with units in their name
        name = re.sub(r'_kw$', '_power', name)
        name = re.sub(r'_kwh$', '_energy', name)
        name = re.sub(r'kw$', '_power', name)
        name = re.sub(r'kwh$', '_energy', name)
        
        # Map common energy-related terms to standardized forms
        if 'totalcwp' in name:
            name = name.replace('totalcwp', 'cooling_water_pump')
        if 'totalchwp' in name:
            name = name.replace('totalchwp', 'chilled_water_pump')
        
        # Remove duplicate underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        return name
    
    def _calculate_similarity(self, pattern1: str, pattern2: str) -> float:
        """
        Calculate similarity between two patterns.
        
        Args:
            pattern1: First pattern
            pattern2: Second pattern
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if not pattern1 or not pattern2:
            return 0.0
            
        # Split patterns into words
        words1 = set(pattern1.split('_'))
        words2 = set(pattern2.split('_'))
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)


class PatternAnalysisEngine:
    """
    Analyzes patterns in mapping successes and failures to identify recurring patterns.
    
    This class implements algorithms for extracting semantic and syntactic patterns
    from point names and grouping related mappings.
    """
    
    def __init__(self, memory_system: MappingMemorySystem):
        """
        Initialize the pattern analysis engine.
        
        Args:
            memory_system: Reference to the mapping memory system
        """
        self.memory_system = memory_system
        self.pattern_clusters = {}
        self.common_prefixes = {}
        self.common_suffixes = {}
        
    def extract_patterns(self, points: List[Dict]) -> Dict:
        """
        Extract common patterns from a list of points.
        
        Args:
            points: List of point dictionaries
            
        Returns:
            Dictionary of extracted patterns
        """
        # Initialize pattern collections
        prefixes = {}
        suffixes = {}
        word_frequencies = {}
        device_patterns = {}
        
        # Extract patterns from each point
        for point in points:
            point_name = point.get('pointName', '')
            device_type = point.get('deviceType', 'unknown')
            
            if not point_name:
                continue
                
            # Handle device-specific patterns
            if device_type not in device_patterns:
                device_patterns[device_type] = {'points': [], 'patterns': {}}
                
            device_patterns[device_type]['points'].append(point_name)
            
            # Process point name for patterns
            words = self._tokenize_point_name(point_name)
            
            # Extract prefix and suffix
            if words:
                prefix = words[0]
                if prefix in prefixes:
                    prefixes[prefix] += 1
                else:
                    prefixes[prefix] = 1
                    
                suffix = words[-1]
                if suffix in suffixes:
                    suffixes[suffix] += 1
                else:
                    suffixes[suffix] = 1
            
            # Count word frequencies
            for word in words:
                if word in word_frequencies:
                    word_frequencies[word] += 1
                else:
                    word_frequencies[word] = 1
        
        # Find common patterns in each device type
        for device_type, data in device_patterns.items():
            device_points = data['points']
            
            if len(device_points) < 2:
                continue
                
            # Extract n-grams from device points
            ngrams = self._extract_ngrams(device_points)
            
            # Store patterns
            device_patterns[device_type]['patterns'] = {
                'ngrams': ngrams,
                'point_count': len(device_points)
            }
        
        # Combine all pattern analyses
        patterns = {
            'common_prefixes': sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:10],
            'common_suffixes': sorted(suffixes.items(), key=lambda x: x[1], reverse=True)[:10],
            'common_words': sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:20],
            'device_patterns': device_patterns
        }
        
        return patterns
    
    def _tokenize_point_name(self, point_name: str) -> List[str]:
        """
        Tokenize a point name into constituent words.
        
        Args:
            point_name: The point name to tokenize
            
        Returns:
            List of tokens
        """
        if not point_name:
            return []
            
        # Replace common separators with a standard one
        name = point_name.lower().replace('-', '_').replace('.', '_').replace(' ', '_')
        
        # Split by underscore
        tokens = [t for t in name.split('_') if t]
        
        return tokens
    
    def _extract_ngrams(self, point_names: List[str], min_n: int = 2, max_n: int = 4) -> Dict:
        """
        Extract n-grams from a list of point names.
        
        Args:
            point_names: List of point names
            min_n: Minimum n-gram size
            max_n: Maximum n-gram size
            
        Returns:
            Dictionary of n-grams and their frequencies
        """
        ngrams = {}
        
        for point_name in point_names:
            tokens = self._tokenize_point_name(point_name)
            
            # Skip if too few tokens
            if len(tokens) < min_n:
                continue
                
            # Extract n-grams
            for n in range(min_n, min(max_n + 1, len(tokens) + 1)):
                for i in range(len(tokens) - n + 1):
                    ngram = '_'.join(tokens[i:i+n])
                    
                    if ngram in ngrams:
                        ngrams[ngram] += 1
                    else:
                        ngrams[ngram] = 1
        
        # Filter out infrequent n-grams
        threshold = max(2, len(point_names) * 0.1)  # At least 10% of points or 2, whichever is higher
        filtered_ngrams = {k: v for k, v in ngrams.items() if v >= threshold}
        
        # Sort by frequency
        sorted_ngrams = sorted(filtered_ngrams.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'all': sorted_ngrams[:30],  # Top 30 n-grams
            'threshold': threshold,
            'total_unique': len(ngrams)
        }
    
    def identify_pattern_families(self, mappings: List[Dict]) -> Dict:
        """
        Identify families of related patterns in mappings.
        
        Args:
            mappings: List of mapping results
            
        Returns:
            Dictionary of pattern families
        """
        # Group mappings by device type
        device_groups = {}
        
        for mapping in mappings:
            if 'original' not in mapping or 'mapping' not in mapping:
                continue
                
            device_type = mapping['original'].get('deviceType', 'unknown')
            
            if device_type not in device_groups:
                device_groups[device_type] = []
                
            device_groups[device_type].append(mapping)
        
        # Analyze each device group
        pattern_families = {}
        
        for device_type, group_mappings in device_groups.items():
            # Skip small groups
            if len(group_mappings) < 3:
                continue
                
            # Extract success patterns
            success_patterns = []
            for mapping in group_mappings:
                if mapping['mapping'].get('status') == 'mapped' and mapping['mapping'].get('enosPoint'):
                    source = mapping['original'].get('pointName', '')
                    target = mapping['mapping'].get('enosPoint', '')
                    
                    if source and target:
                        source_pattern = self.memory_system._extract_pattern(source)
                        target_pattern = self.memory_system._extract_pattern(target)
                        
                        success_patterns.append({
                            'source': source,
                            'target': target,
                            'source_pattern': source_pattern,
                            'target_pattern': target_pattern
                        })
            
            # Skip if not enough success patterns
            if len(success_patterns) < 3:
                continue
                
            # Group by target pattern
            target_groups = {}
            
            for pattern in success_patterns:
                target = pattern['target_pattern']
                
                if target not in target_groups:
                    target_groups[target] = []
                    
                target_groups[target].append(pattern)
            
            # Keep only groups with at least 2 patterns
            significant_groups = {k: v for k, v in target_groups.items() if len(v) >= 2}
            
            if significant_groups:
                pattern_families[device_type] = {
                    'target_groups': significant_groups,
                    'total_mappings': len(group_mappings),
                    'success_count': len(success_patterns)
                }
        
        return pattern_families


class QualityAssessmentFramework:
    """
    Framework for evaluating and scoring mapping decisions.
    
    This class implements multi-dimensional quality metrics to evaluate
    mapping decisions beyond simple binary success/failure.
    """
    
    def __init__(self):
        """Initialize the quality assessment framework."""
        # Define quality dimensions and their weights
        self.quality_dimensions = {
            'semantic_correctness': 0.35,
            'convention_adherence': 0.20,
            'consistency': 0.15,
            'device_context': 0.20,
            'schema_completeness': 0.10
        }
        
        # Thresholds for quality levels
        self.quality_thresholds = {
            'excellent': 0.85,
            'good': 0.70,
            'fair': 0.50,
            'poor': 0.30,
            'unacceptable': 0.0
        }
    
    def assess_mapping_quality(self, 
                              mapping: Dict, 
                              reference_mappings: List[Dict] = None,
                              schema: Dict = None) -> Dict:
        """
        Assess the quality of a mapping along multiple dimensions.
        
        Args:
            mapping: The mapping to assess
            reference_mappings: List of reference mappings for comparison
            schema: EnOS schema for validation
            
        Returns:
            Quality assessment results
        """
        # Initialize quality scores
        scores = {dim: 0.0 for dim in self.quality_dimensions.keys()}
        
        # Extract mapping details
        original = mapping.get('original', {})
        map_result = mapping.get('mapping', {})
        
        point_name = original.get('pointName', '')
        device_type = original.get('deviceType', '')
        enos_point = map_result.get('enosPoint', '')
        
        if not point_name or not enos_point:
            return self._create_quality_report(scores, 'Invalid mapping data')
        
        # 1. Assess semantic correctness
        semantic_score = self._assess_semantic_correctness(point_name, enos_point, device_type)
        scores['semantic_correctness'] = semantic_score
        
        # 2. Assess convention adherence
        convention_score = self._assess_convention_adherence(enos_point, device_type)
        scores['convention_adherence'] = convention_score
        
        # 3. Assess consistency with similar points
        consistency_score = 0.5  # Default mid-range score
        if reference_mappings:
            consistency_score = self._assess_consistency(mapping, reference_mappings)
        scores['consistency'] = consistency_score
        
        # 4. Assess device context alignment
        device_score = self._assess_device_context(enos_point, device_type)
        scores['device_context'] = device_score
        
        # 5. Assess schema completeness
        schema_score = 0.5  # Default mid-range score
        if schema:
            schema_score = self._assess_schema_completeness(enos_point, device_type, schema)
        scores['schema_completeness'] = schema_score
        
        # Calculate weighted average score
        weighted_score = sum(scores[dim] * weight for dim, weight in self.quality_dimensions.items())
        
        # Determine quality level
        quality_level = self._determine_quality_level(weighted_score)
        
        # Create improvement suggestions
        suggestions = self._generate_improvement_suggestions(scores, enos_point, device_type)
        
        # Create final quality report
        return self._create_quality_report(scores, quality_level, weighted_score, suggestions)
    
    def _assess_semantic_correctness(self, point_name: str, enos_point: str, device_type: str) -> float:
        """
        Assess the semantic correctness of a mapping.
        
        Args:
            point_name: Original BMS point name
            enos_point: Mapped EnOS point name
            device_type: Device type
            
        Returns:
            Semantic correctness score (0.0-1.0)
        """
        # Simple heuristic approach for semantic correctness assessment
        point_words = set(point_name.lower().replace('.', '_').replace('-', '_').split('_'))
        enos_words = set(enos_point.lower().split('_')[2:])  # Skip prefix and category
        
        # Check for semantic keyword matches
        common_keywords = {
            'temp': ['temp', 'temperature', 'tmp'],
            'press': ['press', 'pressure', 'pres'],
            'humid': ['humid', 'humidity', 'rh'],
            'flow': ['flow', 'cfm', 'gpm'],
            'status': ['status', 'state', 'on', 'off', 'run'],
            'setpoint': ['setpoint', 'sp', 'set'],
            'valve': ['valve', 'vav', 'damper', 'vpos'],
            'speed': ['speed', 'rpm', 'freq', 'vfd'],
            'power': ['power', 'kw', 'energy', 'demand'],
            'alarm': ['alarm', 'fault', 'error', 'trip']
        }
        
        # Check for semantic matches
        point_semantic_categories = []
        enos_semantic_categories = []
        
        for category, keywords in common_keywords.items():
            if any(kw in point_words for kw in keywords):
                point_semantic_categories.append(category)
            
            if any(kw in enos_words for kw in keywords):
                enos_semantic_categories.append(category)
        
        # Calculate matches between semantic categories
        if point_semantic_categories and enos_semantic_categories:
            matches = set(point_semantic_categories).intersection(enos_semantic_categories)
            score = len(matches) / max(len(point_semantic_categories), 1)
            return min(1.0, score + 0.2)  # Bonus to reward any match
        
        # Fallback: Calculate direct word overlap
        if point_words and enos_words:
            matches = point_words.intersection(enos_words)
            return len(matches) / max(len(point_words), 1) * 0.8  # Maximum 0.8 for direct matching
        
        return 0.3  # Minimum score if no matches found
    
    def _assess_convention_adherence(self, enos_point: str, device_type: str) -> float:
        """
        Assess adherence to EnOS naming conventions.
        
        Args:
            enos_point: Mapped EnOS point name
            device_type: Device type
            
        Returns:
            Convention adherence score (0.0-1.0)
        """
        if not enos_point:
            return 0.0
            
        # Check format compliance: DEVICE_CATEGORY_MEASUREMENT_POINT
        parts = enos_point.split('_')
        score = 0.0
        
        # Check for minimum parts
        if len(parts) >= 3:
            score += 0.4
            
            # Check prefix matches device type or abbreviation
            prefix = parts[0]
            expected_prefixes = {
                'AHU': ['AHU'],
                'FCU': ['FCU'],
                'VAV': ['VAV'],
                'CHILLER': ['CH', 'CHILLER'],
                'PUMP': ['PUMP', 'CWP', 'CHWP', 'HWP'],
                'COOLING_TOWER': ['CT'],
                'BOILER': ['BOIL'],
                'METER': ['METER', 'DPM']
            }
            
            device_normalized = device_type.upper()
            valid_prefixes = []
            
            # Find matching prefixes
            for dt, prefixes in expected_prefixes.items():
                if dt in device_normalized or any(p in device_normalized for p in prefixes):
                    valid_prefixes.extend(prefixes)
            
            if prefix in valid_prefixes:
                score += 0.4
            
            # Check for category (raw/calc)
            if len(parts) > 1 and parts[1] in ['raw', 'calc']:
                score += 0.2
        
        return score
    
    def _assess_consistency(self, mapping: Dict, reference_mappings: List[Dict]) -> float:
        """
        Assess consistency with similar points.
        
        Args:
            mapping: The mapping to assess
            reference_mappings: List of reference mappings
            
        Returns:
            Consistency score (0.0-1.0)
        """
        original = mapping.get('original', {})
        map_result = mapping.get('mapping', {})
        
        point_name = original.get('pointName', '')
        device_type = original.get('deviceType', '')
        enos_point = map_result.get('enosPoint', '')
        
        if not point_name or not enos_point or not reference_mappings:
            return 0.5
            
        # Extract patterns
        point_pattern = point_name.lower().replace('.', '_').replace('-', '_')
        
        # Find similar reference points
        similar_points = []
        
        for ref in reference_mappings:
            ref_original = ref.get('original', {})
            ref_mapping = ref.get('mapping', {})
            
            ref_point = ref_original.get('pointName', '')
            ref_device = ref_original.get('deviceType', '')
            ref_enos = ref_mapping.get('enosPoint', '')
            
            if not ref_point or not ref_enos:
                continue
                
            # Only consider same device type
            if ref_device != device_type:
                continue
                
            # Skip self-comparison
            if ref_point == point_name:
                continue
                
            # Calculate name similarity
            ref_pattern = ref_point.lower().replace('.', '_').replace('-', '_')
            similarity = self._calculate_name_similarity(point_pattern, ref_pattern)
            
            if similarity > 0.5:
                similar_points.append((ref_point, ref_enos, similarity))
        
        # If no similar points found
        if not similar_points:
            return 0.5
            
        # Calculate consistency score
        consistency_scores = []
        for _, ref_enos, similarity in similar_points:
            # Check EnOS point similarity
            enos_similarity = self._calculate_name_similarity(enos_point, ref_enos)
            # Weight by point name similarity
            weighted_score = enos_similarity * similarity
            consistency_scores.append(weighted_score)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    
    def _assess_device_context(self, enos_point: str, device_type: str) -> float:
        """
        Assess alignment with device context.
        
        Args:
            enos_point: Mapped EnOS point name
            device_type: Device type
            
        Returns:
            Device context alignment score (0.0-1.0)
        """
        if not enos_point or not device_type:
            return 0.3
            
        # Define expected point patterns for different device types
        device_patterns = {
            'AHU': [
                'temp', 'humidity', 'pressure', 'flow', 'damper', 'valve',
                'fan', 'filter', 'cooling', 'heating', 'supply', 'return'
            ],
            'FCU': [
                'temp', 'valve', 'fan', 'mode', 'setpoint', 'speed'
            ],
            'CHILLER': [
                'temp', 'pressure', 'flow', 'power', 'current', 'status',
                'chws', 'chwr', 'cws', 'cwr', 'load'
            ],
            'PUMP': [
                'status', 'speed', 'flow', 'pressure', 'power', 'current'
            ],
            'COOLING_TOWER': [
                'temp', 'fan', 'speed', 'vibration', 'flow', 'basin'
            ],
            'BOILER': [
                'temp', 'pressure', 'flow', 'status', 'flame', 'gas'
            ],
            'METER': [
                'power', 'energy', 'demand', 'current', 'voltage', 'frequency'
            ],
            'VAV': [
                'flow', 'damper', 'temp', 'pressure', 'setpoint', 'zone'
            ]
        }
        
        # Normalize device type
        normalized_device = None
        for dt, patterns in device_patterns.items():
            if dt in device_type.upper():
                normalized_device = dt
                break
        
        if not normalized_device:
            return 0.5  # Average score for unknown device types
            
        # Check for expected patterns in the EnOS point
        enos_lower = enos_point.lower()
        matching_patterns = 0
        
        for pattern in device_patterns[normalized_device]:
            if pattern in enos_lower:
                matching_patterns += 1
        
        # Calculate score based on pattern matches
        score = min(1.0, matching_patterns * 0.2 + 0.4)  # Base 0.4 + 0.2 per match, max 1.0
        
        return score
    
    def _assess_schema_completeness(self, enos_point: str, device_type: str, schema: Dict) -> float:
        """
        Assess completeness with respect to EnOS schema.
        
        Args:
            enos_point: Mapped EnOS point name
            device_type: Device type
            schema: EnOS schema for validation
            
        Returns:
            Schema completeness score (0.0-1.0)
        """
        if not enos_point or not schema:
            return 0.5
            
        # Check if device type exists in schema
        device_normalized = device_type.upper()
        device_in_schema = False
        
        for dt in schema.keys():
            if dt in device_normalized:
                device_in_schema = True
                break
        
        if not device_in_schema:
            return 0.5  # Average score if device type not in schema
            
        # Check if point exists in schema for this device type
        point_in_schema = False
        
        for dt, points in schema.items():
            if dt in device_normalized and isinstance(points, dict) and 'points' in points:
                if enos_point in points['points']:
                    point_in_schema = True
                    break
        
        # Score based on schema presence
        return 1.0 if point_in_schema else 0.3
    
    def _determine_quality_level(self, score: float) -> str:
        """
        Determine quality level based on score.
        
        Args:
            score: Quality score (0.0-1.0)
            
        Returns:
            Quality level string
        """
        if score >= self.quality_thresholds['excellent']:
            return 'excellent'
        elif score >= self.quality_thresholds['good']:
            return 'good'
        elif score >= self.quality_thresholds['fair']:
            return 'fair'
        elif score >= self.quality_thresholds['poor']:
            return 'poor'
        else:
            return 'unacceptable'
    
    def _generate_improvement_suggestions(self, 
                                         scores: Dict[str, float], 
                                         enos_point: str,
                                         device_type: str) -> List[str]:
        """
        Generate improvement suggestions based on quality scores.
        
        Args:
            scores: Quality dimension scores
            enos_point: Mapped EnOS point name
            device_type: Device type
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Add suggestions based on lowest scores
        if scores['semantic_correctness'] < 0.5:
            suggestions.append("Improve semantic matching between BMS point name and EnOS point")
            
        if scores['convention_adherence'] < 0.5:
            if not enos_point or '_' not in enos_point:
                suggestions.append("EnOS point should follow DEVICE_CATEGORY_MEASUREMENT_POINT format")
            else:
                parts = enos_point.split('_')
                if len(parts) < 3:
                    suggestions.append("EnOS point should have at least 3 components separated by underscores")
                elif not parts[1] in ['raw', 'calc']:
                    suggestions.append("Second component of EnOS point should be 'raw' or 'calc'")
        
        if scores['device_context'] < 0.5:
            suggestions.append(f"Ensure EnOS point is appropriate for device type {device_type}")
            
        # Limit to 3 suggestions
        return suggestions[:3]
    
    def _create_quality_report(self, 
                              scores: Dict[str, float], 
                              quality_level: str,
                              weighted_score: float = None,
                              suggestions: List[str] = None) -> Dict:
        """
        Create a structured quality report.
        
        Args:
            scores: Quality dimension scores
            quality_level: Quality level string
            weighted_score: Overall weighted quality score
            suggestions: Improvement suggestions
            
        Returns:
            Quality report dictionary
        """
        return {
            'dimension_scores': scores,
            'overall_score': weighted_score if weighted_score is not None else 0.0,
            'quality_level': quality_level,
            'suggestions': suggestions or []
        }
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if not name1 or not name2:
            return 0.0
            
        # Split names into components
        parts1 = name1.lower().split('_')
        parts2 = name2.lower().split('_')
        
        # Calculate Jaccard similarity for parts
        set1 = set(parts1)
        set2 = set(parts2)
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)


class StrategySelectionSystem:
    """
    System for selecting optimal mapping strategies based on point characteristics.
    
    This class implements logic to choose the best mapping strategy for
    different types of points based on historical performance.
    """
    
    def __init__(self, memory_system: MappingMemorySystem):
        """
        Initialize the strategy selection system.
        
        Args:
            memory_system: Reference to the mapping memory system
        """
        self.memory_system = memory_system
        self.strategy_performance = {}
        self.device_strategies = {}
        
        # Initialize strategy library
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize the mapping strategy library."""
        self.strategies = {
            'direct_pattern': {
                'name': 'Direct Pattern Matching',
                'description': 'Matches point names directly based on patterns',
                'confidence_threshold': 0.7,
                'suitable_for': ['all']
            },
            'semantic_inference': {
                'name': 'Semantic Inference',
                'description': 'Uses semantic understanding to infer mappings',
                'confidence_threshold': 0.6,
                'suitable_for': ['complex_points', 'ambiguous_names']
            },
            'device_context': {
                'name': 'Device Context',
                'description': 'Leverages device context for mapping',
                'confidence_threshold': 0.65,
                'suitable_for': ['new_points', 'ambiguous_names']
            },
            'schema_guided': {
                'name': 'Schema-Guided',
                'description': 'Uses EnOS schema to guide mapping',
                'confidence_threshold': 0.75,
                'suitable_for': ['standard_points']
            },
            'hybrid': {
                'name': 'Hybrid Approach',
                'description': 'Combines multiple strategies for optimal mapping',
                'confidence_threshold': 0.6,
                'suitable_for': ['all']
            }
        }
        
        # Define device-specific strategy preferences
        self.device_strategies = {
            'AHU': ['device_context', 'direct_pattern', 'semantic_inference'],
            'FCU': ['direct_pattern', 'device_context', 'semantic_inference'],
            'CHILLER': ['device_context', 'schema_guided', 'semantic_inference'],
            'PUMP': ['direct_pattern', 'schema_guided'],
            'COOLING_TOWER': ['direct_pattern', 'device_context'],
            'VAV': ['direct_pattern', 'semantic_inference'],
            'METER': ['schema_guided', 'direct_pattern'],
            'default': ['hybrid', 'direct_pattern', 'semantic_inference']
        }
    
    def select_strategy(self, point: Dict) -> Dict:
        """
        Select the optimal mapping strategy for a given point.
        
        Args:
            point: Point to select strategy for
            
        Returns:
            Selected strategy information
        """
        if not point:
            return self._get_default_strategy()
            
        point_name = point.get('pointName', '')
        device_type = point.get('deviceType', '')
        
        if not point_name:
            return self._get_default_strategy()
            
        # Get device-specific strategies
        device_specific_strategies = self._get_device_strategies(device_type)
        
        # Check for pattern-based strategy selection
        similar_patterns = self.memory_system.retrieve_similar_patterns(point_name, device_type)
        
        if similar_patterns:
            # Calculate strategy effectiveness from similar patterns
            strategy_scores = self._calculate_strategy_scores(similar_patterns)
            
            # If we have strategy scores, select the best one
            if strategy_scores:
                best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
                return {
                    'strategy': best_strategy,
                    'details': self.strategies[best_strategy],
                    'score': strategy_scores[best_strategy],
                    'reason': 'Selected based on pattern similarity analysis'
                }
        
        # If no patterns or no effective strategy found, use device-specific default
        if device_specific_strategies:
            selected_strategy = device_specific_strategies[0]
            return {
                'strategy': selected_strategy,
                'details': self.strategies[selected_strategy],
                'score': 0.7,  # Default confidence
                'reason': f'Selected based on device type {device_type}'
            }
        
        # Fallback to generic default
        return self._get_default_strategy()
    
    def _get_device_strategies(self, device_type: str) -> List[str]:
        """
        Get preferred strategies for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            List of strategy IDs
        """
        if not device_type:
            return self.device_strategies['default']
            
        device_upper = device_type.upper()
        
        # Try to match device type
        for dt, strategies in self.device_strategies.items():
            if dt in device_upper:
                return strategies
        
        # Fallback to default
        return self.device_strategies['default']
    
    def _get_default_strategy(self) -> Dict:
        """
        Get the default mapping strategy.
        
        Returns:
            Default strategy information
        """
        default_strategy = 'hybrid'
        return {
            'strategy': default_strategy,
            'details': self.strategies[default_strategy],
            'score': 0.6,
            'reason': 'Selected as default strategy'
        }
    
    def _calculate_strategy_scores(self, patterns: List[Dict]) -> Dict[str, float]:
        """
        Calculate strategy effectiveness scores based on patterns.
        
        Args:
            patterns: List of similar patterns
            
        Returns:
            Dictionary of strategy scores
        """
        strategy_counts = {s: 0 for s in self.strategies.keys()}
        strategy_successes = {s: 0 for s in self.strategies.keys()}
        
        # Count successes for each strategy
        for pattern in patterns:
            examples = pattern.get('examples', [])
            
            for example in examples:
                # Skip examples with no context
                context = example.get('context', {})
                if not context or 'strategy' not in context:
                    continue
                    
                strategy = context['strategy']
                result = example.get('result', '')
                
                if strategy in strategy_counts:
                    strategy_counts[strategy] += 1
                    if result == 'success':
                        strategy_successes[strategy] += 1
        
        # Calculate success rates
        strategy_scores = {}
        
        for strategy, count in strategy_counts.items():
            if count > 0:
                success_rate = strategy_successes[strategy] / count
                # Apply confidence threshold
                threshold = self.strategies[strategy]['confidence_threshold']
                if success_rate >= threshold:
                    strategy_scores[strategy] = success_rate
        
        return strategy_scores
    
    def update_strategy_performance(self, 
                                  strategy: str,
                                  success: bool,
                                  device_type: str,
                                  point_pattern: str) -> None:
        """
        Update performance tracking for a strategy.
        
        Args:
            strategy: Strategy ID
            success: Whether the mapping was successful
            device_type: Device type for the mapping
            point_pattern: Point pattern used
        """
        if strategy not in self.strategies:
            return
            
        # Initialize strategy performance record if needed
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                'total_uses': 0,
                'successes': 0,
                'failures': 0,
                'device_stats': {},
                'pattern_stats': {}
            }
        
        # Update general statistics
        perf = self.strategy_performance[strategy]
        perf['total_uses'] += 1
        
        if success:
            perf['successes'] += 1
        else:
            perf['failures'] += 1
        
        # Update device-specific statistics
        if device_type:
            if device_type not in perf['device_stats']:
                perf['device_stats'][device_type] = {'uses': 0, 'successes': 0}
                
            perf['device_stats'][device_type]['uses'] += 1
            
            if success:
                perf['device_stats'][device_type]['successes'] += 1
        
        # Update pattern statistics
        if point_pattern:
            if point_pattern not in perf['pattern_stats']:
                perf['pattern_stats'][point_pattern] = {'uses': 0, 'successes': 0}
                
            perf['pattern_stats'][point_pattern]['uses'] += 1
            
            if success:
                perf['pattern_stats'][point_pattern]['successes'] += 1
    
    def get_strategy_stats(self) -> Dict:
        """
        Get strategy performance statistics.
        
        Returns:
            Dictionary of strategy statistics
        """
        stats = {}
        
        for strategy_id, perf in self.strategy_performance.items():
            success_rate = 0.0
            if perf['total_uses'] > 0:
                success_rate = perf['successes'] / perf['total_uses']
                
            stats[strategy_id] = {
                'name': self.strategies[strategy_id]['name'],
                'total_uses': perf['total_uses'],
                'success_rate': success_rate,
                'device_success_rates': {}
            }
            
            # Calculate device-specific success rates
            for device, device_stat in perf.get('device_stats', {}).items():
                if device_stat['uses'] > 0:
                    device_success_rate = device_stat['successes'] / device_stat['uses']
                    stats[strategy_id]['device_success_rates'][device] = device_success_rate
        
        return stats


class ReflectionSystem:
    """
    Main reflection system that integrates all reflection components.
    
    This class coordinates the memory system, pattern analysis, quality assessment,
    and strategy selection to provide a comprehensive reflection layer.
    """
    
    def __init__(self):
        """Initialize the reflection system."""
        # Initialize components
        self.memory_system = MappingMemorySystem()
        self.pattern_analysis = PatternAnalysisEngine(self.memory_system)
        self.quality_assessment = QualityAssessmentFramework()
        self.strategy_selection = StrategySelectionSystem(self.memory_system)
        
        # Statistics
        self.reflection_stats = {
            'total_reflections': 0,
            'quality_levels': {
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'poor': 0,
                'unacceptable': 0
            },
            'strategy_uses': {}
        }
    
    def reflect_on_mapping(self, 
                          mapping: Dict, 
                          reference_mappings: List[Dict] = None,
                          schema: Dict = None,
                          context: Dict = None) -> Dict:
        """
        Perform a comprehensive reflection on a mapping result.
        
        Args:
            mapping: The mapping to reflect on
            reference_mappings: List of reference mappings for comparison
            schema: EnOS schema for validation
            context: Additional context information
            
        Returns:
            Enhanced mapping with reflection data
        """
        # Update statistics
        self.reflection_stats['total_reflections'] += 1
        
        # Extract mapping details
        original = mapping.get('original', {})
        map_result = mapping.get('mapping', {})
        
        point_name = original.get('pointName', '')
        device_type = original.get('deviceType', '')
        enos_point = map_result.get('enosPoint', '')
        mapping_status = map_result.get('status', '')
        
        # Determine success
        success = mapping_status == 'mapped' and enos_point
        
        # Perform quality assessment
        quality_report = self.quality_assessment.assess_mapping_quality(
            mapping, reference_mappings, schema
        )
        
        # Update quality level statistics
        quality_level = quality_report.get('quality_level', 'fair')
        self.reflection_stats['quality_levels'][quality_level] = self.reflection_stats['quality_levels'].get(quality_level, 0) + 1
        
        # Store in memory system
        if point_name and device_type:
            # Construct context for storage
            storage_context = {
                'mapping_id': mapping.get('mapping', {}).get('pointId', ''),
                'quality_level': quality_level,
                'strategy': context.get('strategy', 'unknown') if context else 'unknown',
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Store the mapping result
            self.memory_system.store_mapping_result(
                source_point=point_name,
                target_point=enos_point,
                device_type=device_type,
                confidence=quality_report.get('overall_score', 0.5),
                success=success,
                quality_score=quality_report.get('overall_score', 0.5),
                context=storage_context
            )
            
            # Update strategy performance
            if context and 'strategy' in context:
                strategy = context['strategy']
                
                # Update strategy usage statistics
                if strategy not in self.reflection_stats['strategy_uses']:
                    self.reflection_stats['strategy_uses'][strategy] = {'total': 0, 'success': 0}
                    
                self.reflection_stats['strategy_uses'][strategy]['total'] += 1
                if success:
                    self.reflection_stats['strategy_uses'][strategy]['success'] += 1
                
                # Update detailed strategy performance
                source_pattern = self.memory_system._extract_pattern(point_name)
                self.strategy_selection.update_strategy_performance(
                    strategy=strategy,
                    success=success,
                    device_type=device_type,
                    point_pattern=source_pattern
                )
        
        # Create reflection data
        reflection_data = {
            'quality': quality_report,
            'pattern_matches': len(self.memory_system.retrieve_similar_patterns(point_name, device_type)) if point_name and device_type else 0,
            'historical_data': {
                'mapping_count': self.reflection_stats['total_reflections'],
                'similar_mappings_count': self._count_similar_mappings(point_name, device_type) if point_name and device_type else 0
            }
        }
        
        # Enhance the mapping with reflection data
        enhanced_mapping = mapping.copy()
        enhanced_mapping['reflection'] = reflection_data
        
        return enhanced_mapping
    
    def suggest_mapping(self, point: Dict) -> Dict:
        """
        Suggest a mapping for a point based on reflection data.
        
        Args:
            point: Point to suggest mapping for
            
        Returns:
            Suggested mapping with confidence and explanation
        """
        if not point or not point.get('pointName') or not point.get('deviceType'):
            return {
                'success': False,
                'error': 'Invalid point data'
            }
            
        point_name = point['pointName']
        device_type = point['deviceType']
        
        # Select best strategy
        strategy_info = self.strategy_selection.select_strategy(point)
        
        # Try to get mapping from memory
        enos_point, confidence, reason = self.memory_system.get_best_mapping(
            point_name, device_type, strategy_info['details']['confidence_threshold']
        )
        
        # If memory-based mapping is successful
        if enos_point and confidence >= strategy_info['details']['confidence_threshold']:
            return {
                'success': True,
                'suggested_mapping': enos_point,
                'confidence': confidence,
                'reason': reason,
                'strategy': strategy_info['strategy'],
                'source': 'memory'
            }
        
        # Otherwise, return recommendation to use the selected strategy
        return {
            'success': True,
            'suggested_mapping': None,
            'confidence': 0.0,
            'reason': 'No confident mapping found in memory',
            'strategy': strategy_info['strategy'],
            'strategy_details': strategy_info,
            'source': 'strategy_selection'
        }
    
    def analyze_patterns(self, points: List[Dict]) -> Dict:
        """
        Analyze patterns in a group of points to provide insights for mapping.
        
        Args:
            points: List of points to analyze
            
        Returns:
            Analysis results with pattern insights and recommended strategy
        """
        # Safely handle empty input
        if not points:
            return {
                'success': True,
                'insights': [],
                'patterns': {},
                'recommended_strategy': 'direct_semantic'
            }
            
        try:
            # Extract point names for analysis
            point_names = [p.get('pointName', '') for p in points if p.get('pointName')]
            device_types = set(p.get('deviceType', '') for p in points if p.get('deviceType'))
            
            # Default device type if multiple or none found
            primary_device_type = list(device_types)[0] if len(device_types) == 1 else "UNKNOWN"
            
            # Use pattern analysis to extract patterns
            patterns_result = self.pattern_analysis.extract_patterns(points)
            
            # Determine recommended strategy based on pattern analysis
            if len(point_names) >= 5:
                # If enough points, use more sophisticated strategy
                recommended_strategy = 'contextual_pattern'
            else:
                # For fewer points, use direct semantic approach
                recommended_strategy = 'direct_semantic'
                
            # Generate basic insights
            insights = [
                f"Analyzed {len(points)} points of device type '{primary_device_type}'",
                f"Recommended mapping strategy: {recommended_strategy}"
            ]
            
            # Add pattern-based insights if available
            if patterns_result and 'common_prefixes' in patterns_result:
                prefixes = patterns_result.get('common_prefixes', [])
                if prefixes:
                    insights.append(f"Detected common prefixes: {', '.join(prefixes[:3])}")
                    
            if patterns_result and 'common_patterns' in patterns_result:
                patterns = patterns_result.get('common_patterns', [])
                if patterns:
                    insights.append(f"Detected common patterns: {', '.join(patterns[:3])}")
            
            return {
                'success': True,
                'insights': insights,
                'patterns': patterns_result,
                'recommended_strategy': recommended_strategy
            }
            
        except Exception as e:
            # Safely handle errors
            return {
                'success': False,
                'error': str(e),
                'insights': [f"Error during pattern analysis: {str(e)}"],
                'recommended_strategy': 'direct_semantic'  # Default to simplest strategy on error
            }
    
    def analyze_mappings(self, mappings: List[Dict]) -> Dict:
        """
        Analyze a batch of mappings to extract patterns and insights.
        
        Args:
            mappings: List of mappings to analyze
            
        Returns:
            Analysis results with patterns and insights
        """
        # Extract points data from mappings
        points = []
        for mapping in mappings:
            if 'original' in mapping:
                points.append(mapping['original'])
        
        # Perform pattern analysis
        patterns = self.pattern_analysis.extract_patterns(points)
        
        # Identify pattern families
        pattern_families = self.pattern_analysis.identify_pattern_families(mappings)
        
        # Calculate quality statistics
        quality_stats = self._calculate_quality_stats(mappings)
        
        # Get strategy statistics
        strategy_stats = self.strategy_selection.get_strategy_stats()
        
        # Combine results
        analysis = {
            'patterns': patterns,
            'pattern_families': pattern_families,
            'quality_stats': quality_stats,
            'strategy_stats': strategy_stats,
            'memory_stats': self.memory_system.get_pattern_statistics(),
            'insights': self._generate_insights(patterns, quality_stats, strategy_stats)
        }
        
        return analysis
    
    def _count_similar_mappings(self, point_name: str, device_type: str) -> int:
        """
        Count mappings similar to the given point.
        
        Args:
            point_name: Point name
            device_type: Device type
            
        Returns:
            Count of similar mappings
        """
        if not point_name or not device_type:
            return 0
            
        similar_patterns = self.memory_system.retrieve_similar_patterns(
            point_name, device_type, threshold=0.5
        )
        
        return len(similar_patterns)
    
    def _calculate_quality_stats(self, mappings: List[Dict]) -> Dict:
        """
        Calculate quality statistics for a set of mappings.
        
        Args:
            mappings: List of mappings
            
        Returns:
            Quality statistics
        """
        quality_counts = {
            'excellent': 0,
            'good': 0,
            'fair': 0,
            'poor': 0,
            'unacceptable': 0
        }
        
        device_quality = {}
        total_mappings = 0
        
        for mapping in mappings:
            reflection = mapping.get('reflection', {})
            quality = reflection.get('quality', {})
            quality_level = quality.get('quality_level', 'fair')
            device_type = mapping.get('original', {}).get('deviceType', 'unknown')
            
            quality_counts[quality_level] = quality_counts.get(quality_level, 0) + 1
            total_mappings += 1
            
            # Track quality by device type
            if device_type not in device_quality:
                device_quality[device_type] = {level: 0 for level in quality_counts.keys()}
                device_quality[device_type]['total'] = 0
                
            device_quality[device_type][quality_level] += 1
            device_quality[device_type]['total'] += 1
        
        # Calculate percentages
        quality_percentages = {}
        for level, count in quality_counts.items():
            quality_percentages[level] = count / max(total_mappings, 1) * 100
            
        # Calculate average scores by device type
        device_scores = {}
        for device, stats in device_quality.items():
            if stats['total'] > 0:
                score = (
                    (stats['excellent'] * 1.0) +
                    (stats['good'] * 0.8) +
                    (stats['fair'] * 0.6) +
                    (stats['poor'] * 0.4) +
                    (stats['unacceptable'] * 0.2)
                ) / stats['total']
                device_scores[device] = score
        
        return {
            'counts': quality_counts,
            'percentages': quality_percentages,
            'by_device_type': device_quality,
            'device_scores': device_scores,
            'total_mappings': total_mappings
        }
    
    def _generate_insights(self, patterns: Dict, quality_stats: Dict, strategy_stats: Dict) -> List[str]:
        """
        Generate insights from analysis results.
        
        Args:
            patterns: Pattern analysis results
            quality_stats: Quality statistics
            strategy_stats: Strategy statistics
            
        Returns:
            List of insights
        """
        insights = []
        
        # Insight: Common mapping patterns
        if patterns and 'common_prefixes' in patterns and patterns['common_prefixes']:
            top_prefixes = patterns['common_prefixes'][:3]
            prefix_insight = f"Common point name prefixes: {', '.join([p[0] for p in top_prefixes])}"
            insights.append(prefix_insight)
        
        # Insight: Quality distribution
        if quality_stats and 'percentages' in quality_stats:
            percentages = quality_stats['percentages']
            if percentages.get('excellent', 0) + percentages.get('good', 0) > 70:
                insights.append("Majority of mappings have excellent or good quality.")
            elif percentages.get('poor', 0) + percentages.get('unacceptable', 0) > 30:
                insights.append("Significant portion of mappings have poor or unacceptable quality.")
        
        # Insight: Device-specific quality
        if quality_stats and 'device_scores' in quality_stats:
            device_scores = quality_stats['device_scores']
            if device_scores:
                best_device = max(device_scores.items(), key=lambda x: x[1])
                worst_device = min(device_scores.items(), key=lambda x: x[1])
                
                if best_device[1] > 0.7:
                    insights.append(f"{best_device[0]} devices have the highest mapping quality.")
                    
                if worst_device[1] < 0.5 and worst_device[0] != best_device[0]:
                    insights.append(f"{worst_device[0]} devices have challenges with mapping quality.")
        
        # Insight: Strategy effectiveness
        if strategy_stats:
            best_strategies = []
            for strategy, stats in strategy_stats.items():
                if stats.get('total_uses', 0) > 5 and stats.get('success_rate', 0) > 0.8:
                    best_strategies.append(strategy)
                    
            if best_strategies:
                strategy_names = [strategy_stats[s].get('name', s) for s in best_strategies[:2]]
                insights.append(f"Most effective strategies: {', '.join(strategy_names)}")
        
        # Limit to 5 insights
        return insights[:5]
    
    def get_reflection_stats(self) -> Dict:
        """
        Get overall reflection system statistics.
        
        Returns:
            Reflection system statistics
        """
        # Calculate strategy success rates
        strategy_success_rates = {}
        for strategy, stats in self.reflection_stats['strategy_uses'].items():
            if stats['total'] > 0:
                strategy_success_rates[strategy] = stats['success'] / stats['total']
        
        # Combine with memory stats
        memory_stats = self.memory_system.get_pattern_statistics()
        
        return {
            'total_reflections': self.reflection_stats['total_reflections'],
            'quality_distribution': self.reflection_stats['quality_levels'],
            'strategy_success_rates': strategy_success_rates,
            'memory_stats': memory_stats
        }