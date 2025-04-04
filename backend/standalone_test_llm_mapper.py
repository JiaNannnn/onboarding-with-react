"""
Standalone test for the LLM-driven BMS point mapping logic.

This script tests the core functionality of our implementation
without importing the actual module, to avoid dependency issues.
"""

import re

# Key mapping dictionary for testing
DEVICE_PREFIX_MAPPING = {
    'FCU': 'FCU',
    'AHU': 'AHU',
    'VAV': 'VAV',
    'CHILLER': 'CH',
    'CH': 'CH',
    'CHPL': 'CH',
    'BOILER': 'BOIL',
    'BOIL': 'BOIL',
    'CWP': 'CWP',
    'CHWP': 'CHWP',
    'HWP': 'HWP',
    'PUMP': 'PUMP',
    'CT': 'CT',
    'COOLING_TOWER': 'CT',
    'RTU': 'RTU',
    'METER': 'METER',
    'DPM': 'DPM',
    'EF': 'EF',
    'EXHAUST_FAN': 'EF',
    'PAU': 'PAU',
    'WST': 'WST',
    'ENERGY': 'ENERGY',
    'POWER': 'ENERGY',
    'OTHER': 'OTHER',
    'UNKNOWN': 'UNKNOWN'
}

# Core functions from our implementation

def get_expected_enos_prefix(device_type: str) -> str:
    """Get the expected EnOS prefix for a device type."""
    device_type_upper = device_type.upper()
    
    # First check for exact match
    if device_type_upper in DEVICE_PREFIX_MAPPING:
        return DEVICE_PREFIX_MAPPING[device_type_upper]
    
    # Then check for partial match
    for key, value in DEVICE_PREFIX_MAPPING.items():
        if key in device_type_upper:
            return value
    
    # If no match, return the input as fallback
    return device_type_upper

def infer_device_type(point_name: str) -> str:
    """Infer device type from point name."""
    if not point_name:
        return "UNKNOWN"
        
    # First try to extract prefix before underscore or dot
    parts = point_name.split('_', 1)
    if len(parts) > 1:
        prefix = parts[0].upper()
        # Check if this is a known device type prefix
        if prefix in {"AHU", "FCU", "CT", "CH", "CHPL", "PUMP", "CWP", "CHWP", "HWP", "VAV", "DPM", "METER", "ENERGY"}:
            return prefix
    
    # If not found with underscore, try with dot
    parts = point_name.split('.', 1)
    if len(parts) > 1:
        # Check for pattern like "CT_1" before the dot
        prefix_parts = parts[0].split('_', 1)
        if prefix_parts:
            prefix = prefix_parts[0].upper()
            if prefix in {"AHU", "FCU", "CT", "CH", "CHPL", "PUMP", "CWP", "CHWP", "HWP", "VAV", "DPM", "METER", "ENERGY"}:
                return prefix
    
    # Based on point name content
    point_lower = point_name.lower()
    
    if "ahu" in point_lower or "air handler" in point_lower:
        return "AHU"
    elif "fcu" in point_lower or "fan coil" in point_lower:
        return "FCU"
    elif "vav" in point_lower:
        return "VAV"
    elif "ct" in point_lower or "cooling tower" in point_lower:
        return "CT"
    elif "chiller" in point_lower or "chw" in point_lower or "chilled water" in point_lower:
        return "CHILLER"
    elif "boiler" in point_lower or "hot water" in point_lower or "hw" in point_lower:
        return "BOILER"
    elif "chwp" in point_lower:
        return "CHWP"
    elif "cwp" in point_lower:
        return "CWP"
    elif "hwp" in point_lower:
        return "HWP"
    elif "pump" in point_lower:
        return "PUMP"
    elif "dpm" in point_lower or "meter" in point_lower:
        return "METER"
    elif "energy" in point_lower or "kw" in point_lower or "kwh" in point_lower:
        return "ENERGY"
    
    # Default
    return "UNKNOWN"

def extract_pattern(point_name: str) -> str:
    """Extract a standardized pattern from a point name."""
    if not point_name:
        return ""
        
    # Convert to lowercase for standardization
    name = point_name.lower()
    
    # Replace common separators with a standard one
    name = name.replace('-', '_').replace('.', '_').replace(' ', '_')
    
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

