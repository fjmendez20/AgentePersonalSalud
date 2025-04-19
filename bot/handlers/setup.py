from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes
)
from bot.config import BotConfig
from bot.helpers import BotHelpers
import logging

logger = logging.getLogger(__name__)

class SetupHandlers:
    def __init__(self):
        self.helpers = BotHelpers()
        self.states = BotConfig.SETUP_STATES
        
    def register(self, application):
        conv_handler = ConversationHandler(
            entry_points=[
            CommandHandler('setup', self.start_setup),
            CallbackQueryHandler(self.start_setup, pattern="^begin_setup$"),
            CallbackQueryHandler(self.force_setup, pattern="^force_setup$")
            ],
            states={
                self.states[0]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_name),
                    CallbackQueryHandler(self.handle_change_name, pattern="^change_name$")
                ],
                self.states[1]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_age),
                    CallbackQueryHandler(self.handle_change_age, pattern="^change_age$")
                ],
                self.states[2]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_weight),
                    CallbackQueryHandler(self.handle_change_weight, pattern="^change_weight$")
                ],
                self.states[3]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_height),
                    CallbackQueryHandler(self.handle_change_height, pattern="^change_height$")
                ],
                self.states[4]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_activity),
                    CallbackQueryHandler(self.activity_callback, pattern="^activity_")
                ],
                self.states[5]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_goals),
                    CallbackQueryHandler(self.goals_callback, pattern="^goal_")
                ],
                self.states[6]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_sleep),
                    CallbackQueryHandler(self.handle_change_sleep, pattern="^change_sleep$")
                ],
                self.states[7]: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_work),
                    CallbackQueryHandler(self.handle_change_work, pattern="^change_work$")
                ],
                "WAITING_FIELD_SELECTION": [
                CallbackQueryHandler(self.handle_profile_actions, pattern="^edit_field:"),
                CallbackQueryHandler(self.view_profile, pattern="^back_to_profile$")
                ],
                "PROCESS_FIELD_UPDATE": [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_field_update)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_setup),
                CallbackQueryHandler(self.cancel_setup, pattern=f"^{BotConfig.CALLBACKS['cancel']}$"),
                CommandHandler('miperfil', self.view_profile)
            ],
            allow_reentry=True,
            per_user=True,
            per_chat=True
        )

        application.add_handler(conv_handler, group=1)
        application.add_handler(CommandHandler('miperfil', self.view_profile))
        application.add_handler(CallbackQueryHandler(
            self.handle_profile_actions, 
            pattern="^(force_setup|generate_plan|edit_specific_field|edit_field:|back_to_profile)$"
        ))
        application.add_handler(CallbackQueryHandler(
            self.cancel_from_profile,
            pattern="^cancel_from_profile$"
        ), group=1)
        application.add_handler(CallbackQueryHandler(
            self.cancel_setup, 
            pattern=f"^{BotConfig.CALLBACKS['cancel']}$"
        ), group=1)
        
        
    async def force_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fuerza la actualización del perfil ignorando el registro existente"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                text="📝 Vamos a actualizar tu perfil de salud.\n\nPor favor, dime tu nombre completo:"
            )
        else:
            await update.message.reply_text(
                "📝 Vamos a actualizar tu perfil de salud.\n\nPor favor, dime tu nombre completo:"
            )
            
        context.user_data.clear()
        context.user_data['in_conversation'] = True
        context.user_data['user_id'] = update.effective_user.id
        return self.states[0]

    async def start_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['in_conversation'] = True  # <-- Añadir esto
        context.user_data['_handled'] = True  # Marcar como manejado
        user_id = update.effective_user.id
        
        # Verificar registro existente
        with self.helpers.db as cursor:
            cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
            existing_user = cursor.fetchone()
        
        if existing_user:
            # Mostrar opciones para usuario existente
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar Todos los Datos", callback_data="force_setup")],
                [InlineKeyboardButton("✏️ Editar Campos Específicos", callback_data="edit_specific")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_from_profile")]
            ]
            
            reply_text = (
                f"📌 Ya tienes un perfil registrado, {existing_user['name']}.\n"
                "¿Qué deseas hacer?"
            )
            
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    reply_text,
                    reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text(
                    reply_text,
                    reply_markup=InlineKeyboardMarkup(keyboard))
            
            return ConversationHandler.END
        
        # Flujo para nuevo registro
        context.user_data.clear()
        context.user_data['user_id'] = user_id
        
        start_message = (
            "📝 Vamos a configurar tu perfil de salud.\n\n"
            "Por favor, dime tu nombre completo:"
        )
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(start_message)
        else:
            await update.message.reply_text(start_message)
        
        return self.states[0]

    # Handlers para cambios
    async def handle_change_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['in_conversation'] = True  # <-- Añadir esto
        context.user_data['_handled'] = True  # Marcar como manejado
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Por favor, dime tu nombre completo:")
        return self.states[0]
    
    async def handle_change_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("¿Cuántos años tienes? (Ejemplo: 28)")
        return self.states[1]
    
    async def handle_change_weight(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("¿Cuál es tu peso en kg? (ejemplo: 68.5)")
        return self.states[2]
    
    async def handle_change_height(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("¿Cuál es tu altura en cm? (ejemplo: 175)")
        return self.states[3]
    
    async def handle_change_sleep(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("¿Cuántas horas duermes normalmente por noche? (ejemplo: 7.5)")
        return self.states[6]
    
    async def handle_change_work(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("¿Cuántas horas trabajas normalmente al día? (ejemplo: 8)")
        return self.states[7]

    # Handlers principales
    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = update.message.text.strip()
        if not name:
            await update.message.reply_text("Por favor ingresa un nombre válido")
            return self.states[0]
            
        context.user_data['name'] = name
        
        await self._send_confirmation(
            update,
            f"✅ Nombre guardado: {name}",
            "¿Cuántos años tienes? (Ejemplo: 28)",
            "change_name"
        )
        return self.states[1]

    async def receive_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            age = int(update.message.text)
            if not 1 <= age <= 120:
                raise ValueError
                
            context.user_data['age'] = age
            
            await self._send_confirmation(
                update,
                f"✅ Edad guardada: {age} años",
                "¿Cuál es tu peso en kg? (ejemplo: 68.5)",
                "change_age"
            )
            return self.states[2]
            
        except ValueError:
            await update.message.reply_text("⚠️ Por favor ingresa una edad válida (1-120)")
            return self.states[1]

    async def receive_weight(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            weight = float(update.message.text)
            if weight <= 0:
                raise ValueError
                
            context.user_data['weight'] = weight
            
            await self._send_confirmation(
                update,
                f"✅ Peso guardado: {weight} kg",
                "¿Cuál es tu altura en cm? (ejemplo: 175)",
                "change_weight"
            )
            return self.states[3]
            
        except ValueError:
            await update.message.reply_text("⚠️ Por favor ingresa un peso válido (mayor que 0)")
            return self.states[2]

    async def receive_height(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            height = float(update.message.text)
            if height <= 0:
                raise ValueError
                
            context.user_data['height'] = height
            
            buttons = [
                [InlineKeyboardButton("🪑 Sedentario", callback_data="activity_low")],
                [InlineKeyboardButton("🚶 Moderado", callback_data="activity_medium")],
                [InlineKeyboardButton("🏃 Activo", callback_data="activity_high")],
                [InlineKeyboardButton("↩️ Cambiar Altura", callback_data="change_height")],
                [InlineKeyboardButton("❌ Cancelar", callback_data=BotConfig.CALLBACKS['cancel'])]
            ]
            
            await update.message.reply_text(
                f"✅ Altura guardada: {height} cm\n\n"
                "¿Cuál es tu nivel de actividad física?",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return self.states[4]
            
        except ValueError:
            await update.message.reply_text("⚠️ Por favor ingresa una altura válida (mayor que 0)")
            return self.states[3]

    async def receive_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        activity = update.message.text.lower()
        valid_activities = {
            'sedentario': 'low',
            'moderado': 'medium',
            'activo': 'high',
            'bajo': 'low',
            'medio': 'medium',
            'alto': 'high'
        }
        
        if activity not in valid_activities:
            await update.message.reply_text("⚠️ Por favor selecciona una opción válida (Sedentario, Moderado o Activo)")
            return self.states[4]
            
        context.user_data['activity_level'] = valid_activities[activity]
        return await self._process_activity(update, context)

    async def activity_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        activity_map = {
            "activity_low": "Sedentario",
            "activity_medium": "Moderado",
            "activity_high": "Activo"
        }
        
        activity = query.data.split('_')[1]
        context.user_data['activity_level'] = activity
        
        buttons = [
            [InlineKeyboardButton(text, callback_data=cb)] 
            for cb, text in [
                ("goal_muscle", "💪 Ganar músculo"),
                ("goal_weight", "⚖️ Perder peso"),
                ("goal_sleep", "😴 Dormir mejor"),
                ("goal_stress", "🧘 Reducir estrés"),
                ("goal_health", "❤️ Salud general"),
                ("goal_custom", "✏️ Personalizado")
            ]
        ]
        buttons.append([InlineKeyboardButton("↩️ Cambiar Actividad", callback_data="change_activity")])
        buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data=BotConfig.CALLBACKS['cancel'])])

        await query.edit_message_text(
            f"✅ Nivel de actividad: {activity_map[query.data]}\n\n"
            "¿Cuáles son tus principales objetivos de salud?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return self.states[5]

    async def _process_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        buttons = [
            [InlineKeyboardButton(text, callback_data=cb)] 
            for cb, text in [
                ("goal_muscle", "💪 Ganar músculo"),
                ("goal_weight", "⚖️ Perder peso"),
                ("goal_sleep", "😴 Dormir mejor"),
                ("goal_stress", "🧘 Reducir estrés"),
                ("goal_health", "❤️ Salud general"),
                ("goal_custom", "✏️ Personalizado")
            ]
        ]
        buttons.append([InlineKeyboardButton("↩️ Cambiar Actividad", callback_data="change_activity")])
        buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data=BotConfig.CALLBACKS['cancel'])])

        await update.message.reply_text(
            f"✅ Nivel de actividad: {context.user_data['activity_level'].capitalize()}\n\n"
            "¿Cuáles son tus principales objetivos de salud?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return self.states[5]

    async def receive_goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['health_goals'] = update.message.text
        
        await self._send_confirmation(
            update,
            f"✅ Objetivos guardados: {context.user_data['health_goals']}",
            "¿Cuántas horas duermes normalmente por noche? (ejemplo: 7.5)",
            "change_goals"
        )
        return self.states[6]

    async def goals_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        goals_map = {
            "goal_muscle": "Ganar masa muscular",
            "goal_weight": "Perder peso",
            "goal_sleep": "Mejorar calidad de sueño",
            "goal_stress": "Reducir estrés",
            "goal_health": "Mejorar salud general",
            "goal_custom": "Objetivos personalizados"
        }
        
        if query.data == "goal_custom":
            await query.edit_message_text(
                "Por favor, describe tus objetivos de salud personalizados:"
            )
            return self.states[5]
        
        context.user_data['health_goals'] = goals_map[query.data]
        
        await query.edit_message_text(
            f"✅ Objetivo guardado: {goals_map[query.data]}\n\n"
            "¿Cuántas horas duermes normalmente por noche? (ejemplo: 7.5)"
        )
        return self.states[6]

    async def receive_sleep(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            sleep_time = float(update.message.text)
            if not 0 < sleep_time <= 24:
                raise ValueError
                
            context.user_data['sleep_time'] = sleep_time
            
            await self._send_confirmation(
                update,
                f"✅ Horas de sueño guardadas: {sleep_time} horas",
                "¿Cuántas horas trabajas normalmente al día? (ejemplo: 8)",
                "change_sleep"
            )
            return self.states[7]
            
        except ValueError:
            await update.message.reply_text("⚠️ Por favor ingresa un valor válido (0-24 horas)")
            return self.states[6]

    async def receive_work(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            work_hours = float(update.message.text)
            if not 0 < work_hours <= 24:
                raise ValueError
                
            context.user_data['work_hours'] = work_hours
            
            try:
                with self.helpers.db as cursor:
                    # Verificar si es nuevo registro o actualización
                    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (context.user_data['user_id'],))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Actualización
                        cursor.execute('''
                            UPDATE users SET
                                name = ?, age = ?, weight = ?, height = ?,
                                activity_level = ?, health_goals = ?,
                                sleep_time = ?, work_hours = ?,
                                last_update = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                        ''', (
                            context.user_data.get('name'),
                            context.user_data.get('age'),
                            context.user_data.get('weight'),
                            context.user_data.get('height'),
                            context.user_data.get('activity_level'),
                            context.user_data.get('health_goals'),
                            context.user_data.get('sleep_time'),
                            work_hours,
                            context.user_data['user_id']
                        ))
                        action = "actualizado"
                    else:
                        # Nuevo registro
                        cursor.execute('''
                            INSERT INTO users (
                                user_id, name, age, weight, height,
                                activity_level, health_goals,
                                sleep_time, work_hours,
                                registration_date, last_update
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (
                            context.user_data['user_id'],
                            context.user_data.get('name'),
                            context.user_data.get('age'),
                            context.user_data.get('weight'),
                            context.user_data.get('height'),
                            context.user_data.get('activity_level'),
                            context.user_data.get('health_goals'),
                            context.user_data.get('sleep_time'),
                            work_hours
                        ))
                        action = "registrado"
                    
                    # Mensaje de confirmación
                    profile_summary = "\n".join(
                        f"🔹 {k}: {v}" for k, v in [
                            ("Nombre", context.user_data.get('name')),
                            ("Edad", f"{context.user_data.get('age')} años"),
                            ("Peso", f"{context.user_data.get('weight')} kg"),
                            ("Altura", f"{context.user_data.get('height')} cm"),
                            ("Actividad", context.user_data.get('activity_level', 'No especificado').capitalize()),
                            ("Objetivos", context.user_data.get('health_goals', 'No especificados')),
                            ("Sueño", f"{context.user_data.get('sleep_time')} horas/noche"),
                            ("Trabajo", f"{work_hours} horas/día")
                        ] if v is not None
                    )
                    
                    await update.message.reply_text(
                        f"🎉 ¡Perfil {action} correctamente!\n\n{profile_summary}\n\n"
                        "Ahora puedes usar /plan para generar tu plan diario personalizado."
                    )
                    return ConversationHandler.END
                    
            except sqlite3.IntegrityError as ie:
                logger.error(f"Error de integridad en DB: {ie}")
                await update.message.reply_text(
                    "⚠️ Error: Los datos proporcionados no cumplen con las validaciones. "
                    "Por favor verifica (edad 1-120, peso/altura positivos, etc.)."
                )
                return self.states[7]
            except Exception as db_error:
                logger.error(f"Error al guardar en DB: {db_error}")
                await update.message.reply_text(
                    "⚠️ Error técnico al guardar tu perfil. Por favor intenta nuevamente."
                )
                return self.states[7]
                
        except ValueError:
            await update.message.reply_text("⚠️ Por favor ingresa un valor válido (0-24 horas)")
            return self.states[7]

    async def _send_confirmation(self, update, confirmation_msg, next_question, change_callback):
        """Método helper para enviar confirmaciones"""
        keyboard = [
            [InlineKeyboardButton(f"↩️ Cambiar {change_callback.split('_')[1].title()}", 
                                callback_data=change_callback)],
            [InlineKeyboardButton("❌ Cancelar", callback_data=BotConfig.CALLBACKS['cancel'])]
        ]
        
        await update.message.reply_text(
            f"{confirmation_msg}\n\n{next_question}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    async def view_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el perfil actual del usuario"""
        user_id = update.effective_user.id
        
        try:
            with self.helpers.db as cursor:
                cursor.execute('''
                    SELECT name, age, weight, height, activity_level, 
                        health_goals, sleep_time, work_hours, 
                        strftime('%d/%m/%Y', registration_date),
                        strftime('%d/%m/%Y', last_update)
                    FROM users WHERE user_id = ?
                ''', (user_id,))
                profile = cursor.fetchone()
                
                if not profile:
                    await update.message.reply_text(
                        "No tienes un perfil registrado. Usa /setup para crear uno."
                    )
                    return
                
                # Formatear los datos del perfil
                profile_data = {
                    "Nombre": profile[0],
                    "Edad": f"{profile[1]} años" if profile[1] else "No especificado",
                    "Peso": f"{profile[2]} kg" if profile[2] else "No especificado",
                    "Altura": f"{profile[3]} cm" if profile[3] else "No especificado",
                    "Nivel de actividad": profile[4].capitalize() if profile[4] else "No especificado",
                    "Objetivos de salud": profile[5] or "No especificados",
                    "Horas de sueño": f"{profile[6]} horas/noche" if profile[6] else "No especificado",
                    "Horas de trabajo": f"{profile[7]} horas/día" if profile[7] else "No especificado",
                    "Fecha de registro": profile[8],
                    "Última actualización": profile[9]
                }
                
                profile_text = "\n".join(f"🔹 {k}: {v}" for k, v in profile_data.items())
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Actualizar Perfil", callback_data="force_setup")],
                    [InlineKeyboardButton("📅 Generar Plan Diario", callback_data="generate_plan")]
                ]
                
                await update.message.reply_text(
                    f"📋 **Tu Perfil de Salud**\n\n{profile_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error al obtener perfil: {e}")
            await update.message.reply_text(
                "⚠️ Error al recuperar tu perfil. Por favor intenta más tarde."
            )
    
    async def handle_profile_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todas las acciones desde la vista de perfil del usuario"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "force_setup":
                # Iniciar flujo de actualización forzada
                context.user_data.clear()
                context.user_data['user_id'] = query.from_user.id
                context.user_data['is_updating'] = True
                
                await query.edit_message_text(
                    "🔄 *Modo actualización de perfil*\n\n"
                    "Por favor, dime tu nombre completo:",
                    parse_mode='Markdown'
                )
                return self.states[0]  # NAME
                
            elif query.data == "generate_plan":
                # Generar plan basado en el perfil existente
                user_id = query.from_user.id
                with self.helpers.db as cursor:
                    cursor.execute('''
                        SELECT name, age, weight, height, activity_level, 
                            health_goals, sleep_time, work_hours 
                        FROM users WHERE user_id = ?
                    ''', (user_id,))
                    profile_data = cursor.fetchone()
                    
                    if not profile_data:
                        await query.edit_message_text(
                            "❌ No tienes un perfil completo. Usa /setup para crear uno."
                        )
                        return ConversationHandler.END
                    
                    # Crear diccionario con los datos
                    keys = ['name', 'age', 'weight', 'height', 'activity_level', 
                        'health_goals', 'sleep_time', 'work_hours']
                    user_profile = dict(zip(keys, profile_data))
                    
                    # Guardar en context para usar en generación de plan
                    context.user_data.update(user_profile)
                    
                    # Redirigir al handler de generación de plan
                    if hasattr(self, 'daily_plan_handler'):
                        await query.edit_message_text("📋 Generando tu plan personalizado...")
                        return await self.daily_plan_handler.show_daily_plan_menu(update, context)
                    else:
                        await query.edit_message_text(
                            "⚠️ El servicio de planes no está disponible actualmente."
                        )
                        return ConversationHandler.END
                        
            elif query.data == "edit_specific_field":
                # Menú para editar campos específicos (opcional)
                keyboard = [
                    [InlineKeyboardButton("✏️ Nombre", callback_data="edit_field:name")],
                    [InlineKeyboardButton("🎂 Edad", callback_data="edit_field:age")],
                    [InlineKeyboardButton("⚖️ Peso", callback_data="edit_field:weight")],
                    [InlineKeyboardButton("📏 Altura", callback_data="edit_field:height")],
                    [InlineKeyboardButton("🔙 Volver", callback_data="back_to_profile")]
                ]
                
                await query.edit_message_text(
                    "✏️ ¿Qué campo deseas editar?",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return "WAITING_FIELD_SELECTION"
                
            elif query.data.startswith("edit_field:"):
                # Edición de campo específico (opcional)
                field = query.data.split(":")[1]
                context.user_data['editing_field'] = field
                
                field_prompts = {
                    'name': "Por favor, escribe tu nuevo nombre completo:",
                    'age': "Por favor, escribe tu nueva edad (ejemplo: 28):",
                    'weight': "Por favor, escribe tu nuevo peso en kg (ejemplo: 68.5):",
                    'height': "Por favor, escribe tu nueva altura en cm (ejemplo: 175):"
                }
                
                await query.edit_message_text(
                    f"🔄 Editando {field}:\n\n{field_prompts.get(field, 'Por favor, escribe el nuevo valor:')}"
                )
                return "PROCESS_FIELD_UPDATE"
                
            elif query.data == "back_to_profile":
                # Regresar a la vista de perfil
                return await self.view_profile(update, context)
                
        except Exception as e:
            logger.error(f"Error en handle_profile_actions: {e}")
            await query.edit_message_text(
                "⚠️ Ocurrió un error al procesar tu solicitud. Por favor intenta nuevamente."
            )
            return ConversationHandler.END
    
    
    async def cancel_from_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el cancelar desde la vista de perfil existente"""
        query = update.callback_query
        await query.answer()
        
        try:
            await query.edit_message_text(
                "✅ Has mantenido tu perfil sin cambios.\n"
                "Usa /miperfil para ver tu información actual."
            )
        except Exception as e:
            logger.error(f"Error al cancelar desde perfil: {e}")
            try:
                await query.message.reply_text("✅ Operación cancelada")
            except:
                pass  # Fallback silencioso
        
        return ConversationHandler.END

    async def cancel_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el cancelar durante el proceso de registro/actualización"""
        context.user_data.clear()
        context.user_data['in_conversation'] = False  # <-- Añadir esto
        # Limpiar datos temporales
        context.user_data.clear()
        
        # Manejar diferente según si es callback o mensaje
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("❌ Configuración cancelada")
        else:
            await update.message.reply_text("❌ Configuración cancelada")
        
        return ConversationHandler.END
    
        
    async def process_field_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa la actualización de un campo específico"""
        field = context.user_data.get('editing_field')
        new_value = update.message.text
        
        try:
            # Validaciones específicas por campo
            if field == 'age':
                new_value = int(new_value)
                if not 1 <= new_value <= 120:
                    raise ValueError("Edad inválida")
            elif field in ['weight', 'height', 'sleep_time', 'work_hours']:
                new_value = float(new_value)
                if new_value <= 0:
                    raise ValueError("Valor debe ser positivo")
                    
            # Actualizar en base de datos
            with self.helpers.db as cursor:
                cursor.execute(f'''
                    UPDATE users SET {field} = ?, last_update = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (new_value, update.effective_user.id))
                
            await update.message.reply_text(
                f"✅ {field.capitalize()} actualizado correctamente a: {new_value}"
            )
            
            # Volver a mostrar el perfil actualizado
            return await self.view_profile(update, context)
            
        except ValueError as ve:
            await update.message.reply_text(f"⚠️ Valor inválido: {str(ve)}")
            return "PROCESS_FIELD_UPDATE"
        except Exception as e:
            logger.error(f"Error al actualizar campo: {e}")
            await update.message.reply_text(
                "⚠️ Error al actualizar tu perfil. Por favor intenta nuevamente."
            )
            return ConversationHandler.END
        
        
