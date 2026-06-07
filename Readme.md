روش تنظیم کرون در aaPanel:
برای ایجاد کرون جاب برای دانلود اتوماتیک آهنگ از musicbaran1.ir

برو توی aaPanel → Cron
دکمه Add Cron Task رو بزن
تنظیمات:
Type of Task: Shell Script
Name: scrape_musicbaran
Period: N Minutes/Days → N Hours = 8 (روزی ۳ بار)
Script Body:
cd /path/to/project && /path/to/venv/bin/python manage.py scrape_musicbaran --pages=10 >> /tmp/scraper.log 2>&1

cd /path/to/project && /path/to/venv/bin/python manage.py separate_songs --reset-failed --limit=2 >> /tmp/scraper.log 2>&1
(اختیاری) یه N Days دیگه هم میتونی بزاری که مثلاً هر ۱ روز اجرا کنه
Save رو بزن



برای تفکیک آهنگ
در سرور demucs نصب بشه
pip install demucs
apt install ffmpeg



کرون جاب:
python manage.py scrape_musicbaran --delay=10 --page=10








0-سایت sinarahmani.ir انتقال داده بشه به hetzner
0-ارسال به اروان چک شد

1- آهنگ هایی که seperate میشن به کانال تلگرامی و کانل بله ارسال بشه.
2- وقتی scrape_musicbaran اجرا میشه از آخر شروع کنه به اول.
3- وقتی scrape_musicbaran اجرا میشه و دارای متغییر page بود از آخرین صفحه شروع کنع. مثلا --page=10 بود اول صفحه 10 رو اجرا کنه
4- برای شروع seperate از کوچکترین id شروع کنه.(هر آهنگی زودتر وارد دیتابیس شد زودتر seperate بشه)
5- اگر آهنگ پاک شد فایل های مریوط به اون آهنگ هم پاک بشه(برای مقاله، آلبوم و هنرمندان هم به همین صورت باشه)