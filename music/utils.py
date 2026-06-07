from django.utils import timezone


def get_active_subscription(user):
    from .models import UserSubscription
    if not user or not user.is_authenticated:
        return None
    now = timezone.now()
    sub = UserSubscription.objects.filter(
        user=user, is_active=True, end_date__gt=now
    ).select_related('plan').first()
    if sub and sub.remaining_downloads <= 0:
        sub.is_active = False
        sub.save()
        return None
    return sub


def get_last_subscription(user):
    from .models import UserSubscription
    if not user or not user.is_authenticated:
        return None, None
    sub = UserSubscription.objects.filter(
        user=user
    ).select_related('plan').order_by('-start_date').first()
    if not sub:
        return None, None
    now = timezone.now()
    if sub.end_date <= now:
        return sub, 'expired'
    if sub.remaining_downloads <= 0:
        return sub, 'downloads_exhausted'
    if not sub.is_active:
        return sub, 'deactivated'
    return sub, 'active'
