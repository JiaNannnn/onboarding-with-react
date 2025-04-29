# OpenAI API Response Tools

This directory contains tools for managing and analyzing OpenAI API responses used in the EnOS Onboarding application.

## Overview

The application uses OpenAI's API for various AI-assisted tasks:

1. **Grouping BMS points** by device type and device ID
2. **Mapping BMS points** to EnOS points
3. **Analyzing point relationships**

These tools help you save, retrieve, and analyze the responses from these API calls, which can be useful for:

- Debugging AI behavior
- Optimizing prompts
- Tracking token usage
- Comparing different strategies
- Sharing results with the team

## Tools

### save_openai_responses.py

This tool saves OpenAI API responses to the `backend/api_responses/openai` directory with unique timestamps and metadata.

```
python backend/tools/save_openai_responses.py --file <path_to_json_file> --type <response_type>
```

Options:
- `--file, -f`: Path to the JSON file containing the API response
- `--type, -t`: Type of response (default: "grouping")
- `--output-dir, -o`: Target directory for saved responses (default: backend/api_responses/openai)
- `--source, -s`: Original source file that was processed (optional)

Example:
```
python backend/tools/save_openai_responses.py --file result.json --type mapping
```

### list_openai_responses.py

This tool lists and displays saved OpenAI API responses.

```
python backend/tools/list_openai_responses.py [options]
```

Options:
- `--list, -l`: List all response files
- `--type, -t`: Filter responses by type (e.g., "grouping")
- `--view, -v`: View a specific response file
- `--latest`: View the most recent response file

Examples:
```
# List all responses
python backend/tools/list_openai_responses.py --list

# List only grouping responses
python backend/tools/list_openai_responses.py --list --type grouping

# View the most recent response
python backend/tools/list_openai_responses.py --latest

# View a specific response file
python backend/tools/list_openai_responses.py --view backend/api_responses/openai/grouping_response_20250425_120543.json
```

## Batch Files

For convenience on Windows systems, batch files are provided:

- `list_responses.bat`: Run the list_openai_responses.py script
- `save_response.bat`: Run the save_openai_responses.py script

Examples:
```
# List all responses
backend\tools\list_responses.bat --list

# Save a response
backend\tools\save_response.bat --file result.json --type mapping
```

## Integration with Application

These tools are integrated with the BMS point grouping functionality in the application. When grouping is performed using OpenAI, the responses are automatically saved to the designated directory.

## Directory Structure

```
backend/
├── api_responses/
│   ├── openai/             # Directory for saved OpenAI responses
│   │   ├── grouping_*.json # Grouping responses
│   │   └── mapping_*.json  # Mapping responses
├── tools/
│   ├── save_openai_responses.py  # Tool for saving responses
│   ├── list_openai_responses.py  # Tool for listing/viewing responses
│   ├── save_response.bat         # Batch file for Windows
│   ├── list_responses.bat        # Batch file for Windows
│   └── README.md                 # This file
```

## Response Format

Each saved response includes:
- Timestamp
- Model used
- Content (response from the model)
- Usage statistics (tokens) 