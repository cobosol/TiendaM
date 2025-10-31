from django.contrib import admin
from .models import Order, OrderItem, PaymentMethod, Coupon
#, DeliveryType

class PaymentMethodInline(admin.TabularInline):
    model = PaymentMethod
    readonly_fields = ('formatted_details',)
    fields = ('method', 'amount', 'transaction_count', 'formatted_details')
    extra = 0
    
    def formatted_details(self, obj):
        if obj.method == 'TRANSFER' and obj.details_json:
            details = []
            for item in obj.details_json:
                details.append(f"{item.get('reference', '')}: ${item.get('amount', 0):.2f}")
            return '<br>'.join(details)
        return obj.transaction_details
    formatted_details.short_description = "Detalles"
    formatted_details.allow_tags = True
    
    
class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('__unicode__','date','status','transaction_id','user', 'is_daily_summary', 'seller')
    list_filter = ('status','date')
    search_fields = ('delivery_email', 'delivery_ci', 'delivery_name', 'id','transaction_id')
    inlines = [OrderItemInline,PaymentMethodInline]
    fieldsets = (
                ('Generales', {'fields': ('consecutivo', 'base_total','end_total','usd_total','cup_total','cup_oficial','mlc_total','total_reported','coupon_percent', 'others_discount', 'currency')}),
                ('Comprador', {'fields': ('user','status','payment_email','payment_phone', 'pay_url')}),
                ('Entrega', {'fields':('delivery_name','delivery_address_2','delivery_state', 'delivery_price')})
                )

admin.site.register(Order, OrderAdmin)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'discount_percent', 'expiration_date', 'used')
    list_filter = ('used', 'expiration_date')
    search_fields = ('user__email', 'code')
    readonly_fields = ('code',)