from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Role)
admin.site.register(Category)
admin.site.register(BusinessUnit)
admin.site.register(UserRole)
admin.site.register(ExternalCustomer)
admin.site.register(Permission)
admin.site.register(RolePermission)
admin.site.register(Profile)

