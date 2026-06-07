import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import F
from .models import Cart, Order, Coupon
import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Cart, CartItem, Order, Coupon


def _clear_cart(user):
    cart = Cart.objects.filter(user=user).first()
    if cart:
        cart.items.all().delete()


def _activate_subscriptions(order):
    from music.models import SubscriptionPlan, UserSubscription
    for item in order.items:
        if item.get('item_type') == 'subscription':
            plan = SubscriptionPlan.objects.filter(id=item['item_id']).first()
            if plan:
                now = timezone.now()
                UserSubscription.objects.create(
                    user=order.user,
                    plan=plan,
                    start_date=now,
                    end_date=now + timedelta(days=plan.duration_days),
                    remaining_downloads=plan.download_limit,
                )


@csrf_exempt
@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)

    try:
        data = json.loads(request.body)
        item_type = data.get('item_type')
        item_id = data.get('item_id')
        title = data.get('title', '')
        artist = data.get('artist', '')
        cover = data.get('cover', '')
        price = data.get('price', 0)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    existing = cart.items.filter(item_type=item_type, item_id=item_id).first()

    if existing:
        existing.quantity += 1
        existing.save()
    else:
        CartItem.objects.create(
            cart=cart, item_type=item_type, item_id=item_id,
            title=title, artist=artist, cover=cover, price=price
        )

    return JsonResponse({'success': True, 'message': 'به سبد خرید اضافه شد'})


@csrf_exempt
@require_POST
def update_cart_item(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)

    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        action = data.get('action')  # 'increase', 'decrease', 'remove'
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return JsonResponse({'success': False, 'message': 'سبد خرید خالی است'})

    item = cart.items.filter(id=item_id).first()
    if not item:
        return JsonResponse({'success': False, 'message': 'آیتم یافت نشد'})

    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()
    elif action == 'remove':
        item.delete()

    return JsonResponse({'success': True, 'cart_total': cart.total, 'cart_count': cart.total_items})


def get_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False, 'items': [], 'total': 0, 'count': 0})

    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return JsonResponse({'items': [], 'total': 0, 'count': 0})

    items = [{
        'id': item.id,
        'item_type': item.item_type,
        'item_id': item.item_id,
        'title': item.title,
        'artist': item.artist,
        'cover': item.cover,
        'price': item.price,
        'quantity': item.quantity,
        'total': item.total_price,
    } for item in cart.items.all()]

    return JsonResponse({
        'authenticated': True,
        'items': items,
        'total': cart.total,
        'count': cart.total_items,
    })


