"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, re_path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def home_view(request):
    if request.user.is_authenticated:
        return redirect('profiles:profile_step1')
    else:
        return redirect('users:login')
    
schema_view = get_schema_view(
    openapi.Info(
        title="TeumTeumi API 문서",
        default_version='v1',
        description="TeumTeumi 서비스의 API 명세서입니다.",

    ),
    public=True,  # True면 누구나 접근 가능, False면 권한 필요
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'), 

    path('users/', include('apps.users.urls', namespace='users')),
    path('profiles/', include('apps.profiles.urls')),
    path('schedules/', include('apps.schedules.urls')),
    path('matches/', include('apps.matches.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('chats/', include('apps.chats.urls')),
    path('interests/', include('apps.interests.urls')), 
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),    # Swagger 문서 경로
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]
