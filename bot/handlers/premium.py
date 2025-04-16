import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from bot.config import BotConfig
from bot.helpers import BotHelpers

logger = logging.getLogger(__name__)

class PremiumHandlers:
    def __init__(self):
        self.helpers = BotHelpers()
        self.start_handler = None

    def register(self, application):
        application.add_handler(CommandHandler("premium", self.show_premium_info))
        application.add_handler(
            CallbackQueryHandler(
                self.premium_button_handler,
                pattern="^premium_"
            )
        )

    async def show_premium_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_benefits_click=False):
        """Muestra la información premium con opciones de suscripción"""
        try:
            buttons = [
                [InlineKeyboardButton("💎 Mensual - $5", callback_data="premium_monthly")],
                [InlineKeyboardButton("🌟 Anual - $50 (¡Ahorra 17%!)", callback_data="premium_yearly")],
                [InlineKeyboardButton("🔍 Ver Beneficios", callback_data="premium_benefits")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="show_main_menu")],
                [InlineKeyboardButton("❌ Cerrar", callback_data="premium_close")]
            ]
            
            if is_benefits_click:
                benefits_text = (
                    "🌟 *Beneficios Detallados Premium:*\n\n"
                    "🍎 *Nutrición Avanzada:*\n"
                    "- Planes personalizados por nutricionistas\n"
                    "- Base de datos de +10,000 alimentos\n"
                    "- Seguimiento de macros y micronutrientes\n\n"
                    "⏰ *Recordatorios Inteligentes:*\n"
                    "- Configuración por horarios o eventos\n"
                    "- Recordatorios de medicación con inventario\n"
                    "- Integración con calendarios\n\n"
                    "📊 *Seguimiento Completo:*\n"
                    "- Gráficos y estadísticas detalladas\n"
                    "- Exportación de datos en PDF/Excel\n"
                    "- Comparativas históricas\n\n"
                    "👨‍⚕️ *Asesoría Premium:*\n"
                    "- Soporte prioritario 24/7\n"
                    "- Consultas mensuales con expertos\n"
                    "- Análisis personalizados\n\n"
                    "🎁 *Contenido Exclusivo:*\n"
                    "- Recetas premium\n"
                    "- Guías de entrenamiento\n"
                    "- Webinars mensuales"
                )
            else:
                benefits_text = (
                    "🌟 *Beneficios Premium:*\n\n"
                    "✅ Planes de nutrición avanzados\n"
                    "✅ Recordatorios personalizables\n"
                    "✅ Seguimiento detallado de progreso\n"
                    "✅ Asesoría prioritaria\n"
                    "✅ Contenido exclusivo\n\n"
                    "Selecciona una opción para más información:"
                )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=benefits_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    text=benefits_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error en show_premium_info: {e}")
            await self.helpers.safe_reply(
                update,
                "⚠️ Error al mostrar información premium. Intenta nuevamente."
            )

    async def premium_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja específicamente los botones premium"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
            
            if data == "premium_monthly":
                await self.show_payment(update, context, "monthly")
            elif data == "premium_yearly":
                await self.show_payment(update, context, "yearly")
            elif data == "premium_benefits":
                # Pasamos is_benefits_click=True para mostrar versión extendida
                await self.show_premium_info(update, context, is_benefits_click=True)
            elif data == "premium_close":
                await query.delete_message()
            elif data == "show_main_menu":
                if self.start_handler:
                    await self.start_handler.show_main_menu(update, context)
                else:
                    await query.edit_message_text("⚠️ No se puede volver al menú principal")
                    
        except Exception as e:
            logger.error(f"Error en premium_button_handler: {e}")
            await self.helpers.safe_reply(
                update,
                "⚠️ Error al procesar tu solicitud premium."
            )

    async def show_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str):
        """Muestra los detalles de pago para un plan específico"""
        try:
            query = update.callback_query
            plans = {
                "monthly": {"price": "$5", "desc": "Mensual", "saving": ""},
                "yearly": {"price": "$50", "desc": "Anual", "saving": " (¡Ahorra 17%!)"}
            }
            
            payment_text = (
                f"💳 *Suscripción {plans[plan_type]['desc']}*{plans[plan_type]['saving']}\n"
                f"Precio: {plans[plan_type]['price']}\n\n"
                "🔒 Pago seguro procesado a través de nuestro socio de pagos.\n\n"
                "Esta es una simulación. En una implementación real, aquí se integraría "
                "con un sistema de pagos como Stripe o PayPal."
            )
            
            buttons = [
                [InlineKeyboardButton("🔙 Volver a Beneficios", callback_data="premium_benefits")],
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="show_main_menu")],
                [InlineKeyboardButton("❌ Cerrar", callback_data="premium_close")]
            ]
            
            await query.edit_message_text(
                text=payment_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error en show_payment: {e}")
            await self.helpers.safe_reply(
                update,
                "⚠️ Error al mostrar opciones de pago."
            )