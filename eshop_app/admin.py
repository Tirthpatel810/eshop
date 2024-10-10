from django.contrib import admin
from .models import *

admin.site.register(CustomUser)
admin.site.register(Contact)
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(Order)