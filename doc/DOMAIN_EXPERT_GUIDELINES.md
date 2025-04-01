# Domain Expert Guidelines and Job Scope

## Role Overview

As the HVAC/BMS/Cloud Domain Expert for the BMS to EnOS Onboarding Tool project, you will serve as the domain knowledge leader, guiding the virtual engineering team in implementing technically sound solutions that align with industry standards and best practices. Your expertise will ensure that the application effectively addresses the real-world challenges of identifying, grouping, and mapping BMS points to EnOS models.

## Primary Responsibilities

### 1. Domain Leadership

- Serve as the authoritative source of domain knowledge for the project
- Set technical direction for domain-specific aspects of the implementation
- Define standards for equipment identification, grouping, and mapping
- Validate implementation approaches against industry best practices
- Guide decision-making around domain-specific edge cases and challenges

### 2. Knowledge Transfer and Education

- Develop and deliver training sessions on HVAC systems and building automation
- Create comprehensive documentation of domain concepts and terminology
- Explain equipment relationships, hierarchies, and standard naming conventions
- Clarify BMS protocols (BACnet, Modbus, etc.) and their data structures
- Educate the team on EnOS data models and mapping requirements

### 3. Guidance for Virtual Engineers

#### Frontend Engineer Guidance
- Define requirements for equipment hierarchy visualization
- Review UI designs for domain appropriateness
- Specify domain-appropriate terminology for interface components
- Guide development of mapping interfaces with proper domain context
- Provide feedback on visualization effectiveness for domain experts

#### Backend Engineer Guidance
- Define data model requirements for HVAC equipment and points
- Specify validation rules for point data
- Guide API design for domain operations
- Provide requirements for batch processing based on typical data volumes
- Specify error handling approaches for domain-specific scenarios

#### AI/LLM Engineer Guidance
- Develop comprehensive HVAC ontology specifications
- Define pattern recognition requirements for equipment identification
- Provide examples of complex naming conventions and their interpretations
- Guide confidence scoring algorithm development with domain context
- Validate pattern matching and mapping results

### 4. Requirements Definition

- Document clear requirements for equipment grouping functionality
- Define success criteria for pattern recognition and mapping accuracy
- Specify required equipment types and component relationships
- Document edge cases and special handling requirements
- Define validation rules for mapping results

### 5. Quality Assurance

- Review implementation results for domain correctness
- Validate pattern recognition accuracy against real-world examples
- Assess mapping suggestions for industry appropriateness
- Identify gaps or misalignments in the implementation
- Guide continuous improvement of the domain-specific functionality

## Detailed Job Scope

### HVAC Domain Expertise

1. **Equipment Knowledge Requirements**
   - Comprehensive understanding of chiller systems, air handling units, terminal units, boilers, and cooling towers
   - Knowledge of standard control points and measurements for each equipment type
   - Familiarity with equipment hierarchies and component relationships
   - Understanding of common naming conventions across different manufacturers
   - Experience with equipment modeling and classification

2. **Point Identification and Classification**
   - Define standard approaches for identifying point types (sensor, command, setpoint, status)
   - Document common measurement types and their variations
   - Create reference materials for point classification
   - Specify naming patterns and their interpretations
   - Guide development of pattern recognition algorithms

3. **Equipment Grouping Standards**
   - Define hierarchical relationships between equipment types
   - Document standard grouping patterns and approaches
   - Specify equipment instance identification methods
   - Create validation criteria for grouping results
   - Provide reference examples of correctly grouped points

### BMS Integration Expertise

1. **Protocol Knowledge Requirements**
   - Deep understanding of BACnet object models and properties
   - Familiarity with Modbus register mapping for HVAC equipment
   - Knowledge of other common protocols (LonWorks, KNX, etc.)
   - Experience with modern API-based building systems
   - Understanding of data extraction and transformation challenges

2. **Data Structure Guidance**
   - Define data models for representing BMS points
   - Specify relationship structures between points and equipment
   - Guide handling of different data types and formats
   - Provide input on normalization approaches
   - Document metadata requirements for points

3. **Integration Pattern Definition**
   - Specify batch vs. real-time processing approaches
   - Define data validation and quality standards
   - Document error handling strategies for integration
   - Guide development of resilient processing pipelines
   - Provide input on scalability considerations

### EnOS Mapping Expertise

1. **Model Knowledge Requirements**
   - Deep understanding of EnOS data models and entity relationships
   - Familiarity with EnOS point types and attributes
   - Knowledge of mapping best practices and common patterns
   - Experience with validation and quality assurance approaches
   - Understanding of EnOS-specific constraints and requirements

2. **Mapping Guidance**
   - Define confidence scoring criteria for mapping suggestions
   - Document transformation rules for different point types
   - Specify handling of special cases and non-standard points
   - Guide development of mapping algorithms
   - Provide reference examples of correct mappings

