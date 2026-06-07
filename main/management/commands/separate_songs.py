import os, ssl, logging, time, urllib.request
from pathlib import Path

import certifi
from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from music.models import ScrapedSong, Song, Artist
from main.notifications import send_song_to_channel

logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

DOWNLOAD_DIR = settings.MEDIA_ROOT / 'scraped' / 'downloads'
MODEL_CACHE = settings.MEDIA_ROOT / 'scraped' / 'models'


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def download_file(url, dest_path, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as resp:
                with open(str(dest_path), 'wb') as f:
                    while True:
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            return
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5)


def get_or_create_artist(name):
    name = name.strip()
    if not name:
        return None
    artist, _ = Artist.objects.get_or_create(
        name=name,
        defaults={'slug': slugify(name, allow_unicode=True)},
    )
    return artist


def upload_to_arvan(file_path, object_name):
    try:
        import boto3
        session = boto3.session.Session()
        client = session.client(
            's3',
            endpoint_url=settings.ARVAN_S3_ENDPOINT,
            aws_access_key_id=settings.ARVAN_S3_ACCESS_KEY,
            aws_secret_access_key=settings.ARVAN_S3_SECRET_KEY,
        )
        client.upload_file(
            str(file_path), settings.ARVAN_S3_BUCKET, object_name,
            ExtraArgs={'ACL': 'public-read'},
        )
        if settings.ARVAN_S3_PUBLIC_URL:
            return f'{settings.ARVAN_S3_PUBLIC_URL}/{object_name}'
        return f'{settings.ARVAN_S3_ENDPOINT}/{settings.ARVAN_S3_BUCKET}/{object_name}'
    except Exception as e:
        logger.warning(f'Arvan upload failed, using local storage: {e}')
        return None


def save_local_file(file_path, sub_dir):
    dest = f'{sub_dir}/{file_path.name}'
    saved = default_storage.save(dest, open(str(file_path), 'rb'))
    return settings.MEDIA_URL + saved


def run_separation(input_path, output_dir, stream):
    from audio_separator.separator import Separator

    separator = Separator(
        output_dir=str(output_dir),
        output_format='MP3',
        sample_rate=44100,
        model_file_dir=str(MODEL_CACHE),
        log_level=logging.WARNING,
    )

    stream.write('  Loading model UVR-MDX-NET-Inst_HQ_3.onnx...\n')
    separator.load_model(model_filename='UVR-MDX-NET-Inst_HQ_3.onnx')

    stream.write('  Separating instruments from vocals...\n')
    output_files = separator.separate(str(input_path))

    return output_files


