"""
URL configuration for projectx project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from user import views

from django.views.generic import TemplateView
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework.routers import DefaultRouter

app_name = 'organogram'

router = DefaultRouter()
router.register('devices', FCMDeviceAuthorizedViewSet)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('dms/', include('dms.urls'), name='dms'),
    path('organogram/', include('organogram.urls'), name='org'),
    path('memotracker/', include('memotracker.urls'), name='memotracker'),
    path('user/', include('user.urls'), name='user'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('notification/', include('notification.urls'), name='notify'),
    path("firebase-messaging-sw.js", TemplateView.as_view(
        template_name="firebase-messaging-sw.js",
        content_type="application/javascript"
    ), name="firebase-messaging-sw.js"),
    path('api/', include(router.urls)),
    #################################### Memo to DMS
    path('memo/', include(('memotracker.urls', 'memotracker'), namespace='memotracker')),
    path('dms/', include(('dms.urls', 'dms'), namespace='dms')),
    ####################################
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)