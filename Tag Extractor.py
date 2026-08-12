import os
import re
import sys
import io
import glob
import time
import logging
import tempfile
import hashlib
from functools import wraps
from urllib.parse import urlparse, quote
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QGroupBox, QSplitter, QTabWidget, QComboBox,
    QDialog, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QByteArray, QMutex, QWaitCondition
from PySide6.QtGui import QPixmap, QFont, QTextCursor, QMouseEvent, QDesktopServices
from PySide6.QtCore import QUrl

CONFIG = {
    'DANBOORU_BASE': 'https://danbooru.donmai.us',
    'USER_AGENT': 'TagExtractor/2.0',
    'TIMEOUT': 15,
    'RETRIES': 3,
    'BACKOFF': 2,
    'MAX_IMAGE_BYTES': 30 * 1024 * 1024,
    'MAX_PREVIEW_WIDTH': 1920,
    'MAX_PREVIEW_HEIGHT': 1080,
    'PREVIEW_CONNECT_TIMEOUT': 5,
    'PREVIEW_READ_TIMEOUT': 20,
    'PREVIEW_CACHE_SIZE': 30,
    'HEAD_TIMEOUT': 1.5,
    'SAUCENAO_TIMEOUT': 8,
    'ASCII2D_TIMEOUT': 8,
    'DANBOORU_SEARCH_TIMEOUT': 8,
    'SEARCH_IMAGE_MAX_SIZE': 512,
}

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TagExtractor')

http_session = requests.Session()
http_session.headers.update({'User-Agent': CONFIG['USER_AGENT']})
cache = {}
preview_cache = {}
preview_error_cache = set()
search_cache = {}

def retry_on_error(max_tries=CONFIG['RETRIES'], backoff=CONFIG['BACKOFF']):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_tries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as e:
                    if e.response.status_code == 429:
                        retry_after = int(e.response.headers.get('Retry-After', backoff ** attempt))
                        logger.warning(f"429 Too Many Requests, sleep {retry_after}s")
                        time.sleep(retry_after)
                        continue
                    raise
                except Exception as e:
                    if attempt == max_tries:
                        raise
                    wait = backoff ** attempt
                    logger.warning(f"Error: {e}, retry in {wait}s ({attempt}/{max_tries})")
                    time.sleep(wait)
            return None
        return wrapper
    return decorator

class DanbooruClient:
    def __init__(self, login: str = None, api_key: str = None):
        self.login = login
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': CONFIG['USER_AGENT'],
            'Accept': 'application/json',
        })
        self.danbooru_cache = {}

    def _auth_params(self, extra: dict = None) -> dict:
        params = extra or {}
        if self.login and self.api_key:
            params.update({'login': self.login, 'api_key': self.api_key})
        return params

    @retry_on_error()
    def _get(self, endpoint: str, params: dict = None, timeout=CONFIG['TIMEOUT']) -> dict:
        url = f"{CONFIG['DANBOORU_BASE']}{endpoint}"
        resp = self.session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def parse_tags(self, post: dict) -> list:
        raw = post.get('tag_string', '')
        return [tag.replace('_', ' ') for tag in raw.split()] if raw else []

    @retry_on_error()
    def get_post(self, identifier: str) -> dict or None:
        if identifier in self.danbooru_cache:
            return self.danbooru_cache[identifier]

        if str(identifier).startswith('md5:'):
            tag = identifier
        else:
            tag = f'id:{identifier}'
        params = self._auth_params({'tags': tag})

        data = self._get('/posts.json', params, timeout=CONFIG['DANBOORU_SEARCH_TIMEOUT'])
        if not data:
            return None

        post = data[0]
        result = {
            'id': post['id'],
            'tags': self.parse_tags(post),
            'file_url': post.get('file_url'),
            'sample_url': post.get('sample_url'),
            'preview_url': post.get('preview_url'),
            'md5': post.get('md5'),
            'source': post.get('source'),
        }
        self.danbooru_cache[identifier] = result
        return result

    @retry_on_error()
    def search_by_md5(self, md5: str) -> dict or None:
        cache_key = f"md5_{md5}"
        if cache_key in self.danbooru_cache:
            return self.danbooru_cache[cache_key]

        params = self._auth_params({'tags': f'md5:{md5}'})
        try:
            data = self._get('/posts.json', params, timeout=CONFIG['DANBOORU_SEARCH_TIMEOUT'])
            if not data:
                return None
        except Exception:
            return None

        post = data[0]
        result = {
            'id': post['id'],
            'tags': self.parse_tags(post),
            'file_url': post.get('file_url'),
            'sample_url': post.get('sample_url'),
            'preview_url': post.get('preview_url'),
            'md5': post.get('md5'),
            'source': post.get('source'),
        }
        self.danbooru_cache[cache_key] = result
        return result

    @staticmethod
    def post_url(post_id: int) -> str:
        return f"{CONFIG['DANBOORU_BASE']}/posts/{post_id}"

def resize_image_for_search(image_data, max_size=CONFIG['SEARCH_IMAGE_MAX_SIZE']):
    try:
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except Exception:
        return image_data

def search_saucenao(image_data, api_key=None):
    try:
        image_data_resized = resize_image_for_search(image_data)
        url = 'https://saucenao.com/search.php'
        params = {
            'api_key': api_key or '',
            'output_type': 2,
            'numres': 1,
            'db': 999,
        }
        files = {'file': ('image.jpg', image_data_resized, 'image/jpeg')}
        headers = {'User-Agent': CONFIG['USER_AGENT']}
        response = requests.post(url, params=params, files=files, headers=headers, timeout=CONFIG['SAUCENAO_TIMEOUT'])
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            if 'data' in result and 'ext_urls' in result['data']:
                for url in result['data']['ext_urls']:
                    if 'danbooru.donmai.us/posts/' in url:
                        match = re.search(r'/posts/(\d+)', url)
                        if match:
                            return match.group(1)
        return None
    except Exception:
        return None

def search_ascii2d(image_data):
    try:
        image_data_resized = resize_image_for_search(image_data)
        files = {'file': ('image.jpg', image_data_resized, 'image/jpeg')}
        headers = {'User-Agent': CONFIG['USER_AGENT']}
        response = requests.post('https://ascii2d.net/search/file', files=files, headers=headers, timeout=CONFIG['ASCII2D_TIMEOUT'])
        if response.status_code != 200:
            return None
        html = response.text
        pattern = r'danbooru\.donmai\.us/posts/(\d+)'
        matches = re.findall(pattern, html)
        if matches:
            return matches[0]
        return None
    except Exception:
        return None

def parallel_search(image_data, saucenao_api_key=None):
    try:
        md5 = hashlib.md5(image_data).hexdigest()
        if md5 in search_cache:
            return search_cache[md5]
    except Exception:
        pass

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(search_saucenao, image_data, saucenao_api_key): 'saucenao',
            executor.submit(search_ascii2d, image_data): 'ascii2d'
        }
        for future in as_completed(futures):
            try:
                result = future.result(timeout=CONFIG['SAUCENAO_TIMEOUT'] + 2)
                if result:
                    if 'md5' in locals():
                        search_cache[md5] = result
                    return result
            except Exception:
                continue
    return None

