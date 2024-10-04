import csv
import sys
import os
import requests
import zipfile
import shutil
from urllib.parse import urlparse

def read_csv_with_fallback_encoding(file_path):
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                return list(reader)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to read the file {file_path} with any of the attempted encodings.")

def download_plugin(plugin_name, download_dir):
    url = f"https://downloads.wordpress.org/plugin/{plugin_name}.zip"
    response = requests.get(url)
    if response.status_code == 200:
        zip_path = os.path.join(download_dir, f"{plugin_name}.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        return zip_path
    else:
        print(f"Failed to download {plugin_name}")
        return None

def unzip_plugin(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def count_lines_of_code(directory):
    total_lines = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.php', '.js', '.css', '.html', '.htm')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        total_lines += sum(1 for line in f if line.strip())
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='iso-8859-1') as f:
                            total_lines += sum(1 for line in f if line.strip())
                    except:
                        print(f"Warning: Unable to read file {file_path}")
    return total_lines

def analyze_plugin_loc(input_csv, output_csv):
    try:
        rows = read_csv_with_fallback_encoding(input_csv)
    except ValueError as e:
        print(f"Error reading input file: {str(e)}")
        return

    if not rows:
        print("The input file is empty.")
        return

    download_dir = 'downloaded_plugins'
    extract_dir = 'extracted_plugins'
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Plugin Name", "Total Lines of Code"])

        for row in rows[1:]:  # Skip header row
            if not row:
                continue

            plugin_name = row[0].strip()
            print(f"Analyzing {plugin_name}...")

            zip_path = download_plugin(plugin_name, download_dir)
            if zip_path:
                plugin_extract_dir = os.path.join(extract_dir, plugin_name)
                unzip_plugin(zip_path, plugin_extract_dir)
                
                total_loc = count_lines_of_code(plugin_extract_dir)
                writer.writerow([plugin_name, total_loc])

                # Clean up extracted files
                shutil.rmtree(plugin_extract_dir)
            else:
                writer.writerow([plugin_name, "Failed to download"])

    # Clean up downloaded zip files
    shutil.rmtree(download_dir)

    print(f"Analysis complete. Results saved to {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python plugin_loc_counter.py woo-input.csv loc-output.csv")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    analyze_plugin_loc(input_csv, output_csv)