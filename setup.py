import os
import json
import getpass
import sys
import time
import traceback

def get_file_path(filename):
    """Get a writable file path in the current directory"""
    try:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, filename)
        
        # Only test write permissions if file doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'a') as f:
                pass
            os.remove(file_path)  # Clean up test file
            
        return file_path
        
    except Exception as e:
        print(f"\n❌ Cannot write to script directory: {str(e)}")
        print("\nTrying to run with elevated privileges...")
        
        if sys.platform == 'win32':
            print("Please run the script as Administrator")
            print("Right-click the script and select 'Run as Administrator'")
        else:
            print("Please run the script with sudo")
            print("Example: sudo python setup.py")
            
        print("\nFull error:")
        traceback.print_exc()
        input("\nPress Enter to continue...")
        sys.exit(1)

def get_secure_input(prompt):
    """Safely get sensitive input"""
    try:
        return getpass.getpass(prompt)
    except getpass.GetPassWarning:
        return input(prompt + " (Warning: input may be visible): ")

def validate_channel_id(channel_id):
    """Validate channel ID is a number"""
    try:
        return int(channel_id)
    except ValueError:
        return None

def create_config():
    print("\n=== Discord Bot Configuration ===")
    print("Please follow these steps to configure your bot:")
    
    # Get Discord configuration
    print("\n1. Discord Bot Setup:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create a New Application")
    print("   - Go to Bot section and create a bot")
    print("   - Copy the bot token")
    token = input("Enter your Discord bot token: ")
    
    while True:
        print("\n2. Discord Channel Setup:")
        print("   - Right-click the channel you want to use for logs")
        print("   - Click 'Copy ID' (Enable Developer Mode if not visible)")
        channel_id = input("Enter the log channel ID: ")
        
        # Validate channel ID
        valid_id = validate_channel_id(channel_id)
        if valid_id:
            break
        print("❌ Invalid channel ID. Please enter a valid number.")
    
    # Create config.json
    config = {
        "discord_bot_token": token,
        "log_channel_id": valid_id,
        "private_ban_checks": False
    }
    
    config_path = get_file_path('config.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"\n✅ config.json created successfully at: {config_path}")
    except Exception as e:
        print(f"\n❌ Error creating config.json: {str(e)}")
        print("\nTrying to run with elevated privileges...")
        
        if sys.platform == 'win32':
            print("Please run the script as Administrator")
            print("Right-click the script and select 'Run as Administrator'")
        else:
            print("Please run the script with sudo")
            print("Example: sudo python setup.py")
            
        print("\nFull error:")
        traceback.print_exc()
        input("\nPress Enter to continue...")
        sys.exit(1)

def create_env():
    print("\n=== Roblox Account Configuration ===")
    print("\n3. Main Roblox Account Setup:")
    print("   - Go to Roblox and log into your main account")
    print("   - Press F12 to open Developer Tools")
    print("   - Go to Application > Cookies > .ROBLOSECURITY")
    print("   - Copy the cookie value")
    
    main_token = input("Enter your main account's .ROBLOSECURITY token: ")
    # Clean the token
    main_token = main_token.strip().strip('"').strip("'")
    # Handle warning message format
    if main_token.startswith('_|WARNING:'):
        main_token = main_token.split('|_', 2)[-1]
    # Handle dictionary format
    if main_token.startswith('{') and main_token.endswith('}'):
        main_token = main_token[1:-1]  # Remove { }
    
    main_username = input("Enter your main account's username: ")
    main_username = main_username.strip()  # Clean username
    
    # Create .env file with proper format
    env_content = [
        "# Main Roblox Account",
        f"ROBLOX_TOKEN='{main_token}'",  # Added quotes
        f"ROBLOX_USERNAME='{main_username}'",  # Added quotes
        "",
        "# Additional Accounts (Optional)",
        "# Format: ROBLOX_ACCOUNT_username=token"
    ]
    
    env_path = get_file_path('.env')
    try:
        # Write initial .env file
        with open(env_path, 'w') as f:
            f.write('\n'.join(env_content))
            f.write('\n')  # Add newline at end
        print(f"\n✅ .env file created successfully at: {env_path}")
        
        # Verify the file was written correctly
        with open(env_path, 'r') as f:
            content = f.read()
            print("\nVerifying .env content:")
            if f"ROBLOX_TOKEN='{main_token}'" in content:
                print("✅ Main token written correctly")
            else:
                print("❌ Main token not written correctly")
            if f"ROBLOX_USERNAME='{main_username}'" in content:
                print("✅ Main username written correctly")
            else:
                print("❌ Main username not written correctly")
            
    except Exception as e:
        print(f"\n❌ Error creating .env file: {str(e)}")
        print("\nTrying to run with elevated privileges...")
        
        if sys.platform == 'win32':
            print("Please run the script as Administrator")
            print("Right-click the script and select 'Run as Administrator'")
        else:
            print("Please run the script with sudo")
            print("Example: sudo python setup.py")
            
        print("\nFull error:")
        traceback.print_exc()
        input("\nPress Enter to continue...")
        sys.exit(1)

def add_additional_accounts():
    print("\n4. Additional Accounts (Optional):")
    while True:
        add_another = input("\nWould you like to add another account? (y/n): ").lower()
        if add_another != 'y':
            break
            
        username = input("Enter account username: ")
        username = username.strip()  # Clean username
        
        token = input("Enter account .ROBLOSECURITY token: ")
        # Clean the token
        token = token.strip().strip('"').strip("'")
        # Handle warning message format
        if token.startswith('_|WARNING:'):
            token = token.split('|_', 2)[-1]
        # Handle dictionary format
        if token.startswith('{') and token.endswith('}'):
            token = token[1:-1]  # Remove { }
        
        env_path = get_file_path('.env')
        try:
            # Check if file exists
            if not os.path.exists(env_path):
                print(f"\n❌ Error: .env file not found at: {env_path}")
                print("Please complete main account setup first.")
                return
            
            # Read existing content
            with open(env_path, 'r') as f:
                content = f.readlines()
            
            # Add new account
            content.append(f"ROBLOX_ACCOUNT_{username}='{token}'\n")
            
            # Write back all content
            with open(env_path, 'w') as f:
                f.writelines(content)
            print(f"✅ Account added successfully to: {env_path}")
            
            # Verify the account was added
            with open(env_path, 'r') as f:
                new_content = f.read()
                if f"ROBLOX_ACCOUNT_{username}='{token}'" in new_content:
                    print("✅ Account written correctly")
                else:
                    print("❌ Account not written correctly")
                    
        except Exception as e:
            print(f"\n❌ Error adding account: {str(e)}")
            print(f"Attempted to write to: {env_path}")
            print("\nFull error:")
            traceback.print_exc()
            input("\nPress Enter to continue...")

def check_files_exist():
    """Check if config files exist in script directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    env_path = os.path.join(script_dir, '.env')
    
    return os.path.exists(config_path), os.path.exists(env_path)

def main():
    print("""
╔════════════════════════════════════════╗
║     Roblox Account Monitor Setup       ║
╚════════════════════════════════════════╝
    """)
    
    try:
        # Check if files already exist
        config_exists, env_exists = check_files_exist()
        if config_exists or env_exists:
            print(f"Current directory: {os.path.dirname(os.path.abspath(__file__))}")
            if config_exists:
                print("✓ config.json exists")
            if env_exists:
                print("✓ .env exists")
                
            overwrite = input("\nExisting configuration found. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                print("Setup cancelled.")
                time.sleep(2)
                return
        
        create_config()
        create_env()
        add_additional_accounts()
        
        print("""
\n✨ Setup Complete! ✨
To start the bot, run: python main.py

Available commands:
!list_accounts - Show all monitored accounts
!add_account - Add a new account
!remove_account - Remove an account
!validate - Check all accounts
!bancheck - Check a single account - Public
!restart - Restart the bot (Admin only)
        """)
        
        # Keep console open
        input("\nPress Enter to exit...")
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        time.sleep(2)
        sys.exit(0)
    except Exception as e:
        print("\n❌ An error occurred during setup!")
        print("\nError details:")
        print(str(e))
        print("\nFull traceback:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
