# Phase 2: Chain of Thought Components for Grouping

## Overview
This phase focuses on implementing step-by-step reasoning for device type identification and group verification mechanisms. The goal is to improve point grouping accuracy before mapping begins.

## Enhanced Grouping Logic

### Update the `_group_points_with_reasoning` Method

```python
def _group_points_with_reasoning(
    self,
    points: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Group points by device type with chain of thought reasoning.
    
    Args:
        points: List of points to group
        
    Returns:
        Dictionary mapping device types to lists of points
    """
    # Initialize reasoning engine
    reasoning_engine = self.get_reasoning_engine()
    
    # First pass: Use explicit device types and extract prefixes
    initial_groups = {}
    points_to_analyze = []
    
    for point in points:
        if "deviceType" in point and point["deviceType"]:
            # Use explicit device type
            device_type = point["deviceType"]
            if device_type not in initial_groups:
                initial_groups[device_type] = []
            initial_groups[device_type].append(point)
        else:
            # Extract potential device type from name prefix
            point_name = point.get("pointName", "")
            prefix = reasoning_engine.extract_device_prefix(point_name)
            
            if prefix:
                # Store prefix for later analysis
                point["extracted_prefix"] = prefix
                
            # Add to points needing further analysis
            points_to_analyze.append(point)
    
    # Second pass: Group points with similar prefixes
    prefix_groups = {}
    points_without_prefix = []
    
    for point in points_to_analyze:
        if "extracted_prefix" in point:
            prefix = point["extracted_prefix"]
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append(point)
        else:
            points_without_prefix.append(point)
    
    # Third pass: Use CoT reasoning to map prefixes to device types
    for prefix, prefix_points in prefix_groups.items():
        # Use reasoning to determine device type from prefix
        reasoning_chain, device_type = reasoning_engine.reason_device_type_from_prefix(
            prefix, prefix_points
        )
        
        # Store reasoning chain in points
        for point in prefix_points:
            point["grouping_reasoning"] = reasoning_chain
        
        # Add to initial groups or create new group
        if device_type not in initial_groups:
            initial_groups[device_type] = []
        initial_groups[device_type].extend(prefix_points)
    
    # Fourth pass: Handle remaining points without prefixes
    if points_without_prefix:
        # Use batch reasoning for remaining points
        reasoned_groups = reasoning_engine.batch_reason_device_types(points_without_prefix)
        
        # Merge with initial groups
        for device_type, device_points in reasoned_groups.items():
            if device_type not in initial_groups:
                initial_groups[device_type] = []
            initial_groups[device_type].extend(device_points)
    
    # Final pass: Verify group assignments
    verified_groups = {}
    
    for device_type, device_points in initial_groups.items():
        # Verify group assignment and potentially reassign points
        verification_result = reasoning_engine.verify_group_assignment(
            device_type, device_points
        )
        
        # Process the verification result
        for verified_type, verified_points in verification_result.items():
            if verified_type not in verified_groups:
                verified_groups[verified_type] = []
            verified_groups[verified_type].extend(verified_points)
    
    return verified_groups
```

## Reasoning Engine Enhancements

### Add Device Type CoT Methods

