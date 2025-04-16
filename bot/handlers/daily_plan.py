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
        self.start_handler = None
        self.llm = GroqAssistant()
        self.reminder_handler = None

    def register(self, application):
        """Registra los handlers de comandos y callbacks"""
        application.add_handler(CommandHandler("plan", self.show_daily_plan_menu))
        application.add_handler(
            CallbackQueryHandler(
                self.button_handler,
                pattern="^(generate_plan|regenerate|nutrition|exercise|mindfulness|save_plan|add_reminder|back_to_plan)$"
            )
        )

    async def show_daily_plan_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal de planes diarios de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = await self.db.get_user_data(user_id)
            
            if not user_data:
                await self.helpers.safe_reply(
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
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            logger.error(f"Error en show_daily_plan_menu: {e}")
            await self.helpers.safe_reply(update, "⚠️ Error al mostrar el menú de planes")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todas las acciones de los botones de forma asíncrona"""
        query = update.callback_query
        await query.answer()

        try:
            if query.data == "generate_plan":
                await self._generate_complete_plan(update, context)
            elif query.data == "nutrition":
                await self._generate_nutrition_plan(update, context)
            elif query.data == "exercise":
                await self._generate_exercise_plan(update, context)
            elif query.data == "mindfulness":
                await self._generate_mindfulness_plan(update, context)
            elif query.data == "regenerate":
                await self._regenerate_plan(update, context)
            elif query.data == "save_plan":
                await self._save_plan(update, context)
            elif query.data == "add_reminder":
                await self._add_reminder(update, context)
            elif query.data == "back_to_plan":
                await self.show_daily_plan_menu(update, context)
        except Exception as e:
            logger.error(f"Error en button_handler: {e}")
            await self._show_error(update, "⚠️ Error al procesar tu solicitud")

    async def _generate_complete_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera un plan completo usando LLM de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = await self.db.get_user_data(user_id)
            
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
            user_data = await self.db.get_user_data(user_id)
            
            prompt = self._build_nutrition_prompt(user_data)
            plan = await self.llm.generate_response(prompt)

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
        """Construye el prompt para el plan completo"""
        return f"""
        Actúa como un experto asistente de salud personal. Genera un plan diario completo basado en:
        - Nombre: {user_data.get('name', 'Usuario')}
        - Edad: {user_data.get('age', 'no especificada')}
        - Peso: {user_data.get('weight', 'no especificado')} kg
        - Altura: {user_data.get('height', 'no especificada')} cm
        - Nivel actividad: {user_data.get('activity_level', 'no especificado')}
        - Objetivos: {user_data.get('health_goals', 'no especificados')}
        - Horas sueño: {user_data.get('sleep_time', 'no especificadas')}
        - Horas trabajo: {user_data.get('work_hours', 'no especificadas')}

        El plan debe incluir:
        1. Nutrición: Desayuno, almuerzo, cena y snacks (con horarios sugeridos)
        2. Ejercicio: Rutina adecuada con duración e intensidad
        3. Mindfulness: Actividades de relajación específicas
        4. Recomendaciones personalizadas de hidratación
        5. Pausas activas si trabaja muchas horas

        Formato: Markdown con emojis. Sé específico y práctico.
        Máximo 600 palabras. Organiza por secciones claras.
        """

    def _build_nutrition_prompt(self, user_data: Dict[str, Any]) -> str:
        """Prompt específico para nutrición"""
        return f"""
        Como nutricionista experto, genera un plan de comidas detallado para {user_data.get('name', 'el usuario')} con:
        - Objetivos: {user_data.get('health_goals', 'generales')}
        - Preferencias: (asumir estándar si no hay datos)
        - Restricciones: (ninguna si no se especifican)

        Incluye para cada comida:
        - Nombre del plato
        - Ingredientes principales
        - Preparación breve (1-2 líneas)
        - Calorías aproximadas
        - Macronutrientes (proteína, carbohidratos, grasas)
        - Horario sugerido

        Añade:
        - Recomendaciones de hidratación específicas
        - Suplementos sugeridos si aplica
        - Tips para preparación rápida

        Formato: Lista detallada con emojis. Máximo 400 palabras.
        """

    async def _safe_reply(self, update: Update, text: str, reply_markup=None):
        """Wrapper seguro para responder/editar mensajes de forma asíncrona"""
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error en _safe_reply: {e}")
            raise

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
            user_data = await self.db.get_user_data(user_id)
            
            prompt = self._build_exercise_prompt(user_data)
            plan = await self.llm.generate_response(prompt)

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
        """Prompt específico para ejercicios"""
        return f"""
        Como entrenador personal experto, genera una rutina de ejercicios para {user_data.get('name', 'el usuario')} con:
        - Edad: {user_data.get('age', 30)}
        - Peso: {user_data.get('weight', 70)} kg
        - Altura: {user_data.get('height', 170)} cm
        - Nivel de actividad: {user_data.get('activity_level', 'medium')}
        - Objetivos: {user_data.get('health_goals', 'mejorar condición física')}

        Incluye:
        1. Calentamiento (5-10 min)
        2. Rutina principal (ejercicios con series y repeticiones)
        3. Enfriamiento (5-10 min)
        4. Recomendaciones de intensidad
        5. Alternativas para diferentes niveles

        Duración total: 30-60 minutos. Formato: Lista clara con emojis.
        """

    async def _generate_mindfulness_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera plan de mindfulness de forma asíncrona"""
        try:
            user_id = update.effective_user.id
            user_data = await self.db.get_user_data(user_id)
            
            prompt = self._build_mindfulness_prompt(user_data)
            plan = await self.llm.generate_response(prompt)

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
        """Prompt específico para mindfulness"""
        return f"""
        Como experto en bienestar mental, genera un plan de mindfulness para {user_data.get('name', 'el usuario')} con:
        - Horas de trabajo: {user_data.get('work_hours', 8)}
        - Horas de sueño: {user_data.get('sleep_time', 7)}
        - Objetivos: {user_data.get('health_goals', 'reducir estrés')}

        Incluye:
        1. Meditación matutina (5-15 min)
        2. Pausas conscientes durante el trabajo
        3. Ejercicio de respiración para estrés
        4. Rutina para antes de dormir
        5. Recomendaciones para mejorar el sueño

        Formato: Lista detallada con horarios sugeridos y emojis.
        """