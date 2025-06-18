#!/bin/bash

# Elixr Bot Startup Script for Railway
echo "🚀 Starting Elixr Trading Bot..."

# Check if environment variables are set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN is not set"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY is not set"
    exit 1
fi

echo "✅ Environment variables are set"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the bot
echo "🤖 Starting bot..."
python main.py 