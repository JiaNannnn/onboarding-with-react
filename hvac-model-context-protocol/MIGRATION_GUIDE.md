# Migration Guide: Integrating HVAC Model Context Protocol

This guide provides instructions for migrating from a basic LLM approach to using the HVAC Model Context Protocol for enhanced HVAC point classification and reasoning.

## Before: Basic LLM Approach

Typically, a basic approach to using LLMs for HVAC point classification might look like this:

```python
def classify_point(point_name, unit=None):
    # Create a simple prompt
    prompt = f"""
    Please analyze this Building Management System point name and determine:
    1. The device type it belongs to
    2. The measurement or control function
    3. Your confidence level (0-1)
    
    Point name: {point_name}
    Unit: {unit or 'Not specified'}
    """
    
    # Call the LLM API
    response = call_llm_api(prompt)
    
    # Parse the response (usually manual or with simple regex)
    result = parse_response(response)
    
    return result
```

This approach has several limitations:
- No structured prompt format for consistent responses
- No domain-specific context to guide the LLM
- Inconsistent reasoning across similar points
- Difficulty extracting structured data from responses

## After: Using HVAC Model Context Protocol

### Step 1: Initialize the Protocol Engine

First, import and initialize the protocol engine:

```python
from hvac_mcp import ProtocolEngine

# Initialize the protocol engine (can be done once and reused)
protocol_engine = ProtocolEngine()
```

### Step 2: Update Your Classification Function

Modify your existing function to use the protocol:

```python
def classify_point_with_protocol(point_name, unit=None):
    # Generate specialized context for this point
    context = protocol_engine.generate_context(
        [point_name],  # Can include similar points for better context
        "point_name_analysis"  # Specify the reasoning task
    )
    
    # Create an enhanced prompt with structured context
    prompt = f"""{context}
    ## USER PROMPT
    Analyze the following Building Management System point:
    Point name: {point_name}
    Unit: {unit or 'Not specified'}
    """
    
    # Call the LLM API with enhanced prompt
    response = call_llm_api(prompt)
    
    # Extract structured reasoning from the response
    structured_result = protocol_engine.extract_reasoning_from_response(
        response,
        "point_name_analysis"
    )
    
    return structured_result
```

### Step 3: Update Group Classification Functions

Similarly, update any group verification functions:

```python
def verify_point_group_with_protocol(points, proposed_device_type):
    # Generate context for group verification
    context = protocol_engine.generate_context(
        points,
        "group_verification"
    )
    
    # Create enhanced prompt
    prompt = f"""{context}
    ## USER PROMPT
    Verify if the following points belong to the same device type:
    Proposed device type: {proposed_device_type}
    Points: {", ".join(points)}
    """
    
    # Call LLM
    response = call_llm_api(prompt)
    
    # Extract structured verification result
    verification_result = protocol_engine.extract_reasoning_from_response(
        response,
        "group_verification"
    )
    
    return verification_result
```

## Benefits of Migration

By migrating to the HVAC Model Context Protocol, you gain:

1. **Structured Reasoning**: Consistent step-by-step reasoning across all point analyses
2. **Domain Knowledge Integration**: HVAC-specific knowledge base and ontology included in every prompt
3. **Optimized Context**: Dynamically selected relevant context to reduce token usage
4. **Ambiguity Handling**: Specialized handling for ambiguous or uncertain classifications
5. **Structured Output**: Systematic extraction of reasoning results for easier integration
6. **Better Group Verification**: Improved validation of point grouping assignments

## Advanced Integration

### Customizing the Knowledge Base

You can use a custom knowledge base by providing a path to the KB file:

```python
engine = ProtocolEngine(kb_path="path/to/your/custom_kb.json")
```

### Handling Ambiguous Points

For points with low confidence scores, consider using the ambiguity resolution protocol:

```python
if result["confidence_score"] < 0.5:
    ambiguity_context = protocol_engine.generate_context(
        [point_name],
        "ambiguity_resolution"
    )
    # ... call LLM with ambiguity resolution prompt ...
```

## Common Migration Issues

1. **Response Format Changes**: The protocol expects structured responses - if your LLM response format changes, the extraction may fail.

   Solution: Test your extraction with small examples and adjust if needed.

2. **Increased Token Usage**: Adding context increases prompt size.

   Solution: The protocol's context optimization helps, but monitor your token usage.

3. **Learning Curve**: Understanding the protocol's capabilities takes time.

   Solution: Start with the basic integration, then explore advanced features.

## Need Help?

If you need additional assistance with migration, please check the README.md file for more examples or contact the development team. 