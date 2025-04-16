from groq import Groq
from config import Config  # Importar la clase Config en lugar del módulo
from typing import Dict, Any

class GroqAssistant:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY  # Acceder a través de la clase
    
    def generate_response(self, prompt: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un experto asistente de salud en español."},
                    {"role": "user", "content": prompt}
                ],
                model=config.GROQ_MODEL,
                temperature=0.7,
                max_tokens=1024
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error en Groq API: {e}")
            return None

    def generate_health_plan(self, user_data):
        prompt = f"""
        Genera un plan de salud diario en español con estos datos:
        - Nombre: {user_data.get('name', 'Usuario')}
        - Edad: {user_data.get('age', 30)}
        - Peso: {user_data.get('weight', 70)} kg
        - Altura: {user_data.get('height', 170)} cm
        - Objetivos: {user_data.get('health_goals', 'mejorar salud')}
        - Horas de trabajo: {user_data.get('work_hours', 8)}
        - Hora de dormir: {user_data.get('sleep_time', '22:00')}

        Incluye:
        1. 💧 Recomendaciones de hidratación
        2. 🏋️ Rutina de ejercicio personalizada
        3. 🥗 Plan de comidas saludables
        4. ⏰ Pausas activas durante el trabajo
        5. 😴 Consejos para mejorar el sueño

        Formato: Usa emojis, listas claras y sé conciso (máx. 400 palabras).
        """
        return "Plan generado con Groq"  # Ejemplo temporal
