import re, time, logging
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.core.management.base import BaseCommand
from music.models import ScrapedSong

logger = logging.getLogger(__name__)

BASE_URL = 'https://musicbaran1.ir'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60, verify=False)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt == retries - 1:
                logger.error(f'Failed to fetch {url}: {e}')
                return None
            time.sleep(2)


def song_exists(source_url):
    return ScrapedSong.objects.filter(source_url=source_url.strip()).exists()


def parse_listing(html):
    soup = BeautifulSoup(html, 'lxml')
    items = []
    for article in soup.select('article.post'):
        ico = article.select_one('figure a.ico')
        if not ico:
            continue
        classes = ico.get('class', [])
        if 'single' not in classes:
            continue
        link = article.select_one('figure a[href*="/music/"]:not([href*="music-cats"])')
        if not link:
            continue
        detail_url = link.get('href', '').strip()
        if not detail_url:
            continue
        slug = detail_url.rstrip('/').split('/')[-1] if detail_url else ''
        title_el = article.select_one('.name h3')
        artist_el = article.select_one('.name h2')
        img = article.select_one('figure img')
        title = title_el.get_text(strip=True) if title_el else ''
        artist_name = artist_el.get_text(strip=True) if artist_el else ''
        thumbnail = img.get('src', '') if img else ''
        date_el = article.select_one('.foot_post span:first-child')
        date_str = date_el.get_text(strip=True) if date_el else ''
        dl_el = article.select_one('.foot_post span:last-child')
        dl_text = dl_el.get_text(strip=True) if dl_el else ''
        dl_count = 0
        if dl_text:
            m = re.search(r'(\d[\d,]*)', dl_text.replace(',', ''))
            if m:
                dl_count = int(m.group(1))
        items.append({
            'title': title,
            'artist_name': artist_name,
            'detail_url': detail_url,
            'slug': slug,
            'thumbnail': thumbnail,
            'date_str': date_str,
            'download_count': dl_count,
        })
    return items


def parse_detail(html):
    soup = BeautifulSoup(html, 'lxml')
    mp3_url = ''
    dl_btn = soup.select_one('.link_dl a.button--wayra')
    if dl_btn:
        mp3_url = dl_btn.get('href', '').strip()
    if not mp3_url:
        for script in soup.select('script'):
            if script.string and 'jPlayer' in script.string and 'mp3:' in script.string:
                m = re.search(r'mp3:\s*"([^"]+)"', script.string)
                if m:
                    mp3_url = m.group(1).strip()
                    break
    cover = ''
    cover_el = soup.select_one('section.single_banner figure img') or soup.select_one('.player figure img')
    if cover_el:
        cover = cover_el.get('src', '')
    return {'mp3_url': mp3_url, 'cover': cover}


class Command(BaseCommand):
    help = 'Scrape songs from musicbaran1.ir into ScrapedSong model'

    def add_arguments(self, parser):
        parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape (default: 1)')
        parser.add_argument('--page', type=int, default=0, help='Start from this page number (default: scrape from last page backward)')
        parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')

    def handle(self, *args, **options):
        total_pages = options['pages']
        start_page = options['page'] if options['page'] > 0 else total_pages
        delay = options['delay']
        added = 0
        skipped = 0

        for page in range(start_page, start_page - total_pages, -1):
            if page < 1:
                break
            url = f'{BASE_URL}/music/page/{page}/' if page > 1 else f'{BASE_URL}/music/'
            self.stdout.write(f'Fetching page {page}...')
            html = fetch_html(url)
            if not html:
                break

            items = parse_listing(html)
            if not items:
                self.stdout.write(f'  No songs found on page {page}, stopping.')
                break

            for item in items:
                if song_exists(item['detail_url']):
                    skipped += 1
                    continue

                mp3_url = ''
                cover = item['thumbnail']
                detail_html = fetch_html(item['detail_url'])
                if detail_html:
                    detail = parse_detail(detail_html)
                    mp3_url = detail['mp3_url']
                    if detail['cover']:
                        cover = detail['cover']

                ScrapedSong.objects.create(
                    title=item['title'],
                    artist_name=item['artist_name'],
                    cover_url=cover,
                    mp3_url=mp3_url,
                    source_url=item['detail_url'],
                    slug=item['slug'],
                    date_str=item['date_str'],
                    download_count=item['download_count'],
                )
                added += 1
                self.stdout.write(f'  Added: {item["title"]} - {item["artist_name"]}')

                time.sleep(delay)

            time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f'Done. Added {added} songs, skipped {skipped} existing.'))
