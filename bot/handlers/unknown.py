import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.helpers import escape_markdown
from bot.helpers import BotHelpers
from bot.handlers.start import StartHandler

logger = logging.getLogger(__name__)

class UnknownHandler:
    def __init__(self):
        self.helpers = BotHelpers()
        self.start_handler = StartHandler()
        
    def register(self, application):
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex(self.start_handler.keywords_regex),
                self.handle_unknown_message
            ),
            group=2
        )
        
        application.add_handler(
            CallbackQueryHandler(
                self.button_handler,
                pattern="^(unknown_help|show_main_menu|close_unknown)$"
            ),
            group=-1
        )
    
    async def handle_unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Verificar si hay una conversación activa en el ConversationHandler
        if context.user_data.get('in_conversation'):
            return
            
        try:
            responses = [
                "🤔 No estoy seguro de entender lo que necesitas. ¿Quieres ver el menú principal?",
                "😅 Parece que no reconozco ese mensaje. ¿Te gustaría ver las opciones disponibles?",
                "💡 No estoy programado para responder eso, pero puedo mostrarte lo que sí sé hacer."
            ]
            
            response_index = hash(update.message.text.lower()) % len(responses)
            
            buttons = [
                [InlineKeyboardButton("📋 Ver Menú Principal", callback_data="show_main_menu")],
                [InlineKeyboardButton("🆘 Mostrar Ayuda", callback_data="unknown_help")],
                [InlineKeyboardButton("❌ Cerrar", callback_data="close_unknown")]
            ]
            
            await update.message.reply_text(
                responses[response_index],
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en handle_unknown_message: {e}")
            await self.helpers.safe_reply(
                update,
                "⚠️ Ocurrió un error al procesar tu mensaje. Por favor intenta con /help"
            )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "unknown_help":
                await self._show_help_message(update)
            elif query.data == "show_main_menu":
                await self.start_handler.show_main_menu(update, context)
            elif query.data == "close_unknown":
                await query.delete_message()
        except Exception as e:
            logger.error(f"Error en button_handler: {e}")
            await query.edit_message_text("⚠️ Error al procesar tu solicitud. Intenta con /help")

    async def _show_help_message(self, update: Update):
        """Muestra el mensaje de ayuda con formato Markdown seguro"""
        try:
            # Texto de ayuda con formato Markdown V2 seguro
            help_text = escape_markdown(
                "🆘 *Ayuda - Comandos Disponibles*\n\n"
                "Estos son los comandos que sí reconozco:\n"
                "• /start, /hola - Menú principal\n"
                "• /recordatorios - Configurar recordatorios\n"
                "• /mis_recordatorios - Ver recordatorios activos\n"
                "• /detener - Detener recordatorios\n"
                "• /plan - Generar plan diario\n"
                "• /setup - Configurar perfil\n"
                "• /premium - Información premium\n"
                "• /help - Mostrar esta ayuda\n\n"
                "También puedes escribir 'hola bot' o 'menú' para comenzar.",
                version=2
            )
            
            buttons = [
                [InlineKeyboardButton("📋 Menú Principal", callback_data="show_main_menu")],
                [InlineKeyboardButton("❌ Cerrar", callback_data="close_unknown")]
            ]

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=help_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode='MarkdownV2'
                )
            else:
                await update.message.reply_text(
                    text=help_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode='MarkdownV2'
                )
        except Exception as e:
            logger.error(f"Error al mostrar ayuda: {e}")
            await self.helpers.safe_reply(
                update,
                "⚠️ No pude mostrar la ayuda. Por favor intenta con /help"
            )