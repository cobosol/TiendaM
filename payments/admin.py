from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'discount_percent', 'expiration_date', 'used')
    list_filter = ('used', 'expiration_date')
    search_fields = ('user__email', 'code')
    readonly_fields = ('code',)