```python
def extract_device_prefix(self, point_name: str) -> Optional[str]:
    """Extract potential device type prefix from point name.
    
    Args:
        point_name: Name of the point
        
    Returns:
        Extracted prefix or None
    """
    # Common patterns for device type prefixes
    patterns = [
        r"^([A-Z]+-[A-Z]+)-\d+",  # e.g., "CH-SYS-1"
        r"^([A-Z]+)-\d+",         # e.g., "AHU-1"
        r"^([A-Z]+\d+)",          # e.g., "VAV12"
    ]
    
    for pattern in patterns:
        match = re.match(pattern, point_name)
        if match:
            return match.group(1)
    
    # Try a more generic pattern for detecting device prefixes
    components = point_name.split(".")
    if components and components[0]:
        # Return first component as potential prefix
        return components[0]
    
    return None

def reason_device_type_from_prefix(
    self,
    prefix: str,
    points: List[Dict[str, Any]]
) -> Tuple[List[str], str]:
    """Reason about device type from prefix with CoT.
    
    Args:
        prefix: Extracted prefix
        points: Points with this prefix
        
    Returns:
        Tuple of (reasoning chain, determined device type)
    """
    # Initialize reasoning chain
    reasoning_chain = [
        f"Analyzing prefix '{prefix}' for {len(points)} points:"
    ]
    
    # Analyze prefix components
    components = re.split(r'[-_.]', prefix)
    reasoning_chain.append(f"Prefix components: {components}")
    
    # Interpret abbreviations in prefix
    abbr_meanings = []
    for component in components:
        if component in self.abbreviations:
            abbr_meanings.append(f"{component} = {self.abbreviations[component]}")
    
    if abbr_meanings:
        reasoning_chain.append(f"Abbreviation meanings: {', '.join(abbr_meanings)}")
    
    # Analyze point names to find common patterns
    suffixes = []
    units = set()
    
    for point in points:
        point_name = point.get("pointName", "")
        if point_name.startswith(prefix):
            suffix = point_name[len(prefix):].lstrip(".-_")
            suffixes.append(suffix)
        
        unit = point.get("unit", "").lower()
        if unit:
            units.add(unit)
    
    reasoning_chain.append(f"Common suffixes: {suffixes[:5]}{' (truncated)' if len(suffixes) > 5 else ''}")
    
    if units:
        reasoning_chain.append(f"Units in group: {', '.join(units)}")
    
    # Apply heuristic rules for device type identification
    device_type = "unknown"
    
    # Check for common device types
    prefix_lower = prefix.lower()
    if "ch" in prefix_lower and "sys" in prefix_lower:
        device_type = "CH-SYS"
        reasoning_chain.append("Prefix contains 'CH' and 'SYS', indicating a Chiller System")
    elif "ahu" in prefix_lower:
        device_type = "AHU"
        reasoning_chain.append("Prefix contains 'AHU', indicating an Air Handling Unit")
    elif "vav" in prefix_lower:
        device_type = "VAV"
        reasoning_chain.append("Prefix contains 'VAV', indicating a Variable Air Volume unit")
    # Add more rules for other device types
    
    # Analyze suffixes for additional clues
    has_temp = any("temp" in suffix.lower() for suffix in suffixes)
    has_flow = any("flow" in suffix.lower() for suffix in suffixes)
    has_pressure = any("pressure" in suffix.lower() or "press" in suffix.lower() for suffix in suffixes)
    
    # Use suffix patterns to refine device type
    if device_type == "unknown":
        if has_temp and has_flow:
            device_type = "AHU"
            reasoning_chain.append("Points include temperature and flow measurements, likely an Air Handling Unit")
        elif has_pressure:
            device_type = "CH-SYS"
            reasoning_chain.append("Points include pressure measurements, likely a Chiller System")
    
    reasoning_chain.append(f"Determined device type: {device_type}")
    
    return reasoning_chain, device_type

def batch_reason_device_types(
    self,
    points: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Use batch reasoning to determine device types for points without clear prefixes.
    
    Args:
        points: Points without clear device type indicators
        
    Returns:
        Dictionary mapping device types to lists of points
    """
    # Prepare LLM prompt for batch reasoning
    point_names = [point.get("pointName", "") for point in points]
    
    prompt = f"""Analyze these Building Management System (BMS) point names and group them by likely device type.
For each point, determine the most probable device type from these categories:
- CH-SYS: Chiller System
- AHU: Air Handling Unit
- VAV: Variable Air Volume unit
- FCU: Fan Coil Unit
- METER: Metering device
- MISC: Miscellaneous device

Point names:
{chr(10).join(point_names)}

Explain your reasoning for each group, then output each group in JSON format:
{{
  "device_type": (determined device type),
  "points": [(indices of points in this group, 0-based)],
  "reasoning": [(reasoning steps)]
}}
"""
    
    # Execute LLM reasoning (this could use self.mapping_agent with an appropriate wrapper)
    # This is a placeholder - in the actual implementation, we would call the LLM
    # For now, we'll implement a simple rule-based grouping
    
    # Mock response parsing (replace with actual LLM response handling)
    groups = self._mock_batch_grouping(points)
    
    return groups

def verify_group_assignment(
    self,
    device_type: str,
    points: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Verify group assignments and resolve potential conflicts.
    
    Args:
        device_type: Proposed device type
        points: Points in this group
        
    Returns:
        Dictionary of verified device types and their points
    """
    # Initialize result with original group
    result = {device_type: []}
    
    # Analyze each point in the group
    for point in points:
        point_name = point.get("pointName", "")
        
        # Start verification reasoning
        verification = [
            f"Verifying '{point_name}' as device type '{device_type}':"
        ]
        
        # Check for contradicting evidence
        contradictions = []
        
        # Example: VAV points shouldn't have chiller-specific terms
        if device_type == "VAV" and any(term in point_name.lower() for term in ["chiller", "compressor", "condenser"]):
            contradictions.append(f"Point name contains chiller-specific terms, inconsistent with VAV classification")
        
        # Example: CH-SYS points shouldn't have airflow-specific terms
        if device_type == "CH-SYS" and any(term in point_name.lower() for term in ["airflow", "damper", "duct"]):
            contradictions.append(f"Point name contains airflow-specific terms, inconsistent with CH-SYS classification")
        
        # If contradictions exist, reassign point
        if contradictions:
            # Determine correct device type
            correct_type = self._determine_correct_device_type(point, contradictions)
            
            # Add reasoning
            verification.append("Contradictions found:")
            verification.extend([f"- {c}" for c in contradictions])
            verification.append(f"Reassigning to device type: {correct_type}")
            
            # Add point to correct group
            if correct_type not in result:
                result[correct_type] = []
            
            # Store verification reasoning
            point["verification_reasoning"] = verification
            
            # Add to correct group
            result[correct_type].append(point)
        else:
            # No contradictions, keep in original group
            verification.append("No contradictions found, assignment verified")
            
            # Store verification reasoning
            point["verification_reasoning"] = verification
            
            # Keep in original group
            result[device_type].append(point)
    
    return result

def _determine_correct_device_type(
    self,
    point: Dict[str, Any],
    contradictions: List[str]
) -> str:
    """Determine correct device type based on contradictions.
    
    Args:
        point: Point data
        contradictions: List of contradiction explanations
        
    Returns:
        Corrected device type
    """
    # This is a simplified version, real implementation would use more sophisticated rules
    point_name = point.get("pointName", "").lower()
    
    if any(term in point_name for term in ["chiller", "compressor", "condenser", "cooling", "ch-", "ch."]):
        return "CH-SYS"
    elif any(term in point_name for term in ["ahu", "air", "handling", "airflow", "damper"]):
        return "AHU"
    elif any(term in point_name for term in ["vav", "variable", "air", "volume", "zone"]):
        return "VAV"
    elif any(term in point_name for term in ["fcu", "fan", "coil"]):
        return "FCU"
    elif any(term in point_name for term in ["meter", "consumption", "energy", "power"]):
        return "METER"
    else:
        return "MISC"

def _mock_batch_grouping(
    self, 
    points: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Mock implementation of batch grouping (for development only).
    
    Args:
        points: Points to group
        
    Returns:
        Dictionary mapping device types to lists of points
    """
    # Simple rule-based grouping
    groups = {
        "CH-SYS": [],
        "AHU": [],
        "VAV": [],
        "MISC": []
    }
    
    for point in points:
        point_name = point.get("pointName", "").lower()
        
        # Add mock reasoning chains
        reasoning = [
            f"Analyzing point name: {point.get('pointName', '')}",
            "Looking for device type indicators in the name"
        ]
        
        # Simple keyword matching
        if any(term in point_name for term in ["chiller", "ch-", "cooling", "condenser"]):
            reasoning.append("Found chiller-related terms, categorizing as CH-SYS")
            point["grouping_reasoning"] = reasoning
            groups["CH-SYS"].append(point)
        elif any(term in point_name for term in ["ahu", "air", "handling"]):
            reasoning.append("Found air handling unit terms, categorizing as AHU")
            point["grouping_reasoning"] = reasoning
            groups["AHU"].append(point)
        elif any(term in point_name for term in ["vav", "variable", "zone"]):
            reasoning.append("Found variable air volume terms, categorizing as VAV")
            point["grouping_reasoning"] = reasoning
            groups["VAV"].append(point)
        else:
            reasoning.append("No clear device type indicators, categorizing as MISC")
            point["grouping_reasoning"] = reasoning
            groups["MISC"].append(point)
    
    # Filter out empty groups
    return {k: v for k, v in groups.items() if v}
```

