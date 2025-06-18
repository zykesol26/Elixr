import logging
from typing import Dict, List, Optional
import yaml
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime
from ..database.operations import DatabaseOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, token: str, database_ops: DatabaseOperations, config_path: str = "config/config.yaml"):
        self.token = token
        self.database_ops = database_ops
        self.config = self._load_config(config_path)
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_handlers(self):
        """Set up command and callback handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("signals", self.signals_command))
        self.app.add_handler(CommandHandler("settings", self.settings_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("monitor", self.monitor_command))
        self.app.add_handler(CommandHandler("list", self.list_monitored_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        try:
            user_id = str(update.effective_user.id)  # type: ignore
            
            # Add user to database if not exists
            try:
                self.database_ops.add_user_preference(user_id)
                logger.info(f"New user registered: {user_id}")
            except Exception as e:
                logger.error(f"Error registering user {user_id}: {str(e)}")
                # Continue even if database registration fails
            
            welcome_message = self.config['telegram']['commands']['start']
            keyboard = [
                [InlineKeyboardButton("📊 Recent Signals", callback_data='recent_signals')],
                [InlineKeyboardButton("📈 Statistics", callback_data='stats')],
                [InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
                [InlineKeyboardButton("❓ Help", callback_data='help')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)  # type: ignore
            logger.info(f"Sent welcome message to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in start_command: {str(e)}")
            # Send a simple fallback message
            try:
                await update.message.reply_text("Welcome to Elixr Trading Bot! 🚀")  # type: ignore
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {str(fallback_error)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = self.config['telegram']['commands']['help']
        await update.message.reply_text(help_message)  # type: ignore
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command."""
        await self.show_recent_signals_message(update.message)  # type: ignore
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        await self.show_settings_message(update.message)  # type: ignore
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        await self.show_statistics_message(update.message)  # type: ignore
    
    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monitor command to add Twitter accounts to monitor."""
        try:
            if not context.args:
                await update.message.reply_text(  # type: ignore
                    "Usage: `/monitor <twitter_username>`\n\n"
                    "Example: `/monitor elonmusk`\n\n"
                    "This will add the Twitter account to monitor for trading signals.",
                    parse_mode='Markdown'
                )
                return
            
            username = context.args[0].replace('@', '')  # Remove @ if present
            user_id = str(update.effective_user.id)  # type: ignore
            
            # Add the account to database
            try:
                # For now, we'll use a placeholder Twitter ID
                # In a real implementation, you'd look up the Twitter ID from username
                twitter_id = f"placeholder_{username}"
                
                self.database_ops.add_monitored_account(twitter_id, username)
                
                await update.message.reply_text(  # type: ignore
                    f"✅ Successfully added `@{username}` to monitoring list!\n\n"
                    f"The bot will now analyze tweets from this account for trading signals.",
                    parse_mode='Markdown'
                )
                
                logger.info(f"User {user_id} added @{username} to monitoring list")
                
            except Exception as e:
                logger.error(f"Error adding monitored account: {str(e)}")
                await update.message.reply_text(  # type: ignore
                    f"❌ Error adding @{username} to monitoring list. Please try again."
                )
                
        except Exception as e:
            logger.error(f"Error in monitor_command: {str(e)}")
            await update.message.reply_text(  # type: ignore
                "❌ An error occurred. Please try again."
            )
    
    async def list_monitored_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command to show monitored Twitter accounts."""
        try:
            # Get monitored accounts from database
            accounts = self.database_ops.get_monitored_accounts()
            
            if not accounts:
                await update.message.reply_text(  # type: ignore
                    "📋 No Twitter accounts are currently being monitored.\n\n"
                    "Use `/monitor <username>` to add accounts to monitor."
                )
                return
            
            response = "📋 *Monitored Twitter Accounts:*\n\n"
            for i, account in enumerate(accounts, 1):
                status = "🟢 Active" if account.is_active else "🔴 Inactive"  # type: ignore
                response += f"{i}. @{account.username} - {status}\n"  # type: ignore
            
            response += "\nUse `/monitor <username>` to add more accounts."
            
            await update.message.reply_text(response, parse_mode='Markdown')  # type: ignore
            
        except Exception as e:
            logger.error(f"Error in list_monitored_command: {str(e)}")
            await update.message.reply_text(  # type: ignore
                "❌ Error retrieving monitored accounts. Please try again."
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()  # type: ignore
        
        if query.data == 'recent_signals':  # type: ignore
            await self.show_recent_signals(query)
        elif query.data == 'stats':  # type: ignore
            await self.show_statistics(query)
        elif query.data == 'settings':  # type: ignore
            await self.show_settings(query)
        elif query.data == 'help':  # type: ignore
            await self.show_help(query)
        elif query.data == 'notifications':  # type: ignore
            await self.show_notification_settings(query)
        elif query.data == 'pairs':  # type: ignore
            await self.show_trading_pairs(query)
        elif query.data == 'risk':  # type: ignore
            await self.show_risk_settings(query)
        elif query.data == 'back_to_main':  # type: ignore
            await self.show_main_menu(query)
        elif query.data.startswith('toggle_notification_'):  # type: ignore
            await self.toggle_notification(query)
        elif query.data.startswith('set_risk_'):  # type: ignore
            await self.set_risk_level(query)
    
    async def send_trading_signal(self, signal: Dict):
        """Send a formatted trading signal message to all active users."""
        try:
            # Get all active users
            active_users = self.database_ops.get_active_users()
            
            message = self.format_signal_message(signal)
            
            # Add inline buttons for actions
            keyboard = [
                [
                    InlineKeyboardButton("✅ Take Trade", callback_data=f'take_{signal["symbol"]}'),
                    InlineKeyboardButton("❌ Skip", callback_data='skip')
                ],
                [
                    InlineKeyboardButton("📊 Chart", callback_data=f'chart_{signal["symbol"]}'),
                    InlineKeyboardButton("ℹ️ More Info", callback_data=f'info_{signal["symbol"]}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to all active users
            for user in active_users:
                try:
                    # Check if user wants signal notifications
                    if user.notification_settings.get('signals', True):  # type: ignore
                        await self.app.bot.send_message(
                            chat_id=user.telegram_id,  # type: ignore
                            text=message,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                except Exception as e:
                    logger.error(f"Error sending signal to user {user.telegram_id}: {str(e)}")  # type: ignore
            
            logger.info(f"Sent trading signal to {len(active_users)} users")
            
        except Exception as e:
            logger.error(f"Error sending trading signal: {str(e)}")
    
    def format_signal_message(self, signal: Dict) -> str:
        """Format trading signal into a message."""
        emoji = "🟢" if signal['direction'] == "LONG" else "🔴"
        
        message = f"""
{emoji} *TRADING SIGNAL* {emoji}

*Symbol:* `{signal['symbol']}`
*Direction:* {signal['direction']}
*Entry:* `${signal['entry_price']:,.2f}`
*Stop Loss:* `${signal['stop_loss']:,.2f}`
*Take Profit:* {', '.join([f'`${tp:,.2f}`' for tp in signal['take_profit']])}
*Timeframe:* {signal['timeframe']}
*Confidence:* {signal['confidence']*100:.1f}%

*Analysis:* {signal['reasoning']}

_Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_
"""
        return message
    
    async def show_recent_signals_message(self, message):
        """Show recent trading signals."""
        try:
            signals = self.database_ops.get_recent_signals(5)
            
            if not signals:  # type: ignore
                await message.reply_text("No recent signals available.")
                return
            
            response = "*📊 Recent Trading Signals*\n\n"
            for i, signal in enumerate(signals, 1):
                emoji = "🟢" if signal.direction == "LONG" else "🔴"  # type: ignore
                response += f"{i}. {emoji} {signal.symbol} {signal.direction}\n"  # type: ignore
                response += f"   Entry: ${signal.entry_price:,.2f} | TP: ${signal.take_profit[0]:,.2f}\n"  # type: ignore
                response += f"   Confidence: {signal.confidence*100:.1f}%\n\n"  # type: ignore
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing recent signals: {str(e)}")
            await message.reply_text("Error retrieving recent signals.")
    
    async def show_recent_signals(self, query):
        """Show recent trading signals for callback queries."""
        try:
            signals = self.database_ops.get_recent_signals(5)
            
            if not signals:
                await query.edit_message_text("No recent signals available.")
                return
            
            response = "*📊 Recent Trading Signals*\n\n"
            for i, signal in enumerate(signals, 1):
                emoji = "🟢" if signal.direction == "LONG" else "🔴"
                response += f"{i}. {emoji} {signal.symbol} {signal.direction}\n"
                response += f"   Entry: ${signal.entry_price:,.2f} | TP: ${signal.take_profit[0]:,.2f}\n"
                response += f"   Confidence: {signal.confidence*100:.1f}%\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing recent signals: {str(e)}")
            await query.edit_message_text("Error retrieving recent signals.")
    
    async def show_statistics_message(self, message):
        """Show trading statistics."""
        try:
            stats = self.database_ops.get_signal_statistics(30)
            
            response = "*📈 Trading Statistics (Last 30 Days)*\n\n"
            response += f"📊 Total Signals: {stats['total_signals']}\n"
            response += f"✅ Executed: {stats['executed_signals']}\n"
            response += f"🔒 Closed: {stats['closed_signals']}\n"
            response += f"💰 Profitable: {stats['profitable_signals']}\n"
            response += f"📈 Success Rate: {stats['success_rate']:.1f}%\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing statistics: {str(e)}")
            await message.reply_text("Error retrieving statistics.")
    
    async def show_statistics(self, query):
        """Show trading statistics for callback queries."""
        try:
            stats = self.database_ops.get_signal_statistics(30)
            
            response = "*📈 Trading Statistics (Last 30 Days)*\n\n"
            response += f"📊 Total Signals: {stats['total_signals']}\n"
            response += f"✅ Executed: {stats['executed_signals']}\n"
            response += f"🔒 Closed: {stats['closed_signals']}\n"
            response += f"💰 Profitable: {stats['profitable_signals']}\n"
            response += f"📈 Success Rate: {stats['success_rate']:.1f}%\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing statistics: {str(e)}")
            await query.edit_message_text("Error retrieving statistics.")
    
    async def show_settings_message(self, message):
        """Show settings menu."""
        keyboard = [
            [InlineKeyboardButton("🔔 Notification Settings", callback_data='notifications')],
            [InlineKeyboardButton("📈 Trading Pairs", callback_data='pairs')],
            [InlineKeyboardButton("⚡️ Risk Level", callback_data='risk')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text("Settings:", reply_markup=reply_markup)
    
    async def show_settings(self, query):
        """Show settings menu."""
        keyboard = [
            [InlineKeyboardButton("🔔 Notification Settings", callback_data='notifications')],
            [InlineKeyboardButton("📈 Trading Pairs", callback_data='pairs')],
            [InlineKeyboardButton("⚡️ Risk Level", callback_data='risk')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("Settings:", reply_markup=reply_markup)
    
    async def show_help(self, query):
        """Show help information."""
        help_message = self.config['telegram']['commands']['help']
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_message, reply_markup=reply_markup)
    
    async def show_notification_settings(self, query):
        """Show notification settings."""
        try:
            user_id = str(query.from_user.id)
            user_pref = self.database_ops.get_user_preference(user_id)
            
            if not user_pref:
                await query.edit_message_text("User preferences not found.")
                return
            
            settings = user_pref.notification_settings
            
            response = "*🔔 Notification Settings*\n\n"
            response += f"📊 Trading Signals: {'✅' if settings.get('signals', True) else '❌'}\n"
            response += f"📈 Market Updates: {'✅' if settings.get('updates', True) else '❌'}\n"
            response += f"🚨 Alerts: {'✅' if settings.get('alerts', True) else '❌'}\n\n"
            response += "Tap to toggle settings:"
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"📊 Signals {'✅' if settings.get('signals', True) else '❌'}", 
                        callback_data='toggle_notification_signals'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"📈 Updates {'✅' if settings.get('updates', True) else '❌'}", 
                        callback_data='toggle_notification_updates'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"🚨 Alerts {'✅' if settings.get('alerts', True) else '❌'}", 
                        callback_data='toggle_notification_alerts'
                    )
                ],
                [InlineKeyboardButton("🔙 Back", callback_data='settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing notification settings: {str(e)}")
            await query.edit_message_text("Error loading notification settings.")
    
    async def show_trading_pairs(self, query):
        """Show trading pairs settings."""
        try:
            user_id = str(query.from_user.id)
            user_pref = self.database_ops.get_user_preference(user_id)
            
            if not user_pref:
                await query.edit_message_text("User preferences not found.")
                return
            
            pairs = user_pref.trading_pairs or ['BTC/USDT', 'ETH/USDT']
            
            response = "*📈 Trading Pairs*\n\n"
            response += "Currently monitoring:\n"
            for pair in pairs:
                response += f"• {pair}\n"
            response += "\nFeature coming soon: Custom pair selection"
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing trading pairs: {str(e)}")
            await query.edit_message_text("Error loading trading pairs.")
    
    async def show_risk_settings(self, query):
        """Show risk level settings."""
        try:
            user_id = str(query.from_user.id)
            user_pref = self.database_ops.get_user_preference(user_id)
            
            if not user_pref:
                await query.edit_message_text("User preferences not found.")
                return
            
            current_risk = user_pref.risk_level
            
            response = "*⚡️ Risk Level Settings*\n\n"
            response += f"Current Risk Level: *{current_risk.upper()}*\n\n"
            response += "Select your risk tolerance:"
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"🟢 Low {'✅' if current_risk == 'low' else ''}", 
                        callback_data='set_risk_low'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"🟡 Medium {'✅' if current_risk == 'medium' else ''}", 
                        callback_data='set_risk_medium'
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"🔴 High {'✅' if current_risk == 'high' else ''}", 
                        callback_data='set_risk_high'
                    )
                ],
                [InlineKeyboardButton("🔙 Back", callback_data='settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing risk settings: {str(e)}")
            await query.edit_message_text("Error loading risk settings.")
    
    async def show_main_menu(self, query):
        """Show main menu."""
        welcome_message = self.config['telegram']['commands']['start']
        keyboard = [
            [InlineKeyboardButton("📊 Recent Signals", callback_data='recent_signals')],
            [InlineKeyboardButton("📈 Statistics", callback_data='stats')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)
    
    async def toggle_notification(self, query):
        """Toggle notification setting."""
        try:
            user_id = str(query.from_user.id)
            setting = query.data.replace('toggle_notification_', '')
            
            user_pref = self.database_ops.get_user_preference(user_id)
            if not user_pref:
                await query.answer("User preferences not found.")
                return
            
            current_settings = user_pref.notification_settings.copy()
            current_settings[setting] = not current_settings.get(setting, True)
            
            self.database_ops.update_notification_settings(user_id, current_settings)
            
            await query.answer(f"{setting.title()} notifications {'enabled' if current_settings[setting] else 'disabled'}")
            
            # Refresh the notification settings view
            await self.show_notification_settings(query)
            
        except Exception as e:
            logger.error(f"Error toggling notification: {str(e)}")
            await query.answer("Error updating notification settings.")
    
    async def set_risk_level(self, query):
        """Set risk level."""
        try:
            user_id = str(query.from_user.id)
            risk_level = query.data.replace('set_risk_', '')
            
            self.database_ops.add_user_preference(user_id, risk_level=risk_level)
            
            await query.answer(f"Risk level set to {risk_level}")
            
            # Refresh the risk settings view
            await self.show_risk_settings(query)
            
        except Exception as e:
            logger.error(f"Error setting risk level: {str(e)}")
            await query.answer("Error updating risk level.")
    
    def run(self):
        """Start the bot."""
        self.app.run_polling() 