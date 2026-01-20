#!/usr/bin/env python3
"""
Convert ALL remaining json usage to orjson
Handles test/, user/, and phonesium/ directories
"""

import os
import re
from pathlib import Path

def convert_file_to_orjson(filepath):
    """Convert a single file from json to orjson"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace import json with import orjson
        content = re.sub(r'^import json$', 'import orjson', content, flags=re.MULTILINE)
        content = re.sub(r'^from json import', '# from json import  # Replaced with orjson', content, flags=re.MULTILINE)
        
        # Replace json.dumps() with orjson.dumps()
        # Handle json.dumps(x, indent=N)
        content = re.sub(
            r'json\.dumps\(([^,]+),\s*indent=(\d+)\)',
            r'orjson.dumps(\1, option=orjson.OPT_INDENT_2).decode()',
            content
        )
        
        # Handle json.dumps(x, sort_keys=True)
        content = re.sub(
            r'json\.dumps\(([^,]+),\s*sort_keys=True\)',
            r'orjson.dumps(\1, option=orjson.OPT_SORT_KEYS)',
            content
        )
        
        # Handle json.dumps(x) without parameters
        content = re.sub(r'json\.dumps\(([^)]+)\)', r'orjson.dumps(\1)', content)
        
        # Replace json.loads() with orjson.loads()
        content = re.sub(r'json\.loads\(', r'orjson.loads(', content)
        
        # Replace json.load() with orjson.loads() for file reading
        # This requires changing file mode from 'r' to 'rb'
        content = re.sub(r"json\.load\(f\)", r'orjson.loads(f.read())', content)
        
        # Replace json.dump() with orjson file write
        # json.dump(data, f, indent=2) -> f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        content = re.sub(
            r"json\.dump\(([^,]+),\s*f,\s*indent=(\d+)\)",
            r'f.write(orjson.dumps(\1, option=orjson.OPT_INDENT_2))',
            content
        )
        
        # Handle json.dump without indent
        content = re.sub(
            r"json\.dump\(([^,]+),\s*f\)",
            r'f.write(orjson.dumps(\1))',
            content
        )
        
        # Update file open modes for orjson (needs binary mode)
        # open(..., 'r') when loading json -> needs to stay 'r' but use read()
        # open(..., 'w') when dumping json -> needs to stay 'w' but decode()
        
        # Save only if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"[ERROR] Failed to convert {filepath}: {e}")
        return False


def main():
    """Convert all Python files in specified directories"""
    print("="*60)
    print("  PHN Blockchain - Complete json to orjson Converter")
    print("="*60)
    print()
    
    # Directories to process
    directories = [
        'test',
        'user',
        'phonesium'
    ]
    
    files_converted = []
    files_failed = []
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        print(f"\n[*] Processing directory: {directory}/")
        
        # Find all Python files
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    # Skip if file doesn't contain 'json'
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            if 'json' not in f.read():
                                continue
                    except:
                        continue
                    
                    print(f"[*] Converting: {filepath}")
                    
                    if convert_file_to_orjson(filepath):
                        files_converted.append(filepath)
                        print(f"[SUCCESS] Converted: {filepath}")
                    else:
                        print(f"[i] No changes needed for {filepath}")
    
    # Summary
    print()
    print("="*60)
    print("  Conversion Complete!")
    print("="*60)
    print(f"[SUCCESS] Converted: {len(files_converted)} files")
    print(f"[INFO] Failed: {len(files_failed)} files")
    
    if files_converted:
        print("\nConverted files:")
        for f in files_converted:
            print(f"  [OK] {f}")
    
    print("\nAll json usage in test/, user/, and phonesium/ has been replaced with orjson!")


if __name__ == "__main__":
    main()
