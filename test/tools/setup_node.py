#!/usr/bin/env python3
"""
PHN Blockchain - Automated Setup Script
Run this to set up everything automatically!
"""
import os
import sys
import subprocess
import platform

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"[*] {description}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, executable='/bin/bash')
        print(f"[[OK]] {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[[FAIL]] {description} - FAILED")
        print(f"    Error: {e.stderr}")
        return False

def main():
    print_header("PHN Blockchain - Automated Setup")
    
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    print(f"[i] Project Directory: {project_root}")
    print(f"[i] Python Version: {sys.version}")
    print(f"[i] Platform: {platform.system()}")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("[[FAIL]] Python 3.8 or higher required!")
        sys.exit(1)
    
    print_header("Step 1: Create Virtual Environment")
    
    venv_path = os.path.join(project_root, "venv")
    
    if os.path.exists(venv_path):
        print("[i] Virtual environment already exists")
    else:
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            print("[!] Failed to create virtual environment")
            sys.exit(1)
    
    print_header("Step 2: Install Dependencies")
    
    # Determine pip path
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
    
    # Upgrade pip
    run_command(f'"{pip_path}" install --upgrade pip', "Upgrading pip")
    
    # Install requirements
    requirements_file = os.path.join(project_root, "requirements.txt")
    if not run_command(f'"{pip_path}" install -r "{requirements_file}"', "Installing dependencies"):
        print("[!] Failed to install dependencies")
        sys.exit(1)
    
    print_header("Step 3: Initialize Database")
    
    # Create lmdb_data directory if it doesn't exist
    lmdb_dir = os.path.join(project_root, "lmdb_data")
    if not os.path.exists(lmdb_dir):
        os.makedirs(lmdb_dir)
        print("[[OK]] Created LMDB data directory")
    else:
        print("[i] LMDB data directory already exists")
    
    print_header("Setup Complete!")
    
    print("[OK] Virtual environment created")
    print("[OK] Dependencies installed")
    print("[OK] Database initialized")
    print("\n" + "="*60)
    print("  HOW TO RUN:")
    print("="*60 + "\n")
    
    if platform.system() == "Windows":
        print("  1. Activate environment:")
        print("     venv\\Scripts\\activate")
        print("\n  2. Start the node:")
        print("     python app/main.py")
    else:
        print("  1. Activate environment:")
        print("     source venv/bin/activate")
        print("\n  2. Start the node:")
        print("     python app/main.py")
    
    print("\n  3. Access API:")
    print("     http://localhost:8545/api/v1/info")
    print("\n" + "="*60 + "\n")
    
    print("[i] See SETUP.md for more details")
    print("[i] See README.md for API documentation")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[[FAIL]] Setup failed: {e}")
        sys.exit(1)
