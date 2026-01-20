#!/usr/bin/env python3
"""
PHN Network - Token Information
Display token information and statistics
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

NODE_URL = os.getenv("NODE_URL", "http://localhost:8765")

def get_token_info():
    """Get token information from node"""
    try:
        response = requests.get(f"{NODE_URL}/token_info", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting token info: {response.text}")
            return None
    except Exception as e:
        print(f"Network error: {e}")
        return None

def get_mining_info():
    """Get mining information from node"""
    try:
        response = requests.get(f"{NODE_URL}/mining_info", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except Exception as e:
        return {}

def display_token_info():
    """Display comprehensive token information"""
    print("PHN Network - Token Information")
    print("=" * 50)
    
    # Get token info
    token_info = get_token_info()
    if not token_info:
        print("Failed to retrieve token information")
        return
    
    # Get mining info
    mining_info = get_mining_info()
    
    # Display basic token info
    print(f"Name:              {token_info.get('name', 'N/A')}")
    print(f"Symbol:            PHN")
    print(f"Total Supply:      {token_info.get('total_supply', 0):,} PHN")
    print(f"Circulating:       {token_info.get('circulating_supply', 0):,.6f} PHN")
    print(f"Supply Left:       {token_info.get('supply_left', 0):,.6f} PHN")
    print(f"Company Holdings:  {token_info.get('company_holdings', 0):,.6f} PHN")
    
    # Calculate percentages
    total_supply = token_info.get('total_supply', 1)
    circulating = token_info.get('circulating_supply', 0)
    company_holdings = token_info.get('company_holdings', 0)
    
    circulation_pct = (circulating / total_supply) * 100 if total_supply > 0 else 0
    company_pct = (company_holdings / total_supply) * 100 if total_supply > 0 else 0
    
    print(f"\nDistribution:")
    print(f"Circulation Rate:  {circulation_pct:.2f}%")
    print(f"Company Holdings:  {company_pct:.2f}%")
    
    # Display mining info if available
    if mining_info:
        print(f"\nMining Information:")
        print(f"Current Difficulty: {mining_info.get('difficulty', 'N/A')}")
        print(f"Block Reward:      {mining_info.get('block_reward', 0):.6f} PHN")
        print(f"Minimum TX Fee:    {mining_info.get('min_tx_fee', 0):.6f} PHN")
        print(f"Current Block:     #{mining_info.get('current_block_height', 0)}")
        print(f"Pending TX:        {mining_info.get('pending_transactions', 0)}")
    
    print("=" * 50)

def save_token_info():
    """Save token information to JSON file"""
    token_info = get_token_info()
    mining_info = get_mining_info()
    
    if token_info:
        # Combine token and mining info
        combined_info = {**token_info, **mining_info}
        
        with open("token_info.json", "w") as f:
            f.write(orjson.dumps(combined_info, option=orjson.OPT_INDENT_2))
        
        print("Token information saved to token_info.json")
        return True
    
    return False

def main():
    """Main token info interface"""
    try:
        display_token_info()
        
        save_choice = input("\nSave token info to file? (y/N): ").strip().lower()
        if save_choice == 'y':
            save_token_info()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
