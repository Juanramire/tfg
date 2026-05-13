import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

VALID_FEATURES = [
    "Gaming",
    "Edicion",
    "Programacion",
    "Ofimatica",
    "Intel",
    "AMD",
    "Intel_Gama_Baja",
    "Intel_Gama_Media",
    "Intel_Gama_Alta",
    "AMD_Gama_Baja",
    "AMD_Gama_Media",
    "AMD_Gama_Alta",
    "DDR4",
    "DDR5",
    "RAM_8GB",
    "RAM_16GB",
    "RAM_32GB",
    "RAM_64GB",
    "GPU_Gama_Baja",
    "GPU_Gama_Media",
    "GPU_Gama_Alta",
    "SSD_NVMe",
    "SSD_SATA",
    "Disco_HDD",
    "PSU_500W",
    "PSU_650W",
    "PSU_750W",
    "PSU_850W",
    "Refrigeracion_Liquida",
    "Refrigeracion_Aire",
    "Placa_ATX",
    "Placa_MicroATX",
    "Placa_MiniITX",
    "Caja_ATX",
    "Caja_MicroATX",
    "Caja_MiniITX",
    "LGA1700",
    "LGA1851",
    "AM4",
    "AM5",
]

SYSTEM_PROMPT = f"""Eres un asistente experto en hardware de PC. Tu tarea es interpretar consultas en lenguaje natural
y extraer información estructurada para un configurador de PCs basado en un Modelo de Características.

Las features válidas del modelo son: {', '.join(VALID_FEATURES)}

Dado el mensaje del usuario, responde ÚNICAMENTE con un JSON válido con esta estructura:
{{
  "perfil": "<Gaming|Edicion|Programacion|Ofimatica|null>",
  "presupuesto": <número en euros o null si no se menciona>,
  "selected": [<lista de features UVL que se deben activar>],
  "deselected": [<lista de features UVL que se deben desactivar>],
  "explicacion": "<una frase explicando tu interpretación de la consulta>"
}}

Reglas de interpretación:
- "jugar", "gaming", "videojuegos", cualquier juego (Minecraft, Fortnite, etc.) → perfil Gaming
- "editar vídeo", "renderizar", "After Effects", "Premiere" → perfil Edicion
- "programar", "desarrollo", "código", "IDE" → perfil Programacion
- "ofimática", "trabajo básico", "navegar", "Word", "Excel" → perfil Ofimatica
- "4K", "ultra settings", "máximo rendimiento" → GPU_Gama_Alta
- "1080p", "calidad media" → GPU_Gama_Media
Rangos de presupuesto orientativos según contexto:
- "lo mínimo", "lo más barato posible", "menos de 500", "muy barato" → 400-500€
- "barato", "económico", "poco presupuesto", "básico" → 500-650€
- "sin gastarme mucho", "asequible", "sin arruinarme", "moderado" → 700-900€
- "gama media", "equilibrado", "relación calidad-precio" → 900-1200€
- "gama alta", "sin límite", "lo mejor", "profesional" → 1500-2500€
- "4K ultra", "máximo rendimiento", "tope de gama" → 2000-3000€
- Si menciona un juego concreto de altos requisitos (Cyberpunk, Elden Ring, Alan Wake 2 en 4K) → Gaming + GPU_Gama_Alta + presupuesto mínimo 1500€
- Si menciona juego en 1080p o "gama media" → Gaming + GPU_Gama_Media + presupuesto 900-1100€
- Si menciona edición en 4K → Edicion + RAM_32GB + presupuesto mínimo 1400€
Almacenamiento:
- "mucho almacenamiento", "bastante espacio", "disco grande", "mucho espacio", "varias unidades" → selected debe incluir ["SSD_NVMe", "Disco_HDD"] y presupuesto mínimo 900€
- "almacenamiento rápido", "SSD rápido", "NVMe" → selected debe incluir "SSD_NVMe"
- "almacenamiento económico", "disco barato" → selected debe incluir "SSD_SATA"
- "disco duro", "HDD", "mucho espacio barato" → selected debe incluir "Disco_HDD"

RESTRICCIONES CRÍTICAS (nunca violarlas):
- Si el usuario menciona "gaming", "jugar", o cualquier videojuego, el perfil SIEMPRE debe ser "Gaming" aunque pida algo aparentemente contradictorio (como "sin GPU" o "sin tarjeta gráfica"). El backend resuelve las inconsistencias; tú solo asegura que el perfil sea correcto.
- Si perfil es Gaming o Edicion, NUNCA añadas TarjetaGrafica a deselected.
- Si perfil es Gaming, deselected debe estar vacío (Gaming tiene sus propias restricciones de compatibilidad).
- Si un juego es de bajos requisitos (Minecraft, Roblox, etc.), usa presupuesto bajo (400-600€) pero mantén perfil Gaming con deselected vacío.

Responde SOLO con el JSON, sin texto adicional, sin markdown."""


def interpretar_consulta(consulta: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "TU_CLAVE_AQUI":
        raise RuntimeError("GEMINI_API_KEY no configurada en .env")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=consulta,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
        raw = response.text.strip()

        # Strip markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        # Sanitize: remove unknown features
        valid_set = set(VALID_FEATURES)
        result["selected"] = [f for f in result.get("selected", []) if f in valid_set]
        result["deselected"] = [
            f for f in result.get("deselected", []) if f in valid_set
        ]

        return result

    except json.JSONDecodeError as e:
        logger.error("Gemini devolvió JSON inválido: %s", e)
        raise RuntimeError("La IA no pudo interpretar la consulta. Inténtalo de nuevo.")
    except Exception as e:
        logger.error("Error llamando a Gemini: %s", e)
        raise RuntimeError(f"Error al contactar con la IA: {e}")
