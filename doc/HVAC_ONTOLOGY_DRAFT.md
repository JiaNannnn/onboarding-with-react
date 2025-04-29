# HVAC Ontology Draft

## Overview

This document provides a draft ontology for HVAC systems to guide the implementation of the BMS to EnOS Onboarding Tool. The ontology defines equipment types, component relationships, standard points, and naming conventions based on industry standards and common practices in building management systems.

## Equipment Hierarchy

### Primary Equipment Types

```
Building Management System
├── Chiller Plant
│   ├── Chiller
│   ├── Cooling Tower
│   ├── Chilled Water Pump
│   ├── Condenser Water Pump
│   ├── Chilled Water Valve
│   └── Condenser Water Valve
├── Air Handling System
│   ├── Air Handling Unit
│   ├── Variable Air Volume Box
│   └── Fan Coil Unit
├── Boiler Plant
│   ├── Boiler
│   ├── Hot Water Pump
│   └── Hot Water Valve
└── Terminal Units
    ├── Fan Coil Unit
    ├── Variable Air Volume Box
    └── Unit Heater
```

## Equipment Definitions

### Chiller Plant Components

#### 1. Chiller (CH)

**Description**: Mechanical device that removes heat from a liquid via vapor-compression or absorption refrigeration cycle.

**Common Abbreviations**: 
- CH
- CH-SYS
- CHILLER
- CLR

**Standard Components**:
- Compressor
- Evaporator
- Condenser
- Expansion Valve
- Controls

**Standard Points**:

| Point Name      | Description                      | Function  | BACnet Type      | Unit             |
|-----------------|----------------------------------|-----------|------------------|------------------|
| ChwSt           | Chilled Water Supply Temperature | Sensor    | analog-input     | degrees-Celsius  |
| ChwRt           | Chilled Water Return Temperature | Sensor    | analog-input     | degrees-Celsius  |
| CwSt            | Condenser Water Supply Temp      | Sensor    | analog-input     | degrees-Celsius  |
| CwRt            | Condenser Water Return Temp      | Sensor    | analog-input     | degrees-Celsius  |
| ChwFls          | Chilled Water Flow               | Sensor    | analog-input     | liters-per-second|
| CwFls           | Condenser Water Flow             | Sensor    | analog-input     | liters-per-second|
| RunStatus       | Running Status                   | Status    | binary-input     | -                |
| TripStatus      | Trip Status                      | Status    | binary-input     | -                |
| ModeStatus      | Operating Mode Status            | Status    | multi-state-input| -                |
| RunCmd          | Run Command                      | Command   | binary-output    | -                |
| ModeCmd         | Mode Command                     | Command   | multi-state-output| -               |
| ChwStSp         | Chilled Water Supply Setpoint    | Setpoint  | analog-value     | degrees-Celsius  |
| LoadSp          | Load Setpoint                    | Setpoint  | analog-value     | percent          |
| Capacity        | Capacity                         | Sensor    | analog-input     | kilowatts        |
| kW              | Power Consumption                | Sensor    | analog-input     | kilowatts        |
| kWh             | Energy Consumption               | Sensor    | analog-input     | kilowatt-hours   |

**Related Equipment**:
- Chilled Water Pump (CHWP)
- Condenser Water Pump (CWP)
- Cooling Tower (CT)
- Chilled Water Valve (CHWV)
- Condenser Water Valve (CWV)

#### 2. Cooling Tower (CT)

**Description**: Heat rejection device that rejects waste heat to the atmosphere through the cooling of water by evaporation.

**Common Abbreviations**:
- CT
- CLG-TWR
- TOWER

**Standard Components**:
- Fan
- Fill (Media)
- Basin
- Controls

**Standard Points**:

