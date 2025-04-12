"""
Protocol Engine Module.

This module implements the core engine for applying the HVAC Model Context Protocol,
managing context injection, ontology and knowledge base access, and reasoning template usage.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union

# Modified imports for standalone package
from hvac_mcp.ontology import load_ontology, ontology_to_markdown
from hvac_mcp.kb import load_knowledge_base, kb_to_markdown
from hvac_mcp.templates import (
    get_reasoning_template,
    format_protocol_context,
    get_protocol_steps,
    parse_llm_response
)

logger = logging.getLogger(__name__)


class ProtocolEngine:
    """
    Core engine for the HVAC Model Context Protocol.
    
    This class manages protocol context creation, ontology and knowledge base access,
    and integration with the reasoning engine.
    """
    
    def __init__(
        self,
        ontology_path: Optional[str] = None,
        kb_path: Optional[str] = None,
        version: str = "1.0.0"
    ):
        """
        Initialize the Protocol Engine.
        
        Args:
            ontology_path: Path to the ontology file (optional, default: use built-in)
            kb_path: Path to the knowledge base file (optional, default: use built-in)
            version: Protocol version string
        """
        self.version = version
        self.ontology = load_ontology(ontology_path)
        self.kb = load_knowledge_base(kb_path)
        logger.info(f"HVAC Model Context Protocol Engine v{version} initialized")
        logger.info(f"Using ontology version: {self.ontology.get('version', 'unknown')}")
        logger.info(f"Using knowledge base version: {self.kb.get('version', 'unknown')}")
    
    def extract_prefixes(self, points: List[str]) -> List[str]:
        """
        Extract potential equipment prefixes from a list of point names with enhanced pattern recognition.
        
        Args:
            points: List of point names
            
        Returns:
            List of potential prefixes
        """
        prefixes = []
        
        for point in points:
            # Common prefix patterns: AHU-1, FCU-2, VAV-3-ZN4, CHWP_1_VSD_HeatSinkTemp
            # First, normalize point name
            point_upper = point.upper()
            
            # Pattern 1: Hierarchical notation (CH-SYS-1.CHWP)
            if '.' in point:
                parts = point.split('.')
                # Add the parent system
                if len(parts) >= 1:
                    prefixes.append(parts[0])
                    
                    # Add parent.child for components
                    if len(parts) >= 2:
                        prefixes.append(f"{parts[0]}.{parts[1]}")
                        
                        # Special case for duplicated hierarchy like FCU.FCU_05_01_8
                        if parts[0] == parts[1].split('_')[0]:
                            prefixes.append(parts[1].split('_')[0])
                            
                            # Also add with the numeric part
                            component_parts = re.split(r'[_-]', parts[1])
                            if len(component_parts) >= 2 and component_parts[1].isdigit():
                                prefixes.append(f"{component_parts[0]}_{component_parts[1]}")
            
            # Pattern 2: Equipment with underscore separators (CHWP_1_VSD_HeatSinkTemp)
            elif '_' in point:
                parts = point.split('_')
                # Add the base equipment type
                prefixes.append(parts[0])
                
                # If second part is numeric, add equipment with number
                if len(parts) > 1 and parts[1].isdigit():
                    prefixes.append(f"{parts[0]}_{parts[1]}")
            
            # Pattern 3: Standard equipment with number (AHU-1, CH-SYS-1)
            elif '-' in point:
                # Extract prefix before the first number
                match = re.match(r'^([A-Za-z\-]+\d*)', point)
                if match:
                    prefixes.append(match.group(1))
                    
                    # Also add system type without number
                    system_type = re.match(r'^([A-Za-z\-]+)-\d+', point)
                    if system_type:
                        prefixes.append(system_type.group(1))
            
            # Pattern 4: Check against known system types in KB and ontology
            for system_id in self.ontology.get("systems", {}).values():
                sys_id = system_id.get("id", "")
                if sys_id and sys_id in point_upper:
                    prefixes.append(sys_id)
                    
                    # Check for numeric suffix
                    match = re.search(f"{sys_id}[-_.]?(\\d+)", point_upper)
                    if match:
                        prefixes.append(f"{sys_id}-{match.group(1)}")
            
            # Pattern 5: Check against specific naming patterns in the KB
            for system_id, patterns in self.kb.get("naming_patterns", {}).items():
                for pattern in patterns:
                    match = re.match(pattern, point_upper)
                    if match:
                        prefixes.append(system_id)
            
            # Pattern 6: Check against hierarchical patterns in the KB
            for system_id, pattern_data in self.kb.get("hierarchical_patterns", {}).items():
                base_pattern = pattern_data.get("pattern", "")
                match = re.search(base_pattern, point_upper)
                if match:
                    prefixes.append(f"{system_id}-{match.group(1)}")
                    prefixes.append(system_id)
                    
                    # Check for component in hierarchical name
                    for component in pattern_data.get("components", []):
                        if component in point_upper:
                            prefixes.append(f"{system_id}.{component}")
            
            # Pattern 7: Special case for VSD in heat sink temperature
            if "VSD" in point_upper and "HEATSINK" in point_upper:
                # Extract equipment before VSD
                match = re.match(r'^([A-Za-z]+)_\d+_VSD', point_upper)
                if match:
                    equipment = match.group(1)
                    prefixes.append(equipment)
        
        # Remove duplicates and return
        return list(set(prefixes))
    
    def extract_keywords(self, points: List[str]) -> List[str]:
        """
        Extract potential keywords from a list of point names.
        
        Args:
            points: List of point names
            
        Returns:
            List of potential keywords
        """
        keywords = []
        
        # Get all keywords from the knowledge base
        all_kb_keywords = self.kb.get("keywords", {}).keys()
        
        for point in points:
            point_upper = point.upper()
            
            # Check for abbreviations
            for abbr in self.kb.get("abbreviations", {}):
                if abbr in point_upper:
                    keywords.append(abbr)
            
            # Check for keywords
            for keyword in all_kb_keywords:
                if keyword.upper() in point_upper:
                    keywords.append(keyword)
            
            # Check for measurement types
            for measurement in self.kb.get("units", {}):
                if measurement.upper() in point_upper:
                    keywords.append(measurement)
        
        return list(set(keywords))  # Remove duplicates
    
    def calculate_system_frequency(self, prefixes: List[str]) -> Dict[str, int]:
        """
        Calculate frequency of potential system types based on prefixes.
        
        Args:
            prefixes: List of extracted prefixes
            
        Returns:
            Dictionary of system types and their frequency counts
        """
        system_counts = {}
        
        # Initialize counts for all system types
        for system_key, system in self.ontology.get("systems", {}).items():
            system_id = system.get("id")
            if system_id:
                system_counts[system_id] = 0
        
        # Count occurrences of each system type in the prefixes
        for prefix in prefixes:
            prefix_upper = prefix.upper()
            
            # Direct match with system ID
            for system_key, system in self.ontology.get("systems", {}).items():
                system_id = system.get("id")
                if system_id and system_id == prefix_upper:
                    system_counts[system_id] += 1
                elif system_id and prefix_upper.startswith(f"{system_id}-"):
                    system_counts[system_id] += 1
            
            # Check against naming patterns
            for system_id, patterns in self.kb.get("naming_patterns", {}).items():
                for pattern in patterns:
                    if re.match(pattern, prefix_upper):
                        if system_id in system_counts:
                            system_counts[system_id] += 1
        
        return system_counts
    
    def _get_flattened_system_hierarchy(self) -> Dict[str, Any]:
        """
        Flatten the hierarchical system ontology for easier lookup.
        
        Returns:
            Dictionary of system types with their properties
        """
        flattened = {}
        
        for system_key, system in self.ontology.get("systems", {}).items():
            system_id = system.get("id")
            if system_id:
                flattened[system_id] = {
                    "name": system.get("name"),
                    "components": []
                }
                
                # Add components
                for component_key, component in system.get("components", {}).items():
                    component_id = component.get("id")
                    if component_id:
                        flattened[system_id]["components"].append({
                            "id": component_id,
                            "name": component.get("name")
                        })
        
        return flattened
    
    def select_ontology_branches(self, system_frequency: Dict[str, int], max_branches: int = 3) -> Dict[str, Any]:
        """
        Select the most relevant ontology branches based on system frequency.
        
        Args:
            system_frequency: Dictionary of system types and their frequency counts
            max_branches: Maximum number of branches to return
            
        Returns:
            Subset of the ontology containing the most relevant branches
        """
        # Sort systems by frequency
        sorted_systems = sorted(system_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Select top N systems
        top_systems = sorted_systems[:max_branches]
        
        # Create subset of ontology
        subset = {
            "version": self.ontology.get("version", "1.0.0"),
            "systems": {},
            "relationships": {
                "upstream_downstream": [],
                "cross_system": []
            },
            "point_types": self.ontology.get("point_types", {})
        }
        
        # Add selected systems to subset
        for system_id, _ in top_systems:
            for system_key, system in self.ontology.get("systems", {}).items():
                if system.get("id") == system_id:
                    subset["systems"][system_key] = system
        
        # Add relationships involving selected systems
        for relationship in self.ontology.get("relationships", {}).get("upstream_downstream", []):
            upstream = relationship.get("upstream")
            downstream = relationship.get("downstream")
            
            if any(system_id == upstream or system_id == downstream.split(".")[0] 
                  for system_id, _ in top_systems):
                subset["relationships"]["upstream_downstream"].append(relationship)
        
        return subset
    
    def select_kb_entries(self, system_frequency: Dict[str, int], keywords: List[str]) -> Dict[str, Any]:
        """
        Select the most relevant knowledge base entries.
        
        Args:
            system_frequency: Dictionary of system types and their frequency counts
            keywords: List of potential keywords from points
            
        Returns:
            Subset of the knowledge base containing relevant entries
        """
        # Sort systems by frequency
        sorted_systems = sorted(system_frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Get top system IDs
        top_system_ids = [system_id for system_id, _ in sorted_systems if system_frequency[system_id] > 0]
        
        # Create relevance filter for KB
        relevance_filter = top_system_ids + keywords
        
        # Create subset of KB by filtering with relevance filter
        subset = {
            "version": self.kb.get("version", "1.0.0"),
            "abbreviations": {},
            "keywords": {},
            "units": {},
            "contradictions": {},
            "naming_patterns": {}
        }
        
        # Filter abbreviations
        for abbr, full_form in self.kb.get("abbreviations", {}).items():
            if any(keyword.upper() in abbr or keyword.upper() in full_form.upper() 
                   for keyword in relevance_filter):
                subset["abbreviations"][abbr] = full_form
        
        # Filter keywords
        for keyword, classification in self.kb.get("keywords", {}).items():
            if any(rf.lower() in keyword.lower() for rf in relevance_filter):
                subset["keywords"][keyword] = classification
        
        # Filter units - include all for now as they're generally relevant
        subset["units"] = self.kb.get("units", {})
        
        # Filter contradictions
        for device_type, contradictions in self.kb.get("contradictions", {}).items():
            if device_type in top_system_ids:
                subset["contradictions"][device_type] = contradictions
        
        # Filter naming patterns
        for device_type, patterns in self.kb.get("naming_patterns", {}).items():
            if device_type in top_system_ids:
                subset["naming_patterns"][device_type] = patterns
        
        return subset
    
    def prioritize_context(self, points: List[str], task_type: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Dynamically selects most relevant protocol sections based on points and task.
        
        Args:
            points: List of points to analyze
            task_type: Type of task being performed (e.g., "point_name_analysis", "group_verification")
            
        Returns:
            Tuple of (ontology_subset, kb_subset)
        """
        # Extract prefixes and keywords from points
        prefixes = self.extract_prefixes(points)
        keywords = self.extract_keywords(points)
        
        # Calculate frequency of system types
        system_frequency = self.calculate_system_frequency(prefixes)
        
        # Select ontology branches and KB entries
        ontology_subset = self.select_ontology_branches(system_frequency)
        kb_subset = self.select_kb_entries(system_frequency, keywords)
        
        return ontology_subset, kb_subset
    
    def generate_context(self, points: List[str], task_type: str) -> str:
        """
        Generate the protocol context for a specific task and set of points.
        
        Args:
            points: List of points to analyze
            task_type: Type of task being performed
            
        Returns:
            Formatted protocol context string
        """
        # Get relevant ontology and KB subsets
        ontology_subset, kb_subset = self.prioritize_context(points, task_type)
        
        # Convert to markdown
        ontology_md = ontology_to_markdown(ontology_subset)
        kb_md = kb_to_markdown(kb_subset)
        
        # Format as protocol context
        context = format_protocol_context(
            task_type,
            ontology_md,
            kb_md,
            protocol_version=self.version
        )
        
        return context
    
    def extract_reasoning_from_response(self, response: str, task_type: str) -> Dict[str, Any]:
        """
        Extract structured reasoning from an LLM response based on the protocol template.
        
        Args:
            response: LLM response text
            task_type: Type of task that was performed
            
        Returns:
            Dictionary with extracted reasoning elements
        """
        return parse_llm_response(response, task_type) 