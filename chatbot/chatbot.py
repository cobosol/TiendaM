import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

class FAQChatbot:
    def __init__(self):
        # Cargar modelo de spaCy para español
        self.nlp = spacy.load("es_core_news_md")
        
        # Base de conocimientos de FAQ
        self.faq_base = self._inicializar_faq()
        
        # Estados de conversación
        self.conversation_context = {
            "last_intent": None,
            "waiting_confirmation": False,
            "pending_action": None,
            "user_data": {}
        }
        
        # Sinónimos para mejorar el reconocimiento
        self.sinonimos = self._inicializar_sinonimos()
        
        # Patrones para confirmaciones
        self.patrones_confirmacion = {
            "si": ["sí", "si", "claro", "por supuesto", "ok", "vale", "de acuerdo", "afirmativo", "correcto"],
            "no": ["no", "negativo", "para nada", "cancelar", "detener"]
        }

    def _inicializar_faq(self):
        """Inicializa la base de conocimientos de preguntas frecuentes"""
        return [
            {
                "intencion": "saludo",
                "preguntas": [
                    "hola", "buenos días", "buenas tardes", "buenas noches",
                    "saludos", "qué tal", "cómo estás"
                ],
                "respuesta": "¡Hola! Soy el asistente virtual de Cobosis. ¿En qué puedo ayudarte hoy?",
                "requiere_contexto": False
            },
            {
                "intencion": "despedida",
                "preguntas": [
                    "adiós", "hasta luego", "chao", "nos vemos", "hasta pronto",
                    "gracias", "bye"
                ],
                "respuesta": "¡Fue un placer ayudarte! Recuerda que estamos aquí para apoyar la transformación digital de tu negocio. ¡Hasta pronto!",
                "requiere_contexto": False
            },
            {
                "intencion": "servicios_generales",
                "preguntas": [
                    "qué servicios ofrecen", "qué hacen", "a qué se dedican",
                    "qué productos tienen", "qué soluciones ofrecen"
                ],
                "respuesta": "En Cobosis ofrecemos:\n• Desarrollo de tiendas virtuales\n• Sistemas de gestión personalizados\n• Análisis de datos empresariales\n• Portales institucionales\n• Gestión de dominios y hosting\n¿Te interesa algún servicio en particular?",
                "requiere_contexto": True,
                "siguiente_paso": "especificar_servicio"
            },
            {
                "intencion": "tienda_virtual",
                "preguntas": [
                    "tienda virtual", "ecommerce", "comercio electrónico",
                    "vender en línea", "tienda online"
                ],
                "respuesta": "Nuestra **Tienda Virtual Integral** incluye:\n\n🛒 Catálogo de productos con imágenes\n💰 Pasarelas de pago integradas\n📦 Gestión de inventario en tiempo real\n🧾 Facturación electrónica\n📊 Análisis de ventas inteligente\n\n¿Te gustaría que te enviemos una cotización detallada?",
                "requiere_contexto": True,
                "siguiente_paso": "cotizacion_tienda"
            },
            {
                "intencion": "sistemas_gestion",
                "preguntas": [
                    "sistema de gestión", "software administrativo",
                    "sistema personalizado", "software a medida"
                ],
                "respuesta": "Desarrollamos **Sistemas de Gestión Personalizados** para:\n\n🏭 Control de inventario y producción\n👥 Gestión de recursos humanos\n📋 Administración de servicios\n🎓 Sistemas de evaluación\n\n¿Podrías contarme más sobre qué procesos necesitas automatizar?",
                "requiere_contexto": True,
                "siguiente_paso": "especificar_proceso"
            },
            {
                "intencion": "precios",
                "preguntas": [
                    "precios", "cuánto cuesta", "costos", "tarifas",
                    "qué precio tiene", "valor"
                ],
                "respuesta": "Nuestros precios varían según el servicio y las necesidades específicas. Para darte una cotización precisa, necesito saber:\n\n1. ¿Qué servicio te interesa?\n2. ¿El tamaño de tu empresa?\n3. ¿Funcionalidades específicas que necesitas?\n\n¿Podrías proporcionarme estos detalles?",
                "requiere_contexto": True,
                "siguiente_paso": "detalles_cotizacion"
            },
            {
                "intencion": "contacto",
                "preguntas": [
                    "contacto", "teléfono", "email", "dirección",
                    "cómo los contacto", "información de contacto"
                ],
                "respuesta": "Puedes contactarnos a través de:\n\n📧 Email: contacto@cobosis.com\n📞 Teléfono: +52 55 1234 5678 (México) / +53 7 123 4567 (Cuba)\n💬 WhatsApp: +52 55 9876 5432\n\n¿Te gustaría que te contactemos nosotros?",
                "requiere_contexto": True,
                "siguiente_paso": "solicitar_contacto"
            },
            {
                "intencion": "demostracion",
                "preguntas": [
                    "demostración", "prueba", "test", "demo",
                    "probar el sistema", "ver en acción"
                ],
                "respuesta": "¡Claro! Podemos agendar una demostración personalizada donde te mostraremos:\n\n• Funcionalidades del sistema\n• Casos similares a tu negocio\n• Respuesta a tus preguntas específicas\n\n¿Te parece bien agendarla para esta semana?",
                "requiere_contexto": True,
                "siguiente_paso": "confirmar_demo"
            }
        ]

    def _inicializar_sinonimos(self):
        """Inicializa el diccionario de sinónimos"""
        return {
            "hola": ["hola", "hi", "hello", "buenas", "saludos"],
            "adiós": ["adiós", "chao", "bye", "hasta luego", "nos vemos"],
            "servicio": ["servicio", "solución", "producto", "sistema", "plataforma"],
            "tienda": ["tienda", "ecommerce", "comercio", "venta", "online"],
            "precio": ["precio", "costo", "valor", "tarifa", "inversión"],
            "contacto": ["contacto", "comunicar", "hablar", "llamar", "escribir"],
            "demo": ["demo", "demostración", "prueba", "test", "ejemplo"]
        }

    def _expandir_sinonimos(self, texto):
        """Expande el texto reemplazando palabras por sus sinónimos"""
        doc = self.nlp(texto.lower())
        palabras_expandidas = []
        
        for token in doc:
            palabra_original = token.text
            # Buscar si la palabra tiene sinónimos
            encontrado = False
            for clave, sinonimos in self.sinonimos.items():
                if palabra_original in sinonimos:
                    palabras_expandidas.extend(sinonimos)
                    encontrado = True
                    break
            if not encontrado:
                palabras_expandidas.append(palabra_original)
        
        return " ".join(set(palabras_expandidas))  # Eliminar duplicados

    def _calcular_similitud(self, texto1, texto2):
        """Calcula la similitud entre dos textos usando embeddings"""
        doc1 = self.nlp(texto1)
        doc2 = self.nlp(texto2)
        return doc1.similarity(doc2)

    def _buscar_intencion(self, texto_usuario):
        """Busca la intención más similar en la base de conocimientos"""
        texto_usuario_limpio = texto_usuario.lower().strip()
        
        # Si estamos esperando confirmación, manejarlo primero
        if self.conversation_context["waiting_confirmation"]:
            return self._manejar_confirmacion(texto_usuario_limpio)
        
        mejor_similitud = 0
        intencion_detectada = None
        respuesta = None
        
        for faq in self.faq_base:
            # Calcular similitud con cada variación de pregunta
            for pregunta in faq["preguntas"]:
                similitud = self._calcular_similitud(texto_usuario_limpio, pregunta)
                
                # También calcular con versión expandida de sinónimos
                pregunta_expandida = self._expandir_sinonimos(pregunta)
                similitud_expandida = self._calcular_similitud(texto_usuario_limpio, pregunta_expandida)
                
                similitud_final = max(similitud, similitud_expandida)
                
                if similitud_final > mejor_similitud and similitud_final > 0.6:
                    mejor_similitud = similitud_final
                    intencion_detectada = faq["intencion"]
                    respuesta = faq["respuesta"]
                    
                    # Actualizar contexto si requiere
                    if faq.get("requiere_contexto", False):
                        self.conversation_context["last_intent"] = faq["intencion"]
                        self.conversation_context["pending_action"] = faq.get("siguiente_paso")
        
        # Si no se detecta intención clara
        if intencion_detectada is None:
            return self._respuesta_por_defecto(texto_usuario_limpio)
        
        return respuesta, intencion_detectada

    def _manejar_confirmacion(self, texto_usuario):
        """Maneja respuestas de confirmación (sí/no)"""
        texto = texto_usuario.lower()
        
        # Detectar confirmación positiva
        if any(palabra in texto for palabra in self.patrones_confirmacion["si"]):
            accion = self.conversation_context["pending_action"]
            
            if accion == "cotizacion_tienda":
                respuesta = "¡Perfecto! Nuestro equipo te enviará una cotización detallada en las próximas 24 horas. ¿Podrías proporcionarnos tu email para enviarte la información?"
                self.conversation_context["pending_action"] = "solicitar_email_cotizacion"
                
            elif accion == "confirmar_demo":
                respuesta = "Excelente. Tenemos disponibilidad para mañana a las 10:00 AM o el jueves a las 3:00 PM. ¿Cuál te funciona mejor?"
                self.conversation_context["pending_action"] = "agendar_horario_demo"
                
            elif accion == "solicitar_contacto":
                respuesta = "Claro, nuestro equipo se pondrá en contacto contigo en las próximas 2 horas. ¿Podrías confirmarnos tu número de teléfono?"
                self.conversation_context["pending_action"] = "solicitar_telefono"
                
            else:
                respuesta = "Confirmado. ¿En qué más puedo ayudarte?"
                self.conversation_context["waiting_confirmation"] = False
                
        # Detectar confirmación negativa
        elif any(palabra in texto for palabra in self.patrones_confirmacion["no"]):
            respuesta = "Entendido. ¿Hay algo más en lo que pueda ayudarte?"
            self.conversation_context["waiting_confirmation"] = False
            self.conversation_context["pending_action"] = None
            
        else:
            respuesta = "No entendí tu respuesta. ¿Podrías confirmar con 'sí' o 'no'?"
        
        return respuesta, "confirmacion"

    def _respuesta_por_defecto(self, texto_usuario):
        """Genera respuesta cuando no se detecta intención clara"""
        patrones_ayuda = ["ayuda", "qué puedes hacer", "funciones", "comandos"]
        
        if any(palabra in texto_usuario for palabra in patrones_ayuda):
            ayuda = "Puedo ayudarte con información sobre:\n"
            ayuda += "• Nuestros servicios y productos\n"
            ayuda += "• Precios y cotizaciones\n"
            ayuda += "• Agendar demostraciones\n"
            ayuda += "• Información de contacto\n"
            ayuda += "¿En qué tema específico necesitas ayuda?"
            return ayuda, "ayuda"
        else:
            default_responses = [
                "No estoy seguro de entender. ¿Podrías reformular tu pregunta?",
                "Mi conocimiento es limitado en ese tema. ¿Tienes alguna pregunta sobre nuestros servicios?",
                "No tengo información sobre eso. ¿Puedo ayudarte con algo relacionado a transformación digital?"
            ]
            import random
            return random.choice(default_responses), "desconocido"

    def procesar_mensaje(self, texto_usuario):
        """Procesa el mensaje del usuario y devuelve respuesta"""
        # Verificar si es un mensaje vacío
        if not texto_usuario or texto_usuario.strip() == "":
            return "Hola, ¿en qué puedo ayudarte?", "saludo"
        
        # Buscar intención y respuesta
        respuesta, intencion = self._buscar_intencion(texto_usuario)
        
        # Si la respuesta requiere confirmación, actualizar estado
        if intencion not in ["saludo", "despedida", "confirmacion", "desconocido"]:
            for faq in self.faq_base:
                if faq["intencion"] == intencion and faq.get("requiere_contexto", False):
                    self.conversation_context["waiting_confirmation"] = True
                    break
        
        return respuesta, intencion

    def reiniciar_conversacion(self):
        """Reinicia el contexto de la conversación"""
        self.conversation_context = {
            "last_intent": None,
            "waiting_confirmation": False,
            "pending_action": None,
            "user_data": {}
        }