LANG = {
    'ru': {
        'title': 'Tag Extractor',
        'tab_main': 'Главная',
        'tab_settings': 'Настройки',
        'lang_label': 'Язык',
        'url_label': 'URL:',
        'process_btn': 'Извлечь теги',
        'merge_btn': 'Объединить все теги',
        'folder_btn': 'Папка сохранения',
        'clear_btn': 'Очистить лог',
        'open_file_btn': 'Открыть файл',
        'exit_btn': 'Выход',
        'status_ready': 'Готов к работе',
        'processing': 'Обработка...',
        'no_url': 'Введите ссылку',
        'select_folder': 'Выберите папку для сохранения',
        'current_folder': 'Текущая папка:',
        'merge_start': 'Начинаю объединение файлов...',
        'merge_done': 'Объединение завершено. Файл: {}',
        'merge_no_files': 'Не найдено файлов с тегами.',
        'preview_not_available': 'Предпросмотр недоступен (кликните для повторной загрузки)',
        'loading': 'Загрузка...',
        'processing_url': '🔄 {}',
        'direct_request': '📌 Прямой запрос к {}',
        'saved_tags': '✅ Сохранено {} тегов в {}',
        'error_extract': '❌ Не удалось распознать ссылку',
        'error_no_tags': '❌ Не удалось получить теги',
        'source_info': '📌 Источник: {}, ID: {}',
        'preview_fail': '⚠️ Не удалось получить URL изображения для предпросмотра',
        'search_md5': '🔎 Ищу по MD5...',
        'found_md5': '✅ Найдено по MD5',
        'danbooru_post': '📌 Пост на Danbooru: ID {}',
        'saved_from_danbooru': '✅ Сохранено {} тегов с Danbooru в {}',
        'saved_from_source': '✅ Сохранено {} тегов с {} в {}',
        'unsupported_domain': '❌ Домен {} не поддерживается',
        'error_exception': '❌ {}',
        'gelbooru_parsing_html': '🔎 Парсинг HTML страницы Gelbooru для получения тегов...',
        'gelbooru_parsed_tags': '✅ Извлечено {} тегов из HTML',
        'choose_source_title': 'Выбор источника тегов',
        'choose_source_msg': 'Найдены теги из нескольких источников. Какой использовать?',
        'btn_danbooru': 'Danbooru ({} тегов)',
        'btn_gelbooru': 'Gelbooru ({} тегов)',
        'btn_source': '{} ({} тегов)',
        'btn_cancel': 'Отмена (использовать исходный сайт)',
        'search_gelbooru': '🔎 Ищу на Gelbooru...',
        'found_gelbooru': '✅ Найдено на Gelbooru',
        'saved_from_gelbooru': '✅ Сохранено {} тегов с Gelbooru в {}',
        'comparing_images': '🔎 Сравниваю изображения по содержимому...',
        'images_match': '✅ Изображения совпадают (расстояние Хэмминга: {}). Использую Danbooru.',
        'images_differ': '⚠️ Изображения визуально различаются. Требуется выбор.',
        'settings_folder': 'Папка для сохранения:',
        'settings_login': 'Логин Danbooru:',
        'settings_api_key': 'API-ключ:',
        'settings_saucenao': 'SauceNAO API Key:',
        'settings_apply': 'Применить',
        'auth_applied': '🔑 Авторизация Danbooru обновлена',
        'auth_empty': '🔓 Работа без авторизации',
        'preview_error': '⚠️ Ошибка загрузки: {} (кликните для повтора)',
        'no_file_to_open': 'Нет сохранённого файла для открытия',
        'file_opened': 'Открыт файл: {}',
        'searching_engines': '🔍 Ищу через SauceNAO и Ascii2D...',
    },
    'en': {
        'title': 'Tag Extractor',
        'tab_main': 'Main',
        'tab_settings': 'Settings',
        'lang_label': 'Language',
        'url_label': 'URL:',
        'process_btn': 'Extract tags',
        'merge_btn': 'Merge all tags',
        'folder_btn': 'Save folder',
        'clear_btn': 'Clear log',
        'open_file_btn': 'Open file',
        'exit_btn': 'Exit',
        'status_ready': 'Ready',
        'processing': 'Processing...',
        'no_url': 'Enter URL',
        'select_folder': 'Select save folder',
        'current_folder': 'Current folder:',
        'merge_start': 'Merging files...',
        'merge_done': 'Merge complete. File: {}',
        'merge_no_files': 'No tag files found.',
        'preview_not_available': 'Preview not available (click to retry)',
        'loading': 'Loading...',
        'processing_url': '🔄 {}',
        'direct_request': '📌 Direct request to {}',
        'saved_tags': '✅ Saved {} tags to {}',
        'error_extract': '❌ Failed to parse URL',
        'error_no_tags': '❌ Failed to get tags',
        'source_info': '📌 Source: {}, ID: {}',
        'preview_fail': '⚠️ Failed to get image URL for preview',
        'search_md5': '🔎 Searching by MD5...',
        'found_md5': '✅ Found by MD5',
        'danbooru_post': '📌 Danbooru post: ID {}',
        'saved_from_danbooru': '✅ Saved {} tags from Danbooru to {}',
        'saved_from_source': '✅ Saved {} tags from {} to {}',
        'unsupported_domain': '❌ Domain {} is not supported',
        'error_exception': '❌ {}',
        'gelbooru_parsing_html': '🔎 Parsing Gelbooru HTML page for tags...',
        'gelbooru_parsed_tags': '✅ Extracted {} tags from HTML',
        'choose_source_title': 'Choose tag source',
        'choose_source_msg': 'Tags found from multiple sources. Which one to use?',
        'btn_danbooru': 'Danbooru ({} tags)',
        'btn_gelbooru': 'Gelbooru ({} tags)',
        'btn_source': '{} ({} tags)',
        'btn_cancel': 'Cancel (use source site)',
        'search_gelbooru': '🔎 Searching on Gelbooru...',
        'found_gelbooru': '✅ Found on Gelbooru',
        'saved_from_gelbooru': '✅ Saved {} tags from Gelbooru to {}',
        'comparing_images': '🔎 Comparing images by content...',
        'images_match': '✅ Images match (Hamming distance: {}). Using Danbooru.',
        'images_differ': '⚠️ Images visually differ. Choice required.',
        'settings_folder': 'Save folder:',
        'settings_login': 'Danbooru login:',
        'settings_api_key': 'API key:',
        'settings_saucenao': 'SauceNAO API Key:',
        'settings_apply': 'Apply',
        'auth_applied': '🔑 Danbooru authorization updated',
        'auth_empty': '🔓 Working without authorization',
        'preview_error': '⚠️ Load error: {} (click to retry)',
        'no_file_to_open': 'No saved file to open',
        'file_opened': 'Opened file: {}',
        'searching_engines': '🔍 Searching via SauceNAO and Ascii2D...',
    }
}

