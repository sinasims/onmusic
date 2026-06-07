from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class Category(models.Model):
    name = models.CharField('نام', max_length=100)
    slug = models.SlugField('اسلاگ', unique=True, blank=True, allow_unicode=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField('عنوان', max_length=200)
    slug = models.SlugField('اسلاگ', unique=True, blank=True, allow_unicode=True)
    excerpt = models.TextField('خلاصه', blank=True)
    content = RichTextField('محتوا', blank=True)
    image = models.URLField('تصویر', blank=True)
    image_file = models.ImageField('فایل تصویر', upload_to='blog/', blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posts', verbose_name='دسته‌بندی'
    )
    date_published = models.DateField('تاریخ انتشار')
    reading_time = models.PositiveSmallIntegerField('زمان مطالعه (دقیقه)', default=0, help_text='در صورت خالی گذاشتن، خودکار محاسبه می‌شود')
    is_published = models.BooleanField('منتشر شده', default=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'پست وبلاگ'
        verbose_name_plural = 'پست‌های وبلاگ'
        ordering = ['-date_published']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if not self.reading_time and self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, round(word_count / 200))
        elif not self.reading_time:
            self.reading_time = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image_file and self.image_file.name:
            self.image_file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title
