import json
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404
from music.models import Artist, Album, SubscriptionPlan, Song
from blog.models import BlogPost
from .models import HeroSlide, Setting, Comment, CommentVote, ContactMessage


def _serialize_song(song, rating_map=None):
    avg = 0
    if rating_map is not None:
        avg = rating_map.get(song.id, 0)
    else:
        from music.models import Rating
        from django.db.models import Avg
        avg = Rating.objects.filter(song=song).aggregate(Avg('score'))['score__avg'] or 0
    return {
        'id': song.id,
        'title': song.title,
        'artist': song.artist.name,
        'price': song.price,
        'cover': song.cover.url if song.cover else '',
        'preview_url': song.preview_url.url if song.preview_url else '',
        'duration': song.duration or '',
        'bpm': song.bpm or 0,
        'avg_rating': round(avg, 1),
        'views_count': song.views_count,
        'purchase_count': song.purchase_count,
    }


def _serialize_hero(slide):
    return {
        'id': slide.id,
        'sort_order': slide.sort_order,
        'badge_icon': slide.badge_icon,
        'badge_text': slide.badge_text,
        'title_line1': slide.title_line1,
        'title_line2': slide.title_line2,
        'title_line3': slide.title_line3 or '',
        'description': slide.description,
        'gradient_name': slide.gradient_name,
        'glow_color': slide.glow_color,
        'bg_image': slide.bg_image,
        'btn1_text': slide.btn1_text or '',
        'btn1_link': slide.btn1_link or '',
        'btn1_gradient': slide.btn1_gradient or '',
        'btn1_icon': slide.btn1_icon or '',
        'btn2_text': slide.btn2_text or '',
        'btn2_link': slide.btn2_link or '',
        'btn2_icon': slide.btn2_icon or '',
        'is_active': slide.is_active,
    }


