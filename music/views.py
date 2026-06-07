from django.views.generic import DetailView, ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, F, Prefetch, Count
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse
import json
from main.models import Comment
from cart.models import Order
from .models import Song, Album, Artist, SubscriptionPlan, Rating, UserDownload, WishlistItem
from .utils import get_active_subscription


class SongListView(ListView):
    model = Song
    template_name = 'music/song_list.html'
    context_object_name = 'songs'
    paginate_by = 12

    def get_queryset(self):
        return Song.objects.filter(is_published=True).select_related('artist').order_by('-created_at')

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('ajax'):
            html = render_to_string('music/_song_items.html', context, self.request)
            return JsonResponse({'html': html, 'has_next': context['page_obj'].has_next()})
        return super().render_to_response(context, **response_kwargs)


class AlbumListView(ListView):
    model = Album
    template_name = 'music/album_list.html'
    context_object_name = 'albums'
    paginate_by = 12

    def get_queryset(self):
        return Album.objects.filter(is_published=True).order_by('-created_at')

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('ajax'):
            html = render_to_string('music/_album_items.html', context, self.request)
            return JsonResponse({'html': html, 'has_next': context['page_obj'].has_next()})
        return super().render_to_response(context, **response_kwargs)


class ArtistListView(ListView):
    model = Artist
    template_name = 'music/artist_list.html'
    context_object_name = 'artists'
    paginate_by = 12

    def get_queryset(self):
        return Artist.objects.annotate(sc=Count('songs')).filter(sc__gt=0).order_by('-sc')

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('ajax'):
            html = render_to_string('music/_artist_items.html', context, self.request)
            return JsonResponse({'html': html, 'has_next': context['page_obj'].has_next()})
        return super().render_to_response(context, **response_kwargs)


class SongDetailView(DetailView):
    model = Song
    template_name = 'music/song_detail.html'
    context_object_name = 'song'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        Song.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song = self.object

        has_purchased = False
        is_directly_purchased = False
        if self.request.user.is_authenticated:
            # Check individual purchase or album purchase
            for o in Order.objects.filter(user=self.request.user, status='paid'):
                for item in o.items:
                    if item.get('item_type') == 'song' and item.get('item_id') == song.id:
                        has_purchased = True
                        is_directly_purchased = True
                        break
                    if item.get('item_type') == 'album':
                        if Song.objects.filter(id=song.id, albums__id=item['item_id']).exists():
                            has_purchased = True
                            is_directly_purchased = True
                            break
                if has_purchased:
                    break
            # Check if downloaded via subscription before (permanent access)
            if not has_purchased:
                if UserDownload.objects.filter(user=self.request.user, song=song, version='arranged').exists():
                    has_purchased = True
                    is_directly_purchased = True
            # Active subscription gives access but not "purchased" status
            if not has_purchased and get_active_subscription(self.request.user):
                has_purchased = True
        context['has_purchased'] = has_purchased
        context['is_directly_purchased'] = is_directly_purchased
        context['has_subscription'] = bool(get_active_subscription(self.request.user)) if self.request.user.is_authenticated else False
        context['purchased_song_ids_json'] = '[]'
        if self.request.user.is_authenticated:
            downloaded_ids = list(UserDownload.objects.filter(
                user=self.request.user, version='arranged'
            ).values_list('song_id', flat=True))
            for o in Order.objects.filter(user=self.request.user, status='paid'):
                for item in o.items:
                    if item.get('item_type') == 'song':
                        downloaded_ids.append(item['item_id'])
                    elif item.get('item_type') == 'album':
                        album_songs = Song.objects.filter(albums__id=item['item_id'])
                        downloaded_ids.extend(album_songs.values_list('id', flat=True))
            context['purchased_song_ids_json'] = json.dumps(list(set(downloaded_ids)))

        ratings = Rating.objects.filter(song=song)
        context['avg_rating'] = ratings.aggregate(Avg('score'))['score__avg'] or 0
        context['rating_count'] = ratings.count()
        if self.request.user.is_authenticated:
            user_rating = ratings.filter(user=self.request.user).first()
            context['user_rating'] = user_rating.score if user_rating else 0
        else:
            context['user_rating'] = 0

        context['related_songs'] = Song.objects.filter(
            artist=song.artist, is_published=True
        ).exclude(id=song.id)[:4]
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(Song),
            object_id=song.id, is_approved=True, parent__isnull=True
        ).prefetch_related(Prefetch('replies', queryset=Comment.objects.filter(is_approved=True)))
        context['content_type_id'] = ContentType.objects.get_for_model(Song).id
        context['object_id'] = song.id
        return context


class AlbumDetailView(DetailView):
    model = Album
    template_name = 'music/album_detail.html'
    context_object_name = 'album'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.object
        has_purchased = False
        if self.request.user.is_authenticated:
            for o in Order.objects.filter(user=self.request.user, status='paid'):
                for item in o.items:
                    if item.get('item_type') == 'album' and item.get('item_id') == album.id:
                        has_purchased = True
                        break
                if has_purchased:
                    break
        context['has_purchased'] = has_purchased
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(Album),
            object_id=album.id, is_approved=True, parent__isnull=True
        ).prefetch_related(Prefetch('replies', queryset=Comment.objects.filter(is_approved=True)))
        context['other_albums'] = Album.objects.filter(
            is_published=True
        ).exclude(id=album.id)[:2]
        context['content_type_id'] = ContentType.objects.get_for_model(Album).id
        context['object_id'] = album.id

        context['has_subscription'] = bool(get_active_subscription(self.request.user)) if self.request.user.is_authenticated else False
        context['purchased_song_ids_json'] = '[]'
        if self.request.user.is_authenticated:
            downloaded_ids = list(UserDownload.objects.filter(
                user=self.request.user, version='arranged'
            ).values_list('song_id', flat=True))
            for o in Order.objects.filter(user=self.request.user, status='paid'):
                for item in o.items:
                    if item.get('item_type') == 'song':
                        downloaded_ids.append(item['item_id'])
                    elif item.get('item_type') == 'album':
                        album_songs = Song.objects.filter(albums__id=item['item_id'])
                        downloaded_ids.extend(album_songs.values_list('id', flat=True))
            context['purchased_song_ids_json'] = json.dumps(list(set(downloaded_ids)))
        return context


