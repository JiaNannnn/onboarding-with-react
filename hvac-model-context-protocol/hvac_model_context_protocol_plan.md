# HVAC Model Context Protocol Implementation Plan

## 1. Protocol Structure Definition

**Purpose:** Create a structured framework for the LLM to consistently reason about HVAC systems and point mappings, enhancing accuracy and explainability.

**Components:**
- **Domain Ontology:** Detailed hierarchical representation of HVAC systems, components, and relationships. (See Section 2)
- **Reasoning Templates:** Standardized step-by-step procedures for common tasks like point analysis and group verification. (See Section 3)
- **Decision Trees:** Predefined logic flows for classifying complex or ambiguous points. (To be developed in later phase)
- **Knowledge Base (KB):** A repository of specific facts, abbreviations, naming conventions, and known patterns. (See Section 4)
- **Protocol Format:** Defined structure for injecting context into the LLM prompt. (See Section 5)
- **Ambiguity Resolution:** Strategies for handling uncertain or conflicting classifications. (See Section 3.3)
- **Security Layer:** Safeguards against protocol manipulation and data integrity. (See Section 9)
- **Error Handling Framework:** Systematic approach for handling LLM failures and edge cases. (See Section 11)
- **Industry Standards Alignment:** Conformity with established building data standards. (See Section 12)

## 2. Domain Knowledge Representation (Ontology)

### Detailed HVAC System Hierarchy
```
Building Management System
├── Primary Systems
│   ├── Chiller Plant (CH-SYS)
│   │   ├── Chiller (CH)
│   │   ├── Chilled Water Pump (CWP)
│   │   ├── Condenser Water Pump (CDWP)
│   │   └── Cooling Tower (CT)
│   ├── Boiler Plant (BLR-SYS)
│   │   ├── Boiler (BLR)
│   │   └── Hot Water Pump (HWP)
│   └── Central Plant Auxiliaries (e.g., Makeup Water, Chemical Treatment)
├── Air Distribution
│   ├── Air Handling Units (AHU)
│   │   ├── Supply Fan (SF)
│   │   ├── Return Fan (RF)
│   │   ├── Cooling Coil (CC)
│   │   ├── Heating Coil (HC)
│   │   ├── Filter (FLTR)
│   │   ├── Mixed Air Damper (MAD)
│   │   └── Outside Air Damper (OAD)
│   └── Exhaust Systems (EF)
└── Terminal Units
    ├── Variable Air Volume (VAV)
    │   ├── Zone Damper
    │   └── Reheat Coil (optional)
    ├── Fan Coil Units (FCU)
    │   ├── Fan
    │   └── Coil (Heating/Cooling)
    └── Zone Controls (e.g., Thermostats, Sensors)

```

### System Relationships and Dependencies
```
Upstream → Downstream Flow
- Chiller Plant → AHU Cooling Coil
- Boiler Plant → AHU Heating Coil, VAV Reheat
- AHU → VAV Boxes → Zone
```

### Cross-System Integration Points
```
Interfaces between HVAC and other building systems:
- HVAC ↔ Electrical: VFD control, power monitoring
- HVAC ↔ Lighting: Occupancy sharing, schedule coordination
- HVAC ↔ Security: Door position status, occupancy integration
- HVAC ↔ Fire Safety: Smoke control dampers, emergency mode
```

### Refined Point Type Classification
- **SensorAnalog:** Continuous value readings (e.g., Temperature, Pressure, Flow, Humidity, CO2 Level)
- **SensorBinary:** Discrete state readings (e.g., Status On/Off, Occupancy Detected/Undetected, Filter Dirty/Clean)
- **SetpointCommand:** Desired value set by control system (e.g., Temperature Setpoint, Damper Position Command)
- **StatusFeedback:** Confirmation of equipment state (e.g., Pump Running/Stopped, Valve Open/Closed)
- **Alarm:** Indication of fault or abnormal condition (e.g., High Temp Alarm, Low Pressure Alarm, Communication Failure)
- **CalculatedValue:** Derived value (e.g., Efficiency, Runtime Hours, Energy Consumption)

## 3. Standard Reasoning Templates

