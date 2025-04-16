import json
import csv
import os
import time
import pprint

# Read the JSON file
json_file = 'mapping_22759e46-108d-4093-be2a-28114df0ccee.json'
# Use timestamp to create a unique filename
timestamp = int(time.time())
csv_file = f'mapping_final_{timestamp}.csv'

with open(json_file, 'r') as f:
    data = json.load(f)

# Print the structure of the first few items to understand the data
print("Examining JSON structure...")
if isinstance(data, dict) and 'mappings' in data:
    sample = data['mappings'][:2] if len(data['mappings']) > 1 else data['mappings']
    print("JSON has 'mappings' key with sample:")
    pprint.pprint(sample)
    mappings = data['mappings']
elif isinstance(data, list) and len(data) > 0:
    sample = data[:2] if len(data) > 1 else data
    print("JSON appears to be a list with sample:")
    pprint.pprint(sample)
    mappings = data
else:
    print("Unknown JSON structure:")
    pprint.pprint(data)
    for key in data.keys():
        print(f"Key: {key}, Type: {type(data[key])}")
        if isinstance(data[key], list) and len(data[key]) > 0:
            sample = data[key][:2] if len(data[key]) > 1 else data[key]
            print(f"Sample of '{key}':")
            pprint.pprint(sample)
    mappings = []
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            mappings = value
            break

print(f"Found {len(mappings)} mapping entries")

# Define our fieldnames based on the actual structure we found
fieldnames = [
    # Key fields at the top level that the user wants
    'pointName', 
    'deviceType', 
    'deviceId',
    'pointId',
    'pointType',
    'unit',
    # EnOS mapping fields
    'enosPoint',
    'status',
    'confidence',
    'mapping_explanation'
]

print(f"CSV will have {len(fieldnames)} columns: {', '.join(fieldnames)}")

try:
    # Write to CSV
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write each mapping as a row
        for item in mappings:
            row = {}
            
            # Extract the fields from the top level of the mapping item
            row['pointName'] = str(item.get('pointName', '')) if item.get('pointName') is not None else ""
            row['deviceType'] = str(item.get('deviceType', '')) if item.get('deviceType') is not None else ""
            row['deviceId'] = str(item.get('deviceId', '')) if item.get('deviceId') is not None else ""
            row['pointId'] = str(item.get('pointId', '')) if item.get('pointId') is not None else ""
            row['pointType'] = str(item.get('pointType', '')) if item.get('pointType') is not None else ""
            row['unit'] = str(item.get('unit', '')) if item.get('unit') is not None else ""
            
            # EnOS mapping fields
            row['enosPoint'] = str(item.get('enosPoint', '')) if item.get('enosPoint') is not None else ""
            row['status'] = str(item.get('status', '')) if item.get('status') is not None else ""
            row['confidence'] = str(item.get('confidence', '')) if item.get('confidence') is not None else ""
            
            # Nested mapping field for explanation
            if 'mapping' in item and 'explanation' in item['mapping']:
                row['mapping_explanation'] = str(item['mapping']['explanation']) if item['mapping']['explanation'] is not None else ""
            else:
                row['mapping_explanation'] = ""
                
            writer.writerow(row)
    
    print(f'Successfully converted {json_file} to {csv_file}')
    print(f'CSV contains {len(mappings)} rows and {len(fieldnames)} columns')
    
    # Verify the CSV was created properly
    print(f"Verifying CSV file...")
    file_size = os.path.getsize(csv_file)
    print(f"CSV file size: {file_size} bytes")
    
    # Display first row for verification
    with open(csv_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"Header: {header}")
        print("First row:")
        row = next(reader, None)
        if row:
            for i, field in enumerate(row):
                print(f"  {header[i]}: '{field}'")
except Exception as e:
    print(f"Error: {str(e)}") 