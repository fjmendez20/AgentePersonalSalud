from bot.handlers.start import StartHandler
from bot.handlers.setup import SetupHandlers
from bot.handlers.reminders import ReminderHandlers
from bot.handlers.premium import PremiumHandlers
from bot.handlers.daily_plan import DailyPlanHandlers
from bot.handlers.unknown import UnknownHandler
import logging
from bot.services.database import DatabaseManager
from bot.helpers import BotHelpers  # Añade esta importación

logger = logging.getLogger(__name__)

def setup_handlers(application):
    """Configura todos los handlers con sus dependencias"""
    
    try:
        # Inicializa la base de datos y helpers
        db = DatabaseManager()
        helpers = BotHelpers()
        helpers.db = db  # Inyecta la conexión a db en helpers

        # Inicializa todos los handlers
        start_handler = StartHandler()
        setup_handler = SetupHandlers()
        reminder_handler = ReminderHandlers()
        premium_handler = PremiumHandlers()
        daily_plan_handler = DailyPlanHandlers()
        unknown_handler = UnknownHandler()

        # Configura las dependencias cruzadas
        start_handler.setup_handler = setup_handler
        start_handler.reminder_handler = reminder_handler
        start_handler.daily_plan_handler = daily_plan_handler
        start_handler.premium_handler = premium_handler
        premium_handler.start_handler = start_handler
        daily_plan_handler.start_handler = start_handler
        
        
        # Configura helpers y start_handler para todos los handlers
        all_handlers = [
            setup_handler,
            reminder_handler,
            premium_handler,
            daily_plan_handler,
            unknown_handler
        ]
        
        for handler in all_handlers:
            handler.helpers = helpers
            handler.start_handler = start_handler

        # Registra los handlers en orden de prioridad
        handlers_to_register = [
            start_handler,  # Alta prioridad
            setup_handler,
            reminder_handler,
            premium_handler,
            daily_plan_handler,
            unknown_handler  # Baja prioridad
        ]
        
        for handler in handlers_to_register:
            try:
                if hasattr(handler, 'register'):
                    handler.register(application)
                    logger.info(f"Handler {handler.__class__.__name__} registrado exitosamente")
                else:
                    logger.warning(f"Ignorando handler {handler.__class__.__name__} sin método register")
            except Exception as e:
                logger.error(f"Error al registrar {handler.__class__.__name__}: {e}")
                raise

        logger.info("Todos los handlers registrados correctamente")
        return True
        
    except Exception as e:
        logger.critical(f"Error crítico al configurar handlers: {e}")
        raise