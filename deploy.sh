#!/bin/bash

# Elixr Bot Deployment Script
# This script helps you deploy your bot to Railway

echo "🚀 Elixr Bot Deployment Helper"
echo "================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found!"
    echo "Please initialize git and push your code to GitHub first:"
    echo "  git init"
    echo "  git add ."
    echo "  git commit -m 'Initial commit'"
    echo "  git remote add origin <your-github-repo-url>"
    echo "  git push -u origin main"
    exit 1
fi

echo "✅ Git repository found"

# Check if required files exist
echo "📋 Checking required files..."

required_files=("requirements.txt" "Procfile" "railway.json" "main.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🎯 Ready for Railway deployment!"
echo ""
echo "📝 Next steps:"
echo "1. Go to https://railway.app"
echo "2. Sign up/Login with GitHub"
echo "3. Click 'New Project' → 'Deploy from GitHub repo'"
echo "4. Select your Elixr repository"
echo "5. Add these environment variables:"
echo ""
echo "   TELEGRAM_BOT_TOKEN=your_new_bot_token"
echo "   OPENAI_API_KEY=your_openai_key"
echo "   TWITTER_BEARER_TOKEN=your_twitter_token"
echo "   TWITTER_API_KEY=your_twitter_api_key"
echo "   TWITTER_API_SECRET=your_twitter_secret"
echo "   TWITTER_ACCESS_TOKEN=your_twitter_access_token"
echo "   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_secret"
echo ""
echo "6. Click 'Deploy Now'"
echo ""
echo "🎉 Your bot will be running 24/7 without conflicts!"
echo ""
echo "💡 Benefits of Railway deployment:"
echo "   ✅ No more 'multiple instance' errors"
echo "   ✅ 24/7 operation"
echo "   ✅ Automatic restarts"
echo "   ✅ Professional logging"
echo "   ✅ Easy scaling" 