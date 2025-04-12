"""
Text processing utilities for HVAC point names and descriptions.
"""

import re
from typing import List, Optional, Tuple

def clean_point_name(point_name: str) -> str:
    """
    Clean and normalize a point name for consistent processing.
    
    Args:
        point_name: Raw point name to clean
        
    Returns:
        Cleaned point name
    """
    # Remove leading/trailing whitespace
    cleaned = point_name.strip()
    
    # Remove any extraneous spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Convert to uppercase for consistent matching
    cleaned = cleaned.upper()
    
    return cleaned

def extract_common_prefix(point_names: List[str]) -> Optional[str]:
    """
    Extract a common prefix from a list of point names.
    
    Args:
        point_names: List of point names to analyze
        
    Returns:
        Common prefix if found, None otherwise
    """
    if not point_names:
        return None
    
    # Clean all point names
    cleaned_names = [clean_point_name(name) for name in point_names]
    
    # Find potential delimiters in the names
    delimiters = ['.', '-', '_']
    delimiter_counts = {d: sum(d in name for name in cleaned_names) for d in delimiters}
    
    # Select the most common delimiter
    primary_delimiter = max(delimiters, key=lambda d: delimiter_counts[d]) if any(delimiter_counts.values()) else None
    
    if not primary_delimiter:
        return None
    
    # Extract prefixes using the primary delimiter
    prefixes = []
    for name in cleaned_names:
        parts = name.split(primary_delimiter)
        if len(parts) > 1:
            # Include the first part and potentially numeric identifiers
            prefix_parts = []
            for part in parts:
                prefix_parts.append(part)
                # If we hit a numeric part, that's typically the end of the prefix
                if re.search(r'\d+', part):
                    break
            prefixes.append(primary_delimiter.join(prefix_parts))
    
    # Count occurrences of each prefix
    prefix_counts = {}
    for prefix in prefixes:
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    # Return the most common prefix if it appears in at least 70% of names
    if prefix_counts:
        most_common = max(prefix_counts.items(), key=lambda x: x[1])
        if most_common[1] / len(cleaned_names) >= 0.7:
            return most_common[0]
    
    return None

def split_point_name(point_name: str) -> Tuple[str, str]:
    """
    Split a point name into prefix and suffix.
    
    Args:
        point_name: Point name to split
        
    Returns:
        Tuple of (prefix, suffix)
    """
    # Clean the point name
    cleaned = clean_point_name(point_name)
    
    # Common delimiters to check
    delimiters = ['.', '-', '_']
    
    # Try to split by each delimiter
    for delimiter in delimiters:
        if delimiter in cleaned:
            parts = cleaned.split(delimiter, 1)
            return parts[0], parts[1]
    
    # If no delimiter found, check for common patterns
    # Pattern: letters followed by numbers, then more letters
    pattern = re.match(r'([A-Za-z]+\d+)([A-Za-z].+)', cleaned)
    if pattern:
        return pattern.group(1), pattern.group(2)
    
    # If still no pattern found, assume everything is the prefix
    return cleaned, ""

def extract_numeric_id(prefix: str) -> Optional[str]:
    """
    Extract numeric identifier from a prefix.
    
    Args:
        prefix: Prefix to extract from (e.g., "AHU-1", "VAV-3A")
        
    Returns:
        Numeric ID if found, None otherwise
    """
    # Look for patterns like: 
    # - "AHU-1" -> "1"
    # - "VAV-3A" -> "3A"
    # - "FCU_2B" -> "2B"
    
    patterns = [
        r'[A-Za-z]+-(\d+[A-Za-z]*)',  # AHU-1, VAV-3A
        r'[A-Za-z]+_(\d+[A-Za-z]*)',  # FCU_2B
        r'[A-Za-z]+\.(\d+[A-Za-z]*)',  # AHU.1
        r'[A-Za-z]+(\d+[A-Za-z]*)'   # AHU1, VAV3A
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prefix)
        if match:
            return match.group(1)
    
    return None

def normalize_units(unit_str: str) -> Optional[str]:
    """
    Normalize a unit string to a standard format.
    
    Args:
        unit_str: Raw unit string
        
    Returns:
        Normalized unit string or None if not recognized
    """
    # Map of raw unit strings to normalized formats
    unit_map = {
        # Temperature
        'F': 'degF',
        'DEG F': 'degF',
        'DEGF': 'degF',
        'DEGREES F': 'degF',
        'C': 'degC',
        'DEG C': 'degC',
        'DEGC': 'degC',
        'DEGREES C': 'degC',
        'K': 'K',
        'KELVIN': 'K',
        
        # Pressure
        'PSI': 'psi',
        'PSIG': 'psi',
        'PA': 'Pa',
        'KPA': 'kPa',
        'BAR': 'bar',
        'MBAR': 'mbar',
        'INWC': 'inWC',
        'IN WC': 'inWC',
        'IN H2O': 'inWC',
        
        # Flow
        'CFM': 'cfm',
        'LPS': 'l/s',
        'L/S': 'l/s',
        'M3/H': 'm3/h',
        'M3/S': 'm3/s',
        'GPM': 'gpm',
        
        # Humidity
        '%': '%RH',
        '%RH': '%RH',
        'PCT': '%RH',
        'PERCENT': '%RH',
        
        # Position
        'PCT OPEN': '%',
        'PERCENT OPEN': '%',
        'DEG': 'deg',
        
        # Speed
        'RPM': 'rpm',
        'HZ': 'Hz',
        
        # Power
        'KW': 'kW',
        'W': 'W',
        'MW': 'MW',
        'HP': 'HP',
        
        # Energy
        'KWH': 'kWh',
        'MWH': 'MWh',
        'BTU': 'BTU',
        'MBTU': 'MBTU'
    }
    
    # Clean and normalize the input
    cleaned = unit_str.strip().upper()
    
    return unit_map.get(cleaned) 