def validate_enos_format(enos_point: str, device_type: str) -> bool:
    """Validate EnOS point name format."""
    if not enos_point:
        return False
        
    parts = enos_point.split('_')
    if len(parts) < 3:
        return False
    
    # Validate prefix
    actual_prefix = parts[0]
    expected_prefix = get_expected_enos_prefix(device_type)
    
    if actual_prefix != expected_prefix:
        return False
        
    # Validate category
    if parts[1] not in {'raw', 'calc'}:
        return False
        
    # Validate measurement type
    valid_measurements = {
        'temp', 'power', 'status', 'speed', 'pressure', 'flow', 'humidity', 'position',
        'energy', 'current', 'voltage', 'frequency', 'level', 'occupancy', 'setpoint',
        'mode', 'command', 'alarm', 'damper', 'valve', 'state', 'volume'
    }
    
    if parts[2] not in valid_measurements:
        return False
        
    return True

def apply_fallback_strategy(point_name: str, device_type: str) -> str:
    """Apply fallback strategy for mapping failures."""
    # Simple pattern matching
    point_lowercase = point_name.lower()
    
    # Extract possible measurement type
    measurement_type = "status"  # Default
    
    if "temp" in point_lowercase or "temperature" in point_lowercase:
        measurement_type = "temp"
    elif "kw" in point_lowercase and not "kwh" in point_lowercase:
        measurement_type = "power"
    elif "kwh" in point_lowercase or "energy" in point_lowercase:
        measurement_type = "energy"
    elif "pressure" in point_lowercase or "pres" in point_lowercase:
        measurement_type = "pressure"
    elif "flow" in point_lowercase:
        measurement_type = "flow"
    elif "humid" in point_lowercase or "rh" in point_lowercase:
        measurement_type = "humidity"
    elif "status" in point_lowercase or "state" in point_lowercase or "run" in point_lowercase:
        measurement_type = "status"
    
    # Construct minimal valid EnOS point
    device_prefix = get_expected_enos_prefix(device_type)
    return f"{device_prefix}_raw_{measurement_type}"

# Test functions

def test_device_prefix_mapping():
    """Test prefix mapping functionality."""
    test_cases = [
        ("AHU", "AHU"),
        ("CHILLER", "CH"),
        ("ENERGY", "ENERGY"),
        ("ahu", "AHU"),  # case insensitivity
        ("energy", "ENERGY"),  # case insensitivity
        ("AHU_1", "AHU"),  # partial match
        ("CHILLER_PLANT", "CH"),  # partial match
        ("UNKNOWN_DEVICE", "UNKNOWN_DEVICE")  # fallback
    ]
    
    for input_value, expected_output in test_cases:
        result = get_expected_enos_prefix(input_value)
        if result == expected_output:
            print(f"✅ get_expected_enos_prefix('{input_value}') = '{result}' as expected")
        else:
            print(f"❌ get_expected_enos_prefix('{input_value}') = '{result}', expected '{expected_output}'")

def test_device_type_inference():
    """Test device type inference from point names."""
    test_cases = [
        ("AHU_123.Temperature", "AHU"),
        ("FCU_Zone1_Temperature", "FCU"),
        ("ZoneTemperature_AHU", "AHU"),
        ("ChillerSupplyTemp", "CHILLER"),
        ("TotalCwpEnergy-kWh", "ENERGY"),
        ("TotalPower-kW", "ENERGY"),
        ("Energy.TotalCwp-kW", "ENERGY"),
        ("Energy.TotalConsumption-kWh", "ENERGY")
    ]
    
    for input_value, expected_output in test_cases:
        result = infer_device_type(input_value)
        if result == expected_output:
            print(f"✅ infer_device_type('{input_value}') = '{result}' as expected")
        else:
            print(f"❌ infer_device_type('{input_value}') = '{result}', expected '{expected_output}'")

def test_pattern_extraction():
    """Test pattern extraction from point names."""
    test_cases = [
        ("Temperature.ReturnAir", "temperature_returnair"),
        ("Zone1.Temp", "zone1_temp"),
        ("AHU1.Supply-Temp", "ahu1_supply_temp"),
        ("Energy.TotalCwp-kW", "energy_totalcwp_power"),
        ("Energy.TotalPower-kWh", "energy_totalpower_energy"),
        ("Energy.TotalChwp-kW", "energy_chilled_water_pump_power")
    ]
    
    for input_value, expected_output in test_cases:
        result = extract_pattern(input_value)
        if result == expected_output:
            print(f"✅ extract_pattern('{input_value}') = '{result}' as expected")
        else:
            print(f"❌ extract_pattern('{input_value}') = '{result}', expected '{expected_output}'")