### 3.1 Point Name Analysis Template (Detailed)
*Input: Point Name, Unit (optional), Description (optional)*
*Output: Classified Device Type, Confidence Score, Reasoning Chain*
```markdown
**Protocol Steps:**
1.  **Parse Point Name:** Break down the point name into components using common delimiters ('.', '-', '_').
2.  **Extract Prefix:** Identify the potential device/system prefix (e.g., 'AHU-1', 'CH-SYS-1.CWP').
3.  **Lookup Prefix in Ontology/KB:** Match prefix against known system types and abbreviations defined in the Knowledge Base.
4.  **Identify Measurement/Control Function:** Analyze suffix components and keywords (e.g., 'Temp', 'Status', 'Cmd', 'Hz', 'SPT') using KB definitions to determine the point's purpose. Cross-reference with Point Type Classification.
5.  **Check Contradictory Evidence:** Based on the potential system type identified in step 3, check if the function identified in step 4 is consistent. *Contradictions are defined in the KB (e.g., an 'AHU' point name containing 'Chiller' terms).*
6.  **Evaluate Unit Consistency:** Check if the provided 'Unit' aligns with the inferred point function (using KB unit mappings).
7.  **Assign Confidence Score:** Calculate a score based on the strength of prefix match, function identification clarity, and absence of contradictions.
8.  **Generate Reasoning Summary:** Construct a human-readable explanation following the steps above.
```

### 3.2 Group Verification Template (Detailed)
*Input: Proposed Device Type, List of Points*
*Output: Verified Group Assignments, Confidence Score per Group*
```markdown
**Protocol Steps:**
1.  **Identify Expected Point Characteristics:** Based on the proposed Device Type, retrieve expected point functions, keywords, and units from the Ontology and KB.
2.  **Validate Naming Consistency:** Analyze prefixes and suffixes across points in the group. Calculate the dominance of the most common naming pattern.
3.  **Check for Outliers:** For each point, compare its inferred function and characteristics against the group's expected characteristics. Flag points with significant deviations or contradictions (as defined in KB).
4.  **Evaluate Cross-System Integration:** Identify points that might link systems (e.g., a VAV reporting AHU supply temperature). *Cross-system links are suggested by shared prefixes or known relationships in the Ontology/KB.*
5.  **Calculate Group Confidence:** Score the group based on naming consistency, the proportion of points matching expected characteristics, and the number of unexplained outliers.
6.  **Propose Reassignments:** Suggest moving outlier points to more appropriate groups based on their individual characteristics.
```

### 3.3 Ambiguity Resolution Protocol
*Input: Point with Multiple Potential Classifications or Low Confidence*
*Output: Best Classification or Explicit Ambiguity Flag*
```markdown
**Protocol Steps:**
1.  **Classification Confidence Threshold:**
    - If confidence score < 0.4, flag for human review
    - If confidence score ≥ 0.4 but < 0.6, apply additional checks
    - If confidence score ≥ 0.6, accept classification but note uncertainty

2.  **Resolution Strategy for Multiple Matches:**
    - Check system relationships (e.g., if point matches both AHU and VAV patterns)
      - Analyze upstream/downstream relationships in system hierarchy
      - Check for parent/child naming conventions (e.g., "AHU-1.VAV-3" indicates VAV as subdomain)
    
    - Analyze temporal and functional patterns:
      - If historical data available, check correlation with known system operations
      - Examine if point function matches primary or secondary system function
    
    - System prevalence weighting:
      - If facility has predominant system type, increase weight for that classification
      - Consider typical point count ratios (e.g., VAVs typically outnumber AHUs)

3.  **Handling Truly Ambiguous Points:**
    - Create multi-classification entry with ranked possibilities
    - Generate explanation of ambiguity sources
    - Propose specific additional information that would resolve ambiguity
    - In GroupVerification UI, highlight with distinct visual indicator
```