## Group Verification UI Components

### Create Group Verification Interface

```typescript
// frontend/src/components/GroupVerification/GroupVerification.tsx

import React, { useState } from 'react';
import { Button, Card, Collapse, Divider, Space, Table, Tag, Typography } from 'antd';
import { CaretRightOutlined } from '@ant-design/icons';
import './GroupVerification.css';

const { Panel } = Collapse;
const { Title, Text } = Typography;

interface GroupVerificationProps {
  groups: {
    [deviceType: string]: {
      points: any[];
      reasoning?: string[];
    }
  };
  onVerify: (verifiedGroups: any) => void;
}

const GroupVerification: React.FC<GroupVerificationProps> = ({ groups, onVerify }) => {
  const [verifiedGroups, setVerifiedGroups] = useState(groups);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  
  // Columns for point details
  const columns = [
    {
      title: 'Point ID',
      dataIndex: 'pointId',
      key: 'pointId',
    },
    {
      title: 'Point Name',
      dataIndex: 'pointName',
      key: 'pointName',
    },
    {
      title: 'Unit',
      dataIndex: 'unit',
      key: 'unit',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (text, record) => (
        <Space size="small">
          <Button size="small" onClick={() => handleMovePoint(record)}>Move</Button>
        </Space>
      ),
    },
  ];
  
  // Handle moving a point to a different group
  const handleMovePoint = (point) => {
    // Show modal for selecting new group
    // Implementation omitted for brevity
  };
  
  // Handle verifying all groups
  const handleVerify = () => {
    onVerify(verifiedGroups);
  };
  
  // Toggle expanded groups
  const handleGroupExpand = (deviceType: string) => {
    if (expandedGroups.includes(deviceType)) {
      setExpandedGroups(expandedGroups.filter(g => g !== deviceType));
    } else {
      setExpandedGroups([...expandedGroups, deviceType]);
    }
  };
  
  return (
    <div className="group-verification">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Title level={4}>Verify Device Type Groups</Title>
        <Text>Review the groups below and make any necessary adjustments before proceeding.</Text>
        
        {Object.entries(verifiedGroups).map(([deviceType, data]) => (
          <Card
            key={deviceType}
            title={`${deviceType} (${data.points.length} points)`}
            extra={
              <Space>
                <Button 
                  type="text" 
                  icon={<CaretRightOutlined rotate={expandedGroups.includes(deviceType) ? 90 : 0} />}
                  onClick={() => handleGroupExpand(deviceType)}
                />
              </Space>
            }
          >
            {data.reasoning && (
              <Collapse ghost>
                <Panel header="View Reasoning" key="reasoning">
                  <ul>
                    {data.reasoning.map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ul>
                </Panel>
              </Collapse>
            )}
            
            {expandedGroups.includes(deviceType) && (
              <Table
                dataSource={data.points}
                columns={columns}
                size="small"
                rowKey="pointId"
                pagination={{ pageSize: 5 }}
              />
            )}
          </Card>
        ))}
        
        <Divider />
        
        <Button type="primary" onClick={handleVerify}>
          Confirm Groups & Proceed
        </Button>
      </Space>
    </div>
  );
};

export default GroupVerification;
```

