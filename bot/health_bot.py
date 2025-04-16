from telegram.ext import Application
from bot.handlers.setup import SetupHandlers
from bot.handlers.reminders import ReminderHandlers
from bot.handlers.premium import PremiumHandlers
from bot.handlers.daily_plan import DailyPlanHandlers
from bot.services.database import DatabaseManager

class HealthBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.setup = SetupHandlers(self)
        self.reminders = ReminderHandlers(self)
        self.premium = PremiumHandlers(self)
        self.daily_plan = DailyPlanHandlers(self)
        
    def setup_handlers(self, application: Application):
        # Configurar todos los handlers
        self.setup.register_handlers(application)
        self.reminders.register_handlers(application)
        self.premium.register_handlers(application)
        self.daily_plan.register_handlers(application)
        
        # Configurar handlers globales
        application.add_error_handler(self.error_handler)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Error: {context.error}")
        await update.message.reply_text("⚠️ Ocurrió un error")