### 3.4 Time-Based Reasoning Template
*Input: Point Name, Historical Data (if available)*
*Output: Enhanced Classification, Confidence Score, Correlation Evidence*
```markdown
**Protocol Steps:**
1.  **Retrieve Historical Data:** Pull time-series data for the point and related points (if available).
2.  **Extract Operational Patterns:**
    - Identify on/off cycles, setpoint changes, and status transitions
    - Detect correlations with upstream/downstream equipment (e.g., pump start → flow increase)
    - Analyze day/night or seasonal operation differences
3.  **Validate Point Function:**
    - Confirm that sensor values fall within expected ranges for the proposed device type
    - Verify that control inputs produce expected responses in related points
    - Ensure alarms trigger under appropriate conditions
4.  **Generate Temporal Evidence:**
    - Document correlations that support classification (e.g., "Valve command correlates with temperature changes")
    - Identify operational anomalies that contradict classification
5.  **Apply Temporal Confidence Boost:**
    - Adjust confidence score based on strength of temporal evidence
    - Prioritize strong temporal correlations over weak naming pattern matches
```

## 4. Knowledge Base (KB) Integration

- **Initial Format:** The KB will start as a structured JSON or YAML file containing:
    - Standard abbreviations and their meanings (e.g., `"CWP": "Chilled Water Pump"`).
    - Keywords mapping to point functions (e.g., `"Temp": ["SensorAnalog", "Temperature"]`).
    - Typical units for different measurement types (e.g., `"Temperature": ["degC", "degF"]`).
    - Known contradictory patterns per device type (e.g., `"VAV_Contradictions": ["chiller", "compressor"]`).
    - Common naming conventions and prefixes.
- **Evolution:** Plan to potentially migrate to a more dynamic database or graph structure if complexity increases. Consider methods for dynamically learning new patterns from successfully verified groupings (Phase 2/Feedback Loop).
- **LLM Interaction:** The relevant sections of the KB (e.g., abbreviations found in current points, expected patterns for potential device types) will be dynamically selected and included in the LLM prompt context. The LLM will be instructed to *strictly adhere* to the definitions and rules provided within the KB context section of the prompt.
- **External System Integration:**
    - **BMS Connection:** API endpoints for validating against live or historical building management system data.
    - **Data Analytics Service:** Microservice for analyzing historical point behavior to improve classification.
    - **Facility Management System:** Schema mapping to connect physical equipment to BMS points.
    - **Standards Alignment:** Reference to ASHRAE, BACnet, and other industry standard nomenclatures.

### 4.1 Automated KB Update Mechanism
```python
def process_feedback_for_kb_updates(feedback_records, min_frequency=3, admin_review=True):
    """Analyzes user feedback to identify potential KB updates.
    
    Args:
        feedback_records: Collection of user corrections with original and corrected classifications
        min_frequency: Minimum occurrences of similar corrections to trigger update recommendation
        admin_review: Whether admin approval is required before implementing updates
        
    Returns:
        kb_update_recommendations: List of potential KB additions/modifications with supporting evidence
    """
    # Group feedback by correction type
    grouped_corrections = group_similar_corrections(feedback_records)
    
    # Filter for corrections that meet frequency threshold
    frequent_corrections = filter_by_frequency(grouped_corrections, min_frequency)
    
    # Analyze patterns to extract potential new abbreviations or rules
    abbreviation_candidates = extract_abbreviation_candidates(frequent_corrections)
    pattern_candidates = extract_pattern_candidates(frequent_corrections)
    contradiction_candidates = extract_contradiction_candidates(frequent_corrections)
    
    # Prepare recommendations with supporting evidence
    recommendations = []
    for candidate in abbreviation_candidates + pattern_candidates + contradiction_candidates:
        recommendations.append({
            'type': candidate.type,  # 'abbreviation', 'pattern', 'contradiction'
            'proposed_addition': candidate.value,
            'supporting_evidence': {
                'correction_count': candidate.frequency,
                'example_points': candidate.examples[:3],  # Limit to 3 examples
                'confidence': candidate.confidence,
                'potential_conflicts': identify_conflicts(candidate, current_kb)
            }
        })
    
    # If admin review required, queue for approval
    if admin_review:
        queue_for_admin_review(recommendations)
        return {'status': 'queued_for_review', 'count': len(recommendations)}
    
    # Otherwise, apply updates directly
    apply_kb_updates(recommendations)
    return {'status': 'applied', 'updates': recommendations}
```

## 5. Protocol Format and Structure