| Point Name      | Description                      | Function  | BACnet Type      | Unit             |
|-----------------|----------------------------------|-----------|------------------|------------------|
| CwSt            | Condenser Water Supply Temp      | Sensor    | analog-input     | degrees-Celsius  |
| CwRt            | Condenser Water Return Temp      | Sensor    | analog-input     | degrees-Celsius  |
| FanStatus       | Fan Status                       | Status    | binary-input     | -                |
| FanSpeed        | Fan Speed                        | Sensor    | analog-input     | percent          |
| FanCmd          | Fan Command                      | Command   | binary-output    | -                |
| FanSpeedCmd     | Fan Speed Command                | Command   | analog-output    | percent          |
| VibrationStatus | Vibration Status                 | Status    | binary-input     | -                |
| WaterLevelLow   | Water Level Low                  | Status    | binary-input     | -                |
| WaterLevelHigh  | Water Level High                 | Status    | binary-input     | -                |
| ModeStatus      | Operating Mode Status            | Status    | multi-state-input| -                |
| VSD.Hz          | VSD Frequency                    | Sensor    | analog-input     | hertz            |
| VSD.Amp         | VSD Current                      | Sensor    | analog-input     | amperes          |
| VSD.kW          | VSD Power                        | Sensor    | analog-input     | kilowatts        |
| CwStSp          | Condenser Water Supply Setpoint  | Setpoint  | analog-value     | degrees-Celsius  |

**Related Equipment**:
- Condenser Water Pump (CWP)
- Chiller (CH)

#### 3. Chilled Water Pump (CHWP)

**Description**: Pump that circulates chilled water from chillers to air handling equipment and back.

**Common Abbreviations**:
- CHWP
- CHW-P
- CHP

**Standard Components**:
- Pump Motor
- Impeller
- VSD (Variable Speed Drive)
- Controls

**Standard Points**:

| Point Name      | Description                      | Function  | BACnet Type      | Unit             |
|-----------------|----------------------------------|-----------|------------------|------------------|
| RunStatus       | Running Status                   | Status    | binary-input     | -                |
| FailStatus      | Failure Status                   | Status    | binary-input     | -                |
| RunCmd          | Run Command                      | Command   | binary-output    | -                |
| VSD.Hz          | VSD Frequency                    | Sensor    | analog-input     | hertz            |
| VSD.Amp         | VSD Current                      | Sensor    | analog-input     | amperes          |
| VSD.kW          | VSD Power                        | Sensor    | analog-input     | kilowatts        |
| VSD.Volt        | VSD Voltage                      | Sensor    | analog-input     | volts            |
| Dp              | Differential Pressure            | Sensor    | analog-input     | kilopascals      |
| DpSp            | Differential Pressure Setpoint   | Setpoint  | analog-value     | kilopascals      |
| ModeStatus      | Operating Mode Status            | Status    | multi-state-input| -                |
| SpeedCmd        | Speed Command                    | Command   | analog-output    | percent          |

**Related Equipment**:
- Chiller (CH)
- Chilled Water Valve (CHWV)

### Air Handling System Components

#### 1. Fan Coil Unit (FCU)

**Description**: A simple device consisting of a heating or cooling coil and fan, used to control the temperature in the space where it is installed.

**Common Abbreviations**:
- FCU
- FC

**Standard Components**:
- Fan
- Cooling Coil
- Heating Coil (optional)
- Filter
- Controls

**Standard Points**:

| Point Name      | Description                      | Function  | BACnet Type      | Unit             |
|-----------------|----------------------------------|-----------|------------------|------------------|
| RoomTemp        | Room Temperature                 | Sensor    | analog-input     | degrees-Celsius  |
| TempSetpoint    | Temperature Setpoint             | Setpoint  | analog-value     | degrees-Celsius  |
| FanStatus       | Fan Status                       | Status    | binary-input     | -                |
| FanOutput       | Fan Output                       | Command   | analog-output    | percent          |
| FanSpeedStatus  | Fan Speed Status                 | Status    | analog-input     | percent          |
| ValveOutput     | Valve Output                     | Command   | analog-output    | percent          |
| RunStatus       | Running Status                   | Status    | binary-input     | -                |
| TripStatus      | Trip Status                      | Status    | binary-input     | -                |
| ModeStatus      | Operating Mode Status            | Status    | multi-state-input| -                |
| ControllerStatus| Controller Status                | Status    | binary-input     | -                |
| CTL_RunStop     | Run/Stop Control                 | Command   | binary-output    | -                |
| CTL_FanSpeed    | Fan Speed Control                | Command   | analog-output    | percent          |
| CTL_CoolingValve| Cooling Valve Control            | Command   | analog-output    | percent          |
| CVControlMode   | Control Valve Control Mode       | Status    | multi-state-input| -                |

