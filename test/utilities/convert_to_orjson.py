#!/usr/bin/env python3
"""
PHN Blockchain - Convert ALL json to orjson
This script automatically replaces all json usage with orjson
"""
import os
import re

# Files to update
FILES_TO_UPDATE = [
    "app/api/v1/endpoints/blockchain.py",
    "app/b.py",
    "app/core/transactions_secure.py",
    "app/core/tunnel_transfer.py",
    "app/info.py",
    "app/utils/helpers.py",
    "app/utils/secure_wallet.py",
    "app/utils/wallet_generator.py",
]

def convert_file(filepath):
    """Convert a file from json to orjson"""
    print(f"[*] Processing: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace import json with import orjson
    content = re.sub(r'^import json$', 'import orjson', content, flags=re.MULTILINE)
    
    # Replace json.dumps() with orjson.dumps()
    # json.dumps(data) -> orjson.dumps(data)
    content = re.sub(r'json\.dumps\(([^,)]+)\)', r'orjson.dumps(\1)', content)
    
    # json.dumps(data, indent=X) -> orjson.dumps(data, option=orjson.OPT_INDENT_2)
    content = re.sub(r'json\.dumps\(([^,)]+),\s*indent=\d+\)', 
                     r'orjson.dumps(\1, option=orjson.OPT_INDENT_2)', content)
    
    # json.dumps(data, sort_keys=True) -> orjson.dumps(data, option=orjson.OPT_SORT_KEYS)
    content = re.sub(r'json\.dumps\(([^,)]+),\s*sort_keys=True\)', 
                     r'orjson.dumps(\1, option=orjson.OPT_SORT_KEYS)', content)
    
    # json.dumps(data, sort_keys=True).encode() -> orjson.dumps(data, option=orjson.OPT_SORT_KEYS)
    content = re.sub(r'json\.dumps\(([^,)]+),\s*sort_keys=True\)\.encode\(\)', 
                     r'orjson.dumps(\1, option=orjson.OPT_SORT_KEYS)', content)
    
    # Replace json.loads() with orjson.loads()
    content = re.sub(r'json\.loads\(([^)]+)\.decode\(\)\)', r'orjson.loads(\1)', content)
    content = re.sub(r'json\.loads\(([^)]+)\.decode\(["\']utf-8["\']\)\)', r'orjson.loads(\1)', content)
    content = re.sub(r'json\.loads\(', r'orjson.loads(', content)
    
    # Replace json.load() with orjson.loads(f.read())
    content = re.sub(r'json\.load\(f\)', r'orjson.loads(f.read())', content)
    
    # Replace json.dump() with f.write(orjson.dumps())
    # json.dump(data, f) -> f.write(orjson.dumps(data))
    content = re.sub(r'json\.dump\(([^,]+),\s*f\)', r'f.write(orjson.dumps(\1))', content)
    
    # json.dump(data, f, indent=X) -> f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    content = re.sub(r'json\.dump\(([^,]+),\s*f,\s*indent=\d+\)', 
                     r'f.write(orjson.dumps(\1, option=orjson.OPT_INDENT_2))', content)
    
    # Fix file open modes for orjson (binary mode)
    content = re.sub(r'open\(([^,]+),\s*["\']w["\']\)', r'open(\1, "wb")', content)
    content = re.sub(r'open\(([^,]+),\s*["\']r["\']\)', r'open(\1, "rb")', content)
    
    if content == original_content:
        print(f"[i] No changes needed for {filepath}")
        return True
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[SUCCESS] Updated: {filepath}")
    return True

def main():
    print("="*60)
    print("  PHN Blockchain - json to orjson Converter")
    print("="*60 + "\n")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    success_count = 0
    fail_count = 0
    
    for filepath in FILES_TO_UPDATE:
        if convert_file(filepath):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "="*60)
    print(f"  Conversion Complete!")
    print("="*60)
    print(f"[SUCCESS] Success: {success_count} files")
    print(f"[FAILED] Failed: {fail_count} files")
    print("\nAll json usage has been replaced with orjson!")
    print("System is now using fast orjson for maximum performance.")
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERROR] Conversion failed: {e}")
        sys.exit(1)