- **Format:** Markdown with clearly defined sections using headings (e.g., `## ONTOLOGY`, `## KNOWLEDGE_BASE`, `## REASONING_TEMPLATE`). This is human-readable and easily parsable.
- **Injection:** The protocol context will be dynamically constructed and prepended to the main task prompt sent to the LLM.
- **Example Snippet (for Point Name Analysis):**
  ```markdown
  ## PROTOCOL CONTEXT V1.1
  ### TASK: Point Name Analysis
  ### ONTOLOGY_SNIPPET
  - AHU: [Supply Fan (SF), Return Fan (RF), Cooling Coil (CC), ...]
  ### KNOWLEDGE_BASE_SNIPPET
  - Abbreviations: {"SA": "Supply Air", "TMP": "Temperature"}
  - Keywords: {"Temp": ["SensorAnalog", "Temperature"]}
  - Units: {"Temperature": ["degC", "degF"]}
  - Contradictions: {"AHU": ["chiller", "vav"]}
  ### REASONING_TEMPLATE
  1. Parse Point Name: ...
  2. Extract Prefix: ...
  [...other steps...]
  ---
  ## USER PROMPT
  Analyze the following point: "AHU-2.SATemp" Unit: "degC"
  ```

- **Context Optimization Strategy:**
  ```python
  def prioritize_context(points, task_type):
      """Dynamically selects most relevant protocol sections based on:
      
      Args:
          points: List of points to analyze
          task_type: Type of task being performed (e.g., "grouping", "verification")
          
      Returns:
          optimized_context: Tailored protocol content prioritizing most relevant information
      """
      # Extract all prefixes and potential keywords from points
      prefixes = extract_prefixes(points)
      potential_keywords = extract_keywords(points)
      
      # Calculate frequency of system types based on prefixes
      system_frequency = calculate_system_frequency(prefixes)
      
      # Select ontology branches for most common system types (e.g., top 3)
      relevant_ontology = select_ontology_branches(system_frequency, max_branches=3)
      
      # Select KB entries relevant to the identified systems and keywords
      relevant_kb_entries = select_kb_entries(system_frequency, potential_keywords)
      
      # Load appropriate reasoning template for the task
      template = load_reasoning_template(task_type)
      
      # Consider recent user feedback for similar points (if available)
      user_feedback = get_recent_feedback(prefixes, max_age_days=30)
      
      # Assemble context with most relevant sections first (for token priority)
      optimized_context = assemble_context(
          template,
          relevant_ontology,
          relevant_kb_entries,
          user_feedback,
          protocol_version=get_latest_version()
      )
      
      return optimized_context
  ```

### 5.1 Non-HVAC System Context Priority
```python
def handle_mixed_system_points(points, detected_systems):
    """Manages context prioritization when points span multiple building systems.
    
    Args:
        points: List of points to analyze
        detected_systems: Dictionary of system types and their confidence scores
        
    Returns:
        system_specific_contexts: Dictionary of system-specific optimized contexts
    """
    # Organize points by suspected system type
    system_point_groups = {}
    for system_type in detected_systems:
        system_point_groups[system_type] = filter_points_by_system(points, system_type)
    
    # For each system type, generate appropriate context
    system_specific_contexts = {}
    for system_type, system_points in system_point_groups.items():
        if system_type == 'HVAC':
            system_specific_contexts[system_type] = prioritize_context(system_points, 'grouping')
        elif system_type == 'Electrical':
            system_specific_contexts[system_type] = prioritize_electrical_context(system_points)
        elif system_type == 'Lighting':
            system_specific_contexts[system_type] = prioritize_lighting_context(system_points)
        elif system_type == 'Security':
            system_specific_contexts[system_type] = prioritize_security_context(system_points)
        # Add more system types as needed
    
    # Add special context for cross-system integration points
    integration_points = identify_cross_system_points(points)
    if integration_points:
        system_specific_contexts['Integration'] = generate_integration_context(integration_points)
    
    return system_specific_contexts
```

## 6. Implementation Steps

1.  **Create Protocol Documentation & Initial KB:** Define V1.0 of the protocol structure, ontology details, templates, and initial KB content (abbreviations, basic patterns) in Markdown and JSON/YAML. **Establish Protocol Versioning Scheme (e.g., V1.0, V1.1).**
2.  **Develop Context Injection Mechanism:** Implement Python functions to:
    *   Load the protocol documentation and KB.
    *   **Dynamically select relevant sections** using the context optimization strategy to prioritize the most relevant content based on point patterns.
    *   Assemble the final prompt string including the selected protocol context.
