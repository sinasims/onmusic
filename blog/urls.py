from django.urls import path
from . import views

urlpatterns = [
    path('', views.BlogListView.as_view(), name='blog_list'),
    path('<str:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
]
