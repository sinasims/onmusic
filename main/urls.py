from django.urls import path, reverse
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap
from music.models import Song, Artist, Album
from blog.models import BlogPost
from django.db.models import Count
from . import views


class SongSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Song.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/song/{obj.id}/'


class ArtistSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Artist.objects.annotate(sc=Count('songs')).filter(sc__gt=0)

    def location(self, obj):
        return f'/artist/{obj.slug}/'


class AlbumSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Album.objects.filter(is_published=True)

    def location(self, obj):
        return f'/album/{obj.slug}/'


class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/blog/{obj.slug}/'


class StaticViewSitemap(Sitemap):
    priority = 0.5

    def items(self):
        return [
            ('home', 'home', 1.0, 'daily'),
            ('song_list', 'song_list', 0.8, 'daily'),
            ('album_list', 'album_list', 0.7, 'daily'),
            ('artist_list', 'artist_list', 0.6, 'daily'),
            ('blog_list', 'blog_list', 0.7, 'daily'),
            ('about', 'about', 0.6, 'monthly'),
            ('contact', 'contact', 0.5, 'monthly'),
            ('terms', 'terms', 0.3, 'yearly'),
            ('privacy', 'privacy', 0.3, 'yearly'),
        ]

    def location(self, obj):
        return reverse(obj[1])

    def priority(self, obj):
        return obj[2]

    def changefreq(self, obj):
        return obj[3]


sitemaps = {
    'static': StaticViewSitemap,
    'songs': SongSitemap,
    'artists': ArtistSitemap,
    'albums': AlbumSitemap,
    'blog': BlogSitemap,
}


def robots(request):
    lines = [
        'User-agent: *',
        'Disallow: /cart/',
        'Disallow: /accounts/',
        'Disallow: /ckeditor/',
        '',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('comment/', views.submit_comment, name='submit_comment'),
    path('comment/vote/', views.vote_comment, name='vote_comment'),
    path('captcha/', views.captcha, name='captcha'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('manifest.json', views.manifest, name='manifest'),
    path('offline/', views.offline_view, name='offline'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', robots, name='robots'),
]