3.  **Implement Protocol Handlers/Adapters:** Modify the `ReasoningEngine` to:
    *   Utilize the context injection mechanism before calling the LLM.
    *   Adapt the parsing of LLM responses to extract structured reasoning based on the protocol templates.
    *   Log protocol version used and context provided for each LLM call.
    *   Implement the ambiguity resolution protocol for handling uncertain classifications.
4.  **Build Protocol Feedback Loop:**
    *   **Feedback Collection:** Gather data from user actions in the `GroupVerification` UI (e.g., point moves, group confirmations) and automated validation checks post-LLM processing.
    *   **Analysis:** Periodically review feedback to identify protocol shortcomings or areas for improvement (e.g., missing abbreviations, incorrect contradiction rules).
    *   **Refinement:** Update the protocol documentation and KB manually based on analysis. *Future Goal: Explore semi-automated extraction of new patterns/rules from high-confidence user verifications.*
    *   **Implement Automated KB Updates:** Deploy the KB update mechanism to systematically detect and apply improvements based on user feedback patterns.
5.  **Design User Interface for Protocol Visibility:** Enhance the `GroupVerification` component to optionally display:
    *   The specific reasoning steps followed (as extracted by the protocol handler).
    *   Highlighting of potential contradictions or low-confidence assignments flagged by the protocol.
    *   Allow users to optionally flag reasoning steps as helpful or incorrect (feeding into the feedback loop).
    *   Implement distinct visual indicators for ambiguous points and confidence levels.
6.  **Develop Error Handling Framework:**
    *   Implement comprehensive error detection for LLM failures, timeout handling, and malformed responses.
    *   Create fallback mechanisms for each critical component of the reasoning pipeline.
    *   Establish retry policies with exponential backoff for transient failures.
7.  **Integrate with Industry Standards:**
    *   Map protocol ontology to Project Haystack and Brick Schema taxonomies.
    *   Develop adapters for importing/exporting standard format definitions.
    *   Implement compliance checking for industry-standard naming conventions.

## 7. Timeline

- **Week 1:** Design protocol structure, documentation V1.0, Initial KB, Versioning scheme.
- **Week 2:** 
  - Implement dynamic context optimization strategy
  - Develop core context injection mechanism
  - Begin ambiguity resolution implementation
- **Week 3:** 
  - Complete protocol handlers for reasoning extraction and validation
  - Implement security validation layer
  - Integrate with `ReasoningEngine`
  - Develop error handling framework and fallbacks
- **Week 4:** 
  - Enhance UI components for protocol visibility
  - Implement ambiguity visualization
  - Develop basic feedback collection mechanism
  - Begin automated KB update mechanism
- **Week 5: Enhanced Testing Plan**
  - **Unit Testing:** Protocol handler edge cases, ambiguity resolution
  - **Integration Testing:** Complete grouping pipeline with all components
  - **User Acceptance Testing:** Real-world scenario simulations with actual BMS data
  - **Load Testing:** Performance evaluation with 10,000+ points
  - **Security Testing:** Validate protection against prompt injection attempts
  - **Real-World Testing Scenarios:**
    - **Legacy System Testing:** Points from pre-2000 control systems
    - **Mixed-Vendor Testing:** Points from multiple BMS manufacturers
    - **Partial Modernization:** Buildings with mix of old and new systems
    - **Non-Standard Naming:** Custom naming conventions from specialized facilities
    - **Day/Night Cycle Simulation:** Testing with operational data from different times
    - **Seasonal Variation Testing:** Both heating and cooling season data sets
  - **Initial protocol refinement** based on test results
- **Week 6:**
  - Implement industry standards integration
  - Begin multi-building knowledge transfer framework
  - Develop time-based reasoning components

## 8. Evaluation Metrics