@csrf_exempt
@require_POST
def checkout(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.total_items == 0:
        return JsonResponse({'success': False, 'message': 'سبد خرید خالی است'})

    items_data = [{
        'item_type': item.item_type,
        'item_id': item.item_id,
        'title': item.title,
        'artist': item.artist,
        'price': item.price,
        'quantity': item.quantity,
    } for item in cart.items.all()]

    coupon_id = request.session.pop('coupon_id', None)
    coupon_code = request.session.pop('coupon_code', '')
    coupon_discount = request.session.pop('coupon_discount', 0)
    final_total = max(0, cart.total - int(coupon_discount))

    order = Order.objects.create(
        user=request.user,
        items=items_data,
        total=final_total,
    )

    if coupon_id:
        order.coupon_code = coupon_code
        order.coupon_discount = int(coupon_discount)
        order.save()
        Coupon.objects.filter(id=coupon_id).update(used_count=F('used_count') + 1)

    merchant_id = settings.ZARINPAL_MERCHANT_ID
    sandbox = settings.ZARINPAL_SANDBOX
    amount = final_total * 10  # Toman → Rial (Zarinpal expects Rial)
    callback_url = request.build_absolute_uri('/cart/verify/')
    description = f'سفارش #{order.id} - {request.user.phone}'

    if not merchant_id:
        merchant_id = '00000000-0000-0000-0000-000000000000'

    api_url = settings.ZARINPAL_REQUEST_URL or f'https://{"sandbox" if sandbox else "api"}.zarinpal.com/pg/v4/payment/request.json'

    payload = {
        'merchant_id': merchant_id,
        'amount': amount,
        'callback_url': callback_url,
        'description': description,
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        data = resp.json()
        authority = data.get('data', {}).get('authority')
        if authority:
            order.authority = authority
            order.save()
            pay_url = f'{settings.ZARINPAL_STARTPAY_URL or "https://www.zarinpal.com/pg/StartPay/"}{authority}'
            return JsonResponse({'success': True, 'url': pay_url})
    except Exception:
        pass

    # Simulation mode — Zarinpal unreachable, redirect to local mock payment
    fake_authority = 'S' + str(order.id).zfill(9)
    order.authority = fake_authority
    order.save()

    sim_url = request.build_absolute_uri(f'/cart/verify/?Authority={fake_authority}&Status=OK')
    return JsonResponse({'success': True, 'url': sim_url})


def _notify_purchase(order):
    items_desc = []
    for item in order.items:
        if item.get('item_type') == 'subscription':
            items_desc.append(f'📦 اشتراک: {item.get("title", "")}')
        elif item.get('item_type') == 'song':
            items_desc.append(f'🎵 آهنگ: {item.get("title", "")}')
        elif item.get('item_type') == 'album':
            items_desc.append(f'💿 آلبوم: {item.get("title", "")}')
    items_str = ' '.join(items_desc)
    text = f'\U0001f6d2 خرید جدید!\n\nکاربر: {order.user.phone}\nمبلغ: {order.total:,} تومان\n{items_str}'
    from main.notify_helper import notify_in_background
    notify_in_background(text)


def _increment_song_purchases(order):
    from music.models import Song
    for item in order.items:
        if item.get('item_type') == 'song':
            Song.objects.filter(pk=item['item_id']).update(purchase_count=F('purchase_count') + 1)
        elif item.get('item_type') == 'album':
            Song.objects.filter(albums__pk=item['item_id']).update(purchase_count=F('purchase_count') + 1)


def payment_callback(request):
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    if status != 'OK':
        order = Order.objects.filter(authority=authority).first()
        if order:
            order.status = 'cancelled'
            order.save()
        return render(request, 'cart/payment_result.html', {
            'success': False,
            'message': 'پرداخت توسط کاربر لغو شد',
        })

    order = Order.objects.filter(authority=authority).first()
    if not order:
        return render(request, 'cart/payment_result.html', {
            'success': False,
            'message': 'سفارش یافت نشد',
        })

    # Simulation mode — authority starting with S is fake/simulated
    if authority.startswith('S'):
        order.status = 'paid'
        order.ref_id = f'SIM-{order.id}'
        order.save()
        _activate_subscriptions(order)
        _increment_song_purchases(order)
        _notify_purchase(order)
        _clear_cart(order.user)
        return render(request, 'cart/payment_result.html', {
            'success': True,
            'order': order,
            'ref_id': f'SIM-{order.id}',
        })

    merchant_id = settings.ZARINPAL_MERCHANT_ID
    sandbox = settings.ZARINPAL_SANDBOX

    if not merchant_id:
        merchant_id = '00000000-0000-0000-0000-000000000000'

    api_url = settings.ZARINPAL_VERIFY_URL or f'https://{"sandbox" if sandbox else "api"}.zarinpal.com/pg/v4/payment/verify.json'

    payload = {
        'merchant_id': merchant_id,
        'amount': order.total * 10,  # Toman → Rial
        'authority': authority,
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        data = resp.json()
        code = data.get('data', {}).get('code')
        if code == 100 or code == 101:
            order.status = 'paid'
            order.ref_id = str(data.get('data', {}).get('ref_id', ''))
            order.save()
            _activate_subscriptions(order)
            _increment_song_purchases(order)
            _notify_purchase(order)
            _clear_cart(order.user)
            return render(request, 'cart/payment_result.html', {
                'success': True,
                'order': order,
                'ref_id': str(data.get('data', {}).get('ref_id', '')),
            })
    except Exception:
        pass

    order.status = 'cancelled'
    order.save()
    return render(request, 'cart/payment_result.html', {
        'success': False,
        'order': order,
        'message': 'پرداخت تایید نشد',
    })


@csrf_exempt
@require_POST
def retry_verification(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً وارد شوید'}, status=401)

    order_id = request.POST.get('order_id')
    if not order_id:
        return JsonResponse({'success': False, 'message': 'شناسه سفارش یافت نشد'})

    order = Order.objects.filter(pk=order_id, user=request.user).exclude(status='paid').first()
    if not order:
        return JsonResponse({'success': False, 'message': 'سفارش یافت نشد یا قبلاً تأیید شده است'})

    authority = order.authority
    if not authority:
        order.delete()
        return JsonResponse({'success': False, 'message': 'این سفارش معتبر نیست'})

    # Simulation / fake authority — redirect back to callback to complete
    if authority.startswith('S'):
        callback_url = request.build_absolute_uri(f'/cart/verify/?Authority={authority}&Status=OK')
        return JsonResponse({'success': True, 'url': callback_url})

    merchant_id = settings.ZARINPAL_MERCHANT_ID or '00000000-0000-0000-0000-000000000000'
    sandbox = settings.ZARINPAL_SANDBOX
    api_url = settings.ZARINPAL_VERIFY_URL or f'https://{"sandbox" if sandbox else "api"}.zarinpal.com/pg/v4/payment/verify.json'

    payload = {
        'merchant_id': merchant_id,
        'amount': order.total * 10,  # Toman → Rial
        'authority': authority,
    }

    try:
        resp = requests.post(api_url, json=payload, timeout=10)
        data = resp.json()
        code = data.get('data', {}).get('code')
        if code == 100 or code == 101:
            order.status = 'paid'
            order.ref_id = str(data.get('data', {}).get('ref_id', ''))
            order.save()
            _activate_subscriptions(order)
            _increment_song_purchases(order)
            _notify_purchase(order)
            _clear_cart(order.user)
            return JsonResponse({'success': True, 'order_id': order.id, 'ref_id': order.ref_id})
    except Exception:
        return JsonResponse({'success': False, 'message': 'خطا در ارتباط با درگاه پرداخت. بعداً تلاش کنید.'})

    return JsonResponse({'success': False, 'message': 'پرداخت قابل تأیید نیست. لطفاً با پشتیبانی تماس بگیرید.'})


@login_required
def invoice_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'cart/invoice.html', {'order': order})


@csrf_exempt
@require_POST
def apply_coupon(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)

    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    if not code:
        return JsonResponse({'success': False, 'message': 'کد تخفیف را وارد کنید'})

    coupon = Coupon.objects.filter(code__iexact=code).first()
    if not coupon:
        return JsonResponse({'success': False, 'message': 'کد تخفیف معتبر نیست'})

    if not coupon.is_valid:
        return JsonResponse({'success': False, 'message': 'این کد تخفیف منقضی شده یا استفاده شده است'})

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.total_items == 0:
        return JsonResponse({'success': False, 'message': 'سبد خرید خالی است'})

    if coupon.min_order_amount > 0 and cart.total < coupon.min_order_amount:
        return JsonResponse({
            'success': False,
            'message': f'حداقل مبلغ سفارش برای این کد {coupon.min_order_amount:,} تومان است'
        })

    discount = coupon.calculate_discount(cart.total)
    final_total = cart.total - discount
    request.session['coupon_id'] = coupon.id
    request.session['coupon_code'] = coupon.code
    request.session['coupon_discount'] = discount

    return JsonResponse({
        'success': True,
        'discount': discount,
        'final_total': final_total,
        'code': coupon.code,
        'message': f'کد تخفیف {coupon.code} اعمال شد'
    })


@csrf_exempt
@require_POST
def remove_coupon(request):
    request.session.pop('coupon_id', None)
    request.session.pop('coupon_code', None)
    request.session.pop('coupon_discount', None)
    return JsonResponse({'success': True, 'message': 'کد تخفیف حذف شد'})
