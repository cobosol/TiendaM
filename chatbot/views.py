from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

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
        return JsonResponse(
            {'error': f'Error del servidor: {str(e)}'}, 
            status=500
        )
# Create your views here.
