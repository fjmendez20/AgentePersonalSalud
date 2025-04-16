from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot.services.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class BotHelpers:
    def __init__(self):
        self.db = DatabaseManager()  # Ahora se inicializa directamente aquí
        self._validate_db_connection()

    def _validate_db_connection(self):
        """Verifica que la conexión a la base de datos esté activa"""
        try:
            with self.db as conn:
                conn.execute("SELECT 1")
        except Exception as e:
            logger.error(f"Error validando conexión a DB: {e}")
            raise RuntimeError("No se pudo establecer conexión con la base de datos")

    @staticmethod
    async def safe_reply(update: Update, text: str, reply_markup=None, parse_mode=None):
        """
        Envía o edita mensajes de forma segura con manejo de errores mejorado
        Args:
            update: Objeto Update de telegram
            text: Texto del mensaje
            reply_markup: Teclado inline (opcional)
            parse_mode: Modo de parseo (Markdown/HTML)
        """
        try:
            if update.message:
                await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            elif update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        except Exception as e:
            logger.error(f"Error en safe_reply: {e}", exc_info=True)
            # Fallback básico si todo falla
            try:
                await update.effective_message.reply_text(
                    "⚠️ Ocurrió un error. Por favor intenta nuevamente."
                )
            except:
                pass

    @staticmethod
    def create_keyboard(buttons, columns=2, add_back_button=False):
        """
        Crea teclados inline organizados con validación mejorada
        Args:
            buttons: Lista de botones (InlineKeyboardButton o listas)
            columns: Número de columnas (default: 2)
            add_back_button: Añade botón "Atrás" (default: False)
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = []
        
        # Normalizar entrada a lista de listas
        if buttons and not isinstance(buttons[0], list):
            buttons = [buttons]
        
        # Organizar en columnas
        try:
            for row in buttons:
                if not all(isinstance(b, InlineKeyboardButton) for b in row):
                    raise ValueError("Todos los elementos deben ser InlineKeyboardButton")
                
                # Dividir filas según columnas
                for i in range(0, len(row), columns):
                    keyboard.append(row[i:i + columns])
            
            # Añadir botón de retroceso si se solicita
            if add_back_button:
                keyboard.append([InlineKeyboardButton("🔙 Atrás", callback_data="back")])
                
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Error en create_keyboard: {e}")
            raise ValueError(f"Error al crear teclado: {str(e)}")

    def get_user_data(self, user_id):
        """Obtiene datos del usuario desde la base de datos"""
        try:
            with self.db as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error obteniendo datos usuario {user_id}: {e}")
            return None