## Backend Routes for Group Verification

```python
# app/bms/routes.py

@router.post("/points/group-with-reasoning")
async def group_points_with_reasoning(
    points_data: List[PointData],
    request: Request
):
    """Group BMS points by device type with reasoning.
    
    Args:
        points_data: List of points to group
        
    Returns:
        Grouped points with reasoning chains
    """
    mapper = get_mapper(request.app.state)
    grouped_points = mapper._group_points_with_reasoning(points_data)
    
    # Format response
    response = {}
    
    for device_type, points in grouped_points.items():
        # Extract reasoning chains
        all_reasoning = []
        for point in points:
            if "grouping_reasoning" in point:
                all_reasoning.extend(point["grouping_reasoning"])
            
            # Remove reasoning from individual points
            if "grouping_reasoning" in point:
                del point["grouping_reasoning"]
        
        # Deduplicate reasoning steps
        unique_reasoning = list(dict.fromkeys(all_reasoning))
        
        response[device_type] = {
            "points": points,
            "reasoning": unique_reasoning
        }
    
    return response

@router.post("/points/verify-groups")
async def verify_point_groups(
    verified_groups: Dict[str, List[PointData]],
    request: Request
):
    """Verify and finalize point groupings.
    
    Args:
        verified_groups: Dictionary mapping device types to lists of points
        
    Returns:
        Verified groups with additional confidence metrics
    """
    # Initialize reasoning engine
    reasoning_engine = get_reasoning_engine(request.app.state)
    
    # Verify each group
    verification_results = {}
    
    for device_type, points in verified_groups.items():
        # Verify the group
        confidence_scores = reasoning_engine.calculate_group_confidence(device_type, points)
        
        # Store results
        verification_results[device_type] = {
            "points": points,
            "confidence": confidence_scores["overall"],
            "confidence_details": confidence_scores["details"]
        }
    
    return verification_results
```

