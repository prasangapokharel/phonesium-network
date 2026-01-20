#!/usr/bin/env python3
"""
PHN Blockchain - Comprehensive Test Suite Runner
Runs all tests and reports results
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_test_file(filepath, description):
    """Run a test file and return results"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"File: {filepath}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout + result.stderr
        success = result.returncode == 0
        
        # Parse results from output
        if "tests passed (100" in output or "All" in output and "passed" in output:
            status = "[PASS]"
        elif "PASS" in output and "FAIL" not in output:
            status = "[PASS]"
        elif result.returncode == 0:
            status = "[PASS]"
        else:
            status = "[FAIL]"
            
        return {
            'name': description,
            'status': status,
            'success': success,
            'output': output
        }
        
    except subprocess.TimeoutExpired:
        return {
            'name': description,
            'status': "[TIMEOUT]",
            'success': False,
            'output': "Test timed out after 120 seconds"
        }
    except Exception as e:
        return {
            'name': description,
            'status': "[ERROR]",
            'success': False,
            'output': str(e)
        }


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PHN BLOCKCHAIN - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("Running all tests to verify system integrity...")
    print("="*80)
    
    test_suite = [
        ("tools/final_verification.py", "Final Verification - Module & Performance Tests"),
        ("unit/test_security_fixes.py", "Security Tests - Attack Prevention"),
        ("unit/test_encryption.py", "Encryption Tests - Wallet Security"),
        ("unit/test_assets.py", "Asset Tests - Tokenization"),
        ("unit/test_sdk.py", "SDK Tests - Phonesium Library"),
    ]
    
    results = []
    
    for filepath, description in test_suite:
        if os.path.exists(filepath):
            result = run_test_file(filepath, description)
            results.append(result)
        else:
            print(f"\n[SKIPPED]: {description} (file not found: {filepath})")
            results.append({
                'name': description,
                'status': "[SKIP]",
                'success': False,
                'output': f"File not found: {filepath}"
            })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        print(f"{result['status']:<15} {result['name']}")
    
    print("="*80)
    print(f"Results: {passed}/{total} test suites passed ({passed/total*100:.1f}%)")
    print("="*80)
    
    if passed == total:
        print("\n[SUCCESS]: All test suites passed!")
        print("The PHN Blockchain system is fully tested and ready for production.")
        return 0
    else:
        print(f"\n[WARNING]: {total - passed} test suite(s) failed")
        print("\nFailed Tests:")
        for result in results:
            if not result['success']:
                print(f"\n  - {result['name']}")
                print(f"    Status: {result['status']}")
                # Print last 10 lines of output
                lines = result['output'].split('\n')
                relevant_lines = [l for l in lines[-15:] if l.strip()]
                for line in relevant_lines:
                    print(f"    {line}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
