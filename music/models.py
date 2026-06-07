from django.db import models
from django.utils.text import slugify
from django.conf import settings
from ckeditor.fields import RichTextField


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings', verbose_name='کاربر')
    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='ratings', verbose_name='آهنگ')
    score = models.PositiveSmallIntegerField('امتیاز')
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'امتیاز'
        verbose_name_plural = 'امتیازها'
        unique_together = ['user', 'song']

    def __str__(self):
        return f'{self.user.phone} - {self.song.title}: {self.score}'


class Artist(models.Model):
    name = models.CharField('نام', max_length=200)
    slug = models.SlugField('اسلاگ', unique=True, blank=True, allow_unicode=True)
    image = models.URLField('تصویر', blank=True)
    image_file = models.ImageField('فایل تصویر', upload_to='artists/', blank=True)
    bio = RichTextField('بیوگرافی', blank=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'هنرمند'
        verbose_name_plural = 'هنرمندان'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image_file and self.image_file.name:
            self.image_file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class Song(models.Model):
    title = models.CharField('عنوان', max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='songs', verbose_name='هنرمند')
    price = models.PositiveIntegerField('قیمت (تومان)')
    cover = models.FileField('تصویر', upload_to='songs/covers/', blank=True)
    preview_url = models.FileField('فایل دمو', upload_to='songs/demos/', blank=True, help_text='دموی ۱ دقیقه‌ای - رایگان برای همه')
    original_audio = models.FileField('فایل آهنگ اصلی', upload_to='songs/audio_original/', blank=True)
    arranged_audio = models.FileField('فایل تنظیم جدید', upload_to='songs/arranged/', blank=True, help_text='خروجی تفکیک سازها - فقط برای خریداران')
    description = RichTextField('توضیحات', blank=True, help_text='توضیح کامل درباره آهنگ (برای SEO)')
    lyrics = models.TextField('متن آهنگ', blank=True, help_text='متن کامل ترانه')
    duration = models.CharField('مدت زمان', max_length=10, blank=True, help_text='مثلاً 3:45')
    composer = models.CharField('آهنگساز', max_length=200, blank=True)
    lyricist = models.CharField('ترانه‌سرا', max_length=200, blank=True)
    bpm = models.PositiveSmallIntegerField('BPM', blank=True, null=True)
    musical_key = models.CharField('گام', max_length=50, blank=True, help_text='مثلاً C major, A minor')
    is_published = models.BooleanField('منتشر شده', default=True)
    is_best_seller = models.BooleanField('پرفروش', default=False)
    is_popular = models.BooleanField('پرطرفدار', default=False)
    views_count = models.PositiveIntegerField('تعداد بازدید', default=0)
    purchase_count = models.PositiveIntegerField('تعداد خرید', default=0)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'آهنگ'
        verbose_name_plural = 'آهنگ‌ها'
        ordering = ['-created_at']

    def delete(self, *args, **kwargs):
        for f in (self.cover, self.preview_url, self.original_audio, self.arranged_audio):
            if f and f.name:
                f.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.title} - {self.artist.name}'


class Album(models.Model):
    title = models.CharField('عنوان', max_length=200)
    slug = models.SlugField('اسلاگ', unique=True, blank=True, allow_unicode=True)
    description = models.TextField('توضیحات', blank=True)
    cover = models.URLField('تصویر', blank=True)
    cover_file = models.ImageField('فایل تصویر', upload_to='albums/', blank=True)
    price = models.PositiveIntegerField('قیمت (تومان)')
    songs = models.ManyToManyField(Song, related_name='albums', verbose_name='آهنگ‌ها', blank=True)
    is_published = models.BooleanField('منتشر شده', default=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'آلبوم'
        verbose_name_plural = 'آلبوم‌ها'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.cover_file and self.cover_file.name:
            self.cover_file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title


class SubscriptionPlan(models.Model):
    title = models.CharField('عنوان', max_length=200)
    description = models.TextField('توضیحات')
    duration_days = models.PositiveIntegerField('مدت (روز)')
    download_limit = models.PositiveIntegerField('محدودیت دانلود')
    price = models.PositiveIntegerField('قیمت (تومان)')
    icon = models.CharField('آیکون', max_length=50, default='zap')
    gradient = models.CharField('گرادینت', max_length=200, default='from-purple-600 to-indigo-600')
    is_active = models.BooleanField('فعال', default=True)
    is_popular = models.BooleanField('محبوب', default=False)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'طرح اشتراک'
        verbose_name_plural = 'طرح‌های اشتراک'
        ordering = ['price']

    def __str__(self):
        return self.title


class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', verbose_name='کاربر')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='user_subscriptions', verbose_name='طرح')
    start_date = models.DateTimeField('تاریخ شروع', auto_now_add=True)
    end_date = models.DateTimeField('تاریخ پایان')
    remaining_downloads = models.PositiveIntegerField('دانلود باقی‌مانده', default=0)
    is_active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'اشتراک کاربر'
        verbose_name_plural = 'اشتراک‌های کاربران'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.user.phone} - {self.plan.title}'


class UserDownload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='downloads', verbose_name='کاربر')
    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='downloads', verbose_name='آهنگ')
    version = models.CharField('نسخه', max_length=20, choices=[('demo', 'دمو'), ('original', 'اصلی'), ('arranged', 'تنظیم جدید')])
    downloaded_at = models.DateTimeField('زمان دانلود', auto_now_add=True)

    class Meta:
        verbose_name = 'دانلود کاربر'
        verbose_name_plural = 'دانلودهای کاربران'
        ordering = ['-downloaded_at']

    def __str__(self):
        return f'{self.user.phone} - {self.song.title}'


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist', verbose_name='کاربر')
    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='wishlisted_by', verbose_name='آهنگ')
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'آهنگ موردعلاقه'
        verbose_name_plural = 'آهنگ‌های موردعلاقه'
        unique_together = ['user', 'song']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.phone} - {self.song.title}'


class ScrapedSong(models.Model):
    title = models.CharField('عنوان', max_length=200)
    artist_name = models.CharField('نام هنرمند', max_length=200)
    cover_url = models.URLField('تصویر', blank=True)
    mp3_url = models.URLField('لینک دانلود', blank=True)
    source_url = models.URLField('لینک مبدأ', unique=True, help_text='آدرس صفحه جزئیات آهنگ')
    slug = models.CharField('اسلاگ', max_length=200, blank=True)
    date_str = models.CharField('تاریخ انتشار', max_length=100, blank=True)
    download_count = models.PositiveIntegerField('تعداد دانلود', default=0)
    is_imported = models.BooleanField('وارد شده به آهنگ‌های اصلی', default=False)
    separate_instruments = models.BooleanField('تفکیک سازها', default=False, help_text='فعالسازی تفکیک وکال و ساز با MDX-Net و ساخت آهنگ جدید')
    separation_status = models.CharField(
        'وضعیت تفکیک', max_length=20,
        choices=[
            ('pending', 'در انتظار'),
            ('processing', 'در حال پردازش'),
            ('done', 'انجام شده'),
            ('failed', 'خطا'),
        ],
        default='pending',
    )
    error_message = models.TextField('پیام خطا', blank=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'آهنگ اسکرپ شده'
        verbose_name_plural = 'آهنگ‌های اسکرپ شده'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.artist_name}'