## Confidence Scoring Method

```python
def calculate_group_confidence(
    self,
    device_type: str,
    points: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate confidence scores for group assignment.
    
    Args:
        device_type: Device type
        points: Points in this group
        
    Returns:
        Dictionary with confidence scores
    """
    # Initialize scores
    scores = {
        "overall": 0.0,
        "details": {
            "naming_pattern": 0.0,
            "point_types": 0.0,
            "units": 0.0,
            "coherence": 0.0
        }
    }
    
    # Check naming pattern consistency
    prefix_patterns = self._analyze_naming_patterns(points)
    pattern_score = self._score_naming_patterns(prefix_patterns, device_type)
    scores["details"]["naming_pattern"] = pattern_score
    
    # Check point type consistency
    point_types = [p.get("pointType", "") for p in points]
    expected_types = self._get_expected_point_types(device_type)
    type_score = self._score_point_types(point_types, expected_types)
    scores["details"]["point_types"] = type_score
    
    # Check unit consistency
    units = [p.get("unit", "") for p in points]
    expected_units = self._get_expected_units(device_type)
    unit_score = self._score_units(units, expected_units)
    scores["details"]["units"] = unit_score
    
    # Check overall coherence
    coherence_score = self._calculate_coherence(points, device_type)
    scores["details"]["coherence"] = coherence_score
    
    # Calculate overall score (weighted average)
    weights = {
        "naming_pattern": 0.4,
        "point_types": 0.2,
        "units": 0.2,
        "coherence": 0.2
    }
    
    overall_score = sum(
        scores["details"][key] * weight 
        for key, weight in weights.items()
    )
    
    scores["overall"] = overall_score
    
    return scores

def _analyze_naming_patterns(
    self,
    points: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Analyze naming patterns in a group of points.
    
    Args:
        points: Points to analyze
        
    Returns:
        Dictionary mapping patterns to counts
    """
    patterns = {}
    
    for point in points:
        point_name = point.get("pointName", "")
        
        # Extract pattern (simplistic approach)
        components = point_name.split(".")
        if components:
            prefix = components[0]
            patterns[prefix] = patterns.get(prefix, 0) + 1
    
    return patterns

def _score_naming_patterns(
    self,
    patterns: Dict[str, int],
    device_type: str
) -> float:
    """Score naming patterns for consistency with device type.
    
    Args:
        patterns: Dictionary mapping patterns to counts
        device_type: Expected device type
        
    Returns:
        Consistency score (0.0 to 1.0)
    """
    if not patterns:
        return 0.0
    
    total_points = sum(patterns.values())
    
    # Find most common pattern
    most_common = max(patterns.items(), key=lambda x: x[1])
    most_common_prefix, most_common_count = most_common
    
    # Calculate dominance of most common pattern
    dominance = most_common_count / total_points
    
    # Check if most common prefix is consistent with device type
    prefix_matches_type = False
    
    if device_type == "CH-SYS" and any(term in most_common_prefix.lower() for term in ["ch", "chiller"]):
        prefix_matches_type = True
    elif device_type == "AHU" and "ahu" in most_common_prefix.lower():
        prefix_matches_type = True
    elif device_type == "VAV" and "vav" in most_common_prefix.lower():
        prefix_matches_type = True
    # Add more device type checks
    
    # Calculate final score
    if prefix_matches_type:
        return 0.5 + (dominance * 0.5)  # 0.5 to 1.0
    else:
        return dominance * 0.5  # 0.0 to 0.5
``` 