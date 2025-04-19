from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from bot.config import BotConfig
from bot.helpers import BotHelpers
from utils.llm_groq import GroqAssistant
from bot.services.database import DatabaseManager
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DailyPlanHandlers:
    def __init__(self):
        self.helpers = BotHelpers()
        self.db = DatabaseManager()
        self.llm = GroqAssistant()
        self.reminder_handler = None
        self.user_states = {}  # Para manejar estados de usuario

    def register(self, application):
        """Registra los handlers de comandos y callbacks"""
        application.add_handler(CommandHandler("plan", self.show_daily_plan_menu))
        application.add_handler(
            CallbackQueryHandler(
                self.handle_button_press,
                pattern="^(generate_plan|regenerate|nutrition|exercise|mindfulness|save_plan|add_reminder|back_to_plan|setup_profile)$"
            )
        )

    async def show_daily_plan_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Muestra el menú principal de planes diarios"""
            try:
                user_id = update.effective_user.id
                user_data = self.db.get_user_data(user_id)
                
                if not user_data:
                    await self._safe_reply(
                        update,
                        "⚠️ Primero completa tu configuración con /setup",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⚙️ Configurar Perfil", callback_data="setup_profile")]
                        ])
                    )
                    return

                text = "📅 *Plan Diario Personalizado*\n\nElige qué plan generar:"
                buttons = [
                    [InlineKeyboardButton("🍎 Plan Nutricional", callback_data="nutrition")],
                    [InlineKeyboardButton("💪 Rutina de Ejercicios", callback_data="exercise")],
                    [InlineKeyboardButton("🧘 Plan Mindfulness", callback_data="mindfulness")],
                    [InlineKeyboardButton("🔄 Generar Plan Completo", callback_data="generate_plan")]
                ]

                await self._safe_reply(
                    update,
                    text,
                    reply_markup=InlineKeyboardMarkup(buttons))
            except Exception as e:
                logger.error(f"Error en show_daily_plan_menu: {e}", exc_info=True)
                await self._safe_reply(update, "⚠️ Error al mostrar el menú de planes")

    async def handle_button_press(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todas las acciones de los botones"""
        query = update.callback_query
        await query.answer()
        
        try:
            action = query.data
            logger.info(f"Botón presionado: {action}")
            
            if action == "generate_plan":
                await self._generate_complete_plan(update, context)
            elif action == "nutrition":
                await self._generate_nutrition_plan(update, context)
            elif action == "exercise":
                await self._generate_exercise_plan(update, context)
            elif action == "mindfulness":
                await self._generate_mindfulness_plan(update, context)
            elif action == "regenerate":
                await self._regenerate_plan(update, context)
            elif action == "save_plan":
                await self._save_plan(update, context)
            elif action == "add_reminder":
                await self._add_reminder(update, context)
            elif action == "back_to_plan":
                await self.show_daily_plan_menu(update, context)
            elif action == "setup_profile":
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Por favor, ejecuta /setup para configurar tu perfil")
            else:
                logger.warning(f"Acción no reconocida: {action}")
                await query.answer("⚠️ Acción no reconocida")
        except Exception as e:
            logger.error(f"Error en handle_button_press: {e}", exc_info=True)
            await query.answer("⚠️ Error al procesar tu solicitud")
    
    async def _generate_complete_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera un plan completo usando LLM de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = self.db.get_user_data(user_id)  # Removido await
            
            if not user_data:
                await self._show_error(update, "❌ Datos de usuario no encontrados. Completa /setup primero")
                return

            prompt = self._build_complete_prompt(user_data)
            plan = await self.llm.generate_response(prompt)

            if not plan:
                raise ValueError("No se pudo generar el plan")

            buttons = [
                [InlineKeyboardButton("🍎 Nutrición", callback_data="nutrition")],
                [InlineKeyboardButton("💪 Ejercicio", callback_data="exercise")],
                [InlineKeyboardButton("🧘 Mindfulness", callback_data="mindfulness")],
                [
                    InlineKeyboardButton("🔄 Regenerar", callback_data="regenerate"),
                    InlineKeyboardButton("⏰ Recordatorio", callback_data="add_reminder")
                ],
                [InlineKeyboardButton("💾 Guardar Plan", callback_data="save_plan")]
            ]

            await self._safe_reply(
                update,
                f"📅 *Plan Completo para Hoy* ({datetime.now().strftime('%d/%m/%Y')})\n\n{plan}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en _generate_complete_plan: {e}")
            await self._show_error(update, "⚠️ Error al generar el plan completo")

    async def _generate_nutrition_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera plan nutricional específico de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = self.db.get_user_data(user_id)
            
            if not user_data:
                await self.helpers.safe_reply(update, "❌ Datos de usuario no encontrados")
                return

            prompt = self._build_nutrition_prompt(user_data)
            plan = await self.llm.generate_response(prompt)  # Usa await aquí

            if not plan:
                raise ValueError("No se pudo generar el plan nutricional")

            buttons = [
                [InlineKeyboardButton("🔄 Regenerar", callback_data="regenerate")],
                [InlineKeyboardButton("🔙 Menú Planes", callback_data="back_to_plan")]
            ]

            await self._safe_reply(
                update,
                f"🍎 *Plan Nutricional* ({datetime.now().strftime('%d/%m/%Y')})\n\n{plan}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en _generate_nutrition_plan: {e}")
            await self._show_error(update, "⚠️ Error al generar el plan nutricional")

    def _build_complete_prompt(self, user_data: Dict[str, Any]) -> str:
        """Prompt para plan completo en estilo conversacional"""
        return f"""
        Como coach personal, crea un plan diario completo para {user_data.get('name', 'el usuario')} con:
        - Edad: {user_data.get('age', 30)} años
        - Objetivos: {user_data.get('health_goals', 'mejorar salud')}
        
        Habla directamente como a un amigo. Incluye:
        1. Alimentación (3 comidas + snacks)
        2. Ejercicio (rutina breve)
        3. Descanso (pausas y sueño)
        
        Ejemplo: "Para hoy te recomiendo... Luego podrías..."
        Sin formatos, solo texto natural. Máximo 2 emojis.
        """

    def _build_nutrition_prompt(self, user_data: Dict[str, Any]) -> str:
        """Prompt para nutrición en estilo conversacional"""
        return f"""
        Como nutricionista, sugiere comidas para {user_data.get('name', 'el usuario')}:
        - Objetivos: {user_data.get('health_goals', 'alimentación saludable')}
        - Horas trabajo: {user_data.get('work_hours', 8)}
        
        Habla coloquialmente. Ejemplo: 
        "Un buen desayuno sería... Para llevar al trabajo..."
        Ideas prácticas, sin medidas exactas. Máximo 1 emoji por comida.
        """

    async def _safe_reply(self, update: Update, text: str, reply_markup=None):
        """Wrapper seguro para responder/editar mensajes con mejor manejo de Markdown"""
        try:
            # Limpia el texto de posibles errores de formato
            cleaned_text = self._clean_markdown(text)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=cleaned_text[:4000],  # Trunca a 4000 caracteres por seguridad
                    reply_markup=reply_markup,
                    parse_mode='MarkdownV2',
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    text=cleaned_text[:4000],
                    reply_markup=reply_markup,
                    parse_mode='MarkdownV2'
                )
        except Exception as e:
            logger.error(f"Error en _safe_reply: {e}")
            # Intento de fallback sin formato
            try:
                plain_text = self._remove_markdown(text)[:4000]
                if update.callback_query:
                    await update.callback_query.edit_message_text(
                        text=plain_text,
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(
                        text=plain_text,
                        reply_markup=reply_markup
                    )
            except Exception as fallback_error:
                logger.error(f"Error en fallback de _safe_reply: {fallback_error}")
                await self.helpers.safe_reply(update, "⚠️ Error al mostrar el contenido")

    async def _show_error(self, update: Update, message: str):
        """Muestra mensaje de error de forma asíncrona"""
        await self.helpers.safe_reply(update, message)

    async def _regenerate_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Regenera el plan actual de forma asíncrona"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Determinar qué tipo de plan regenerar basado en el mensaje actual
            message = query.message.text
            if "Plan Completo" in message:
                await self._generate_complete_plan(update, context)
            elif "Plan Nutricional" in message:
                await self._generate_nutrition_plan(update, context)
            elif "Rutina de Ejercicios" in message:
                await self._generate_exercise_plan(update, context)
            elif "Plan Mindfulness" in message:
                await self._generate_mindfulness_plan(update, context)
        except Exception as e:
            logger.error(f"Error en _regenerate_plan: {e}")
            await self._show_error(update, "⚠️ Error al regenerar el plan")

    async def _save_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Guarda el plan en la base de datos de forma asíncrona"""
        query = update.callback_query
        await query.answer()
        
        try:
            user_id = update.effective_user.id
            message = query.message.text
            plan_type = "completo"
            
            if "Plan Nutricional" in message:
                plan_type = "nutrición"
            elif "Rutina de Ejercicios" in message:
                plan_type = "ejercicio"
            elif "Plan Mindfulness" in message:
                plan_type = "mindfulness"
            
            success = await self.db.save_plan(user_id, plan_type, message)
            if success:
                await query.answer("✅ Plan guardado correctamente")
            else:
                await query.answer("⚠️ Error al guardar el plan")
        except Exception as e:
            logger.error(f"Error en _save_plan: {e}")
            await query.answer("⚠️ Error al guardar el plan")

    async def _add_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Añade recordatorio para el plan de forma asíncrona"""
        if not self.reminder_handler:
            await update.callback_query.answer("⚠️ Módulo de recordatorios no disponible")
            return
            
        try:
            # Implementar lógica para añadir recordatorio
            await update.callback_query.answer("⏰ Funcionalidad de recordatorios en desarrollo")
        except Exception as e:
            logger.error(f"Error en _add_reminder: {e}")
            await update.callback_query.answer("⚠️ Error al añadir recordatorio")

    async def _generate_exercise_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera plan de ejercicios de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = self.db.get_user_data(user_id)
            if not user_data:
                await self.helpers.safe_reply(update, "❌ Datos de usuario no encontrados")
                return
            prompt = self._build_exercise_prompt(user_data)
            plan = await self.llm.generate_response(prompt)
            if not plan:
                raise ValueError("No se pudo generar el plan de ejercicios")
            
            buttons = [
                [InlineKeyboardButton("🔄 Regenerar", callback_data="regenerate")],
                [InlineKeyboardButton("🔙 Menú Planes", callback_data="back_to_plan")]
            ]

            await self._safe_reply(
                update,
                f"💪 *Rutina de Ejercicios* ({datetime.now().strftime('%d/%m/%Y')})\n\n{plan}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en _generate_exercise_plan: {e}")
            await self._show_error(update, "⚠️ Error al generar la rutina de ejercicios")

    def _build_exercise_prompt(self, user_data: Dict[str, Any]) -> str:
        """Prompt para ejercicio en estilo conversacional"""
        return f"""
        Como entrenador, recomienda una rutina para {user_data.get('name', 'el usuario')}:
        - Edad: {user_data.get('age', 30)}
        - Nivel: {user_data.get('activity_level', 'moderado')}
        
        Ejemplo: "Hoy podrías empezar con... descansando entre series..."
        Sin listas ni formatos. Texto fluido. 1-2 emojis máximo.
        """

    async def _generate_mindfulness_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera plan de mindfulness de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = self.db.get_user_data(user_id)
            if not user_data:
                await self.helpers.safe_reply(update, "❌ Datos de usuario no encontrados")
                return
            
            prompt = self._build_mindfulness_prompt(user_data)
            plan = await self.llm.generate_response(prompt)
            if not plan:
                raise ValueError("No se pudo generar el plan nutricional")
            buttons = [
                [InlineKeyboardButton("🔄 Regenerar", callback_data="regenerate")],
                [InlineKeyboardButton("🔙 Menú Planes", callback_data="back_to_plan")]
            ]

            await self._safe_reply(
                update,
                f"🧘 *Plan Mindfulness* ({datetime.now().strftime('%d/%m/%Y')})\n\n{plan}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en _generate_mindfulness_plan: {e}")
            await self._show_error(update, "⚠️ Error al generar el plan de mindfulness")

    def _build_mindfulness_prompt(self, user_data: Dict[str, Any]) -> str:
        """Prompt para mindfulness en estilo conversacional"""
        return f"""
        Como experto en relajación, da tips para {user_data.get('name', 'el usuario')}:
        - Horas trabajo: {user_data.get('work_hours', 8)}
        - Estrés: {user_data.get('stress_level', 'moderado')}
        
        Ejemplo: "Cuando sientas presión, prueba esto..."
        Lenguaje calmado. Sin términos técnicos. 1 emoji opcional.
        """
    
    def _clean_markdown(self, text: str) -> str:
        """Limpia el texto para evitar errores de formato MarkdownV2"""
        # Escapa caracteres especiales de MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def _remove_markdown(self, text: str) -> str:
        """Elimina todo formato Markdown del texto"""
        import re
        # Elimina patrones comunes de Markdown
        text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)  # *bold* **bold**
        text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)    # _italic_ __italic__
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)    # `code` ```code```
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)     # [link](url)
        return text