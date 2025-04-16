import csv
import os

# Find the most recent mapping_final_*.csv file
csv_files = [f for f in os.listdir('.') if f.startswith('mapping_final_') and f.endswith('.csv')]
if not csv_files:
    print("No mapping_final_*.csv files found")
    exit(1)

csv_file = sorted(csv_files)[-1]  # Get the most recent one
print(f"Examining: {csv_file}")
file_size = os.path.getsize(csv_file)
print(f"File size: {file_size} bytes")

# Open the CSV file
with open(csv_file, 'r', newline='') as csvfile:
    # Create a CSV reader
    reader = csv.reader(csvfile)
    
    # Read the header
    header = next(reader)
    print(f"\nFound {len(header)} columns in the CSV file")
    
    # Read first 2 rows into memory
    sample_rows = []
    for i, row in enumerate(reader):
        if i < 2:
            sample_rows.append(row)
        else:
            break
    
    # Print key fields for sample rows
    print("\nSample data (first 2 rows):")
    print("Row | pointName | deviceType | deviceId | enosPoint | status")
    print("-" * 70)
    for i, row in enumerate(sample_rows):
        pointName = row[0] if len(row) > 0 else ""
        deviceType = row[1] if len(row) > 1 else ""
        deviceId = row[2] if len(row) > 2 else ""
        enosPoint = row[6] if len(row) > 6 else ""
        status = row[7] if len(row) > 7 else ""
        print(f"{i+1}   | {pointName[:15]:<15} | {deviceType:<10} | {deviceId:<8} | {enosPoint:<15} | {status}")
    
    # Reset and count non-empty values for key fields
    csvfile.seek(0)
    next(reader)  # Skip header
    count_pointName = 0
    count_deviceType = 0
    count_deviceId = 0
    total_rows = 0
    
    for row in reader:
        if len(row) < 3:
            continue  # Skip incomplete rows
        total_rows += 1
        if row[0] and row[0].strip():  # pointName
            count_pointName += 1
        if row[1] and row[1].strip():  # deviceType
            count_deviceType += 1
        if row[2] and row[2].strip():  # deviceId
            count_deviceId += 1
    
    print(f"\nTotal rows: {total_rows}")
    print(f"Rows with non-empty pointName: {count_pointName} ({count_pointName/total_rows*100:.1f}%)")
    print(f"Rows with non-empty deviceType: {count_deviceType} ({count_deviceType/total_rows*100:.1f}%)")
    print(f"Rows with non-empty deviceId: {count_deviceId} ({count_deviceId/total_rows*100:.1f}%)") 