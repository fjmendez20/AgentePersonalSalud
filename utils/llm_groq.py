import logging
from groq import Groq
from config import Config
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)

class GroqAssistant:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
    
    async def generate_response(self, prompt: str) -> Optional[str]:
        """Genera respuestas conversacionales sin formato estructurado"""
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "Eres un experto de salud que habla como un amigo cercano. "
                            "Usa lenguaje natural, sin markdown (*, -, #, ```). "
                            "Máximo 3 emojis por respuesta. "
                            "Ejemplo de estilo: 'Para empezar podrías... luego...'"
                        )
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=800
            )
            return self._clean_response(completion.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error en Groq API: {e}")
            return None

    def _clean_response(self, text: str) -> str:
        """Elimina cualquier formato residual no deseado"""
        clean_patterns = [
            (r'\*{1,2}(.*?)\*{1,2}', r'\1'),  # Quita negritas/cursivas
            (r'#{1,3}\s*', ''),     # Elimina encabezados
            (r'-\s', '• '),          # Reemplaza guiones
            (r'```\w*', ''),         # Quita bloques de código
            (r'\n{3,}', '\n\n')      # Normaliza saltos de línea
        ]
        
        for pattern, replacement in clean_patterns:
            text = re.sub(pattern, replacement, text)
            
        return text.strip()

    async def generate_health_plan(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Versión simplificada que usa los prompts de daily_plan.py"""
        # Nota: Los prompts específicos ahora están en daily_plan.py
        return await self.generate_response(
            "Por favor genera una respuesta conversacional basada en los datos proporcionados"
        )