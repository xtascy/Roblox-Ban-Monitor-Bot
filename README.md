# Roblox Account Manager Discord Bot

A Discord bot for managing and monitoring Roblox accounts, with features for tracking ban status and handling appeals.

## Features

- **Account Management**
  - Add/remove Roblox accounts
  - Monitor multiple accounts simultaneously
  - Validate account credentials
  - List all registered accounts with status

- **Ban Monitoring**
  - Real-time ban detection
  - Detailed ban information including:
    - Ban duration
    - Ban end date
    - Game/place where ban occurred
    - Ban reason
  - Appeal system integration
  - Public ban status checking

- **Commands**
  - `!add_account <username> <token>` - Add a Roblox account
  - `!remove_account <username>` - Remove an account
  - `!list_accounts` - Show all registered accounts with status
  - `!validate` - Validate all account credentials
  - `!checkban <username>` (aliases: `!bancheck`, `!checkstatus`) - Check ban status for any Roblox user
  - `!restart` - Restart the bot (Admin only)
  - 
## Quick Setup

Run the interactive setup script:
```bash
python setup.py
```

This will guide you through:
1. Discord bot configuration
2. Main Roblox account setup
3. Additional accounts (optional)
4. Creating necessary config files

Or follow the manual setup instructions below:
[rest of the README remains the same]

## Setup

1. Clone the repository
2. Install requirements:
       bash
        pip install -r requirements.txt

3. Configure `config.json`:


```json
{
  "discord_bot_token": "YOUR_DISCORD_BOT_TOKEN",
  "log_channel_id": "YOUR_LOG_CHANNEL_ID",
  "appeal_url": "YOUR_APPEAL_FORM_URL",
  "mod_role_id": "YOUR_MOD_ROLE_ID",
  "private_ban_checks": false
}

```
Replace YOUR_DISCORD_BOT_TOKEN with your bot's token.
Replace YOUR_LOG_CHANNEL_ID with the ID of the channel where logs will be posted.
Replace YOUR_APPEAL_FORM_URL with the URL for the appeal form.
Replace YOUR_MOD_ROLE_ID with the ID of the moderator role.
Set private_ban_checks to true if you want to enable private checks for bans, otherwise leave it as false.


4. Create or modify the .env file with the following environment variables:
```.env
ROBLOX_USERNAME=main_account_username
ROBLOX_API_TOKEN=main_account_token
```
Replace main_account_username with your Roblox account username.
Replace main_account_token with your Roblox account .ROBOSECURITYTOKEN.

YOUR TOKEN SHOULD ONLY BE NUMBERS. DO NOT INCLUDE ANYTHING BEFORE.

## Configuration Options

- `discord_bot_token`: Your Discord bot token
- `log_channel_id`: Channel ID for bot notifications
- `appeal_url`: URL to your ban appeal form (optional)
- `mod_role_id`: Role ID for moderators who handle appeals
- `private_ban_checks`: Send ban check results via DM if true

## Security Features

- Automatic token validation
- Secure credential storage
- Message deletion for sensitive commands
- Permission-based command access

## Error Handling

- DNS resolution checks
- Connection timeout handling
- Detailed error logging
- User-friendly error messages

## Requirements

- Python 3.8+
- discord.py
- aiohttp
- python-dotenv
- Additional requirements in `requirements.txt`

## License

UNDER THE GNU LICENSE
