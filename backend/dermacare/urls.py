from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import obtain_auth_token
from django.views.decorators.csrf import csrf_exempt  # modify - added

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API authentication
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', csrf_exempt(obtain_auth_token), name='api_token_auth'),  # modify - wrapped with csrf_exempt
    
    # API endpoints
    path('api/', include('api.urls_api')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