class ArtistDetailView(DetailView):
    model = Artist
    template_name = 'music/artist_detail.html'
    context_object_name = 'artist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        artist = self.object
        context['songs'] = Song.objects.filter(artist=artist, is_published=True)
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(Artist),
            object_id=artist.id, is_approved=True, parent__isnull=True
        ).prefetch_related(Prefetch('replies', queryset=Comment.objects.filter(is_approved=True)))
        context['content_type_id'] = ContentType.objects.get_for_model(Artist).id
        context['object_id'] = artist.id
        return context


class SubscriptionDetailView(DetailView):
    model = SubscriptionPlan
    template_name = 'music/subscription_detail.html'
    context_object_name = 'plan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_plans'] = SubscriptionPlan.objects.filter(
            is_active=True
        ).exclude(id=self.object.id)
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(SubscriptionPlan),
            object_id=self.object.id, is_approved=True, parent__isnull=True
        ).prefetch_related(Prefetch('replies', queryset=Comment.objects.filter(is_approved=True)))
        context['content_type_id'] = ContentType.objects.get_for_model(SubscriptionPlan).id
        context['object_id'] = self.object.id
        return context


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def submit_rating(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'متد نامعتبر'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)

    try:
        data = json.loads(request.body)
        song_id = int(data.get('song_id'))
        score = int(data.get('score'))
    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    if score < 1 or score > 5:
        return JsonResponse({'success': False, 'message': 'امتیاز باید بین ۱ تا ۵ باشد'}, status=400)

    song = Song.objects.filter(id=song_id, is_published=True).first()
    if not song:
        return JsonResponse({'success': False, 'message': 'آهنگ یافت نشد'}, status=404)

    rating, created = Rating.objects.update_or_create(
        user=request.user, song=song,
        defaults={'score': score}
    )

    avg = Rating.objects.filter(song=song).aggregate(Avg('score'))['score__avg']
    return JsonResponse({
        'success': True,
        'message': 'امتیاز شما ثبت شد' if created else 'امتیاز شما بروزرسانی شد',
        'avg_rating': round(avg, 1) if avg else 0,
        'rating_count': Rating.objects.filter(song=song).count(),
        'user_score': score,
    })


@csrf_exempt
def toggle_wishlist(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'متد نامعتبر'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'لطفاً ابتدا وارد شوید'}, status=401)

    try:
        data = json.loads(request.body)
        song_id = int(data.get('song_id'))
    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
        return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)

    song = Song.objects.filter(id=song_id, is_published=True).first()
    if not song:
        return JsonResponse({'success': False, 'message': 'آهنگ یافت نشد'}, status=404)

    item, created = WishlistItem.objects.get_or_create(user=request.user, song=song)
    if not created:
        item.delete()
        return JsonResponse({'success': True, 'wishlisted': False, 'message': 'از لیست علاقه‌مندی‌ها حذف شد'})

    return JsonResponse({'success': True, 'wishlisted': True, 'message': 'به لیست علاقه‌مندی‌ها اضافه شد'})


@csrf_exempt
def get_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'wishlisted_ids': []})

    ids = list(WishlistItem.objects.filter(user=request.user).values_list('song_id', flat=True))
    return JsonResponse({'wishlisted_ids': ids})


@login_required
def download_song(request, song_id, version):
    song = get_object_or_404(Song, id=song_id, is_published=True)

    if version == 'demo':
        url = song.preview_url.url if song.preview_url else None
    elif version == 'original':
        url = song.original_audio.url if song.original_audio else None
    elif version == 'arranged':
        url = song.arranged_audio.url if song.arranged_audio else None
    else:
        return redirect('home')

    if not url:
        return redirect('home')

    # demo and original are free for all authenticated users
    if version in ('demo', 'original'):
        return redirect(url)

    # arranged requires purchase or subscription
    has_access = False
    via_subscription = False
    active_sub = get_active_subscription(request.user)
    if active_sub:
        has_access = True
        via_subscription = True
    else:
        # Check direct purchase / album purchase
        for o in Order.objects.filter(user=request.user, status='paid'):
            for item in o.items:
                if item.get('item_type') == 'song' and item.get('item_id') == song.id:
                    has_access = True
                    break
                if item.get('item_type') == 'album':
                    if Song.objects.filter(id=song.id, albums__id=item['item_id']).exists():
                        has_access = True
                        break
            if has_access:
                break
    # Permanent access from previous subscription downloads
    if not has_access:
        if UserDownload.objects.filter(user=request.user, song=song, version='arranged').exists():
            has_access = True

    if not has_access:
        return redirect('home')

    # Record download for arranged (both play and download)
    if version == 'arranged':
        _, created = UserDownload.objects.get_or_create(user=request.user, song=song, version=version)

        # Decrement subscription count only on first download of this song
        if created and via_subscription and active_sub and active_sub.remaining_downloads > 0:
            active_sub.remaining_downloads -= 1
            if active_sub.remaining_downloads <= 0:
                active_sub.is_active = False
            active_sub.save()

        # Increment purchase count on first download via subscription
        if created and via_subscription:
            Song.objects.filter(pk=song.id).update(purchase_count=F('purchase_count') + 1)

    return redirect(url)
