import csv
import collections
from pathlib import Path

def analyze_devices():
    """Analyze the CSV file to count device categories and assets"""
    file_path = Path("backend/data_test/Frasers CS/Frases_CS_Mapped_30%_95%.csv")
    
    device_types = set()
    device_ids = collections.defaultdict(set)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            device_types.add(row['deviceType'])
            device_ids[row['deviceType']].add(row['deviceId'])
    
    print('Device Categories:', len(device_types), sorted(list(device_types)))
    print('\nDevice Assets per Category:')
    for device_type in sorted(device_ids.keys()):
        print(f'  {device_type}: {len(device_ids[device_type])} assets')
    
    total_assets = sum(len(assets) for assets in device_ids.values())
    print('\nTotal Unique Device Assets:', total_assets)

if __name__ == "__main__":
    analyze_devices() 