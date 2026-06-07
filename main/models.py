from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class HeroSlide(models.Model):
    title_line1 = models.CharField('خط اول عنوان', max_length=200)
    title_line2 = models.CharField('خط دوم عنوان', max_length=200)
    title_line3 = models.CharField('خط سوم عنوان', max_length=200, blank=True)
    description = models.TextField('توضیحات')
    badge_icon = models.CharField('آیکون نشان', max_length=50, default='music')
    badge_text = models.CharField('متن نشان', max_length=200)
    gradient_name = models.CharField('گرادینت', max_length=200, default='from-purple-400 via-indigo-400 to-cyan-400')
    glow_color = models.CharField('رنگ درخشش', max_length=100, default='bg-purple-600/20')
    bg_image = models.URLField('تصویر پس‌زمینه', blank=True)
    bg_image_file = models.ImageField('فایل تصویر پس‌زمینه', upload_to='hero/', blank=True)
    btn1_text = models.CharField('متن دکمه اول', max_length=100, blank=True)
    btn1_link = models.CharField('لینک دکمه اول', max_length=200, blank=True)
    btn1_gradient = models.CharField('گرادینت دکمه اول', max_length=200, blank=True)
    btn1_icon = models.CharField('آیکون دکمه اول', max_length=50, blank=True)
    btn2_text = models.CharField('متن دکمه دوم', max_length=100, blank=True, null=True)
    btn2_link = models.CharField('لینک دکمه دوم', max_length=200, blank=True, null=True)
    btn2_icon = models.CharField('آیکون دکمه دوم', max_length=50, blank=True, null=True)
    sort_order = models.PositiveIntegerField('ترتیب', default=0)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'اسلاید هدر'
        verbose_name_plural = 'اسلایدهای هدر'
        ordering = ['sort_order']

    def __str__(self):
        return self.title_line1


class Setting(models.Model):
    key = models.CharField('کلید', max_length=100, unique=True)
    value = models.TextField('مقدار', blank=True)

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return self.key


class Comment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='نوع محتوا')
    object_id = models.PositiveIntegerField('شناسه محتوا')
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='کاربر')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='پاسخ به')
    name = models.CharField('نام', max_length=100)
    text = models.TextField('متن نظر')
    rating = models.PositiveSmallIntegerField('امتیاز', default=0, help_text='از ۱ تا ۵')
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)
    is_approved = models.BooleanField('تایید شده', default=False)
    is_testimonial = models.BooleanField('نمایش در صفحه اصلی', default=False, help_text='با فعال‌سازی در بخش نظرات صفحه اصلی نمایش داده می‌شود')
    likes = models.PositiveIntegerField('پسندها', default=0)
    dislikes = models.PositiveIntegerField('نپسندها', default=0)

    class Meta:
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['-created_at']

    def __str__(self):
        try:
            obj = self.content_object
            if obj is None:
                return self.name
            return f'{self.name} - {obj}'
        except Exception:
            return self.name


class CommentVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='کاربر')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='votes', verbose_name='نظر')
    vote = models.SmallIntegerField('رأی', choices=[(1, 'پسند'), (-1, 'نپسند')])

    class Meta:
        verbose_name = 'رأی به نظر'
        verbose_name_plural = 'رأی‌های نظرات'
        unique_together = ['user', 'comment']


class ContactMessage(models.Model):
    name = models.CharField('نام', max_length=100)
    email = models.EmailField('ایمیل', blank=True)
    phone = models.CharField('شماره تماس', max_length=20, blank=True)
    subject = models.CharField('موضوع', max_length=200, blank=True)
    message = models.TextField('پیام')
    is_read = models.BooleanField('خوانده شده', default=False)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'پیام تماس'
        verbose_name_plural = 'پیام‌های تماس'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.subject or "بدون موضوع"}'


class Advertisement(models.Model):
    title = models.CharField('عنوان', max_length=200)
    description = models.TextField('توضیحات', blank=True)
    link = models.URLField('لینک', blank=True, help_text='در صورت وارد کردن لینک، کاربر با کلیک به آن هدایت می‌شود')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'تبلیغ'
        verbose_name_plural = 'تبلیغات'

    def __str__(self):
        return self.title