class HomeView(TemplateView):
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Avg
        from music.models import Rating

        slides = HeroSlide.objects.filter(is_active=True).order_by('sort_order')
        context['hero_slides'] = slides

        context['testimonials'] = Comment.objects.filter(is_approved=True, is_testimonial=True).order_by('-created_at')

        page_num = self.request.GET.get('page', 1)
        try:
            page_num = int(page_num)
        except (ValueError, TypeError):
            page_num = 1
        paginator = Paginator(Song.objects.filter(is_published=True).order_by('-created_at'), 24)
        page_obj = paginator.get_page(page_num)
        context['page_obj'] = page_obj
        context['latest_songs'] = page_obj.object_list

        best = Song.objects.filter(is_published=True, is_best_seller=True)[:4]
        context['best_sellers'] = best

        pop = Song.objects.filter(is_published=True, is_popular=True)[:4]
        context['popular'] = pop

        context['artists'] = Artist.objects.annotate(sc=Count('songs')).filter(sc__gt=0).order_by('-sc')[:6]
        context['blog_posts'] = BlogPost.objects.filter(is_published=True).order_by('-date_published')[:3]
        context['albums'] = Album.objects.filter(is_published=True)[:2]
        context['subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True).order_by('price')

        all_song_ids = set()
        for s in page_obj.object_list:
            all_song_ids.add(s.id)
        for s in best:
            all_song_ids.add(s.id)
        for s in pop:
            all_song_ids.add(s.id)
        rating_qs = Rating.objects.filter(song_id__in=all_song_ids).values('song_id').annotate(avg=Avg('score'))
        rating_map = {r['song_id']: r['avg'] for r in rating_qs}

        purchased_song_ids = set()
        purchased_album_ids = set()
        has_subscription = False
        if self.request.user.is_authenticated:
            from music.utils import get_active_subscription
            from music.models import UserDownload
            # Songs downloaded via subscription are permanently accessible
            downloaded_ids = UserDownload.objects.filter(
                user=self.request.user, version='arranged'
            ).values_list('song_id', flat=True)
            purchased_song_ids.update(downloaded_ids)
            if get_active_subscription(self.request.user):
                has_subscription = True
            from cart.models import Order
            from music.models import Song as SongModel
            paid_orders = Order.objects.filter(user=self.request.user, status='paid')
            for o in paid_orders:
                for item in o.items:
                    if item.get('item_type') == 'song':
                        purchased_song_ids.add(item['item_id'])
                    elif item.get('item_type') == 'album':
                        purchased_album_ids.add(item['item_id'])
                        album_songs = SongModel.objects.filter(albums__id=item['item_id'])
                        purchased_song_ids.update(album_songs.values_list('id', flat=True))
        context['purchased_song_ids'] = purchased_song_ids
        context['purchased_album_ids'] = purchased_album_ids
        context['has_subscription'] = has_subscription
        context['purchased_song_ids_json'] = json.dumps(list(purchased_song_ids))
        context['has_subscription_json'] = 'true' if has_subscription else 'false'

        settings_dict = {s.key: s.value for s in Setting.objects.all()}

        context['hero_slides_json'] = json.dumps([_serialize_hero(s) for s in slides], ensure_ascii=False)
        context['site_config_json'] = json.dumps(settings_dict, ensure_ascii=False)

        for name, qs in [('latest_songs_json', [_serialize_song(s, rating_map) for s in page_obj.object_list]),
                          ('best_sellers_json', [_serialize_song(s, rating_map) for s in best]),
                          ('popular_json', [_serialize_song(s, rating_map) for s in pop]),
                           ('artists_json', [{'id': a.id, 'name': a.name, 'song_count': a.sc, 'image': a.image} for a in context['artists']]),
                          ('blog_posts_json', [{'id': p.id, 'title': p.title, 'excerpt': p.excerpt, 'image': p.image, 'date_str': p.date_published.isoformat(), 'category': p.category.name if p.category else ''} for p in context['blog_posts']]),
                          ('testimonials_json', [{'id': t.id, 'name': t.name, 'text': t.text, 'rating': t.rating} for t in context['testimonials']]),
                          ('albums_json', [{'id': a.id, 'title': a.title, 'description': a.description, 'cover': a.cover, 'price': a.price, 'song_ids': list(a.songs.values_list('id', flat=True))} for a in context['albums']]),
                          ('plans_json', [{'id': p.id, 'title': p.title, 'description': p.description, 'duration_days': p.duration_days, 'download_limit': p.download_limit, 'price': p.price} for p in context['subscription_plans']])]:
            context[name] = json.dumps(qs, ensure_ascii=False)

        return context


def search_autocomplete(request):
    q = request.GET.get('q', '').strip()
    results = {'songs': [], 'artists': [], 'albums': [], 'posts': []}

    if len(q) < 1:
        return JsonResponse(results)

    songs = Song.objects.filter(
        Q(title__icontains=q) |
        Q(artist__name__icontains=q),
        is_published=True
    ).select_related('artist').distinct()[:5]

    artists = Artist.objects.annotate(sc=Count('songs')).filter(
        Q(name__icontains=q),
        sc__gt=0
    ).distinct()[:3]

    albums = Album.objects.filter(
        Q(title__icontains=q),
        is_published=True
    ).distinct()[:3]

    posts = BlogPost.objects.filter(
        Q(title__icontains=q),
        is_published=True
    ).distinct()[:3]

    results['songs'] = [
        {'id': s.id, 'title': s.title, 'artist': s.artist.name, 'cover': s.cover, 'url': '/song/' + str(s.id) + '/'}
        for s in songs
    ]
    results['artists'] = [
        {'id': a.id, 'name': a.name, 'image': a.image, 'url': '/artist/' + a.slug + '/'}
        for a in artists
    ]
    results['albums'] = [
        {'id': a.id, 'title': a.title, 'cover': a.cover, 'url': '/album/' + a.slug + '/'}
        for a in albums
    ]
    results['posts'] = [
        {'id': p.id, 'title': p.title, 'url': '/blog/' + p.slug + '/'}
        for p in posts
    ]
    return JsonResponse(results)


class SearchView(TemplateView):
    template_name = 'main/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        context['query'] = q

        if not q:
            context['songs'] = []
            context['artists'] = []
            context['albums'] = []
            context['posts'] = []
            context['total_count'] = 0
            return context

        songs = Song.objects.filter(
            Q(title__icontains=q) |
            Q(artist__name__icontains=q) |
            Q(composer__icontains=q) |
            Q(lyricist__icontains=q),
            is_published=True
        ).select_related('artist').distinct()

        artists = Artist.objects.annotate(sc=Count('songs')).filter(
            Q(name__icontains=q),
            sc__gt=0
        ).distinct()

        albums = Album.objects.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q),
            is_published=True
        ).distinct()

        posts = BlogPost.objects.filter(
            Q(title__icontains=q) |
            Q(excerpt__icontains=q) |
            Q(content__icontains=q),
            is_published=True
        ).distinct()

        context['songs'] = songs
        context['artists'] = artists
        context['albums'] = albums
        context['posts'] = posts
        context['total_count'] = songs.count() + artists.count() + albums.count() + posts.count()
        return context


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from hashlib import sha256
import random
from .models import Comment


def captcha(request):
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    ops = [('+', a + b), ('-', a - b), ('×', a * b)]
    op, answer = random.choice(ops)
    question = f'{a} {op} {b} = ?'
    token = sha256(f'{a}:{op}:{b}:captcha_salt'.encode()).hexdigest()[:12]
    request.session['captcha_answer'] = token + sha256(str(answer).encode()).hexdigest()[:12]
    return JsonResponse({'question': question, 'token': token})


