from django.db import models
from django.conf import settings
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percent', 'درصد'),
        ('fixed', 'مبلغ ثابت'),
    ]
    code = models.CharField('کد تخفیف', max_length=50, unique=True)
    discount_type = models.CharField('نوع تخفیف', max_length=10, choices=DISCOUNT_TYPES, default='percent')
    value = models.PositiveIntegerField('مقدار تخفیف', help_text='درصد (۱-۱۰۰) یا مبلغ ثابت به تومان')
    max_uses = models.PositiveIntegerField('حداکثر استفاده', default=0, help_text='۰ = نامحدود')
    used_count = models.PositiveIntegerField('تعداد استفاده', default=0)
    min_order_amount = models.PositiveIntegerField('حداقل مبلغ سفارش', default=0, help_text='۰ = بدون حداقل')
    is_active = models.BooleanField('فعال', default=True)
    expires_at = models.DateTimeField('تاریخ انقضا', blank=True, null=True)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def calculate_discount(self, total):
        if self.discount_type == 'percent':
            return int(total * self.value / 100)
        return min(self.value, total)


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart', verbose_name='کاربر'
    )
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)
    updated_at = models.DateTimeField('بروزرسانی', auto_now=True)

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    def __str__(self):
        return f'سبد خرید {self.user.phone}'

    @property
    def total(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    ITEM_TYPES = [
        ('song', 'آهنگ'),
        ('album', 'آلبوم'),
        ('subscription', 'اشتراک'),
    ]

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='سبد خرید')
    item_type = models.CharField('نوع', max_length=20, choices=ITEM_TYPES)
    item_id = models.PositiveIntegerField('شناسه آیتم')
    title = models.CharField('عنوان', max_length=200, blank=True)
    artist = models.CharField('هنرمند', max_length=200, blank=True)
    cover = models.URLField('تصویر', blank=True)
    price = models.PositiveIntegerField('قیمت واحد')
    quantity = models.PositiveIntegerField('تعداد', default=1)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)

    class Meta:
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'

    def __str__(self):
        return f'{self.title} x{self.quantity}'

    @property
    def total_price(self):
        return self.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('cancelled', 'لغو شده'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='orders', verbose_name='کاربر'
    )
    items = models.JSONField('آیتم‌ها', default=list)
    total = models.PositiveIntegerField('جمع کل')
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='pending')
    authority = models.CharField('کد مرجع زرین‌پال', max_length=100, blank=True, default='')
    ref_id = models.CharField('شناسه تراکنش', max_length=100, blank=True, default='')
    coupon_code = models.CharField('کد تخفیف', max_length=50, blank=True, default='')
    coupon_discount = models.PositiveIntegerField('تخفیف', default=0)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)
    paid_at = models.DateTimeField('تاریخ پرداخت', blank=True, null=True)

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']

    @property
    def is_simulated(self):
        return self.authority.startswith('S')

    def __str__(self):
        return f'سفارش #{self.id} - {self.user.phone}'
