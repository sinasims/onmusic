from django.urls import path
from . import views

urlpatterns = [
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('logout/', views.logout_view, name='logout_api'),
    path('me/', views.get_user_info, name='user_info'),
    path('profile/', views.profile_view, name='profile'),
]
