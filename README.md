# Elixr - Crypto Trading Signal Bot

A sophisticated crypto trading signal bot that monitors Twitter accounts, analyzes content using AI, generates trading signals, and sends them via Telegram.

## Features

- 🤖 **AI-Powered Analysis**: Uses OpenAI GPT-4 for content analysis
- 📱 **Telegram Integration**: Real-time signal delivery via Telegram bot
- 🐦 **Twitter Monitoring**: Monitors specified Twitter accounts for trading signals
- 📊 **Signal Generation**: Generates buy/sell signals based on AI analysis
- 🎥 **Video Analysis**: Analyzes video content for trading insights
- 💾 **Database Storage**: SQLite database for signal storage and user management
- 🔄 **Real-time Updates**: Continuous monitoring and signal generation

## Quick Start

### Prerequisites

- Python 3.9+
- Telegram Bot Token
- OpenAI API Key
- Twitter API Credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Elixr
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API keys
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. Run the bot:
```bash
python main.py
```

## 🚀 Cloud Deployment (Recommended)

### Deploy to Railway (Easiest & Cheapest)

Railway is the perfect hosting solution for your bot - it solves the "multiple instance" conflict issues and provides 24/7 operation.

#### Step 1: Prepare Your Repository
1. Make sure your code is in a Git repository (GitHub, GitLab, etc.)
2. Ensure you have these files in your project:
   - `requirements.txt`
   - `Procfile` (already exists)
   - `railway.json` (already created)

#### Step 2: Deploy to Railway
1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** account
3. **Create new project** → "Deploy from GitHub repo"
4. **Select your Elixr repository**
5. **Add environment variables**:
   ```
   TELEGRAM_BOT_TOKEN=your_new_bot_token
   OPENAI_API_KEY=your_openai_key
   TWITTER_BEARER_TOKEN=your_twitter_token
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_secret
   ```
6. **Deploy** - Railway will automatically build and start your bot

#### Step 3: Verify Deployment
- Check the Railway dashboard for deployment status
- Your bot will be running 24/7 without conflicts
- Monitor logs in the Railway dashboard

### Alternative: Deploy to Render

1. **Sign up** at [render.com](https://render.com)
2. **Create new Web Service**
3. **Connect your repository**
4. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
5. **Add environment variables** (same as Railway)
6. **Deploy**

## Telegram Bot Commands

Once deployed, your bot will respond to these commands:

- `/start` - Welcome message with interactive buttons
- `/help` - Show all available commands
- `/signals` - Show recent trading signals
- `/stats` - Show trading statistics
- `/settings` - Configure your preferences
- `/monitor <username>` - Add Twitter account to monitor
- `/list` - Show all monitored Twitter accounts

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Twitter API
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Database
DATABASE_URL=sqlite:///trading_signals.db

# Logging
LOG_LEVEL=INFO
```

### Twitter Account Monitoring

Add Twitter accounts to monitor by sending `/monitor <username>` to your bot.

## Project Structure

```
Elixr/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku/Railway deployment config
├── railway.json           # Railway deployment config
├── config/
│   └── config.yaml        # Configuration file
├── src/
│   ├── ai/
│   │   └── analyzer.py    # AI content analysis
│   ├── database/
│   │   ├── models.py      # Database models
│   │   └── operations.py  # Database operations
│   ├── signals/
│   │   └── generator.py   # Signal generation logic
│   ├── telegram/
│   │   └── bot.py         # Telegram bot implementation
│   └── twitter/
│       └── monitor.py     # Twitter monitoring
├── scripts/
│   └── init_db.py         # Database initialization
└── tests/
    └── test_signal_generator.py
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Database Operations

```bash
# Initialize database
python scripts/init_db.py

# View database contents
sqlite3 trading_signals.db
```

## Troubleshooting

### Common Issues

1. **Telegram Bot Conflict Error**
   - **Local**: Ensure only one instance is running
   - **Cloud**: Use Railway/Render for automatic process management

2. **Twitter API Errors**
   - Check your Twitter API credentials
   - Ensure you have the correct access level

3. **OpenAI API Errors**
   - Verify your OpenAI API key
   - Check your API usage limits

### Cloud Deployment Benefits

- ✅ **No more conflict errors** - Single instance management
- ✅ **24/7 operation** - Always running
- ✅ **Automatic restarts** - Self-healing
- ✅ **Easy scaling** - Handle more users
- ✅ **Professional logs** - Better debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the deployment guides above 