# Roblox Account Monitor

A Discord bot that monitors multiple Roblox accounts for bans, unbans, and authorization issues in real-time.

## Features
- Monitor multiple Roblox accounts simultaneously
- Real-time ban/unban notifications
- Account credential validation
- Discord commands for account management
- Secure token handling

## Prerequisites
- Python 3.8+
- Discord Bot Token
- Roblox Account Credentials

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/roblox-account-monitor.git
cd roblox-account-monitor
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure your environment

Create a `.env` file in the root directory:
```env
# Main Roblox Account
ROBLOX_TOKEN=your_main_account_token
ROBLOX_USERNAME=your_main_account_username

# Additional Accounts (Optional)
ROBLOX_ACCOUNT_username1=token1
ROBLOX_ACCOUNT_username2=token2
```

Create a `config.json` file:
```json
{
    "discord_bot_token": "your_discord_bot_token",
    "log_channel_id": your_discord_channel_id
}
```

## Usage

Start the bot:
```bash
python main.py
```

# Make sure that you have the intents enabled in the discord developer portal
# WHEN ENTERING TOKEN MAKE SURE TO REMOVE EVERYTHING BEFORE THE TOKEN

### Discord Commands
- `!list_accounts` - Show all monitored accounts
- `!add_account <username> <token>` - Add a new account to monitor
- `!remove_account <username>` - Remove an account from monitoring
- `!validate` - Check all account credentials
- `!restart` - Restart the bot (Admin only)

## Security
- Tokens are stored securely in .env file
- Messages containing tokens are automatically deleted
- Token validation before adding accounts
- Admin-only commands for sensitive operations

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the  GNU GENERAL PUBLIC LICENSE License

## Acknowledgments
- Discord.py library
- Roblox API documentation
- Python-dotenv

## Support
For support, please open an issue in the GitHub repository.