# Función principal para ejecutar el chatbot
def encontrar_respuesta(pregunta_usuario):
    print("En encontrar respuesta")
    bot = FAQChatbot()
    try:
        if pregunta_usuario.lower() in ['salir', 'exit', 'quit']:
            return "¡Hasta luego! Espero haber sido de ayuda."
            
        respuesta, intencion = bot.procesar_mensaje(encontrar_respuesta)
        print(f"🤖 Cobosis: {respuesta}")
        print(f"   [Intención detectada: {intencion}]")
        print()    
    except KeyboardInterrupt:
        print("\n🤖 Chatbot: Conversación terminada. ¡Hasta pronto!")
    except Exception as e:
        print(f"🤖 Chatbot: Lo siento, hubo un error. Por favor, intenta nuevamente.")
        print(f"   [Error: {e}]")


# Ejemplo de uso programático
def ejemplo_uso():
    bot = FAQChatbot()
    
    # Simular una conversación
    conversacion = [
        "Hola",
        "Qué servicios tienen",
        "Me interesa la tienda virtual",
        "Sí, quiero cotización",
        "mi.email@empresa.com",
        "Gracias"
    ]
    
    print("💬 Simulación de conversación:\n")
    for mensaje in conversacion:
        print(f"👤 Usuario: {mensaje}")
        respuesta, intencion = bot.procesar_mensaje(mensaje)
        print(f"🤖 Chatbot: {respuesta}")
        print(f"   [Intención: {intencion}]\n")

    
    # O ejecutar ejemplo de uso
    # ejemplo_uso()