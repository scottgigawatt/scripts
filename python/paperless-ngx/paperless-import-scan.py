import os
import shutil
import hashlib
import argparse
import sys
from collections import defaultdict
from pathlib import Path
from termcolor import colored

def get_file_hash(file_path, block_size=65536):
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b""):
                hasher.update(block)
        return hasher.hexdigest()
    except Exception as e:
        print(colored(f"Error reading {file_path}: {e}", "red"))
        return None

def find_documents(source_dirs, file_types):
    found_files = []
    for source_dir in source_dirs:
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(file_types):
                    full_path = os.path.join(root, file)
                    found_files.append(full_path)
    return found_files

def scan_and_copy(source_dirs, target_dir, dry_run):
    file_types = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".odt", ".rtf")
    found_files = find_documents(source_dirs, file_types)

    if not found_files:
        print(colored("No document files found.", "yellow"))
        return

    # Statistics
    file_stats = defaultdict(list)
    total_size = 0
    hash_set = set()

    for file in found_files:
        file_ext = Path(file).suffix.lower()
        file_size = os.path.getsize(file)
        total_size += file_size
        file_stats[file_ext].append((file, file_size))

        # Generate hash for duplicate check
        file_hash = get_file_hash(file)
        if file_hash:
            if file_hash in hash_set:
                print(colored(f"Skipping duplicate: {file}", "red"))
                continue
            hash_set.add(file_hash)

        if dry_run:
            print(colored(f"[Dry Run] Found: {file} ({file_size / 1024:.2f} KB)", "cyan"))
        else:
            dest_path = os.path.join(target_dir, os.path.basename(file))
            shutil.copy2(file, dest_path)
            print(colored(f"Copied: {file} -> {dest_path}", "green"))

    # Summary
    print(colored("\nSummary:", "blue"))
    for ext, files in file_stats.items():
        total_type_size = sum(size for _, size in files)
        print(colored(f"{ext}: {len(files)} files, {total_type_size / (1024 * 1024):.2f} MB", "magenta"))
    print(colored(f"Total files: {len(found_files)}", "yellow"))
    print(colored(f"Total size: {total_size / (1024 * 1024):.2f} MB", "yellow"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan and copy documents for Paperless-NGX processing.")
    parser.add_argument("-s", "--source", nargs='+', required=True, help="Source directories to scan (multiple allowed)")
    parser.add_argument("-t", "--target", required=True, help="Destination directory to copy files")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without copying files")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    for src in args.source:
        if not os.path.exists(src):
            print(colored(f"Source directory does not exist: {src}", "red"))
            sys.exit(1)

    os.makedirs(args.target, exist_ok=True)

    scan_and_copy(args.source, args.target, args.dry_run)
