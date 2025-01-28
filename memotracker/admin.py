from django.contrib import admin
from .models import Memo, ApprovalRoute, MemoRoute, MemoAttachment, MemoAction

# Register your models here.
admin.site.register(Memo)
admin.site.register(ApprovalRoute)
admin.site.register(MemoRoute)
admin.site.register(MemoAttachment)
admin.site.register(MemoAction)

