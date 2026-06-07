from django.contrib import admin
from .models import Artist, Song, Album, SubscriptionPlan, Rating, UserSubscription, UserDownload, WishlistItem, ScrapedSong


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'get_song_count']

    @admin.display(description='تعداد آثار')
    def get_song_count(self, obj):
        return obj.songs.count()
    search_fields = ['name', 'bio']


class AlbumSongsInline(admin.TabularInline):
    model = Album.songs.through
    extra = 1


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'price', 'duration', 'bpm', 'musical_key', 'is_published', 'is_best_seller', 'is_popular', 'views_count', 'purchase_count']
    list_editable = ['is_published', 'is_best_seller', 'is_popular']
    list_filter = ['artist', 'is_published', 'is_best_seller', 'is_popular']
    search_fields = ['title', 'artist__name', 'composer', 'lyricist', 'description']
    list_select_related = ['artist']
    fieldsets = [
        ('اطلاعات اصلی', {'fields': ['title', 'artist', 'description', 'price', 'cover']}),
        ('فایل‌های صوتی', {'fields': ['original_audio', 'arranged_audio', 'preview_url']}),
        ('جزئیات موسیقی', {'fields': ['duration', 'composer', 'lyricist', 'bpm', 'musical_key', 'lyrics']}),
        ('وضعیت', {'fields': ['is_published', 'is_best_seller', 'is_popular', 'views_count', 'purchase_count']}),
    ]


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ['title', 'price', 'is_published']
    list_editable = ['is_published']
    list_filter = ['is_published']
    search_fields = ['title', 'description']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'duration_days', 'download_limit', 'is_active', 'is_popular']
    list_editable = ['is_active', 'is_popular']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'remaining_downloads', 'is_active']
    list_filter = ['is_active', 'plan']
    search_fields = ['user__phone', 'plan__title']
    list_select_related = ['user', 'plan']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['song', 'user', 'score', 'created_at']
    list_filter = ['score']
    search_fields = ['user__phone', 'song__title']


@admin.register(UserDownload)
class UserDownloadAdmin(admin.ModelAdmin):
    list_display = ['user', 'song', 'version', 'downloaded_at']
    list_filter = ['version']
    search_fields = ['user__phone', 'song__title']
    list_select_related = ['user', 'song']


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'song', 'created_at']
    search_fields = ['user__phone', 'song__title']
    list_select_related = ['user', 'song']


@admin.register(ScrapedSong)
class ScrapedSongAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist_name', 'date_str', 'download_count', 'is_imported', 'separate_instruments', 'separation_status', 'created_at']
    list_editable = ['separate_instruments']
    list_filter = ['is_imported', 'separate_instruments', 'separation_status']
    search_fields = ['title', 'artist_name']
    readonly_fields = ['created_at', 'separation_status', 'error_message']
    actions = ['mark_as_imported', 'mark_as_not_imported', 'mark_separate_true', 'mark_separate_false', 'reset_separation']
    fieldsets = [
        ('اطلاعات آهنگ', {'fields': ['title', 'artist_name', 'cover_url', 'mp3_url', 'source_url', 'slug', 'date_str', 'download_count']}),
        ('تفکیک سازها', {'fields': ['separate_instruments', 'separation_status', 'error_message', 'is_imported'], 'classes': ['collapse']}),
    ]

    @admin.action(description='علامت‌گذاری به عنوان وارد شده')
    def mark_as_imported(self, request, queryset):
        queryset.update(is_imported=True)

    @admin.action(description='علامت‌گذاری به عنوان وارد نشده')
    def mark_as_not_imported(self, request, queryset):
        updated = queryset.update(is_imported=False)
        self.message_user(request, f'{updated} مورد به عنوان وارد نشده علامت‌گذاری شد.')

    @admin.action(description='علامت‌گذاری تفکیک سازها: فعال')
    def mark_separate_true(self, request, queryset):
        updated = queryset.update(separate_instruments=True)
        self.message_user(request, f'{updated} مورد برای تفکیک سازها فعال شد.')

    @admin.action(description='علامت‌گذاری تفکیک سازها: غیرفعال')
    def mark_separate_false(self, request, queryset):
        updated = queryset.update(separate_instruments=False)
        self.message_user(request, f'{updated} مورد برای تفکیک سازها غیرفعال شد.')

    @admin.action(description='بازنشانی وضعیت تفکیک به در انتظار')
    def reset_separation(self, request, queryset):
        updated = queryset.update(separation_status='pending', error_message='')
        self.message_user(request, f'{updated} مورد به وضعیت "در انتظار" بازنشانی شد.')
