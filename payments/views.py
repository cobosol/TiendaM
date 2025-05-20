from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .validators import CouponValidator

@require_POST
@login_required
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code')
    try:
        coupon = CouponValidator.validate(coupon_code, request.user)
        # Aplicar descuento a la orden en sesión o base de datos
        request.session['active_coupon'] = str(coupon.code)
        return JsonResponse({'success': True, 'discount': coupon.discount_percent})
    except: #forms.ValidationError as e
        return JsonResponse({'success': False, 'error': str('e')})