**Related Equipment**:
- None (terminal device)

## Naming Conventions

### Common Naming Patterns

#### 1. Equipment Identification Patterns

```
<EquipmentType>-<Number>
<EquipmentType>_<Number>
<EquipmentType>.<Number>
<EquipmentType><Number>
```

Examples:
- `CH-SYS-1` (Chiller System 1)
- `CT_1` (Cooling Tower 1)
- `FCU-101` (Fan Coil Unit 101)
- `AHU2` (Air Handling Unit 2)

#### 2. Point Naming Patterns

```
<EquipmentInstance>.<Component>.<Measurement>
<EquipmentInstance>_<Measurement>
<EquipmentInstance>-<Measurement>
<Component>.<EquipmentInstance>.<Measurement>
```

Examples:
- `CH-SYS-1.CH.ChwSt` (Chiller System 1, Chiller, Chilled Water Supply Temperature)
- `FCU_101_RoomTemp` (Fan Coil Unit 101 Room Temperature)
- `CT-1-FanStatus` (Cooling Tower 1 Fan Status)
- `Pump.CH-SYS-2.RunStatus` (Chiller System 2, Pump, Run Status)

#### 3. Building/Zone Based Patterns

```
<EquipmentType>_<Building>_<Floor>_<Zone>.<Measurement>
<EquipmentType>_<Building>_<Floor>.<Measurement>
```

Examples:
- `FCU_01_25.RoomTemp` (Fan Coil Unit in Building 01, Zone 25, Room Temperature)
- `FCU_05_01_7.ValveOutput` (Fan Coil Unit in Building 05, Floor 01, Zone 7, Valve Output)

## Point Classification

### 1. Point Functions

| Function | Description | Common Suffixes | BACnet Types |
|----------|-------------|----------------|--------------|
| Sensor   | Measures physical values | Temp, Pressure, Flow, Level | analog-input, binary-input, multi-state-input |
| Command  | Controls equipment operation | Cmd, Output, Control | analog-output, binary-output, multi-state-output |
| Setpoint | Desired value for operation | Sp, Setpoint, Setting | analog-value, binary-value, multi-state-value |
| Status   | Indicates operational state | Status, State, Alarm | binary-input, multi-state-input |

### 2. Common Measurement Types

| Measurement Type | Description | Common Abbreviations | Typical Units |
|------------------|-------------|----------------------|---------------|
| Temperature | Thermal measurement | Temp, T | degrees-Celsius, degrees-Fahrenheit |
| Pressure | Force per unit area | Press, P, DP, Dp | pascals, kilopascals, psi |
| Flow | Volume of fluid per time | Flow, Fls, F | liters-per-second, gallons-per-minute |
| Speed | Rotational or linear velocity | Speed, RPM, Hz | revolutions-per-minute, hertz, percent |
| Power | Electrical power consumption | kW, Power | kilowatts, watts |
| Energy | Cumulative energy use | kWh, Energy | kilowatt-hours |
| Status | Operational state | Status, State | - |
| Position | Physical position of actuator | Pos, Position | percent, degrees |

## Pattern Recognition Strategies

### 1. Equipment Type Identification

```python
# Pseudo-code for equipment type identification
def identify_equipment_type(point_name, ontology):
    # Strategy 1: Direct pattern matching
    for eq_type in ontology["equipment_types"]:
        abbreviations = ontology["equipment_types"][eq_type]["abbreviations"]
        for abbr in abbreviations:
            if re.search(f"{abbr}[-_.]?\\d+", point_name, re.IGNORECASE):
                return eq_type
                
    # Strategy 2: Component-based inference
    for eq_type in ontology["equipment_types"]:
        components = ontology["equipment_types"][eq_type]["components"]
        for component in components:
            if re.search(component, point_name, re.IGNORECASE):
                return eq_type
                
    # Strategy 3: Point measurement inference
    for eq_type in ontology["equipment_types"]:
        points = ontology["equipment_types"][eq_type]["standard_points"]
        for point in points:
            if re.search(point["name"], point_name, re.IGNORECASE):
                return eq_type
    
    # Fall back to LLM-based analysis
    return infer_equipment_with_llm(point_name)
```

