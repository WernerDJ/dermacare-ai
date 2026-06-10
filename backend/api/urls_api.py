from django.urls import path  # modify - added
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'portfolios', views.BrandPortfolioViewSet, basename='portfolio')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')
router.register(r'user-session', views.UserSessionViewSet, basename='user-session')

# modify # - Add registration endpoint separately (not a ViewSet)
urlpatterns = [
    path('auth/register/', views.register_user, name='register'),  
    path('user/admin-status/', views.check_user_admin_status, name='check_admin_status'),# modify
]

# modify # - Add all router URLs
urlpatterns += router.urls
