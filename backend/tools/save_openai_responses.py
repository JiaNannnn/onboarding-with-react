#!/usr/bin/env python
"""
Save OpenAI API responses for the grouping functionality to a specified directory.
This allows for better tracking, debugging, and analysis of the AI responses.
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('openai_response_saver')

def save_openai_response(response_data, source_file=None, response_type="grouping"):
    """
    Save an OpenAI API response to the designated directory
    
    Args:
        response_data: The JSON response data from OpenAI API
        source_file: Optional path to the source file that was processed
        response_type: Type of response (default: "grouping")
    
    Returns:
        Path to the saved response file
    """
    # Create the target directory if it doesn't exist
    target_dir = Path("backend/api_responses/openai")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create filename with metadata
    source_name = ""
    if source_file:
        source_name = f"_{Path(source_file).stem}"
    
    filename = f"{response_type}{source_name}_{timestamp}.json"
    target_path = target_dir / filename
    
    # Save the response data
    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            if isinstance(response_data, str):
                # If response_data is already a JSON string
                f.write(response_data)
            else:
                # If response_data is a dict or similar
                json.dump(response_data, f, indent=2)
        
        logger.info(f"OpenAI {response_type} response saved to {target_path}")
        return target_path
    
    except Exception as e:
        logger.error(f"Failed to save OpenAI response: {e}")
        return None

def save_latest_response_from_file(source_file, target_dir=None, response_type="grouping"):
    """
    Save the latest response from a file to the target directory
    
    Args:
        source_file: Path to the source file containing the OpenAI response
        target_dir: Target directory (default: backend/api_responses/openai)
        response_type: Type of response (default: "grouping")
    
    Returns:
        Path to the saved response file
    """
    if target_dir is None:
        target_dir = Path("backend/api_responses/openai")
    else:
        target_dir = Path(target_dir)
    
    # Create the target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Read the source file
        with open(source_file, 'r', encoding='utf-8') as f:
            response_data = json.load(f)
        
        # Create filename with metadata
        source_name = f"_{Path(source_file).stem}"
        filename = f"{response_type}{source_name}_{timestamp}.json"
        target_path = target_dir / filename
        
        # Save the response data
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2)
        
        logger.info(f"OpenAI {response_type} response saved to {target_path}")
        return target_path
    
    except Exception as e:
        logger.error(f"Failed to save OpenAI response from file {source_file}: {e}")
        return None

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Save OpenAI API responses to a designated directory')
    parser.add_argument('--file', '-f', help='Path to the JSON file containing the response')
    parser.add_argument('--source', '-s', help='Original source file that was processed')
    parser.add_argument('--type', '-t', default='grouping', help='Type of response (default: grouping)')
    parser.add_argument('--output-dir', '-o', default=None, help='Target directory for saved responses')
    
    args = parser.parse_args()
    
    if args.file:
        target_dir = args.output_dir or "backend/api_responses/openai"
        result = save_latest_response_from_file(
            args.file, 
            target_dir=target_dir,
            response_type=args.type
        )
        if result:
            print(f"Response saved to: {result}")
        else:
            print("Failed to save response")
            return 1
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main()) 