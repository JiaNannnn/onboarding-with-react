import csv
import os

file_path = 'mapping_output_1744771382.csv'
file_size = os.path.getsize(file_path)
print(f"CSV file size: {file_size} bytes")

# Open the CSV file
with open(file_path, 'r', newline='') as csvfile:
    # Create a CSV reader
    reader = csv.reader(csvfile)
    
    # Read and print the header
    header = next(reader)
    print("\nHeaders:")
    for i, field in enumerate(header):
        print(f"{i+1}. {field}")
    
    # Print just the first 2 rows with clear formatting
    print("\nFirst 2 rows:")
    for i, row in enumerate(reader):
        if i < 2:
            print(f"\nRow {i+1} Details:")
            for j, field in enumerate(row):
                if j < len(header):  # Ensure we don't go out of bounds
                    print(f"  {header[j]}: '{field}'")
                else:
                    print(f"  Field {j}: '{field}' (No header)")
        else:
            break
            
    # Count total rows
    csvfile.seek(0)
    next(reader)  # Skip header
    row_count = sum(1 for _ in reader)
    print(f"Total rows in CSV: {row_count + 1}")  # +1 for header 