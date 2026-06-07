from django.urls import path
from . import views

urlpatterns = [
    path('songs/', views.SongListView.as_view(), name='song_list'),
    path('albums/', views.AlbumListView.as_view(), name='album_list'),
    path('artists/', views.ArtistListView.as_view(), name='artist_list'),
    path('song/<int:pk>/', views.SongDetailView.as_view(), name='song_detail'),
    path('album/<str:slug>/', views.AlbumDetailView.as_view(), name='album_detail'),
    path('artist/<str:slug>/', views.ArtistDetailView.as_view(), name='artist_detail'),
    path('subscription/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('api/rate/', views.submit_rating, name='submit_rating'),
    path('api/wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('api/wishlist/', views.get_wishlist, name='get_wishlist'),
    path('download/<int:song_id>/<str:version>/', views.download_song, name='download_song'),
]
