#!/usr/bin/env python3
"""
API Key Configuration Helper

This script helps you set up API keys for the XAUUSD Gold AI Analyst.
Run this script and follow the prompts to configure your API keys.
"""

import os
import sys
from pathlib import Path


def get_env_file_path():
    """Get or create .env file path."""
    env_path = Path(__file__).parent.parent / ".env"
    
    # Create .env from .env.example if it doesn't exist
    if not env_path.exists():
        env_example = Path(__file__).parent.parent / ".env.example"
        if env_example.exists():
            with open(env_example, "r") as f:
                content = f.read()
            with open(env_path, "w") as f:
                f.write(content)
            print(f"Created .env file from .env.example")
    
    return env_path


def load_current_keys():
    """Load current API keys from .env file."""
    env_path = get_env_file_path()
    keys = {}
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    keys[key.strip()] = value.strip()
    
    return keys


def save_api_key(key_name: str, value: str):
    """Save API key to .env file."""
    env_path = get_env_file_path()
    keys = load_current_keys()
    keys[key_name] = value
    
    # Write back to file
    lines = []
    keys_written = set()
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    lines.append(line)
                else:
                    key = stripped.split("=")[0].strip()
                    if key in keys and key not in keys_written:
                        lines.append(f"{key}={keys[key]}\n")
                        keys_written.add(key)
                    elif key not in keys:
                        lines.append(line)
    
    # Add any missing keys
    for key, value in keys.items():
        if key not in keys_written:
            lines.append(f"{key}={value}\n")
    
    with open(env_path, "w") as f:
        f.writelines(lines)
    
    print(f"  Saved {key_name}")


def check_key_availability(key_name: str) -> bool:
    """Check if a key is set in environment."""
    return bool(os.getenv(key_name))


def print_status_table(keys_needed: dict, keys_current: dict):
    """Print status of API keys."""
    print("\n" + "=" * 60)
    print("API Key Configuration Status")
    print("=" * 60)
    print(f"{'API Key':<30} {'Status':<15} {'Required'}")
    print("-" * 60)
    
    for key, info in keys_needed.items():
        current = keys_current.get(key, "")
        is_set = bool(current and current != f"your-{key.lower()}-key")
        
        status = "✅ Configured" if is_set else "❌ Not Set"
        required = "Yes" if info.get("required") else "No"
        
        print(f"{key:<30} {status:<15} {required}")
    
    print("-" * 60)
    print("\nRequired for basic functionality (no API keys needed):")
    print("  - Price data: Uses Yahoo Finance (free, no key)")
    print("  - CFTC data: Public data from CFTC.gov")
    print("\nOptional but recommended:")
    print("  - News data: NewsAPI (free tier: 100 req/day)")
    print("  - Macro data: FRED API (completely free)")


def main():
    """Main configuration flow."""
    print("\n" + "=" * 60)
    print("XAUUSD Gold AI Analyst - API Configuration")
    print("=" * 60)
    
    # Define required keys
    keys_needed = {
        "FRED_API_KEY": {
            "name": "FRED API Key",
            "description": "Federal Reserve Economic Data - completely free",
            "url": "https://fred.stlouisfed.org/docs/api/api_key.html",
            "required": False,
        },
        "NEWS_API_KEY": {
            "name": "NewsAPI Key",
            "description": "News data (free tier: 100 requests/day)",
            "url": "https://newsapi.org/register",
            "required": False,
        },
    }
    
    # Load current keys
    keys_current = load_current_keys()
    
    # Show status
    print_status_table(keys_needed, keys_current)
    
    # Ask if user wants to configure keys
    print("\nWould you like to configure API keys?")
    print("  1. Configure FRED API Key (recommended - free)")
    print("  2. Configure NewsAPI Key")
    print("  3. Configure both")
    print("  4. Skip configuration (use mock data)")
    print("  5. Check key status and exit")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
    except EOFError:
        choice = "5"
    
    if choice == "1":
        key = "FRED_API_KEY"
        print(f"\n--- Configuring {key} ---")
        print("Get your free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        value = input("Enter your FRED API key: ").strip()
        if value:
            save_api_key(key, value)
            print(f"✅ {key} configured successfully!")
    
    elif choice == "2":
        key = "NEWS_API_KEY"
        print(f"\n--- Configuring {key} ---")
        print("Get your free key at: https://newsapi.org/register")
        value = input("Enter your NewsAPI key: ").strip()
        if value:
            save_api_key(key, value)
            print(f"✅ {key} configured successfully!")
    
    elif choice == "3":
        for key in ["FRED_API_KEY", "NEWS_API_KEY"]:
            print(f"\n--- Configuring {key} ---")
            print(f"Info: {keys_needed[key]['description']}")
            print(f"URL: {keys_needed[key]['url']}")
            value = input(f"Enter your {key} (or press Enter to skip): ").strip()
            if value:
                save_api_key(key, value)
                print(f"✅ {key} configured!")
    
    elif choice == "4":
        print("\nSkipping configuration.")
        print("The system will use mock data for missing sources.")
        print("You can run this script later to configure keys.")
    
    elif choice == "5":
        print("\nExiting. Run this script anytime to configure keys.")
    
    else:
        print("\nInvalid choice. Exiting.")
    
    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
