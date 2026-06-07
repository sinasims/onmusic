from django.contrib import admin
from django.db import models
from ckeditor.widgets import CKEditorWidget
from .models import HeroSlide, Setting, Comment, CommentVote, Advertisement, ContactMessage


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ['title_line1', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_object', 'parent', 'rating', 'likes', 'dislikes', 'created_at', 'is_approved', 'is_testimonial']
    list_editable = ['is_approved', 'is_testimonial']
    list_filter = ['is_approved', 'content_type', 'is_testimonial']
    search_fields = ['name', 'text']
    list_select_related = ['parent']


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'vote']
    list_filter = ['vote']
    search_fields = ['user__phone']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'email', 'created_at', 'is_read']
    list_editable = ['is_read']
    list_filter = ['is_read']
    search_fields = ['name', 'subject', 'message', 'email', 'phone']


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_editable = ['is_active']
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget},
    }
