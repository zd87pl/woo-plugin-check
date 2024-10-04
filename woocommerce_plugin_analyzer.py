import sys
import csv
import os
import shutil
import tempfile
import urllib.request
import zipfile
from urllib.error import URLError

def extract_plugin_name(file_path):
    parts = file_path.split('/')
    return parts[0] if parts else None

def download_plugin(plugin_name, download_dir):
    url = f"https://downloads.wordpress.org/plugin/{plugin_name}.zip"
    zip_path = os.path.join(download_dir, f"{plugin_name}.zip")
    try:
        urllib.request.urlretrieve(url, zip_path)
        return zip_path
    except URLError as e:
        print(f"Failed to download {plugin_name}: {e}")
        return None

def unzip_plugin(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def find_api_calls(plugin_dir):
    api_calls = []
    for root, _, files in os.walk(plugin_dir):
        for file in files:
            if file.endswith('.php'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if 'woocommerce.com' in line:
                            relative_path = os.path.relpath(file_path, plugin_dir)
                            api_calls.append(f"{relative_path}:{i} - {line.strip()}")
    return api_calls

def get_processed_plugins(output_csv):
    processed_plugins = set()
    if os.path.exists(output_csv):
        with open(output_csv, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip the header
            for row in reader:
                if row:  # Ensure the row is not empty
                    processed_plugins.add(row[0])
    return processed_plugins

def analyze_plugins(input_csv, output_csv):
    processed_plugins = get_processed_plugins(output_csv)
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        download_dir = os.path.join(tmpdirname, 'downloads')
        extract_dir = os.path.join(tmpdirname, 'extracted')
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(extract_dir, exist_ok=True)

        mode = 'a' if processed_plugins else 'w'
        with open(input_csv, 'r', newline='') as infile, open(output_csv, mode, newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            if mode == 'w':
                writer.writerow(['Plugin', 'API Calls'])
            
            for row in reader:
                if len(row) == 0:
                    continue
                
                file_path = row[0].strip()
                plugin_name = extract_plugin_name(file_path)
                if not plugin_name or plugin_name in processed_plugins:
                    continue
                
                print(f"Analyzing {plugin_name}...")
                
                zip_path = download_plugin(plugin_name, download_dir)
                if zip_path:
                    plugin_extract_dir = os.path.join(extract_dir, plugin_name)
                    unzip_plugin(zip_path, plugin_extract_dir)
                    api_calls = find_api_calls(plugin_extract_dir)
                    
                    if api_calls:
                        writer.writerow([plugin_name, '\n'.join(api_calls)])
                    else:
                        writer.writerow([plugin_name, "No API calls found"])
                else:
                    writer.writerow([plugin_name, "Failed to download plugin"])
                
                processed_plugins.add(plugin_name)
                outfile.flush()  # Ensure the data is written to the file

    print(f"Analysis complete. Results saved to {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python woocommerce_plugin_analyzer.py input.csv output.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    analyze_plugins(input_csv, output_csv)