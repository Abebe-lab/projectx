from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(DocumentCategory)
admin.site.register(Document)
admin.site.register(SharedDocument)
admin.site.register(MemoToDMS)
