import requests
from .models import Setting


def _get_setting(key, default=''):
    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return default


def _send_bot(api_url, token, chat_id, message):
    if not token or not chat_id:
        return False
    try:
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        resp = requests.post(
            f'{api_url}/bot{token}/sendMessage',
            json=payload, timeout=10,
        )
        if resp.ok:
            return True
        payload.pop('parse_mode', None)
        resp = requests.post(
            f'{api_url}/bot{token}/sendMessage',
            json=payload, timeout=10,
        )
        return resp.ok
    except requests.RequestException:
        return False


def _send_photo(api_url, token, chat_id, photo_url, caption):
    if not token or not chat_id or not photo_url:
        return False
    try:
        payload = {'chat_id': chat_id, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
        resp = requests.post(
            f'{api_url}/bot{token}/sendPhoto',
            json=payload, timeout=15,
        )
        if resp.ok:
            return True
        payload.pop('parse_mode', None)
        resp = requests.post(
            f'{api_url}/bot{token}/sendPhoto',
            json=payload, timeout=15,
        )
        return resp.ok
    except requests.RequestException:
        return False


def send_telegram(message):
    return _send_bot(
        'https://api.telegram.org',
        _get_setting('telegram_bot_token'),
        _get_setting('telegram_chat_id'),
        message,
    )


def send_bale(message):
    token = _get_setting('bale_bot_token')
    chat_id = _get_setting('bale_chat_id')
    for url in ('https://api.bale.ai', 'https://tapi.bale.ai'):
        if _send_bot(url, token, chat_id, message):
            return True
    return False


def notify_admin(message):
    sent = send_telegram(message)
    send_bale(message)
    return sent


def _full_url(path):
    if not path:
        return ''
    if path.startswith('http://') or path.startswith('https://'):
        return path
    base = _get_setting('site_url', 'http://127.0.0.1:8000').rstrip('/')
    return f'{base}{path}'


def _send_audio(api_url, token, chat_id, audio_url, title, performer, caption=''):
    if not token or not chat_id or not audio_url:
        return False
    try:
        payload = {
            'chat_id': chat_id,
            'audio': audio_url,
            'title': title,
            'performer': performer,
            'caption': caption,
            'parse_mode': 'HTML',
        }
        resp = requests.post(
            f'{api_url}/bot{token}/sendAudio',
            json=payload, timeout=30,
        )
        if resp.ok:
            return True
        payload.pop('parse_mode', None)
        resp = requests.post(
            f'{api_url}/bot{token}/sendAudio',
            json=payload, timeout=30,
        )
        return resp.ok
    except requests.RequestException:
        return False


def _build_song_caption(song):
    lines = [
        f'🎵 <b>{song.title}</b> — <i>{song.artist.name}</i>',
        '',
    ]
    parts = []
    if song.duration:
        parts.append(f'⏱ {song.duration}')
    if song.bpm:
        parts.append(f'🎹 BPM: {song.bpm}')
    if song.musical_key:
        parts.append(f'گام: {song.musical_key}')
    if parts:
        lines.append(' | '.join(parts))
        lines.append('')
    if song.price:
        lines.append(f'💰 {song.price:,} تومان')
        lines.append('')
    return '\n'.join(lines)


def _send_song_to_api(api_url, token, channel, song):
    sent = False
    if not token or not channel:
        return False

    cover_url = _full_url(song.cover.url if song.cover and song.cover.name else '')
    caption = _build_song_caption(song)

    # 1) Send photo with caption
    if cover_url:
        sent = _send_photo(api_url, token, channel, cover_url, caption)
    if not sent:
        sent = _send_bot(api_url, token, channel, caption)
    if not sent:
        return False

    # 2) Send demo audio
    demo_url = _full_url(song.preview_url.url if song.preview_url and song.preview_url.name else '')
    if demo_url:
        _send_audio(api_url, token, channel, demo_url, song.title, song.artist.name, '🎧 دمو (پیش‌نمایش)')

    # 3) Send original audio
    orig_url = _full_url(song.original_audio.url if song.original_audio and song.original_audio.name else '')
    if orig_url:
        _send_audio(api_url, token, channel, orig_url, song.title, song.artist.name, '🎵 نسخه اصلی')

    return True


def send_song_to_channel(song):
    tg_token = _get_setting('telegram_bot_token')
    tg_channel = _get_setting('telegram_channel')
    _send_song_to_api('https://api.telegram.org', tg_token, tg_channel, song)

    bale_token = _get_setting('bale_bot_token')
    bale_channel = _get_setting('bale_channel')
    if bale_channel:
        for url in ('https://api.bale.ai', 'https://tapi.bale.ai'):
            if _send_song_to_api(url, bale_token, bale_channel, song):
                break
