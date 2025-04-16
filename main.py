import logging
from telegram.ext import Application
from config import Config
from bot.services.database import DatabaseManager
from bot.handlers.base import setup_handlers
from utils.logger import setup_logging

def configure_application():
    """Configura y retorna la aplicación de Telegram"""
    return Application.builder().token(Config.TELEGRAM_TOKEN).build()

def main():
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Configuración de DB con manejo de errores mejorado
        db_manager = DatabaseManager()
        
        # Intento principal
        if not db_manager.init_db():
            # Intento alternativo con ruta absoluta
            try:
                alt_path = Path.cwd() / 'database' / 'user_profiles.db'
                logger.warning(f"Intentando ubicación alternativa: {alt_path}")
                db_manager = DatabaseManager(str(alt_path))
                if not db_manager.init_db():
                    raise RuntimeError("No se pudo inicializar DB en ubicación alternativa")
            except Exception as alt_e:
                logger.critical(f"Fallo alternativo: {alt_e}")
                raise

        # Resto de la configuración
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        setup_handlers(application)
        
        logger.info("Bot iniciado correctamente")
        application.run_polling()

    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()