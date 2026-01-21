#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path

HELLO_WORLD_SCHEMA = {
    "formTitle": "Hello World Drona Environment",
    "formDescription": "A simple starter environment to test Drona",
    "fields": [
        {
            "type": "text",
            "name": "job_name",
            "label": "Job Name",
            "value": "hello_world",
            "required": True
        },
        {
            "type": "textarea",
            "name": "message",
            "label": "Message to Display",
            "value": "Hello from Drona!",
            "required": True
        },
        {
            "type": "number",
            "name": "repeat_count",
            "label": "Repeat Count",
            "value": 1,
            "min": 1,
            "max": 10
        }
    ]
}

HELLO_WORLD_MAP = {
    "JOBNAME": "$job_name",
    "MESSAGE": "$message",
    "REPEAT": "$repeat_count"
}

HELLO_WORLD_DRIVER = """#!/bin/bash
# Hello World Drona Environment
source /etc/profile
cd ${DRONA_JOB_DIR}

echo "Job Name: [JOBNAME]"
echo "Repeating message [REPEAT] times:"
echo ""

for i in $(seq 1 [REPEAT]); do
    echo "$i: [MESSAGE]"
done

echo ""
echo "Hello World job completed successfully!"
"""

HELLO_WORLD_UTILS = """#!/usr/bin/env python3
\"\"\"
Utility functions for Hello World environment
\"\"\"

def example_function(param1, param2="default"):
    \"\"\"
    Example utility function
    \"\"\"
    return f"Processing {param1} with {param2}"
"""

def init_environment(directory=None):
    """Create a new Drona hello world environment"""
    if directory is None:
        directory = "drona_hello_world"
    
    target_dir = Path(directory)
    
    # Check if directory exists
    if target_dir.exists():
        print(f"Error: Directory '{directory}' already exists!")
        return False
    
    # Create directory
    target_dir.mkdir(parents=True)
    print(f"Created directory: {directory}")
    
    # Create Schema.json
    schema_path = target_dir / "schema.json"
    with open(schema_path, 'w') as f:
        json.dump(HELLO_WORLD_SCHEMA, f, indent=2)
    print(f"  ✓ Created Schema.json")
    
    # Create Map.json
    map_path = target_dir / "map.json"
    with open(map_path, 'w') as f:
        json.dump(HELLO_WORLD_MAP, f, indent=2)
    print(f"  ✓ Created Map.json")
    
    # Create driver.sh
    driver_path = target_dir / "driver.sh"
    with open(driver_path, 'w') as f:
        f.write(HELLO_WORLD_DRIVER)
    driver_path.chmod(0o755)  # Make executable
    print(f"  ✓ Created driver.sh")
    
    # Create utils.py
    utils_path = target_dir / "utils.py"
    with open(utils_path, 'w') as f:
        f.write(HELLO_WORLD_UTILS)
    print(f"  ✓ Created utils.py")
    
    print(f"\n✓ Environment created in '{directory}'")
    print(f"\nNext steps:")
    print(f"  1. cd {directory}")
    print(f"  2. Customize schema.json, map.json, and driver.sh")
    print(f"  3. Deploy to Drona Composer")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Drona Utils - Helper tools for Drona Composer environments'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize a new Drona environment'
    )
    init_parser.add_argument(
        'directory',
        nargs='?',
        default='drona_hello_world',
        help='Directory name for the new environment (default: drona_hello_world)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_environment(args.directory)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