@csrf_exempt
@require_POST
def submit_comment(request):
    # Rate limiting: one comment per 30s per IP
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    key = f'comment_rate_{request.user.id if request.user.is_authenticated else ip}'
    last = cache.get(key)
    if last:
        return JsonResponse({'success': False, 'message': 'شما می‌توانید هر ۳۰ ثانیه یک نظر ارسال کنید'}, status=429)

    try:
        data = json.loads(request.body)
        ct_id = int(data.get('content_type'))
        obj_id = int(data.get('object_id'))
        name = data.get('name', '').strip()
        text = data.get('text', '').strip()
        rating = int(data.get('rating', 5))
        parent_id = data.get('parent_id')
        parent = Comment.objects.get(id=parent_id) if parent_id else None
        captcha_answer = str(data.get('captcha_answer', '')).strip()
        captcha_token = str(data.get('captcha_token', '')).strip()
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    # Verify captcha
    stored = request.session.pop('captcha_answer', '')
    expected = captcha_token + sha256(captcha_answer.encode()).hexdigest()[:12]
    if not stored or stored != expected:
        return JsonResponse({'success': False, 'message': 'پاسخ سوال امنیتی اشتباه است'}, status=400)

    if not name or not text:
        return JsonResponse({'success': False, 'message': 'نام و متن نظر الزامی است'}, status=400)

    if rating < 1 or rating > 5:
        rating = 5

    Comment.objects.create(
        content_type_id=ct_id, object_id=obj_id,
        name=name, text=text, rating=rating,
        user=request.user if request.user.is_authenticated else None,
        parent=parent,
    )

    cache.set(key, True, 30)

    # Notify admin in background
    from .notify_helper import notify_in_background
    notify_in_background(f'📝 نظر جدید از {name}\n{text[:200]}')

    return JsonResponse({'success': True, 'message': 'نظر شما ثبت شد'})


from django.shortcuts import render


@csrf_exempt
@require_POST
def vote_comment(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)
    try:
        data = json.loads(request.body)
        comment_id = int(data.get('comment_id'))
        vote = int(data.get('vote'))  # 1 or -1
    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)
    if vote not in (1, -1):
        return JsonResponse({'success': False, 'message': 'رأی نامعتبر'}, status=400)
    comment = get_object_or_404(Comment, id=comment_id)
    existing = CommentVote.objects.filter(user=request.user, comment=comment).first()
    if existing:
        if existing.vote == vote:
            existing.delete()
            if vote == 1:
                comment.likes = max(comment.likes - 1, 0)
            else:
                comment.dislikes = max(comment.dislikes - 1, 0)
            comment.save(update_fields=['likes', 'dislikes'])
            return JsonResponse({'success': True, 'action': 'removed', 'likes': comment.likes, 'dislikes': comment.dislikes})
        old_vote = existing.vote
        existing.vote = vote
        existing.save()
    else:
        CommentVote.objects.create(user=request.user, comment=comment, vote=vote)
        old_vote = 0
    if vote == 1:
        comment.likes += 1
        if old_vote == -1:
            comment.dislikes = max(comment.dislikes - 1, 0)
    else:
        comment.dislikes += 1
        if old_vote == 1:
            comment.likes = max(comment.likes - 1, 0)
    comment.save(update_fields=['likes', 'dislikes'])
    return JsonResponse({'success': True, 'action': 'voted', 'likes': comment.likes, 'dislikes': comment.dislikes})


class AboutView(TemplateView):
    template_name = 'main/about.html'


class ContactView(TemplateView):
    template_name = 'main/contact.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not message:
            return render(request, 'main/contact.html', {'error': 'نام و پیام الزامی است'})

        # Rate limiting: max 2 messages per 10 minutes per IP
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        rl_key = f'contact_rate_{ip}'
        from django.core.cache import cache
        count = cache.get(rl_key, 0)
        if count >= 2:
            return render(request, 'main/contact.html', {'error': 'شما می‌توانید هر ۱۰ دقیقه حداکثر ۲ پیام ارسال کنید'})
        cache.set(rl_key, count + 1, 600)  # 10 minutes

        ContactMessage.objects.create(name=name, email=email, phone=phone, subject=subject, message=message)

        # Notify admin in background
        from .notify_helper import notify_in_background
        notify_in_background(f'📩 پیام جدید از {name}\n{subject or "بدون موضوع"}\n{message[:300]}')

        return render(request, 'main/contact.html', {'success': 'پیام شما با موفقیت ارسال شد'})


class TermsView(TemplateView):
    template_name = 'main/terms.html'


class PrivacyView(TemplateView):
    template_name = 'main/privacy.html'


def manifest(request):
    settings_dict = {s.key: s.value for s in Setting.objects.all()}
    name = settings_dict.get('logo_text', 'نواهای بیکلام')
    return JsonResponse({
        'name': name,
        'short_name': name,
        'description': settings_dict.get('site_description', ''),
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#0f172a',
        'theme_color': '#7c3aed',
        'orientation': 'portrait-primary',
        'lang': 'fa',
        'dir': 'rtl',
        'icons': [
            {'src': '/static/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/static/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
            {'src': '/static/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    })


def offline_view(request):
    return render(request, 'main/offline.html')