def get_duration(audio_path):
    from pydub import AudioSegment
    audio = AudioSegment.from_file(str(audio_path))
    total_seconds = int(len(audio) / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f'{minutes}:{seconds:02d}', total_seconds


def create_demo(input_path, output_path, stream, total_sec=None):
    from pydub import AudioSegment

    demo_duration = max(15, min(120, int(total_sec / 4))) if total_sec else 60
    stream.write(f'  Creating {demo_duration}s demo (1/4 of song)...\n')
    audio = AudioSegment.from_file(str(input_path))
    demo = audio[:demo_duration * 1000]
    demo.export(str(output_path), format='mp3', bitrate='128k')


def detect_bpm(audio_path):
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(str(audio_path), duration=60, res_type='kaiser_fast')
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(tempo, np.ndarray):
            tempo = tempo.item() if tempo.size == 1 else float(tempo[0])
        return int(round(tempo))
    except Exception as e:
        logger.warning(f'BPM detection failed: {e}')
        return None


def detect_key(audio_path):
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(str(audio_path), duration=60, res_type='kaiser_fast')
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_idx = int(np.argmax(chroma_mean))
        return keys[key_idx % 12]
    except Exception as e:
        logger.warning(f'Key detection failed: {e}')
        return None


class Command(BaseCommand):
    help = 'Separate scraped songs and create Song records'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=5, help='Max songs to process per run')
        parser.add_argument('--reset-failed', action='store_true', help='Reset failed songs to pending before processing')

    def handle(self, *args, **options):
        limit = options['limit']
        if options['reset_failed']:
            reset = ScrapedSong.objects.filter(
                separate_instruments=True, separation_status='failed',
            ).update(separation_status='pending', error_message='')
            self.stdout.write(f'Reset {reset} failed songs to pending.')

        items = ScrapedSong.objects.filter(
            separate_instruments=True,
            separation_status='pending',
        ).order_by('id')[:limit]

        if not items:
            self.stdout.write('No scraped songs pending separation.')
            return

        ensure_dir(DOWNLOAD_DIR)
        ensure_dir(MODEL_CACHE)

        for item in items:
            self.stdout.write(f'--- Scraped song #{item.id} ---')

            if not item.mp3_url:
                item.separation_status = 'failed'
                item.error_message = 'No mp3_url'
                item.save(update_fields=['separation_status', 'error_message'])
                self.stdout.write(self.style.WARNING('  No mp3_url'))
                continue

            item.separation_status = 'processing'
            item.error_message = ''
            item.save(update_fields=['separation_status', 'error_message'])

            try:
                input_path = DOWNLOAD_DIR / f'scraped_{item.id}.mp3'
                self.stdout.write(f'  Download: {item.mp3_url}')
                download_file(item.mp3_url, input_path)
                if not input_path.exists() or input_path.stat().st_size == 0:
                    raise Exception('Downloaded file is empty or missing')
                self.stdout.write(self.style.SUCCESS('  Download OK'))

                duration_str, total_sec = get_duration(input_path)
                self.stdout.write(f'  Duration: {duration_str}')

                self.stdout.write('  Detecting BPM...')
                bpm = detect_bpm(input_path)

                self.stdout.write('  Detecting musical key...')
                musical_key = detect_key(input_path)

                cover_path = None
                if item.cover_url:
                    try:
                        ext = Path(item.cover_url.split('?')[0]).suffix or '.jpg'
                        cover_path = DOWNLOAD_DIR / f'cover_{item.id}{ext}'
                        self.stdout.write(f'  Downloading cover: {item.cover_url}')
                        download_file(item.cover_url, cover_path)
                    except Exception as e:
                        self.stdout.write(f'  Cover download failed: {e}')
                        cover_path = None

                output_dir = DOWNLOAD_DIR / f'output_{item.id}'
                ensure_dir(output_dir)

                output_files = run_separation(input_path, output_dir, self.stdout)

                vocals_keywords = ['(vocals)', '_vocals', 'vocals_', 'voice', 'no_inst']
                inst_keywords = ['(instrumental)', '_instrumental', 'instrumental_', '(instrument)', '_inst_', '_inst)', 'no_vocals', 'karaoke', 'accompaniment', 'backing_track']

                vocals_file = None
                inst_file = None
                for f in output_files:
                    fpath = Path(output_dir) / f
                    name_lower = fpath.stem.lower()
                    if any(kw in name_lower for kw in vocals_keywords):
                        vocals_file = fpath
                    elif any(kw in name_lower for kw in inst_keywords):
                        inst_file = fpath

                if not inst_file:
                    if vocals_file and len(output_files) >= 2:
                        other = [Path(output_dir) / f for f in output_files if (Path(output_dir) / f) != vocals_file]
                        inst_file = other[0]
                    elif output_files:
                        inst_file = Path(output_dir) / output_files[-1]

                if not inst_file or not inst_file.exists():
                    raise FileNotFoundError(f'Instruments file not found: {output_files}')

                if inst_file.suffix.lower() != '.mp3':
                    mp3_file = output_dir / f'{item.id}_arranged.mp3'
                    from pydub import AudioSegment
                    AudioSegment.from_file(str(inst_file)).export(str(mp3_file), format='mp3', bitrate='320k')
                    inst_file = mp3_file

                demo_path = DOWNLOAD_DIR / f'demo_{item.id}.mp3'
                create_demo(inst_file, demo_path, self.stdout, total_sec)

                artist = get_or_create_artist(item.artist_name)

                song = Song(
                    title=item.title,
                    artist=artist,
                    price=total_sec * 520,
                    duration=duration_str,
                    bpm=bpm,
                    musical_key=musical_key or '',
                    is_published=True,
                )

                with open(str(input_path), 'rb') as f:
                    song.original_audio.save(f'original_{item.id}.mp3', File(f), save=False)

                with open(str(demo_path), 'rb') as f:
                    song.preview_url.save(f'demo_{item.id}.mp3', File(f), save=False)

                with open(str(inst_file), 'rb') as f:
                    song.arranged_audio.save(f'arranged_{item.id}.mp3', File(f), save=False)

                if cover_path and cover_path.exists():
                    with open(str(cover_path), 'rb') as f:
                        ext = Path(item.cover_url.split('?')[0]).suffix or '.jpg'
                        song.cover.save(f'cover_{item.id}{ext}', File(f), save=False)

                song.save()

                item.is_imported = True
                item.separation_status = 'done'
                item.save(update_fields=['is_imported', 'separation_status'])

                # clean up temp files
                try:
                    if input_path and input_path.exists():
                        input_path.unlink()
                    if cover_path and cover_path.exists():
                        cover_path.unlink()
                    if demo_path and demo_path.exists():
                        demo_path.unlink()
                    if output_dir and output_dir.exists():
                        import shutil
                        shutil.rmtree(output_dir)
                except Exception as cleanup_err:
                    logger.warning(f'Cleanup warning for song {item.id}: {cleanup_err}')

                self.stdout.write(self.style.SUCCESS(f'  Created song #{song.id} - Price: {total_sec * 520:,} Toman'))

                try:
                    send_song_to_channel(song)
                except Exception:
                    logger.warning(f'Channel notification failed for song #{song.id}')

            except Exception as e:
                logger.exception(f'Separation failed for scraped song {item.id}')
                item.separation_status = 'failed'
                item.error_message = f'{type(e).__name__}: {e}'
                item.save(update_fields=['separation_status', 'error_message'])
                self.stdout.write(self.style.ERROR(f'  Failed: {e}'))