def test_enos_format_validation():
    """Test EnOS format validation."""
    test_cases = [
        ("AHU_raw_temp_rt", "AHU", True),
        ("CH_raw_status", "CHILLER", True),
        ("ENERGY_raw_power_total", "ENERGY", True),
        ("CH_raw_temp_rt", "AHU", False),  # wrong prefix
        ("AHU_invalid_temp_rt", "AHU", False),  # wrong category
        ("AHU_raw_invalid_rt", "AHU", False),  # wrong measurement
        ("AHU_raw", "AHU", False)  # too few parts
    ]
    
    for enos_point, device_type, expected_result in test_cases:
        result = validate_enos_format(enos_point, device_type)
        if result == expected_result:
            print(f"✅ validate_enos_format('{enos_point}', '{device_type}') = {result} as expected")
        else:
            print(f"❌ validate_enos_format('{enos_point}', '{device_type}') = {result}, expected {expected_result}")

def test_fallback_strategy():
    """Test fallback mapping strategy."""
    test_cases = [
        ("Temperature.ReturnAir", "AHU", "AHU_raw_temp"),
        ("Zone1.Humidity", "FCU", "FCU_raw_humidity"),
        ("Energy.TotalCwp-kW", "ENERGY", "ENERGY_raw_power"),
        ("Energy.TotalPower-kWh", "ENERGY", "ENERGY_raw_energy"),
        ("Supply.Pressure", "AHU", "AHU_raw_pressure"),
        ("Status.Fan1", "AHU", "AHU_raw_status")
    ]
    
    for point_name, device_type, expected_result in test_cases:
        result = apply_fallback_strategy(point_name, device_type)
        if result == expected_result:
            print(f"✅ apply_fallback_strategy('{point_name}', '{device_type}') = '{result}' as expected")
        else:
            print(f"❌ apply_fallback_strategy('{point_name}', '{device_type}') = '{result}', expected '{expected_result}'")

def test_energy_points_special_cases():
    """Test special cases for energy points that were problematic before."""
    energy_points = [
        "Energy.TotalCwp-kW",
        "Energy.TotalChwp-kW",
        "Energy.TotalConsumption-kWh",
        "TotalEnergyUse-kWh",
        "PowerMeter.ChillerDemand"
    ]
    
    print("\nEnergy Points Special Testing:")
    
    # Test device type inference
    print("\nDevice Type Inference:")
    for point in energy_points:
        device_type = infer_device_type(point)
        print(f"  {point} -> {device_type}")
        if "energy" in point.lower() or "kw" in point.lower() or "kwh" in point.lower():
            if device_type != "ENERGY" and "meter" not in point.lower():
                print(f"    ⚠️ Expected ENERGY for {point}")
    
    # Test pattern extraction
    print("\nPattern Extraction:")
    for point in energy_points:
        pattern = extract_pattern(point)
        print(f"  {point} -> {pattern}")
        if "kw" in point.lower() and "kwh" not in point.lower():
            if "_power" not in pattern:
                print(f"    ⚠️ Expected '_power' in pattern for {point}")
        if "kwh" in point.lower():
            if "_energy" not in pattern:
                print(f"    ⚠️ Expected '_energy' in pattern for {point}")
    
    # Test fallback mapping
    print("\nFallback Mapping:")
    for point in energy_points:
        device_type = infer_device_type(point)
        fallback = apply_fallback_strategy(point, device_type)
        print(f"  {point} -> {fallback}")
        
        # Validate the fallback mapping
        is_valid = validate_enos_format(fallback, device_type)
        print(f"    Valid format: {is_valid}")
        
        # Check device type matching
        expected_prefix = get_expected_enos_prefix(device_type)
        actual_prefix = fallback.split('_')[0]
        if actual_prefix != expected_prefix:
            print(f"    ⚠️ Prefix mismatch: expected {expected_prefix}, got {actual_prefix}")

def print_separator():
    """Print a separator line for better readability."""
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    print("Starting standalone tests for LLM Mapper logic...")
    print_separator()
    
    print("Testing device prefix mapping...")
    test_device_prefix_mapping()
    print_separator()
    
    print("Testing device type inference...")
    test_device_type_inference()
    print_separator()
    
    print("Testing pattern extraction...")
    test_pattern_extraction()
    print_separator()
    
    print("Testing EnOS format validation...")
    test_enos_format_validation()
    print_separator()
    
    print("Testing fallback strategy...")
    test_fallback_strategy()
    print_separator()
    
    print("Testing energy points special cases...")
    test_energy_points_special_cases()
    print_separator()
    
    print("Testing complete.")