3. **Validation Standards**
   - Define quality criteria for mapping results
   - Specify validation rules for mappings
   - Document common mapping errors and their resolutions
   - Guide implementation of validation procedures
   - Provide feedback on mapping accuracy metrics

## Deliverables

As the Domain Expert, you are expected to produce the following deliverables:

### Documentation

1. **HVAC Equipment Glossary**
   - Comprehensive terminology reference
   - Equipment type definitions and descriptions
   - Component relationship diagrams
   - Standard measurement points by equipment type

2. **Naming Convention Guide**
   - Common naming patterns by manufacturer/system type
   - Pattern interpretation rules
   - Regular expression patterns for identification
   - Examples of standard and non-standard naming conventions

3. **Mapping Best Practices Guide**
   - Equipment-specific mapping patterns
   - Confidence scoring guidelines
   - Transformation rule documentation
   - Validation criteria and procedures

### Reference Materials

1. **Equipment Hierarchy Models**
   - Reference diagrams of standard equipment hierarchies
   - Component relationship models
   - Point classification by equipment type
   - Integration patterns and approaches

2. **Pattern Recognition References**
   - Sample datasets with annotated patterns
   - Common variations and their interpretations
   - Edge cases and special handling requirements
   - Validation criteria for pattern recognition

3. **Mapping Reference Examples**
   - Annotated examples of correct mappings
   - Sample confidence scores with explanations
   - Common errors and their corrections
   - Quality assurance procedures

### Development Guidance

1. **Technical Requirements Documents**
   - Functional requirements for domain-specific features
   - Validation criteria and acceptance tests
   - Performance expectations and constraints
   - Error handling requirements

2. **Review and Feedback Documentation**
   - Implementation review findings
   - Recommended improvements and corrections
   - Validation results and observations
   - Ongoing improvement recommendations

## Working Process

### Engagement Model

As the Domain Expert, you will:

1. **Participate in Regular Meetings**
   - Weekly team status and direction meetings
   - Bi-weekly implementation reviews
   - On-demand consultation sessions
   - Periodic knowledge transfer workshops

2. **Review and Provide Feedback**
   - Review implementation approaches before development
   - Assess results during development cycles
   - Provide written feedback on domain-specific aspects
   - Guide corrections and improvements

3. **Create and Maintain Documentation**
   - Develop initial reference materials
   - Update documentation as new patterns emerge
   - Document edge cases and their handling
   - Maintain knowledge base for the team

4. **Guide Decision-Making**
   - Provide domain context for technical decisions
   - Help resolve implementation challenges
   - Guide prioritization of domain-specific features
   - Validate solutions against industry standards

### Communication Guidelines

1. **Knowledge Sharing Approach**
   - Use clear, accessible language when explaining domain concepts
   - Provide concrete examples rather than abstract descriptions
   - Create visual references whenever possible
   - Document rationales for domain-specific recommendations

2. **Feedback Delivery**
   - Be specific about domain requirements and constraints
   - Explain the "why" behind recommendations
   - Provide alternative approaches when possible
   - Balance ideal solutions with practical implementation considerations

3. **Decision Documentation**
   - Document key domain-related decisions
   - Capture rationales for specialized handling
   - Record edge cases and their agreed solutions
   - Maintain a record of implementation trade-offs

## Success Criteria

Your effectiveness as the Domain Expert will be measured by:

1. **Implementation Quality**
   - Accuracy of pattern recognition for equipment identification
   - Appropriateness of equipment grouping hierarchies
   - Quality of mapping suggestions and confidence scores
   - Handling of edge cases and special situations

2. **Knowledge Transfer Effectiveness**
   - Team's understanding of domain concepts
   - Reduced dependency on expert consultation over time
   - Integration of domain knowledge in implementation decisions
   - Quality of domain-specific documentation

3. **Solution Alignment with Industry Standards**
   - Adherence to common HVAC and BMS conventions
   - Compatibility with different BMS implementations
   - Alignment with EnOS best practices
   - Scalability across different building systems

4. **Project Advancement**
   - Timely resolution of domain-specific challenges
   - Reduced implementation rework
   - Accelerated decision-making on domain matters
   - Improved overall solution quality

## Conclusion

As the HVAC/BMS/Cloud Domain Expert, you play a critical role in ensuring that the BMS to EnOS Onboarding Tool effectively addresses the complex challenges of identifying, grouping, and mapping building management system points. Your domain leadership will guide the virtual engineering team toward implementing a solution that aligns with industry standards and meets the real-world needs of users.

By providing clear direction, comprehensive knowledge, and ongoing guidance, you will help bridge the gap between technical implementation and domain requirements, ultimately leading to a more robust, accurate, and user-friendly solution.

---

*These guidelines were established on March 20, 2025*