### 2. Point Function Classification

```python
# Pseudo-code for point function classification
def classify_point_function(point_name, bacnet_type, ontology):
    # Strategy 1: BACnet object type mapping
    for function, info in ontology["point_functions"].items():
        if bacnet_type in info["bacnet_types"]:
            return function
    
    # Strategy 2: Name pattern recognition
    for function, info in ontology["point_functions"].items():
        for pattern in info["name_patterns"]:
            if re.search(pattern, point_name, re.IGNORECASE):
                return function
    
    # Strategy 3: Standard point lookup
    for eq_type in ontology["equipment_types"]:
        for point in ontology["equipment_types"][eq_type]["standard_points"]:
            if re.search(point["name"], point_name, re.IGNORECASE):
                return point["function"]
                
    # Fall back to default based on BACnet type family
    if bacnet_type.endswith("input"):
        return "sensor"
    elif bacnet_type.endswith("output"):
        return "command"
    elif bacnet_type.endswith("value"):
        return "setpoint"
    else:
        return "unknown"
```

## BACnet Object Types

| Object Type | Description | Typical Functions |
|-------------|-------------|-------------------|
| analog-input | Represents an analog input | Sensor (temperature, pressure, etc.) |
| analog-output | Represents an analog output | Command (valve position, speed, etc.) |
| analog-value | Represents an analog value | Setpoint, parameter |
| binary-input | Represents a binary input | Status (on/off, alarm, etc.) |
| binary-output | Represents a binary output | Command (start/stop, enable/disable) |
| binary-value | Represents a binary value | Mode selection, parameter |
| multi-state-input | Represents an input with multiple states | Status with multiple states |
| multi-state-output | Represents an output with multiple states | Command with multiple options |
| multi-state-value | Represents a value with multiple states | Mode selection, parameter |
| structured-view | Represents a structured view/folder | Organization element |
| device | Represents a physical device | Device |

## Data Transformation and Mapping

### 1. Common Unit Conversions

| Source Unit | Target Unit | Conversion Formula |
|-------------|-------------|-------------------|
| degrees-Fahrenheit | degrees-Celsius | (F - 32) * 5/9 |
| degrees-Celsius | degrees-Fahrenheit | (C * 9/5) + 32 |
| psi | kilopascals | psi * 6.89476 |
| kilopascals | psi | kPa / 6.89476 |
| gallons-per-minute | liters-per-second | gpm * 0.0630902 |
| liters-per-second | gallons-per-minute | lps / 0.0630902 |

### 2. Confidence Scoring Factors

| Factor | Description | Weight | Criteria |
|--------|-------------|--------|----------|
| Name Similarity | Similarity between BMS and EnOS point names | 0.30 | String similarity algorithms |
| Function Match | Match between point functions | 0.25 | Exact match of functions |
| Equipment Type Match | Match of equipment types | 0.20 | Exact match of equipment types |
| Measurement Type Match | Match of measurement types | 0.15 | Exact match of measurement types |
| Unit Compatibility | Compatibility of engineering units | 0.10 | Direct match or convertible units |

## Conclusion

This draft ontology provides a foundation for implementing the BMS to EnOS Onboarding Tool with domain-specific knowledge about HVAC systems, equipment types, naming conventions, and point classifications. It should be extended and refined as new patterns and equipment types are encountered during development and testing.

The pattern recognition strategies outlined in this document aim to handle the diverse naming conventions found in real-world BMS data, while the hierarchical equipment model provides a structure for representing the complex relationships between HVAC components.

---

*This draft ontology was created on March 20, 2025 and should be considered a living document that will evolve as the project progresses.*