class BotConfig:
    SETUP_STATES = [
        "NAME",
        "AGE",
        "WEIGHT",
        "HEIGHT",
        "ACTIVITY",
        "GOALS",
        "SLEEP",
        "WORK"
    ]
    
    #START_COMMANDS = ['start', 'hola', 'inicio', 'menu', 'help', 'ayuda']
    #START_KEYWORDS = ['hola bot', 'empezar', 'quiero comenzar', 'bot ayuda']
    
    REMINDER_TYPES = {
        'agua': {
            'interval': 7200,  # 2 horas en segundos
            'message': "💧 ¡Hora de tomar agua! ¡Mantente hidratado!"
        },
        'pausa': {
            'interval': 2700,  # 45 minutos
            'message': "🧘 ¡Hora de una pausa activa! Estira tus piernas"
        },
        'postura': {
            'interval': 1800,  # 30 minutos
            'message': "👀 ¡Revisa tu postura! Siéntate derecho"
        }
    }
    
    CALLBACKS = {
        'setup': "setup_profile",
        'daily_plan': "daily_plan_menu",
        'reminders': "reminders_menu",
        'premium': "premium_info",
        'cancel': "cancel",
        'activities': ["activity_low", "activity_medium", "activity_high"],
        'goals': ["goal_muscle", "goal_weight", "goal_sleep", "goal_stress", "goal_health", "goal_custom"],
        'cancel': "cancel_setup",
    }