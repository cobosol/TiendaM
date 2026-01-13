from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from catalog.models import Product
from catalog.serializers import ProductsCoboChatSerializer
import json
import logging
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods
from chatbot.chatbotAuth import encontrar_respuesta
from datetime import datetime, timezone
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from registration.models import Profile

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAuthAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            action = data.get('action', '')
            
            if action == 'login':
                username = data.get('username', '')
                password = data.get('password', '')
                
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Autenticación exitosa',
                        'user': {
                            'nombre': f"{user.first_name} {user.last_name}".strip() or user.username,
                            'email': user.email
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Usuario o contraseña incorrectos'
                    }, status=401)
                    
            return JsonResponse({
                'status': 'error',
                'message': 'Acción no válida'
            }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotPrivateAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            # Obtener información del cliente autenticado
            try:
                usuario = Profile.objects.get(user=request.user)
            except Profile.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Perfil de cliente no encontrado'
                }, status=404)
            
            # Procesar mensaje con acceso a datos privados
            respuesta = encontrar_respuesta(user_message, usuario=usuario)
            
            return JsonResponse({
                'status': 'success',
                'message': respuesta
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }, status=500)
        

@require_http_methods(["POST"])
@csrf_exempt
def chatbot_api(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '').strip()
        chat_history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({
                'status': 'error',
                'message': 'Mensaje vacío'
            }, status=400)
        
        # Obtener respuesta del chatbot (puedes pasar el historial si lo necesitas)
        print("Voy a encontrar respuesta")
        bot_response = encontrar_respuesta(user_message)
        return JsonResponse({
            'status': 'success',
            'message': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Formato JSON inválido'
        }, status=400)
        
    except Exception as e:
        # Log del error para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error en chatbot API: {str(e)}")
        
        return JsonResponse({
            'status': 'error',
            'message': 'Error interno del servidor'
        }, status=500)
    

@csrf_exempt  # Solo si necesitas deshabilitar CSRF para esta vista
@require_POST
def chat_query(request):
    try:
        # Decodificar los datos JSON del cuerpo de la solicitud
        body = json.loads(request.body)
        intent = body.get('intent')
        entities = body.get('entities', [])
        
        # Validar datos requeridos
        if not intent:
            return JsonResponse(
                {'error': 'El campo "intent" es requerido'}, 
                status=400
            )
        if intent == "consultar_estado_pedido":
            response_data = {
                'response': f"Recibida intención: {intent}",
                'entities_procesadas': entities,
                'status': 'éxito'
            }
        elif intent == "consultar_stock":
            product = entities.get('product', [])
            formato = entities.get('formato', [])
            if product and formato:
                print("Buscar por nombre y formato. Devolver disponibilidad")
            elif product:
                print("Buscar todos los formatos del producto. Devolver disponibilidad")
        elif intent == "consultar_precio":
            product = entities.get('product', [])
            formato = entities.get('formato', [])
            if product and formato:
                print("Buscar por nombre y formato. Devolver precio")
            elif product:
                print("Buscar todos los formatos del producto. Devolver precio")
        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Formato JSON inválido'}, 
            status=400
        )
    except Exception as e:
        logging.exception("Unhandled exception in chat_query")
        return JsonResponse(
            {'error': 'Error interno del servidor'}, 
            status=500
        )
# Create your views here.

# views.py

class ProductoBusquedaExactaAPIView(generics.RetrieveAPIView):
    """
    API para búsqueda exacta por nombre
    Devuelve un solo producto si el nombre coincide exactamente
    """
    serializer_class = ProductsCoboChatSerializer

    def get_object(self):
        nombre = self.request.query_params.get('name', '').strip()
        if not nombre:
            return None
        
        try:
            # Búsqueda exacta case-insensitive
            return Product.objects.get(name__iexact=nombre, is_active=True)
        except Product.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance is None:
            nombre = request.query_params.get('name', '')
            if not nombre:
                return Response(
                    {"error": "El parámetro 'nombre' es requerido"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"error": f"No se encontró un producto con el nombre exacto: '{nombre}'"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class ProductoBusquedaParcialAPIView(generics.ListAPIView):
    """
    API para búsqueda parcial por nombre
    Devuelve todos los productos cuyo nombre contenga el término buscado
    """
    serializer_class = ProductsCoboChatSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        nombre = self.request.query_params.get('name', '').strip()
        
        if nombre:
            # Búsqueda parcial case-insensitive
            queryset = queryset.filter(name__icontains=nombre)
        
        return queryset.order_by('name')

    def list(self, request, *args, **kwargs):
        nombre = request.query_params.get('name', '').strip()
        
        if not nombre:
            return Response(
                {"error": "El parámetro 'nombre' es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response(
                {
                    "mensaje": f"No se encontraron productos que contengan: '{nombre}'",
                    "resultados": []
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "termino_busqueda": nombre,
            "cantidad_resultados": queryset.count(),
            "resultados": serializer.data
        })

class ProductoBusquedaFlexibleAPIView(generics.ListAPIView):
    """
    API que combina ambas búsquedas: primero exacta, luego parcial
    """
    serializer_class = ProductsCoboChatSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        nombre = self.request.query_params.get('name', '').strip()
        tipo_busqueda = self.request.query_params.get('tipo', 'flexible')  # exacta, parcial, flexible
        
        if nombre:
            if tipo_busqueda == 'exacta':
                queryset = queryset.filter(name__iexact=nombre)
            elif tipo_busqueda == 'parcial':
                queryset = queryset.filter(name__icontains=nombre)
            else:  # flexible - por defecto
                # Primero intenta búsqueda exacta, si no hay resultados, busca parcial
                exacta = queryset.filter(name__iexact=nombre)
                if exacta.exists():
                    queryset = exacta
                else:
                    queryset = queryset.filter(name__icontains=nombre)
        
        return queryset.order_by('name')

    def list(self, request, *args, **kwargs):
        nombre = request.query_params.get('name', '').strip()
        tipo_busqueda = request.query_params.get('tipo', 'flexible')
        
        if not nombre:
            return Response(
                {"error": "El parámetro 'nombre' es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        response_data = {
            "termino_busqueda": nombre,
            "tipo_busqueda": tipo_busqueda,
            "cantidad_resultados": queryset.count(),
            "resultados": serializer.data
        }
        
        if not queryset.exists():
            response_data["mensaje"] = f"No se encontraron productos para: '{nombre}'"
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        
        return Response(response_data)