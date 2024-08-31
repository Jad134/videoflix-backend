"""
URL configuration for videoflix project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path
from content.views import VideoListView
from users.views import ActivateAccountView, CheckUsernameView, FavoriteVideoToggle, UserFavoritesByIdView,  UserLoginView, UserRegistrationView, ResendActivationLinkView
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('check-username/<str:username>/', CheckUsernameView.as_view(), name='check-username'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('resend-activation/', ResendActivationLinkView.as_view(), name='resend-activation'),
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('django-rq/', include('django_rq.urls')),
    path('favorites/toggle/<int:video_id>/', FavoriteVideoToggle.as_view(), name='favorite-toggle'),
    path('favorites/user/<int:user_id>/', UserFavoritesByIdView.as_view(), name='user-favorites-by-id')
]  + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT) + debug_toolbar_urls()
