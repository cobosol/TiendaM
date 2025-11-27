import spacy
from django.db import close_old_connections
from registration.models import Profile
#from enlac_preg.models import FAQ
from datetime import datetime, timedelta

# Cargar modelo de español de spaCy
try:
    nlp = spacy.load("es_core_news_md")
except:
    # Fallback si no está instalado
    nlp = None

def encontrar_respuesta(pregunta_usuario, usuario=None):
    close_old_connections()
    print("En encontrar respuestas")
    pregunta = pregunta_usuario.lower()
    print(pregunta)
    # 1. Verificar si es una consulta de autenticación
    if any(palabra in pregunta for palabra in ['iniciar sesión', 'login', 'autenticar', 'registrarse', 'entrar']):
        return "Para acceder a tus datos personales, necesito que te autentiques. Por favor, proporciona tu usuario y contraseña."
    
    # 2. Si el cliente está autenticado, buscar información personal
    if usuario:
        # Consultas sobre pedidos
        print("usuario autenticado")
        print(usuario)
        if any(palabra in pregunta for palabra in ['mis datos', 'perfil', 'currículo']):
            print("Encontró perfil")
            datos = Profile.objects.filter(user=usuario.id).order_by('-created_at')[:5]
            if datos:
                respuesta = "Tus datos:\n"
                for dato in datos:
                    respuesta += f"- Cargo #{dato.cargo}: {dato.title} {dato.location})\n"
                return respuesta
            else:
                return "No tienes datos registrados."
        
        # Consultas sobre datos personales
    """         if any(palabra in pregunta for palabra in ['mis datos', 'mi perfil', 'información personal']):
            return f"Tus datos:\nNombre: {cliente.usuario.first_name} {cliente.usuario.last_name}\nEmail: {cliente.usuario.email}\nTeléfono: {cliente.telefono}\nDirección: {cliente.direccion}"
    
    # 3. Consultas de inventario en tiempo real
    if any(palabra in pregunta for palabra in ['stock', 'disponible', 'inventario', 'hay', 'existencias']):
        # Buscar nombres de productos en la pregunta
        productos = Producto.objects.all()
        productos_encontrados = []
        
        for producto in productos:
            if producto.nombre.lower() in pregunta:
                productos_encontrados.append(producto)
        
        if productos_encontrados:
            respuesta = "Información de disponibilidad:\n"
            for producto in productos_encontrados:
                estado = "Disponible" if producto.disponible and producto.stock > 0 else "Agotado"
                respuesta += f"- {producto.nombre}: {estado} ({producto.stock} unidades)\n"
            return respuesta
        else:
            # Si no se menciona un producto específico, buscar por similitud
            if nlp:
                doc_usuario = nlp(pregunta)
                for producto in productos:
                    doc_producto = nlp(producto.nombre.lower())
                    similitud = doc_usuario.similarity(doc_producto)
                    if similitud > 0.7:
                        estado = "Disponible" if producto.disponible and producto.stock > 0 else "Agotado"
                        return f"El producto {producto.nombre} está {estado} ({producto.stock} unidades). Precio: ${producto.precio}"
    
    # 4. Consultas de precios
    if any(palabra in pregunta for palabra in ['precio', 'costo', 'valor', 'cuánto cuesta']):
        productos = Producto.objects.all()
        for producto in productos:
            if producto.nombre.lower() in pregunta:
                return f"El precio de {producto.nombre} es ${producto.precio}. {'Disponible' if producto.disponible else 'Agotado'}." """
    
    # 5. Búsqueda en FAQs (sistema original)
    """ preguntas_faq = FAQ.objects.all()
    mejor_coincidencia = None
    mejor_puntaje = 0
    
    if nlp:
        doc_usuario = nlp(pregunta)
        for faq in preguntas_faq:
            doc_faq = nlp(faq.pregunta.text.lower())
            puntaje = doc_usuario.similarity(doc_faq)
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_coincidencia = faq
    
    if mejor_coincidencia and mejor_puntaje > 0.6:
        return mejor_coincidencia.respuesta.text """
    
    # 6. Respuesta por defecto
    return "Lo siento, no tengo información sobre eso. ¿Puedes intentar con otra pregunta o contactar con nuestro equipo de soporte?"