- Grouping accuracy improvement (compared to baseline without MCP).
- Reasoning consistency across similar inputs.
- Reduction in points requiring manual reassignment.
- Protocol adaptation rate (frequency of required updates based on feedback).
- User acceptance/satisfaction rating of protocol-guided explanations.
- **Ambiguity resolution success rate:** Percentage of ambiguous points correctly resolved.
- **Context optimization efficiency:** Token count reduction while maintaining accuracy.
- **System integration value:** Improved accuracy when using external system data.
- **Error recovery effectiveness:** Percentage of potential failures successfully mitigated by fallback mechanisms.
- **KB evolution metrics:** Rate of automated KB improvements that are accepted by administrators.
- **Cross-building transferability:** Percentage of protocol effectiveness maintained when applied to new buildings without customization.
- **Time-based reasoning value:** Accuracy improvement when temporal data is incorporated vs. name-only analysis.
- **Standards compliance score:** Percentage of protocol elements that map cleanly to industry standard taxonomies.

## 9. Security Considerations

- **Protocol Access Control:**
  - KB modification requires admin approval and validation
  - Protocol version changes undergo peer review process
  - Audit trail of all protocol modifications
  
- **User Authentication and Authorization:**
  - User feedback authenticated via JWT tokens
  - Role-based access for protocol modification
  - User-specific feedback tracking for quality assessment
  
- **Data Protection:**
  - Context injection sanitized to prevent prompt injection attacks
  - Input validation for all user-provided feedback
  - Sensitive building data protection (e.g., no specific location information)
  
- **Operational Security:**
  - Rate limiting for LLM API calls
  - Fallback mechanisms for service disruptions
  - Regular security reviews of protocol content

### 9.1 Advanced Governance Model

- **Change Management System:**
  - **Protocol Change Request (PCR)** formal process for significant changes
  - **Technical Review Board** with domain experts to evaluate complex changes
  - **Change Impact Analysis** required for modifications affecting multiple components
  
- **Version Control and Release Management:**
  - **Semantic Versioning** for protocol (MAJOR.MINOR.PATCH)
  - **Release Notes** documenting all changes and compatibility impacts
  - **Deprecation Policy** for phasing out outdated knowledge patterns
  
- **Data Provenance:**
  - **Origin Tracking** for all KB entries and rule additions
  - **Confidence Metadata** for each KB entry (e.g., manually verified vs. algorithm-generated)
  - **Usage Statistics** tracking which KB elements are most frequently used in reasoning

## 10. Long-Term Evolution

- **Self-Improving Protocol:** Implementing machine learning to automatically refine the KB based on feedback patterns
- **Multi-Building Knowledge Transfer:** Sharing protocol improvements across different building implementations
- **Protocol Extension:** Adding support for additional building systems (electrical, security, lighting)
- **Standards Alignment:** Evolving the protocol to align with emerging industry standards for building data

### 10.1 Enhanced Multi-Building Knowledge Transfer

- **Global and Local Knowledge Separation:**
  - Core KB with universally applicable patterns and abbreviations
  - Building-specific KB extensions for unique naming conventions
  - Regional KB extensions for location-specific terminology
  
- **Knowledge Propagation Mechanisms:**
  - **Peer-to-Peer Learning:** Automatic suggestion of successful patterns from one building to similar buildings
  - **Confidence-Based Propagation:** Higher confidence rules propagate more widely
  - **Building Similarity Scoring:** Measuring how likely knowledge is to transfer based on building characteristics
  
- **Naming Convention Normalization:**
  - **Pattern Abstraction:** Converting specific naming patterns to more general forms
  - **Translation Layer:** Mapping between different naming conventions while preserving semantic meaning
  - **Gradual Standardization:** Suggesting industry-standard naming while maintaining backward compatibility

## 11. Error Handling Framework

### 11.1 LLM Failure Handling

- **Response Validation:**
  - **Schema Validation:** Ensuring LLM responses match expected structure
  - **Reasoning Chain Validation:** Verifying that steps follow logical progression
  - **Contradiction Detection:** Identifying internal inconsistencies in reasoning

