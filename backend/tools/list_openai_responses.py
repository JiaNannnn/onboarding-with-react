#!/usr/bin/env python
"""
List and display saved OpenAI responses

This script allows you to list all saved OpenAI responses and optionally view the contents
of specific response files.
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('openai_response_viewer')

def list_openai_responses(response_type=None):
    """
    List all saved OpenAI responses
    
    Args:
        response_type: Optional filter for response type (e.g., "grouping")
    
    Returns:
        List of response file paths
    """
    # Find all response files in the designated directory
    target_dir = Path("backend/api_responses/openai")
    if not target_dir.exists():
        logger.warning(f"Response directory not found: {target_dir}")
        return []
    
    # Get all JSON files in the directory
    response_files = [f for f in target_dir.glob("*.json")]
    
    # Filter by type if specified
    if response_type:
        response_files = [f for f in response_files if response_type in f.name]
    
    # Sort by modification time (most recent first)
    response_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    return response_files

def display_openai_response(file_path):
    """
    Display the contents of a specific OpenAI response file
    
    Args:
        file_path: Path to the response file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            response_data = json.load(f)
        
        # Format the output
        print("\n" + "="*80)
        print(f"RESPONSE FILE: {file_path}")
        print("="*80)
        
        # Display metadata
        print(f"Timestamp: {response_data.get('timestamp', 'N/A')}")
        print(f"Model: {response_data.get('model', 'N/A')}")
        
        # Display usage stats if available
        usage = response_data.get('usage', {})
        if usage:
            print("\nUsage Statistics:")
            print(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  Total Tokens: {usage.get('total_tokens', 'N/A')}")
        
        # Display content
        print("\nContent:")
        content = response_data.get('content', 'No content available')
        
        # Try to parse and pretty-print JSON content
        try:
            content_json = json.loads(content)
            print(json.dumps(content_json, indent=2))
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, print as is
            print(content)
        
        print("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"Error displaying response file {file_path}: {str(e)}")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='List and display saved OpenAI responses')
    parser.add_argument('--type', '-t', help='Filter responses by type (e.g., "grouping")')
    parser.add_argument('--list', '-l', action='store_true', help='List all response files')
    parser.add_argument('--view', '-v', help='View a specific response file')
    parser.add_argument('--latest', action='store_true', help='View the most recent response file')
    
    args = parser.parse_args()
    
    if args.list:
        # List all response files
        response_files = list_openai_responses(args.type)
        
        if not response_files:
            print("No OpenAI response files found.")
            return 0
        
        print(f"\nFound {len(response_files)} OpenAI response files:")
        for i, file_path in enumerate(response_files):
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i+1}. {file_path.name} ({mod_time_str})")
    
    elif args.view:
        # View a specific response file
        file_path = Path(args.view)
        if not file_path.exists():
            # Try to find it in the default directory
            default_dir = Path("backend/api_responses/openai")
            file_path = default_dir / args.view
        
        if not file_path.exists():
            logger.error(f"Response file not found: {args.view}")
            return 1
        
        display_openai_response(file_path)
    
    elif args.latest:
        # View the most recent response file
        response_files = list_openai_responses(args.type)
        
        if not response_files:
            print("No OpenAI response files found.")
            return 0
        
        latest_file = response_files[0]
        display_openai_response(latest_file)
    
    else:
        parser.print_help()
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main()) 