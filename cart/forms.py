from django import forms
from stores.models import Store
import datetime
import re
from django.shortcuts import render, redirect, get_object_or_404
from registration.models import Profile
from cart.models import DeliveryInfo

class DeliveryForm(forms.ModelForm):
    def __init__(self, request=None, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        # override default attributes

    class Meta:
        model = DeliveryInfo
        fields = ['storeDelivery', 'deliveryZone']