- **Failure Response Strategy:**
  - **Timeout Handling:** If LLM does not respond within expected timeframe (5s):
    ```python
    def handle_llm_timeout(point_name, max_retries=3):
        for attempt in range(max_retries):
            try:
                # Retry with exponential backoff
                response = call_llm_with_timeout(point_name, timeout=5 * (2**attempt))
                return response
            except TimeoutError:
                log.warning(f"LLM timeout on attempt {attempt+1}/{max_retries}")
        
        # If all retries fail, fall back to rule-based classification
        return rule_based_fallback_classification(point_name)
    ```
  
  - **Malformed Response Handling:** If LLM returns invalid or incomplete reasoning:
   ```python
    def handle_malformed_response(point_name, response):
        # Check if partial reasoning can be salvaged
        valid_steps = extract_valid_reasoning_steps(response)
        
        if len(valid_steps) >= min_required_steps:
            # Complete missing steps with rule-based reasoning
            return complete_partial_reasoning(valid_steps, point_name)
        else:
            # Fall back to simpler classification approach
            return simplified_classification_strategy(point_name)
    ```
  
  - **Confidence Threshold Failures:** When no classification meets minimum confidence:
   ```python
    def handle_low_confidence(point_name, classifications, threshold=0.4):
        # Try alternative reasoning template
        if all(c.confidence < threshold for c in classifications):
            alt_classifications = alternate_reasoning_approach(point_name)
            
            # If still low confidence, use most common pattern from similar points
            if all(c.confidence < threshold for c in alt_classifications):
                return {'classification': best_guess_from_similar_points(point_name),
                        'confidence': 'low',
                        'requires_review': True}
            return alt_classifications
        
        return classifications
    ```

### 11.2 Default Classification Rules

- **Point Type Default Rules:**
  - Points containing "temp" or "tmp" with units of "degF" or "degC" default to Temperature Sensor
  - Points ending with "cmd" or "command" default to Control Output
  - Points containing "status" or "stat" default to Status Feedback
  - Points containing "alarm" default to Alarm Point

- **System Type Default Rules:**
  - Points with no identifiable system type default to "Unknown"
  - In case of ambiguity between VAV and AHU, default to system with more points
  - Legacy points following no standardized convention default to "Legacy"

- **Default Type Assignment Flow:**
  ```
  1. Apply LLM-based reasoning with protocol context
  2. If confidence < threshold, apply rules-based classification
  3. If still uncertain, default to most statistically likely classification
  4. Flag for human review with explicit indication of default assignment
  ```

## 12. Industry Standards Alignment

### 12.1 Project Haystack Integration

- **Tag Mapping:**
  - Protocol device types → Haystack equipment tags
  - Protocol point types → Haystack point tags
  - Protocol function types → Haystack marker tags

- **Example Mappings:**
  ```
  Protocol:
  {
    "device_type": "AHU",
    "point_type": "SensorAnalog",
    "function": "Temperature",
    "location": "Supply Air"
  }
  
  Haystack:
  {
    "equip": "m:ahu",
    "point": "m:sensor",
    "temp": "m:",
    "air": "m:",
    "supply": "m:"
  }
  ```

- **Import/Export Functions:**
  - Import Haystack-tagged points into protocol format
  - Export protocol classifications as Haystack tags
  - Validate protocol ontology against Haystack taxonomy

### 12.2 Brick Schema Integration

- **Class Mapping:**
  - Protocol device types → Brick classes
  - Protocol point types → Brick point classes
  - Protocol relationships → Brick relationships

- **Example Mappings:**
  ```
  Protocol:
  {
    "device_type": "AHU",
    "contains": ["Supply Fan", "Cooling Coil"],
    "feeds": "VAV"
  }
  
  Brick:
  {
    "class": "Air Handler Unit",
    "relationships": [
      {"predicate": "hasPart", "object": "Supply Fan"},
      {"predicate": "hasPart", "object": "Cooling Coil"},
      {"predicate": "feeds", "object": "Variable Air Volume Box"}
    ]
  }
  ```

- **RDF Graph Generation:**
  - Convert protocol knowledge base to Brick-compatible RDF
  - Generate visual graph representations of system relationships
  - Enable SPARQL queries against protocol-derived building model

### 12.3 BACnet Integration

- **Object Mapping:**
  - Protocol point types → BACnet object types
  - Protocol functions → BACnet properties
  - Protocol units → BACnet engineering units

- **Standard Property Support:**
  - BACnet instance number tracking in protocol
  - Standard BACnet naming conventions in KB
  - BACnet-specific abbreviations in protocol dictionary 