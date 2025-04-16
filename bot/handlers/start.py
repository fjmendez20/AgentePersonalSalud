import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from bot.config import BotConfig
from bot.helpers import BotHelpers


logger = logging.getLogger(__name__)

class StartHandler:
    def __init__(self):
        self.helpers = BotHelpers()
        self.reminder_handler = None
        self.premium_handler = None
        self.daily_plan_handler = None
        self.setup_handler = None
        
        #self.reminder_handler = ReminderHandlers()  # Añade esta línea
        # Comandos que activarán el menú de inicio
        self.commands = ['start', 'hola', 'inicio', 'menu', 'help', 'ayuda', 'comenzar']
        # Palabras clave que activarán el menú
        self.keywords = [
            'hola bot', 
            'empezar', 
            'quiero comenzar',
            'qué puedes hacer',
            'opciones',
            'menú principal',
            'hola',
            'buenos días',
            'buenas tardes'
        ]
        self.keywords_regex = re.compile(
            r'(?i)^(' + '|'.join(map(re.escape, self.keywords)) + ')$'
        )
        
    def register(self, application):
        """Registra todos los handlers"""
        # Handlers de comandos
        for cmd in self.commands:
            application.add_handler(
                CommandHandler(cmd, self.show_main_menu),
                group=1
            )
        
        # Handler para palabras clave
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.Regex(self.keywords_regex),
                self.show_main_menu
            ),
            group=1
        )
        
        # Handler para botones principales
        application.add_handler(
            CallbackQueryHandler(
                self.main_button_handler,
                pattern="^(" + "|".join([
                    BotConfig.CALLBACKS['setup'],
                    BotConfig.CALLBACKS['daily_plan'],
                    BotConfig.CALLBACKS['reminders'],
                    BotConfig.CALLBACKS['premium']
                ]) + ")$"
            ),
            group=1
        )
        
        # Handler para botones auxiliares
        application.add_handler(
            CallbackQueryHandler(
                self.aux_button_handler,
                pattern="^(show_main_menu|help|close)$"
            ),
            group=1
        )
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal con manejo robusto de errores"""
        try:
            user = update.effective_user
            welcome_text = self._generate_welcome_text(user.first_name)
            buttons = self._generate_menu_buttons()
            reply_markup = InlineKeyboardMarkup(buttons)
            
            # Si es un mensaje nuevo (no callback)
            if update.message:
                await update.message.reply_text(
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
                
            # Si es una callback query
            query = update.callback_query
            await query.answer()
            
            try:
                # Intenta editar el mensaje
                await query.edit_message_text(
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as edit_error:
                # Si falla por "mensaje no modificado", es inofensivo
                if "Message is not modified" in str(edit_error):
                    logger.debug("El mensaje no requería modificaciones")
                    return
                    
                # Si es otro tipo de error, hacer fallback
                logger.error(f"Error al editar mensaje: {edit_error}")
                try:
                    await query.message.reply_text(
                        text=welcome_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                except Exception as fallback_error:
                    logger.error(f"Error en fallback: {fallback_error}")
                    await self.helpers.safe_reply(
                        update,
                        "⚠️ Error al mostrar el menú. Intenta con /start"
                    )
                    
        except Exception as e:
            logger.error(f"Error crítico en show_main_menu: {e}")
            await self.helpers.safe_reply(
                update,
                "¡Hola! Hubo un error al cargar el menú. Por favor intenta con /start"
            )

    async def main_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "daily_plan_menu":
                if self.daily_plan_handler:
                    await self.daily_plan_handler.show_daily_plan_menu(update, context)
                else:
                    await query.edit_message_text("⚠️ Módulo de planes no disponible")
            elif query.data == "setup_profile":  # <-- Maneja el botón "Configurar Perfil"
                if self.setup_handler:
                    await self.setup_handler.start_setup(update, context)  # Redirige al setup
                else:
                    await query.edit_message_text("⚠️ Módulo de configuración no disponible")
            elif query.data == "reminders_menu":
                if self.reminder_handler:
                    await self.reminder_handler.set_reminders(update, context)
                else:
                    await query.edit_message_text("⚠️ Módulo de recordatorios no disponible")
            elif query.data == "premium_info":
                if self.premium_handler:
                    await self.premium_handler.show_premium_info(update, context)
                else:
                    await query.edit_message_text("⚠️ Módulo premium no disponible")
        except Exception as e:
            logger.error(f"Error en main_button_handler: {e}")
            await self._show_error_message(update)

    async def aux_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja botones auxiliares"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "show_main_menu":
                await self.show_main_menu(update, context)
            elif query.data == "help":
                await self.show_help(update, context)
            elif query.data == "close":
                await query.delete_message()
        except Exception as e:
            logger.error(f"Error en aux_button_handler: {e}")
            await self._show_error_message(update)

    async def _handle_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configuración de perfil"""
        await self._show_temp_message(
            update,
            "⚙️ *Configuración de Perfil*\n\n"
            "Aquí puedes configurar tus datos personales y preferencias.\n\n"
            "_Esta función estará disponible pronto_"
        )

    async def _handle_daily_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Plan diario"""
        await self._show_temp_message(
            update,
            "📅 *Plan Diario*\n\n"
            "Aquí encontrarás tu plan de salud personalizado para hoy.\n\n"
            "_Esta función estará disponible pronto_"
        )

    async def _handle_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recordatorios"""
        await self._show_temp_message(
            update,
            "⏰ *Gestión de Recordatorios*\n\n"
            "Configura tus recordatorios para medicamentos, ejercicios, etc.\n\n"
            "_Esta función estará disponible pronto_"
        )

    async def _handle_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Información premium"""
        await self._show_temp_message(
            update,
            "💎 *Funciones Premium*\n\n"
            "Desbloquea características exclusivas con nuestra versión premium.\n\n"
            "_Esta función estará disponible pronto_"
        )

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la ayuda con formato HTML"""
        try:
            help_text = (
                "<b>🆘 Ayuda - Comandos Disponibles</b>\n\n"
                "<b>📌 Comandos principales:</b>\n"
                "• /start, /hola - Menú principal\n"
                "• /recordatorios - Configurar recordatorios\n"
                "• /mis_recordatorios - Ver recordatorios activos\n"
                "• /detener - Detener recordatorios\n"
                "• /plan - Generar plan diario\n"
                "• /setup - Configurar perfil\n"
                "• /premium - Información premium\n"
                "• /help - Mostrar esta ayuda\n\n"
                "<b>📌 También puedes escribir:</b>\n"
                "- 'hola bot' o 'menú principal' para comenzar\n"
                "- 'quiero comenzar' para ver opciones\n"
                "- 'ayuda' para ver esta información"
            )
            
            buttons = [
                [InlineKeyboardButton("📋 Menú Principal", callback_data="show_main_menu")],
                [InlineKeyboardButton("✉️ Soporte", url="https://t.me/tu_soporte")]
            ]

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=help_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    text=help_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error en show_help: {e}")
            await self.helpers.safe_reply(
                update,
                "⚠️ No pude mostrar la ayuda. Por favor intenta con /help"
            )

    async def _show_temp_message(self, update: Update, text: str):
        """Muestra mensaje temporal con manejo de errores mejorado"""
        buttons = [
            [InlineKeyboardButton("🔙 Volver al menú", callback_data="show_main_menu")],
            [InlineKeyboardButton("🆘 Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        query = update.callback_query
        await query.answer()
        
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                return  # Error inofensivo
                
            logger.error(f"Error al mostrar mensaje temporal: {e}")
            try:
                await query.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as fallback_error:
                logger.error(f"Error en fallback: {fallback_error}")
                await self.helpers.safe_reply(
                    update,
                    "⚠️ Error temporal. Intenta nuevamente."
                )

    async def _show_error_message(self, update: Update):
        """Muestra mensaje de error genérico"""
        await self.helpers.safe_reply(
            update,
            "⚠️ Ocurrió un error. Por favor intenta nuevamente."
        )

    def _generate_welcome_text(self, first_name: str) -> str:
        """Genera texto de bienvenida"""
        return (
            f"👋 ¡Hola {first_name}! Soy tu Asistente de Salud Personal.\n\n"
            "📌 *¿Qué necesitas hacer hoy?*\n"
            "• ⏰ Configurar recordatorios\n"
            "• 📅 Generar plan diario\n"
            "• ⚙️ Actualizar mi perfil\n"
            "• 💎 Conocer ventajas premium"
        )

    def _generate_menu_buttons(self):
        return [
            [
                InlineKeyboardButton("⚙️ Configurar Perfil", callback_data="setup_profile"),
                InlineKeyboardButton("📅 Plan Diario", callback_data="daily_plan_menu")
            ],
            [
                InlineKeyboardButton("⏰ Recordatorios", callback_data="reminders_menu"),
                InlineKeyboardButton("💎 Premium", callback_data="premium_info")
            ],
            [
                InlineKeyboardButton("🆘 Ayuda", callback_data="help"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close")
            ]
        ]