def clean_tag(tag):
    return tag.replace('_', ' ')

def extract_identifier(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    query = parsed.query

    if 'danbooru.donmai.us' in domain or 'aibooru' in domain:
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/data/[^?]+\?(\d+)', url)
        if m:
            return domain, m.group(1)
        m = re.search(r'/([a-f0-9]{32})\.[a-z]+', url, re.I)
        if m:
            return domain, f"md5:{m.group(1)}"

    elif 'konachan.com' in domain or 'konachan.net' in domain:
        m = re.search(r'/post/show/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/([a-f0-9]{32})\.[a-z]+', url, re.I)
        if m:
            return domain, f"md5:{m.group(1)}"
        m = re.search(r'[?&]post_id=(\d+)', query)
        if m:
            return domain, m.group(1)

    elif 'yande.re' in domain:
        m = re.search(r'/post/show/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)

    elif 'gelbooru.com' in domain:
        m = re.search(r'id=(\d+)', query)
        if m:
            return domain, m.group(1)
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)

    return None, None

def fetch_aibooru_post(identifier, base_url='https://aibooru.online'):
    cache_key = ('aibooru', base_url, identifier)
    if cache_key in cache:
        return cache[cache_key]

    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = f"{base_url}/posts.json"
    headers = {
        'User-Agent': CONFIG['USER_AGENT'],
        'Referer': base_url + '/'
    }

    try:
        resp = http_session.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            cache[cache_key] = None
            return None
        post = data[0]
        raw_tags = post.get('tag_string', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        result = {
            'tags': tags,
            'file_url': post.get('file_url'),
            'sample_url': post.get('sample_url'),
            'preview_url': post.get('preview_url'),
            'md5': post.get('md5')
        }
        cache[cache_key] = result
        return result
    except Exception:
        cache[cache_key] = None
        return None

def fetch_konachan_post(domain, identifier):
    cache_key = ('konachan', domain, identifier)
    if cache_key in cache:
        return cache[cache_key]

    base_url = f"https://{domain}"
    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = f"{base_url}/post.json"

    try:
        resp = http_session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            cache[cache_key] = None
            return None
        post = data[0]
        raw_tags = post.get('tags', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        file_url = post.get('file_url')
        sample_url = post.get('sample_url')
        jpeg_url = post.get('jpeg_url')
        preview_url = sample_url or jpeg_url or file_url
        result = {
            'tags': tags,
            'file_url': file_url,
            'sample_url': sample_url,
            'jpeg_url': jpeg_url,
            'preview_url': preview_url,
            'md5': post.get('md5')
        }
        cache[cache_key] = result
        return result
    except Exception:
        cache[cache_key] = None
        return None

def fetch_yandere_post(identifier):
    cache_key = ('yandere', identifier)
    if cache_key in cache:
        return cache[cache_key]

    url = f"https://yande.re/post.json?tags=id:{identifier}"
    try:
        resp = http_session.get(url, timeout=10)
        data = resp.json()
        if not data or len(data) == 0:
            cache[cache_key] = None
            return None
        post = data[0]
        raw_tags = post.get('tags', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        file_url = post.get('file_url')
        sample_url = post.get('sample_url')
        jpeg_url = post.get('jpeg_url')
        preview_url = sample_url or jpeg_url or file_url
        result = {
            'tags': tags,
            'file_url': file_url,
            'sample_url': sample_url,
            'jpeg_url': jpeg_url,
            'preview_url': preview_url,
            'md5': post.get('md5')
        }
        cache[cache_key] = result
        return result
    except Exception:
        cache[cache_key] = None
        return None

def filter_gelbooru_tags(tags):
    if not tags:
        return tags

    marker_index = -1
    for i, t in enumerate(tags):
        if 'imageboard-' in t.lower():
            marker_index = i
            break

    if marker_index != -1:
        marker = tags[marker_index]
        lower_marker = marker.lower()
        pos = lower_marker.find('imageboard-')
        if pos != -1:
            after = marker[pos + len('imageboard-'):].strip()
            if after:
                extra_tags = after.split()
            else:
                extra_tags = []
        else:
            extra_tags = []

        new_tags = tags[marker_index + 1:] + extra_tags
    else:
        new_tags = tags

    filtered = []
    for t in new_tags:
        t_clean = t.strip()
        if not t_clean:
            continue
        if len(t_clean) < 2:
            continue
        if not re.search(r'[a-zA-Zа-яА-Я0-9]', t_clean):
            continue
        filtered.append(t_clean)
    return filtered

def check_url_accessible(url, timeout=CONFIG['HEAD_TIMEOUT']):
    try:
        resp = requests.head(url, headers={'User-Agent': CONFIG['USER_AGENT']}, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False

def get_best_preview_url(candidate_urls):
    for url in candidate_urls:
        if not url:
            continue
        if url in preview_error_cache:
            continue
        if check_url_accessible(url):
            return url
    for url in candidate_urls:
        if url:
            return url
    return None

def fetch_gelbooru_post(identifier, log_callback=None, lang_dict=None):
    cache_key = ('gelbooru', identifier)
    if cache_key in cache:
        return cache[cache_key]

    url = "https://gelbooru.com/index.php"
    params = {
        'page': 'dapi',
        's': 'post',
        'q': 'index',
        'json': '1',
        'id': identifier
    }
    tags = None
    file_url = None
    sample_url = None
    preview_url = None
    md5 = None

    try:
        resp = http_session.get(url, params=params, timeout=10)
        data = resp.json()
        if isinstance(data, dict) and 'post' in data:
            posts = data['post']
        elif isinstance(data, list):
            posts = data
        else:
            posts = []
        if posts:
            post = posts[0]
            raw_tags = post.get('tags', '').split()
            tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
            if tags:
                tags = filter_gelbooru_tags(tags)
            file_url = post.get('file_url')
            if file_url and file_url.startswith('//'):
                file_url = 'https:' + file_url
            sample_url = post.get('sample_url')
            if sample_url and sample_url.startswith('//'):
                sample_url = 'https:' + sample_url
            candidate_urls = [sample_url, file_url]
            preview_url = get_best_preview_url(candidate_urls)
            if not preview_url:
                preview_url = file_url
            md5 = post.get('md5')
            if tags:
                if log_callback and lang_dict:
                    log_callback(lang_dict['gelbooru_parsed_tags'].format(len(tags)))
                result = {
                    'tags': tags,
                    'file_url': file_url,
                    'sample_url': sample_url,
                    'preview_url': preview_url,
                    'md5': md5
                }
                cache[cache_key] = result
                return result
    except Exception:
        pass

    html_url = f"https://gelbooru.com/index.php?page=post&s=view&id={identifier}"
    try:
        html_resp = http_session.get(html_url, timeout=10)
        html = html_resp.text

        og_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if og_match:
            file_url = og_match.group(1)
            if file_url.startswith('//'):
                file_url = 'https:' + file_url
            md5_match = re.search(r'/([a-f0-9]{32})\.[a-z]+', file_url, re.I)
            md5 = md5_match.group(1) if md5_match else None
            preview_url = file_url

        meta_keywords = re.search(r'<meta name="keywords" content="([^"]+)"', html, re.I)
        if meta_keywords:
            keywords = meta_keywords.group(1)
            raw_tags = [t.strip() for t in keywords.split(',') if t.strip()]
            filtered_keywords = filter_gelbooru_tags(raw_tags)
            tags = [clean_tag(t) for t in filtered_keywords] if filtered_keywords else None
            if tags and log_callback and lang_dict:
                log_callback(lang_dict['gelbooru_parsed_tags'].format(len(tags)))
                result = {
                    'tags': tags,
                    'file_url': file_url,
                    'sample_url': sample_url,
                    'preview_url': preview_url,
                    'md5': md5
                }
                cache[cache_key] = result
                return result

        if not tags:
            tag_list_section = re.search(r'<div[^>]*(?:id="tag-list"|class="[^"]*tag-list[^"]*")[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
            if tag_list_section:
                tag_section = tag_list_section.group(1)
                tag_matches = re.findall(r'<a[^>]+href="[^"]*"[^>]*>([^<]+)</a>', tag_section)
                if tag_matches:
                    raw_tags = [t.strip() for t in tag_matches if t.strip()]
                    filtered_tags = filter_gelbooru_tags(raw_tags)
                    if filtered_tags:
                        tags = [clean_tag(t) for t in filtered_tags]
                        if tags and log_callback and lang_dict:
                            log_callback(lang_dict['gelbooru_parsed_tags'].format(len(tags)))
                            result = {
                                'tags': tags,
                                'file_url': file_url,
                                'sample_url': sample_url,
                                'preview_url': preview_url,
                                'md5': md5
                            }
                            cache[cache_key] = result
                            return result

        result = {
            'tags': tags,
            'file_url': file_url,
            'sample_url': sample_url,
            'preview_url': preview_url,
            'md5': md5
        }
        cache[cache_key] = result
        return result
    except Exception:
        result = {
            'tags': None,
            'file_url': None,
            'sample_url': None,
            'preview_url': None,
            'md5': None
        }
        cache[cache_key] = result
        return result

def get_image_info_from_source(domain, identifier):
    if 'yande.re' in domain:
        post = fetch_yandere_post(identifier)
        if post:
            return {'file_url': post['file_url'], 'preview_url': post['preview_url'], 'md5': post['md5']}
    elif 'gelbooru.com' in domain:
        post = fetch_gelbooru_post(identifier)
        if post:
            return {'file_url': post['file_url'], 'preview_url': post['preview_url'], 'md5': post['md5']}
    elif 'konachan.com' in domain or 'konachan.net' in domain:
        post = fetch_konachan_post(domain, identifier)
        if post:
            return {'file_url': post['file_url'], 'preview_url': post['preview_url'], 'md5': post['md5']}
    return {'file_url': None, 'preview_url': None, 'md5': None}

def search_on_gelbooru_by_md5(md5):
    url = "https://gelbooru.com/index.php"
    params = {
        'page': 'dapi',
        's': 'post',
        'q': 'index',
        'json': '1',
        'tags': f'md5:{md5}'
    }
    try:
        resp = http_session.get(url, params=params, timeout=10)
        data = resp.json()
        if isinstance(data, dict) and 'post' in data:
            posts = data['post']
        elif isinstance(data, list):
            posts = data
        else:
            posts = []
        if posts:
            return posts[0].get('id')
    except Exception:
        pass
    return None

def get_image_hash(image_url, hash_size=8):
    try:
        headers = {'User-Agent': CONFIG['USER_AGENT']}
        if 'gelbooru.com' in image_url:
            headers['Referer'] = 'https://gelbooru.com/'
        elif 'cdn.donmai.us' in image_url:
            headers['Referer'] = 'https://danbooru.donmai.us/'
        resp = http_session.get(image_url, headers=headers, timeout=10)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        img = img.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        try:
            pixels = list(img.get_flattened_data())
        except AttributeError:
            pixels = list(img.getdata())
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                left = pixels[row * (hash_size + 1) + col]
                right = pixels[row * (hash_size + 1) + col + 1]
                diff.append(left > right)
        hash_int = 0
        for i, bit in enumerate(diff):
            if bit:
                hash_int |= 1 << i
        return hash_int
    except Exception:
        return None

def compare_images_by_hash(url1, url2, hash_size=8, threshold=5):
    hash1 = get_image_hash(url1, hash_size)
    hash2 = get_image_hash(url2, hash_size)
    if hash1 is None or hash2 is None:
        return False
    distance = bin(hash1 ^ hash2).count('1')
    return distance <= threshold

def save_tags_to_file(tags, source_url, save_folder, danbooru_url=None, gelbooru_url=None, domain_slug=None, post_id=None):
    if not domain_slug or not post_id:
        domain, ident = extract_identifier(source_url)
        if domain and ident:
            domain_slug = domain.replace('.', '_')
            post_id = ident.replace(':', '_')
        else:
            domain_slug = 'unknown'
            post_id = 'unknown'

    filename = f"tags_{domain_slug}_{post_id}_clean.txt"
    full_path = os.path.join(save_folder, filename)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(", ".join(tags))
        f.write(f"\n\nВсего тегов: {len(tags)}")
        f.write(f"\n\nSource: {source_url}")
        if danbooru_url and danbooru_url != source_url:
            f.write(f"\nDanbooru: {danbooru_url}")
        if gelbooru_url and gelbooru_url != source_url:
            f.write(f"\nGelbooru: {gelbooru_url}")
    return full_path

def merge_all_tags(save_folder, log_callback, lang_dict):
    pattern = os.path.join(save_folder, "tags_*_clean.txt")
    tag_files = glob.glob(pattern)

    if not tag_files:
        log_callback(lang_dict['merge_no_files'])
        return

    log_callback(lang_dict['merge_start'])
    output_filename = os.path.join(save_folder, "all_tags_combined.txt")

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for filename in sorted(tag_files):
            try:
                with open(filename, 'r', encoding='utf-8') as infile:
                    first_line = infile.readline().strip()
                    if first_line:
                        outfile.write(first_line + '\n\n')
                        log_callback(f"  + {os.path.basename(filename)}")
            except Exception as e:
                log_callback(f"  ❌ Error with {os.path.basename(filename)}: {e}")

    log_callback(lang_dict['merge_done'].format(os.path.basename(output_filename)))

class ExtractionThread(QThread):
    log_signal = Signal(str)
    preview_signal = Signal(str)
    finished_signal = Signal()
    ask_source_signal = Signal(list, str, str, str)

    def __init__(self, client, url, save_folder, lang_dict):
        super().__init__()
        self.client = client
        self.url = url
        self.save_folder = save_folder
        self.lang_dict = lang_dict
        self.main_window = None
        self.saucenao_api_key = None

    def run(self):
        try:
            self._extract()
        except Exception as e:
            self.log_signal.emit(self.lang_dict['error_exception'].format(str(e)))
        finally:
            self.finished_signal.emit()

    def _extract(self):
        domain, identifier = extract_identifier(self.url)
        if not domain or not identifier:
            self.log_signal.emit(self.lang_dict['error_extract'])
            return

        file_id = identifier.replace(':', '_')
        domain_slug = domain.replace('.', '_')

        if 'danbooru.donmai.us' in domain:
            if not self.client:
                self.log_signal.emit("❌ Danbooru client not initialized. Check settings.")
                return
            self.log_signal.emit(self.lang_dict['direct_request'].format(domain))
            post_data = self.client.get_post(identifier)
            if not post_data or not post_data['tags']:
                self.log_signal.emit(self.lang_dict['error_no_tags'])
                return
            tags = post_data['tags']
            preview_url = post_data.get('sample_url') or post_data.get('preview_url') or post_data.get('file_url')
            if preview_url:
                self.preview_signal.emit(preview_url)
            saved = save_tags_to_file(tags, self.url, self.save_folder,
                                      domain_slug=domain_slug, post_id=file_id)
            self.log_signal.emit(self.lang_dict['saved_tags'].format(len(tags), os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved

        elif 'aibooru' in domain:
            self.log_signal.emit(self.lang_dict['direct_request'].format(domain))
            base_url = f"https://{domain}"
            post_data = fetch_aibooru_post(identifier, base_url=base_url)
            if not post_data or not post_data['tags']:
                self.log_signal.emit(self.lang_dict['error_no_tags'])
                return
            tags = post_data['tags']
            preview_url = post_data.get('sample_url') or post_data.get('preview_url') or post_data.get('file_url')
            if preview_url:
                self.preview_signal.emit(preview_url)
            saved = save_tags_to_file(tags, self.url, self.save_folder,
                                      domain_slug=domain_slug, post_id=file_id)
            self.log_signal.emit(self.lang_dict['saved_tags'].format(len(tags), os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved

        elif 'konachan.com' in domain or 'konachan.net' in domain:
            self._handle_generic_source(domain, identifier, file_id, domain_slug, 'Konachan')

        elif 'yande.re' in domain:
            self._handle_generic_source(domain, identifier, file_id, domain_slug, 'Yande.re')

        elif 'gelbooru.com' in domain:
            self.log_signal.emit(self.lang_dict['source_info'].format(domain, identifier))
            post_data = fetch_gelbooru_post(identifier, log_callback=self.log_signal.emit, lang_dict=self.lang_dict)
            if not post_data or not post_data['tags']:
                self.log_signal.emit(self.lang_dict['error_no_tags'])
                return
            tags = post_data['tags']
            preview_url = post_data.get('preview_url')
            if preview_url:
                self.preview_signal.emit(preview_url)
            saved = save_tags_to_file(tags, self.url, self.save_folder,
                                      domain_slug=domain_slug, post_id=file_id)
            self.log_signal.emit(self.lang_dict['saved_from_source'].format(len(tags), 'Gelbooru', os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved

        else:
            self.log_signal.emit(self.lang_dict['unsupported_domain'].format(domain))

    def _handle_generic_source(self, domain, identifier, file_id, domain_slug, source_name):
        self.log_signal.emit(self.lang_dict['source_info'].format(domain, identifier))
        info = get_image_info_from_source(domain, identifier)
        source_image_url = info.get('preview_url') or info.get('file_url')
        md5 = info.get('md5')
        file_url = info.get('file_url')
        source_tags = None

        if source_name == 'Konachan':
            direct_post = fetch_konachan_post(domain, identifier)
        else:
            direct_post = fetch_yandere_post(identifier)
        if direct_post:
            source_tags = direct_post['tags']
            if not source_image_url:
                source_image_url = direct_post.get('preview_url') or direct_post.get('file_url')

        db_post = None
        danbooru_image_url = None

        if md5 and self.client:
            self.log_signal.emit(self.lang_dict['search_md5'])
            db_post = self.client.search_by_md5(md5)
            if db_post:
                self.log_signal.emit(self.lang_dict['found_md5'])
                danbooru_image_url = db_post.get('sample_url') or db_post.get('preview_url') or db_post.get('file_url')
                db_tags = db_post.get('tags')
                if source_image_url and danbooru_image_url and db_post.get('md5') != md5:
                    self.log_signal.emit(self.lang_dict['comparing_images'])
                    if compare_images_by_hash(source_image_url, danbooru_image_url):
                        self.log_signal.emit(self.lang_dict['images_match'].format('?'))
                        self._save_from_single_source(('danbooru', db_tags, db_post['id'], danbooru_image_url), file_id, domain_slug, source_name)
                        return
                    else:
                        self.log_signal.emit(self.lang_dict['images_differ'])
                        sources = [('danbooru', db_tags, db_post['id'], danbooru_image_url)]
                        if source_tags:
                            sources.append(('source', source_tags, source_name, source_image_url))
                        self.ask_source_signal.emit(sources, self.url, domain_slug, file_id)
                        return
                else:
                    self._save_from_single_source(('danbooru', db_tags, db_post['id'], danbooru_image_url), file_id, domain_slug, source_name)
                    return

        if file_url:
            try:
                self.log_signal.emit(self.lang_dict['searching_engines'])
                img_resp = http_session.get(file_url, timeout=CONFIG['TIMEOUT'])
                if img_resp.status_code == 200:
                    image_data = img_resp.content
                    danbooru_id = parallel_search(image_data, self.saucenao_api_key)
                    if danbooru_id:
                        self.log_signal.emit("✅ Найдено через SauceNAO/Ascii2D")
                        db_post = self.client.get_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('sample_url') or db_post.get('preview_url') or db_post.get('file_url')
                            db_tags = db_post.get('tags')
                            sources = [('danbooru', db_tags, db_post['id'], danbooru_image_url)]
                            if source_tags:
                                sources.append(('source', source_tags, source_name, source_image_url))
                            if source_image_url and danbooru_image_url:
                                self.log_signal.emit(self.lang_dict['comparing_images'])
                                if compare_images_by_hash(source_image_url, danbooru_image_url):
                                    self.log_signal.emit(self.lang_dict['images_match'].format('?'))
                                    sources = [('danbooru', db_tags, db_post['id'], danbooru_image_url)]
                                else:
                                    self.log_signal.emit(self.lang_dict['images_differ'])
                            if len(sources) == 1:
                                self._save_from_single_source(sources[0], file_id, domain_slug, source_name)
                            else:
                                self.ask_source_signal.emit(sources, self.url, domain_slug, file_id)
                            return
            except Exception:
                pass

        if (not db_post or not db_post.get('tags')) and file_url:
            self.log_signal.emit(self.lang_dict['search_gelbooru'])
            gelbooru_id = search_on_gelbooru_by_md5(md5) if md5 else None
            if gelbooru_id:
                self.log_signal.emit(self.lang_dict['found_gelbooru'])
                gelbooru_post = fetch_gelbooru_post(gelbooru_id, log_callback=self.log_signal.emit, lang_dict=self.lang_dict)
                if gelbooru_post and gelbooru_post.get('tags'):
                    gelbooru_image_url = gelbooru_post.get('preview_url') or gelbooru_post.get('file_url')
                    sources = [('gelbooru', gelbooru_post['tags'], gelbooru_id, gelbooru_image_url)]
                    if source_tags:
                        sources.append(('source', source_tags, source_name, source_image_url))
                    if len(sources) == 1:
                        self._save_from_single_source(sources[0], file_id, domain_slug, source_name)
                    else:
                        self.ask_source_signal.emit(sources, self.url, domain_slug, file_id)
                    return

        if source_tags:
            saved = save_tags_to_file(source_tags, self.url, self.save_folder,
                                      domain_slug=domain_slug, post_id=file_id)
            if source_image_url:
                self.preview_signal.emit(source_image_url)
            self.log_signal.emit(self.lang_dict['saved_from_source'].format(len(source_tags), source_name, os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved
        else:
            self.log_signal.emit(self.lang_dict['error_no_tags'])

    def _save_from_single_source(self, src, file_id, domain_slug, fallback_name):
        src_type, tags, ident, img_url = src
        danbooru_url = None
        gelbooru_url = None
        if img_url:
            self.preview_signal.emit(img_url)
        if src_type == 'danbooru':
            danbooru_url = self.client.post_url(ident)
            saved = save_tags_to_file(tags, self.url, self.save_folder,
                                      danbooru_url=danbooru_url,
                                      domain_slug=domain_slug, post_id=file_id)
            self.log_signal.emit(self.lang_dict['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved
        elif src_type == 'gelbooru':
            gelbooru_url = f"https://gelbooru.com/index.php?page=post&s=view&id={ident}"
            saved = save_tags_to_file(tags, self.url, self.save_folder,
                                      gelbooru_url=gelbooru_url,
                                      domain_slug=domain_slug, post_id=file_id)
            self.log_signal.emit(self.lang_dict['saved_from_gelbooru'].format(len(tags), os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved
        else:
            saved = save_tags_to_file(tags, self.url, self.save_folder,
                                      domain_slug=domain_slug, post_id=file_id)
            self.log_signal.emit(self.lang_dict['saved_from_source'].format(len(tags), fallback_name, os.path.basename(saved)))
            if self.main_window:
                self.main_window.last_saved_file_path = saved

class MergeThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, save_folder, lang_dict):
        super().__init__()
        self.save_folder = save_folder
        self.lang_dict = lang_dict

    def run(self):
        try:
            merge_all_tags(self.save_folder, self.log_signal.emit, self.lang_dict)
        except Exception as e:
            self.log_signal.emit(self.lang_dict['error_exception'].format(str(e)))
        finally:
            self.finished_signal.emit()

class ImageLoader(QThread):
    image_ready = Signal(str, QByteArray)
    error_occurred = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._url = None
        self._running = True
        self._mutex = QMutex()
        self._cond = QWaitCondition()
        self._cancelled = False

    def load(self, url: str):
        self._mutex.lock()
        self._url = url
        self._cancelled = False
        self._mutex.unlock()
        if not self.isRunning():
            self.start()
        else:
            self._cond.wakeAll()

    def cancel(self):
        self._mutex.lock()
        self._cancelled = True
        self._mutex.unlock()
        self._cond.wakeAll()

    def stop(self):
        self._running = False
        self._cond.wakeAll()
        self.wait(3000)

    def run(self):
        while self._running:
            self._mutex.lock()
            url = self._url
            self._mutex.unlock()
            if not url:
                self._mutex.lock()
                self._cond.wait(self._mutex)
                self._mutex.unlock()
                continue

            if url in preview_cache:
                self.image_ready.emit(url, preview_cache[url])
                self._mutex.lock()
                self._url = None
                self._mutex.unlock()
                continue

            if url in preview_error_cache:
                self.error_occurred.emit(url, "URL ранее дал ошибку (закешировано)")
                self._mutex.lock()
                self._url = None
                self._mutex.unlock()
                continue

            try:
                headers = {'User-Agent': CONFIG['USER_AGENT']}
                if 'gelbooru.com' in url:
                    headers['Referer'] = 'https://gelbooru.com/'
                elif 'cdn.donmai.us' in url:
                    headers['Referer'] = 'https://danbooru.donmai.us/'
                elif 'aibooru' in url:
                    headers['Referer'] = 'https://aibooru.online/'

                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=(CONFIG['PREVIEW_CONNECT_TIMEOUT'], CONFIG['PREVIEW_READ_TIMEOUT'])
                )
                resp.raise_for_status()
                data = resp.content

                if len(data) > CONFIG['MAX_IMAGE_BYTES']:
                    self.error_occurred.emit(url, f"Слишком большой ответ ({len(data) / 1024 / 1024:.1f} МБ)")
                    preview_error_cache.add(url)
                    self._mutex.lock()
                    self._url = None
                    self._mutex.unlock()
                    continue

                self._mutex.lock()
                cancelled = self._cancelled
                self._mutex.unlock()
                if cancelled:
                    continue

                if len(preview_cache) >= CONFIG['PREVIEW_CACHE_SIZE']:
                    first_key = next(iter(preview_cache))
                    del preview_cache[first_key]
                preview_cache[url] = QByteArray(data)

                self.image_ready.emit(url, QByteArray(data))

            except Exception as e:
                if self._running:
                    preview_error_cache.add(url)
                    self.error_occurred.emit(url, str(e))

            self._mutex.lock()
            self._url = None
            self._cancelled = False
            self._mutex.unlock()

class SourceChoiceDialog(QDialog):
    def __init__(self, sources, lang_dict, parent=None):
        super().__init__(parent)
        self.lang_dict = lang_dict
        self.sources = sources
        self.selected = None
        self.setWindowTitle(lang_dict['choose_source_title'])
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel(self.lang_dict['choose_source_msg'])
        label.setWordWrap(True)
        layout.addWidget(label)

        grid = QGridLayout()
        self.thumbs = []
        row = 0
        col = 0
        for src in self.sources:
            src_type, tags, ident, img_url = src
            frame = QWidget()
            vbox = QVBoxLayout(frame)
            thumb = QLabel()
            thumb.setFixedSize(150, 150)
            thumb.setAlignment(Qt.AlignCenter)
            thumb.setStyleSheet("border: 1px solid gray;")
            vbox.addWidget(thumb)
            btn_text = ""
            if src_type == 'danbooru':
                btn_text = self.lang_dict['btn_danbooru'].format(len(tags))
            elif src_type == 'gelbooru':
                btn_text = self.lang_dict['btn_gelbooru'].format(len(tags))
            else:
                btn_text = self.lang_dict['btn_source'].format(ident.capitalize(), len(tags))
            btn = QPushButton(btn_text)
            btn.clicked.connect(lambda checked, s=src: self._on_choose(s))
            vbox.addWidget(btn)
            grid.addWidget(frame, row, col)
            if img_url:
                loader = ImageLoader()
                loader.image_ready.connect(lambda url, data, lbl=thumb: self._set_thumb(lbl, data))
                loader.error_occurred.connect(lambda url, err, lbl=thumb: lbl.setText("⚠️"))
                loader.load(img_url)
                self.thumbs.append((thumb, img_url, loader))
            else:
                thumb.setText("❌")
            col += 1
            if col >= 3:
                col = 0
                row += 1

        layout.addLayout(grid)

        cancel_btn = QPushButton(self.lang_dict['btn_cancel'])
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def _set_thumb(self, label, data):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            scaled = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
        else:
            label.setText("❌")

    def _on_choose(self, src):
        self.selected = src
        self.accept()

    def reject(self):
        for _, _, loader in self.thumbs:
            loader.stop()
        super().reject()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tag Extractor")
        self.resize(1000, 800)

        self.danbooru_client = None
        self.save_folder = tempfile.gettempdir()
        self.current_lang = 'ru'
        self.lang_dict = LANG[self.current_lang]
        self.extract_thread = None
        self.merge_thread = None
        self.image_loader = None
        self.current_pixmap = None
        self.last_preview_size = QSize(0, 0)
        self._pending_preview_url = None
        self.last_saved_file_path = None
        self.saucenao_api_key = ""

        self._init_ui()
        self._apply_auth()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(self.lang_dict['lang_label'] + ":"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['ru', 'en'])
        self.lang_combo.setCurrentText(self.current_lang)
        self.lang_combo.currentTextChanged.connect(self._on_lang_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        main_layout.addLayout(lang_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.main_tab = QWidget()
        self.tabs.addTab(self.main_tab, self.lang_dict['tab_main'])
        self._build_main_tab()

        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, self.lang_dict['tab_settings'])
        self._build_settings_tab()

        self.status_bar = self.statusBar()
        self.status_label = QLabel(self.lang_dict['status_ready'])
        self.status_bar.addWidget(self.status_label)

        self._update_texts()

    def _build_main_tab(self):
        layout = QVBoxLayout(self.main_tab)

        top = QHBoxLayout()
        self.url_label = QLabel(self.lang_dict['url_label'])
        top.addWidget(self.url_label)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://...")
        self.url_edit.returnPressed.connect(self.process_url)
        top.addWidget(self.url_edit)

        self.process_btn = QPushButton(self.lang_dict['process_btn'])
        self.process_btn.clicked.connect(self.process_url)
        top.addWidget(self.process_btn)

        self.merge_btn = QPushButton(self.lang_dict['merge_btn'])
        self.merge_btn.clicked.connect(self.merge_tags)
        top.addWidget(self.merge_btn)

        self.clear_log_btn = QPushButton(self.lang_dict['clear_btn'])
        self.clear_log_btn.clicked.connect(self.clear_log)
        top.addWidget(self.clear_log_btn)

        self.open_file_btn = QPushButton(self.lang_dict['open_file_btn'])
        self.open_file_btn.clicked.connect(self.open_saved_file)
        top.addWidget(self.open_file_btn)

        self.exit_btn = QPushButton(self.lang_dict['exit_btn'])
        self.exit_btn.clicked.connect(self.close)
        top.addWidget(self.exit_btn)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        splitter.addWidget(self.log_text)

        self.preview_label = QLabel(self.lang_dict['preview_not_available'])
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #555; background-color: #333; color: white;")
        self.preview_label.setMinimumWidth(300)
        self.preview_label.mousePressEvent = self._on_preview_click
        splitter.addWidget(self.preview_label)

        layout.addWidget(splitter, stretch=1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def _build_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)

        self.folder_group = QGroupBox(self.lang_dict['settings_folder'])
        folder_layout = QHBoxLayout(self.folder_group)
        self.folder_edit = QLineEdit(self.save_folder)
        self.folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.folder_edit)
        self.folder_btn = QPushButton(self.lang_dict['folder_btn'])
        self.folder_btn.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_btn)
        layout.addWidget(self.folder_group)

        self.auth_group = QGroupBox("Danbooru")
        auth_layout = QVBoxLayout(self.auth_group)
        form = QHBoxLayout()
        self.login_label = QLabel(self.lang_dict['settings_login'])
        form.addWidget(self.login_label)
        self.login_edit = QLineEdit()
        form.addWidget(self.login_edit)
        self.key_label = QLabel(self.lang_dict['settings_api_key'])
        form.addWidget(self.key_label)
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        form.addWidget(self.key_edit)
        auth_layout.addLayout(form)

        self.apply_btn = QPushButton(self.lang_dict['settings_apply'])
        self.apply_btn.clicked.connect(self._apply_auth)
        auth_layout.addWidget(self.apply_btn)
        layout.addWidget(self.auth_group)

        self.saucenao_group = QGroupBox("SauceNAO")
        saucenao_layout = QHBoxLayout(self.saucenao_group)
        self.saucenao_label = QLabel(self.lang_dict['settings_saucenao'])
        saucenao_layout.addWidget(self.saucenao_label)
        self.saucenao_edit = QLineEdit()
        self.saucenao_edit.setEchoMode(QLineEdit.Password)
        saucenao_layout.addWidget(self.saucenao_edit)
        self.apply_saucenao_btn = QPushButton(self.lang_dict['settings_apply'])
        self.apply_saucenao_btn.clicked.connect(self._apply_saucenao)
        saucenao_layout.addWidget(self.apply_saucenao_btn)
        layout.addWidget(self.saucenao_group)

        info_label = QLabel("<a href='https://saucenao.com/user.php'>Получить бесплатный API-ключ</a>")
        info_label.setOpenExternalLinks(True)
        layout.addWidget(info_label)

        layout.addStretch()

    def _apply_saucenao(self):
        self.saucenao_api_key = self.saucenao_edit.text().strip()
        self.log("🔑 Ключ SauceNAO обновлён")

    def _update_texts(self):
        self.tabs.setTabText(0, self.lang_dict['tab_main'])
        self.tabs.setTabText(1, self.lang_dict['tab_settings'])

        self.url_label.setText(self.lang_dict['url_label'])
        self.process_btn.setText(self.lang_dict['process_btn'])
        self.merge_btn.setText(self.lang_dict['merge_btn'])
        self.clear_log_btn.setText(self.lang_dict['clear_btn'])
        self.open_file_btn.setText(self.lang_dict['open_file_btn'])
        self.exit_btn.setText(self.lang_dict['exit_btn'])

        if not self.current_pixmap:
            self.preview_label.setText(self.lang_dict['preview_not_available'])
        self.status_label.setText(self.lang_dict['status_ready'])

        self.folder_group.setTitle(self.lang_dict['settings_folder'])
        self.folder_btn.setText(self.lang_dict['folder_btn'])

        self.login_label.setText(self.lang_dict['settings_login'])
        self.key_label.setText(self.lang_dict['settings_api_key'])
        self.apply_btn.setText(self.lang_dict['settings_apply'])

        self.saucenao_label.setText(self.lang_dict['settings_saucenao'])
        self.apply_saucenao_btn.setText(self.lang_dict['settings_apply'])

    def _on_lang_changed(self, lang):
        self.current_lang = lang
        self.lang_dict = LANG[lang]
        self._update_texts()

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.lang_dict['select_folder'], self.save_folder)
        if folder:
            self.save_folder = folder
            self.folder_edit.setText(folder)

    def _apply_auth(self):
        login = self.login_edit.text().strip()
        api_key = self.key_edit.text().strip()
        self.danbooru_client = DanbooruClient(login if login else None,
                                              api_key if api_key else None)
        if login and api_key:
            self.log(self.lang_dict['auth_applied'])
        else:
            self.log(self.lang_dict['auth_empty'])

    def log(self, message):
        self.log_text.append(message)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        self.log_text.clear()

    def _set_preview(self, url):
        if not url:
            return
        if url in preview_error_cache:
            preview_error_cache.discard(url)
        if self.image_loader:
            self.image_loader.cancel()
            self.image_loader.stop()
            self.image_loader = None
        self.preview_label.setText(self.lang_dict['loading'])
        self.current_pixmap = None
        self._pending_preview_url = url

        self.image_loader = ImageLoader()
        self.image_loader.image_ready.connect(self._on_image_ready)
        self.image_loader.error_occurred.connect(self._on_image_error)
        self.image_loader.load(url)

    def _on_image_ready(self, url, data: QByteArray):
        if url != self._pending_preview_url:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            if pixmap.width() > CONFIG['MAX_PREVIEW_WIDTH'] or pixmap.height() > CONFIG['MAX_PREVIEW_HEIGHT']:
                pixmap = pixmap.scaled(
                    CONFIG['MAX_PREVIEW_WIDTH'],
                    CONFIG['MAX_PREVIEW_HEIGHT'],
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            self.current_pixmap = pixmap
            self._scale_preview(force=True)
        else:
            self.preview_label.setText(self.lang_dict['preview_not_available'])
            self.log(self.lang_dict['preview_fail'])
            self._pending_preview_url = None

    def _on_image_error(self, url, error_msg):
        if url == self._pending_preview_url:
            self.preview_label.setText(self.lang_dict['preview_error'].format(error_msg))
            self.current_pixmap = None
            self.log(f"⚠️ Предпросмотр ошибка: {error_msg}")

    def _on_preview_click(self, event: QMouseEvent):
        if self._pending_preview_url:
            if self._pending_preview_url in preview_error_cache:
                preview_error_cache.discard(self._pending_preview_url)
                self.log("🔄 Кеш ошибок сброшен для этого URL, повторная попытка")
            self._set_preview(self._pending_preview_url)
        else:
            self.log("Нет URL для повторной загрузки")

    def _scale_preview(self, force=False):
        if self.current_pixmap and not self.current_pixmap.isNull():
            if force:
                self.last_preview_size = QSize(0, 0)
            label_size = self.preview_label.size()
            if force or (abs(label_size.width() - self.last_preview_size.width()) > 10 or
                         abs(label_size.height() - self.last_preview_size.height()) > 10):
                scaled = self.current_pixmap.scaled(
                    label_size - QSize(10, 10),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)
                self.last_preview_size = label_size

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_preview()

    def open_saved_file(self):
        if self.last_saved_file_path and os.path.exists(self.last_saved_file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_saved_file_path))
            self.log(self.lang_dict['file_opened'].format(os.path.basename(self.last_saved_file_path)))
        else:
            self.log(self.lang_dict['no_file_to_open'])

    def process_url(self):
        url = self.url_edit.text().strip()
        if not url:
            self.log(self.lang_dict['no_url'])
            return
        if not self.danbooru_client:
            self.log("❌ Сначала примените настройки авторизации")
            return

        self.url_edit.clear()
        self.process_btn.setEnabled(False)
        self.progress.setVisible(True)

        if self.extract_thread and self.extract_thread.isRunning():
            self.extract_thread.quit()
            self.extract_thread.wait(3000)

        self.extract_thread = ExtractionThread(self.danbooru_client, url, self.save_folder, self.lang_dict)
        self.extract_thread.main_window = self
        self.extract_thread.saucenao_api_key = self.saucenao_api_key
        self.extract_thread.log_signal.connect(self.log)
        self.extract_thread.preview_signal.connect(self._set_preview)
        self.extract_thread.finished_signal.connect(self._on_extract_finished)
        self.extract_thread.ask_source_signal.connect(self._handle_source_choice)
        self.extract_thread.start()

    def _on_extract_finished(self):
        self.progress.setVisible(False)
        self.process_btn.setEnabled(True)

    def _handle_source_choice(self, sources, url, domain_slug, file_id):
        dialog = SourceChoiceDialog(sources, self.lang_dict, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected:
            src_type, tags, ident, img_url = dialog.selected
            if img_url:
                self._set_preview(img_url)
            danbooru_url = None
            gelbooru_url = None
            if src_type == 'danbooru':
                danbooru_url = self.danbooru_client.post_url(ident)
                saved = save_tags_to_file(tags, url, self.save_folder,
                                          danbooru_url=danbooru_url,
                                          domain_slug=domain_slug, post_id=file_id)
                self.last_saved_file_path = saved
                self.log(self.lang_dict['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
            elif src_type == 'gelbooru':
                gelbooru_url = f"https://gelbooru.com/index.php?page=post&s=view&id={ident}"
                saved = save_tags_to_file(tags, url, self.save_folder,
                                          gelbooru_url=gelbooru_url,
                                          domain_slug=domain_slug, post_id=file_id)
                self.last_saved_file_path = saved
                self.log(self.lang_dict['saved_from_gelbooru'].format(len(tags), os.path.basename(saved)))
            else:
                saved = save_tags_to_file(tags, url, self.save_folder,
                                          domain_slug=domain_slug, post_id=file_id)
                self.last_saved_file_path = saved
                self.log(self.lang_dict['saved_from_source'].format(len(tags), 'source', os.path.basename(saved)))

    def merge_tags(self):
        self.merge_btn.setEnabled(False)
        self.progress.setVisible(True)

        if self.merge_thread and self.merge_thread.isRunning():
            self.merge_thread.quit()
            self.merge_thread.wait(3000)

        self.merge_thread = MergeThread(self.save_folder, self.lang_dict)
        self.merge_thread.log_signal.connect(self.log)
        self.merge_thread.finished_signal.connect(self._on_merge_finished)
        self.merge_thread.start()

    def _on_merge_finished(self):
        self.progress.setVisible(False)
        self.merge_btn.setEnabled(True)

    def closeEvent(self, event):
        if self.extract_thread and self.extract_thread.isRunning():
            self.extract_thread.quit()
            self.extract_thread.wait(3000)
        if self.merge_thread and self.merge_thread.isRunning():
            self.merge_thread.quit()
            self.merge_thread.wait(3000)
        if self.image_loader:
            self.image_loader.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())