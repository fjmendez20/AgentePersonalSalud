import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from bot.config import BotConfig
from bot.helpers import BotHelpers
from bot.services.database import DatabaseManager

logger = logging.getLogger(__name__)

class ReminderHandlers:
    def __init__(self):
        self.helpers = None  # Se establecerá desde base.py
        self.db = DatabaseManager()
        self.start_handler = None  # Se establecerá desde base.py
    
    def set_start_handler(self, start_handler):
        self.start_handler = start_handler
        
    def register(self, application):
        """Registra comandos y handlers específicos"""
        try:
            application.add_handler(CommandHandler("recordatorios", self.set_reminders))
            application.add_handler(CommandHandler("detener", self.stop_reminders))
            application.add_handler(CommandHandler("mis_recordatorios", self.show_reminders))
            
            # Patrones actualizados para mejor manejo
            application.add_handler(
                CallbackQueryHandler(
                    self.button_handler, 
                    pattern="^(reminder_|stop_|edit_|show_main_menu|reminder_cancel)"
                ),
                group=2
            )
        except Exception as e:
            logger.error(f"Error al registrar ReminderHandlers: {e}")
            raise
        
    async def set_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal de recordatorios"""
        try:
            buttons = [
                [InlineKeyboardButton("💧 Agua (cada 2h)", callback_data="reminder_water")],
                [InlineKeyboardButton("🧘 Pausa activa (cada 45m)", callback_data="reminder_break")],
                [InlineKeyboardButton("👀 Postura (cada 30m)", callback_data="reminder_posture")],
                [
                    InlineKeyboardButton("✅ Activar Todos", callback_data="reminder_all"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="reminder_cancel"),
                    InlineKeyboardButton("🔙 Menú Principal", callback_data="show_main_menu")
                ]
            ]
            
            await self._safe_reply(
                update,
                "🔔 Configuración de Recordatorios:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en set_reminders: {e}")
            await self._safe_reply(update, "⚠️ Error al mostrar menú de recordatorios")

    async def _safe_reply(self, update: Update, text: str, reply_markup=None):
        """Método seguro para responder a updates y callback queries"""
        try:
            if update.message:
                await update.message.reply_text(text, reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                logger.warning("No se pudo responder - tipo de update no soportado")
        except Exception as e:
            logger.error(f"Error en _safe_reply: {e}")

    async def stop_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detiene todos los recordatorios activos"""
        try:
            user_id = update.effective_user.id
            
            with self.db as cursor:
                cursor.execute('''
                    UPDATE reminders 
                    SET is_active = 0 
                    WHERE user_id = ?
                ''', (user_id,))
            
            if context.job_queue:
                for reminder_type in BotConfig.REMINDER_TYPES.keys():
                    jobs = context.job_queue.get_jobs_by_name(f"{user_id}_{reminder_type}")
                    for job in jobs:
                        job.schedule_removal()
            
            await self._safe_reply(
                update,
                "🛑 Todos tus recordatorios han sido detenidos.\n"
                "Puedes reactivarlos con /recordatorios"
            )
        except Exception as e:
            logger.error(f"Error en stop_reminders: {e}")
            await self._safe_reply(update, "⚠️ Error al detener recordatorios")

    async def show_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra los recordatorios activos del usuario"""
        try:
            user_id = update.effective_user.id
            
            with self.db as cursor:
                cursor.execute('''
                    SELECT reminder_type, interval_seconds 
                    FROM reminders 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY reminder_type
                ''', (user_id,))
                reminders = cursor.fetchall()
            
            buttons = []
            message = "📋 Tus recordatorios activos:\n\n"
            
            if not reminders:
                message = "ℹ️ No tienes recordatorios activos actualmente."
                buttons.append([InlineKeyboardButton("⏰ Configurar Recordatorios", callback_data="reminder_menu")])
            else:
                for rem in reminders:
                    reminder_type = rem[0]
                    interval = rem[1]
                    hours = interval // 3600
                    minutes = (interval % 3600) // 60
                    
                    reminder_info = BotConfig.REMINDER_TYPES.get(reminder_type, {})
                    friendly_name = reminder_info.get("message", reminder_type).split("!")[0]
                    
                    message += (
                        f"• {friendly_name}: "
                        f"Cada {f'{hours}h ' if hours > 0 else ''}"
                        f"{minutes}m\n"
                    )
                
                buttons.extend([
                    [
                        InlineKeyboardButton("✏️ Editar", callback_data="edit_reminders"),
                        InlineKeyboardButton("🛑 Detener Todos", callback_data="stop_reminders")
                    ],
                    [
                        InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")
                    ]
                ])
            
            await self._safe_reply(
                update,
                message,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
        except Exception as e:
            logger.error(f"Error en show_reminders: {e}")
            await self._safe_reply(update, "⚠️ Error al mostrar recordatorios")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todas las acciones de los botones de recordatorios"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "show_main_menu" and self.start_handler:
                await self.start_handler.show_main_menu(update, context)
            elif query.data == "reminder_water":
                await self._activate_reminder(update, context, "agua")
            elif query.data == "reminder_break":
                await self._activate_reminder(update, context, "pausa")
            elif query.data == "reminder_posture":
                await self._activate_reminder(update, context, "postura")
            elif query.data == "reminder_all":
                await self._activate_all_reminders(update, context)
            elif query.data == "stop_reminders":
                await self.stop_reminders(update, context)
            elif query.data == "edit_reminders":
                await self.set_reminders(update, context)
            elif query.data == "reminder_menu":
                await self.set_reminders(update, context)
            elif query.data == "reminder_cancel":
                await query.edit_message_text("✅ Operación cancelada")
        except Exception as e:
            logger.error(f"Error en button_handler: {e}")
            await self._safe_reply(update, "⚠️ Error al procesar tu solicitud")

    async def _activate_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reminder_type: str):
        """Activa un recordatorio específico"""
        try:
            if not context.job_queue:
                raise ValueError("Job queue no disponible")
            
            user_id = update.effective_user.id
            interval = BotConfig.REMINDER_TYPES[reminder_type]["interval"]
            message = BotConfig.REMINDER_TYPES[reminder_type]["message"]
            
            # Cancelar job existente
            jobs = context.job_queue.get_jobs_by_name(f"{user_id}_{reminder_type}")
            for job in jobs:
                job.schedule_removal()
            
            # Crear nuevo job
            context.job_queue.run_repeating(
                self._send_reminder,
                interval=interval,
                first=5,
                chat_id=user_id,
                name=f"{user_id}_{reminder_type}",
                data={"type": reminder_type, "message": message}
            )
            
            # Actualizar base de datos
            with self.db as cursor:
                cursor.execute('''
                    INSERT OR REPLACE INTO reminders 
                    (user_id, reminder_type, interval_seconds, is_active)
                    VALUES (?, ?, ?, 1)
                ''', (user_id, reminder_type, interval))
            
            friendly_name = message.split("!")[0].strip()
            hours = interval // 3600
            minutes = (interval % 3600) // 60
            time_str = f"{f'{hours}h ' if hours > 0 else ''}{minutes}m"
            
            await self._safe_reply(
                update,
                f"✅ {friendly_name} activado cada {time_str}\n\n"
                "Usa /mis_recordatorios para ver tus recordatorios activos"
            )
        except Exception as e:
            logger.error(f"Error al activar recordatorio {reminder_type}: {e}")
            await self._safe_reply(
                update,
                f"⚠️ No se pudo activar el recordatorio. Error: {str(e)}"
            )

    async def _activate_all_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activa todos los recordatorios disponibles"""
        try:
            for reminder_type in BotConfig.REMINDER_TYPES:
                await self._activate_reminder(update, context, reminder_type)
            
            await self._safe_reply(
                update,
                "✅ Todos los recordatorios han sido activados correctamente.\n\n"
                "Usa /mis_recordatorios para ver el listado completo."
            )
        except Exception as e:
            logger.error(f"Error al activar todos los recordatorios: {e}")
            await self._safe_reply(
                update,
                "⚠️ Ocurrió un error al activar los recordatorios. "
                f"Detalle: {str(e)}"
            )

    async def _send_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        """Envía el mensaje de recordatorio"""
        job = context.job
        try:
            await context.bot.send_message(
                chat_id=job.chat_id,
                text=job.data["message"]
            )
            
            with self.db as cursor:
                cursor.execute('''
                    UPDATE reminders 
                    SET last_sent = CURRENT_TIMESTAMP 
                    WHERE user_id = ? AND reminder_type = ? AND is_active = 1
                ''', (job.chat_id, job.data["type"]))
        except Exception as e:
            logger.error(f"Error al enviar recordatorio: {e}")