import json
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from .utils import create_and_send_otp, verify_otp, get_or_create_user
from .models import User
from cart.models import Order


def _rate_limit_key(phone, ip):
    return f'otp_rate_{phone}_{ip}'


@csrf_exempt
@require_POST
def send_otp(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    if not phone or len(phone) < 10:
        return JsonResponse({'success': False, 'message': 'شماره موبایل نامعتبر است'}, status=400)

    ip = request.META.get('REMOTE_ADDR', '')
    rl_key = _rate_limit_key(phone, ip)
    count = cache.get(rl_key, 0)
    if count >= 3:
        return JsonResponse({'success': False, 'message': 'درخواست بیش از حد. لطفاً ۱۲۰ ثانیه صبر کنید.'}, status=429)
    cache.set(rl_key, count + 1, 120)

    code, sent = create_and_send_otp(phone)
    if sent:
        return JsonResponse({'success': True, 'message': 'کد تایید ارسال شد'})
    else:
        return JsonResponse({'success': False, 'message': 'خطا در ارسال پیامک. لطفاً بعداً تلاش کنید، فیلتر شکن خود را خاموش کنید.'}, status=503)


@csrf_exempt
@require_POST
def verify_otp_view(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    if not verify_otp(phone, code):
        return JsonResponse({'success': False, 'message': 'کد نامعتبر یا منقضی شده'}, status=400)

    user, created = get_or_create_user(phone)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({
        'success': True,
        'message': 'ورود موفق',
        'is_new': created,
        'user': {
            'phone': user.phone,
            'name': user.get_full_name() or user.phone,
        }
    })


@csrf_exempt
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({'success': True, 'message': 'خروج موفق'})


@login_required
def profile_view(request):
    error = None
    success = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email and User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            error = 'این ایمیل قبلاً ثبت شده است'
        else:
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = email
            request.user.save()
            success = 'اطلاعات با موفقیت به‌روز شد'

    orders = Order.objects.filter(user=request.user)[:10]
    from music.models import Song, Album, UserDownload, WishlistItem
    from music.utils import get_active_subscription
    paid_orders = Order.objects.filter(user=request.user, status='paid')
    song_ids = set()
    album_ids = set()
    for o in paid_orders:
        for item in o.items:
            if item.get('item_type') == 'song':
                song_ids.add(item['item_id'])
            elif item.get('item_type') == 'album':
                album_ids.add(item['item_id'])
    # Also include subscription-downloaded songs
    downloaded_ids = UserDownload.objects.filter(
        user=request.user, version='arranged'
    ).values_list('song_id', flat=True)
    song_ids.update(downloaded_ids)
    purchased_songs = Song.objects.filter(id__in=song_ids, is_published=True)
    purchased_albums = Album.objects.filter(id__in=album_ids, is_published=True)
    active_subscription = get_active_subscription(request.user)
    from music.utils import get_last_subscription
    last_sub, sub_status = get_last_subscription(request.user)

    pending_orders = Order.objects.filter(user=request.user, status='pending')
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('song__artist')[:20]

    return render(request, 'accounts/profile.html', {
        'orders': orders,
        'purchased_songs': purchased_songs,
        'purchased_albums': purchased_albums,
        'active_subscription': active_subscription,
        'last_subscription': last_sub,
        'subscription_status': sub_status,
        'pending_orders': pending_orders,
        'wishlist_items': wishlist_items,
        'error': error,
        'success': success,
    })


@csrf_exempt
def get_user_info(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False})
    return JsonResponse({
        'authenticated': True,
        'user': {
            'phone': request.user.phone,
            'name': request.user.get_full_name() or request.user.phone,
        }
    })
