import os
import re
import subprocess
import sys
import json

config_extension = ['.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.config']

# Function to load cryptographic terms and libraries from JSON file
def load_crypto_data(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data['crypto_terms'], data['crypto_libraries']


def clone_repo(repo_url, local_dir):
    """Clone the Github repository to a local directory"""
    if not os.path.exists(local_dir):
        subprocess.run(["git", "clone", repo_url, local_dir], check=True)
    else:
        print(f"Directory {local_dir} already exists. Skipping clone.")

def search_files(directory, terms, context_lines=2):
    """Search for cryptographic terms in all files of the given directory"""
    matches = {}
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if is_binary(file_path):
                continue
            with open(file_path, 'r', errors = 'ignore') as f:
                lines = f.readlines()
                for line_number, line in enumerate(f, start=1):
                    for term in terms:
                        if re.search(r'\b' +re.escape(term) + r'\b', line, re.IGNORECASE):
                            context = lines[max(0, line_number - context_lines - 1):min(len(lines),line_number + context_lines)]
                            if term not in matches:
                                matches[term] = []
                            matches[term].append({
                                'file': file_path, 
                                'line_number': line_number, 
                                'line': line.strip(),
                                'context': ''.join(context).strip()
                                })
    return matches

def detect_libraries(directory, libraries):
    libraries_found = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if 'requirements.txt' in file_path or 'setup.py' in file_path or 'package.json' in file_path:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                    for lib in libraries:
                        if re.search(r'\b' + re.escape(lib) + r'\b', content, re.IGNORECASE):
                            libraries_found.append((lib, file_path))
    return libraries_found

def analyze_config_files(directory, terms):
    """Analyze configuration files for crytographic settings."""
    config_matches = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in config_extension):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', errors='ignore') as f:
                    lines = f.readlines()
                    for line_number, line in enumerate(lines, start=1):
                        for term in terms:
                            if re.search(r'\b' + re.escape(term) + r'\b', line, re.IGNORECASE):
                                context = lines[max(0, line_number - 2):min(len(lines), line_number + 2)]
                                if term not in config_matches:
                                    config_matches[term] = []
                                config_matches[term].append({
                                    'file': file_path,
                                    'line_number': line_number,
                                    'line': line.strip(),
                                    'context': ''.join(context).strip()
                                })
    return config_matches

def is_binary(file_path):
    """Check if a file is binary"""
    with open(file_path, 'rb') as f:
        chunk = f.read(1024)
        return b'\0' in chunk
    
def save_matches_to_file(matches, libraries, config_matches, output_file):
    """Save the search results to a file"""
    report = {
        'cryptographic_terms': matches,
        'cryptographic_libraries': libraries,
        'configuration_matches': config_matches
    }
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=4)

def main(repo_url, json_file):
    local_dir = "cloned_repo"
    output_file = "crypto_search_results.txt"

    # Load cryptographic terms and libraries from JSON file
    crypto_terms, crypto_libraries = load_crypto_data(json_file)

    # Cloned the repository
    clone_repo(repo_url, local_dir)

    # Search for cryptographic terms
    matches = search_files(local_dir, crypto_terms)

    # Detect cryptographic libraries
    libraries = detect_libraries(local_dir, crypto_libraries)

    # Analyze configuration files
    config_matches = analyze_config_files(local_dir, crypto_terms)

    # Save the results to a file
    save_matches_to_file(matches, libraries, config_matches, output_file)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python crypto_assets.py <repository_url> <json file>")
        sys.exit(1)

    repo_url = sys.argv[1]
    json_file = sys.argv[2]
    main(repo_url, json_file)