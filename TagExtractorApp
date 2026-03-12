import os
import re
import glob
import threading
import requests
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import io
import locale
import tempfile

LANG = {
    'ru': {
        'title': 'Tag Extractor',
        'lang_label': 'Язык',
        'url_label': 'URL:',
        'process_btn': 'Извлечь теги',
        'merge_btn': 'Объединить все теги',
        'folder_btn': 'Папка сохранения',
        'clear_btn': 'Очистить лог',
        'exit_btn': 'Выход',
        'status_ready': 'Готов к работе',
        'processing': 'Обработка...',
        'success': '✅ Готово',
        'error': '❌ Ошибка',
        'no_url': 'Введите ссылку',
        'select_folder': 'Выберите папку для сохранения',
        'current_folder': 'Текущая папка:',
        'merge_start': 'Начинаю объединение файлов...',
        'merge_done': 'Объединение завершено. Файл: {}',
        'merge_no_files': 'Не найдено файлов с тегами.',
        'log_placeholder': 'Здесь будут появляться сообщения...',
        'preview_not_available': 'Предпросмотр недоступен',
        'paste_btn': 'Вставить',
        'clear_btn_entry': 'Очистить',
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
        'search_iqdb': '🔎 Ищу через IQDB...',
        'found_iqdb': '✅ Найдено через IQDB',
        'danbooru_post': '📌 Пост на Danbooru: ID {}',
        'saved_from_danbooru': '✅ Сохранено {} тегов с Danbooru в {}',
        'trying_direct': '⚠️ Не найдено на Danbooru, пробую получить теги напрямую с {}',
        'saved_from_source': '✅ Сохранено {} тегов с {} в {}',
        'failed_all': '❌ Не удалось получить теги ни с Danbooru, ни с {}',
        'unsupported_domain': '❌ Домен {} не поддерживается',
        'error_exception': '❌ {}',
        'gelbooru_no_tags_danbooru_search': '⚠️ Не удалось получить теги напрямую с Gelbooru, ищу через Danbooru...',
        'gelbooru_fallback': '⚠️ Не найдено на Danbooru, использую теги с Gelbooru (если есть)',
        'no_tags_gelbooru': '❌ Не удалось получить теги ни с Gelbooru, ни через Danbooru',
        'gelbooru_parsing_html': '🔎 Парсинг HTML страницы Gelbooru для получения тегов...',
        'gelbooru_parsed_tags': '✅ Извлечено {} тегов из HTML',
        'md5_mismatch': '⚠️ IQDB вернул пост, но MD5 не совпадает. Игнорирую Danbooru.',
        'no_md5_use_danbooru': '⚠️ Нет MD5 для проверки, но использую Danbooru по IQDB.',
        'md5_mismatch_but_use': '⚠️ IQDB вернул пост, MD5 не совпадает, но использую Danbooru (пост найден).',
        'choose_source_title': 'Выбор источника тегов',
        'choose_source_msg': 'Найдены теги из нескольких источников. Какой использовать?',
        'btn_danbooru': 'Danbooru ({} тегов)',
        'btn_gelbooru': 'Gelbooru ({} тегов)',
        'btn_source': '{} ({} тегов)',
        'btn_cancel': 'Отмена (использовать исходный сайт)',
        'search_gelbooru': '🔎 Ищу на Gelbooru...',
        'found_gelbooru': '✅ Найдено на Gelbooru',
        'gelbooru_post': '📌 Пост на Gelbooru: ID {}',
        'saved_from_gelbooru': '✅ Сохранено {} тегов с Gelbooru в {}',
        'comparing_images': '🔎 Сравниваю изображения по содержимому...',
        'images_match': '✅ Изображения совпадают (расстояние Хэмминга: {}). Использую Danbooru.',
        'images_differ': '⚠️ Изображения визуально различаются. Требуется выбор.'
    },
    'en': {
        'title': 'Tag Extractor',
        'lang_label': 'Language',
        'url_label': 'URL:',
        'process_btn': 'Extract tags',
        'merge_btn': 'Merge all tags',
        'folder_btn': 'Save folder',
        'clear_btn': 'Clear log',
        'exit_btn': 'Exit',
        'status_ready': 'Ready',
        'processing': 'Processing...',
        'success': '✅ Success',
        'error': '❌ Error',
        'no_url': 'Enter URL',
        'select_folder': 'Select save folder',
        'current_folder': 'Current folder:',
        'merge_start': 'Merging files...',
        'merge_done': 'Merge complete. File: {}',
        'merge_no_files': 'No tag files found.',
        'log_placeholder': 'Messages will appear here...',
        'preview_not_available': 'Preview not available',
        'paste_btn': 'Paste',
        'clear_btn_entry': 'Clear',
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
        'search_iqdb': '🔎 Searching via IQDB...',
        'found_iqdb': '✅ Found via IQDB',
        'danbooru_post': '📌 Danbooru post: ID {}',
        'saved_from_danbooru': '✅ Saved {} tags from Danbooru to {}',
        'trying_direct': '⚠️ Not found on Danbooru, trying direct tags from {}',
        'saved_from_source': '✅ Saved {} tags from {} to {}',
        'failed_all': '❌ Failed to get tags from Danbooru or {}',
        'unsupported_domain': '❌ Domain {} is not supported',
        'error_exception': '❌ {}',
        'gelbooru_no_tags_danbooru_search': '⚠️ Could not get tags directly from Gelbooru, searching via Danbooru...',
        'gelbooru_fallback': '⚠️ Not found on Danbooru, using Gelbooru tags (if available)',
        'no_tags_gelbooru': '❌ Failed to get tags from Gelbooru or via Danbooru',
        'gelbooru_parsing_html': '🔎 Parsing Gelbooru HTML page for tags...',
        'gelbooru_parsed_tags': '✅ Extracted {} tags from HTML',
        'md5_mismatch': '⚠️ IQDB returned a post but MD5 does not match. Ignoring Danbooru.',
        'no_md5_use_danbooru': '⚠️ No MD5 for verification, but using Danbooru from IQDB.',
        'md5_mismatch_but_use': '⚠️ IQDB returned a post, MD5 mismatch, but using Danbooru (post found).',
        'choose_source_title': 'Choose tag source',
        'choose_source_msg': 'Tags found from multiple sources. Which one to use?',
        'btn_danbooru': 'Danbooru ({} tags)',
        'btn_gelbooru': 'Gelbooru ({} tags)',
        'btn_source': '{} ({} tags)',
        'btn_cancel': 'Cancel (use source site)',
        'search_gelbooru': '🔎 Searching on Gelbooru...',
        'found_gelbooru': '✅ Found on Gelbooru',
        'gelbooru_post': '📌 Gelbooru post: ID {}',
        'saved_from_gelbooru': '✅ Saved {} tags from Gelbooru to {}',
        'comparing_images': '🔎 Comparing images by content...',
        'images_match': '✅ Images match (Hamming distance: {}). Using Danbooru.',
        'images_differ': '⚠️ Images visually differ. Choice required.'
    }
}

def clean_tag(tag):
    return tag.replace('_', ' ')

def extract_identifier(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    query = parsed.query

    if 'danbooru.donmai.us' in domain or 'aibooru.online' in domain:
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

def fetch_danbooru_post(identifier):
    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = 'https://danbooru.donmai.us/posts.json'

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        post = data[0]
        raw_tags = post.get('tag_string', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        return {
            'tags': tags,
            'file_url': post.get('file_url'),
            'md5': post.get('md5')
        }
    except:
        return None

def fetch_aibooru_post(identifier):
    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = 'https://aibooru.online/posts.json'

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        post = data[0]
        raw_tags = post.get('tag_string', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        return {
            'tags': tags,
            'file_url': post.get('file_url'),
            'md5': post.get('md5')
        }
    except:
        return None

def fetch_konachan_post(domain, identifier):
    base_url = f"https://{domain}"
    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = f"{base_url}/post.json"

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        post = data[0]
        raw_tags = post.get('tags', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        file_url = post.get('file_url') or post.get('jpeg_url') or post.get('sample_url')
        return {
            'tags': tags,
            'file_url': file_url,
            'md5': post.get('md5')
        }
    except:
        return None

def fetch_yandere_post(identifier):
    url = f"https://yande.re/post.json?tags=id:{identifier}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data or len(data) == 0:
            return None
        post = data[0]
        raw_tags = post.get('tags', '').split()
        tags = [clean_tag(t) for t in raw_tags] if raw_tags else None
        return {
            'tags': tags,
            'file_url': post.get('file_url'),
            'md5': post.get('md5')
        }
    except:
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

def fetch_gelbooru_post(identifier, log_callback=None, lang_dict=None):
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
    md5 = None
    try:
        resp = requests.get(url, params=params, timeout=10)
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
            md5 = post.get('md5')
            if tags:
                if log_callback and lang_dict:
                    log_callback(lang_dict['gelbooru_parsed_tags'].format(len(tags)))
                return {
                    'tags': tags,
                    'file_url': file_url,
                    'md5': md5
                }
    except Exception as e:
        pass

    html_url = f"https://gelbooru.com/index.php?page=post&s=view&id={identifier}"
    try:
        html_resp = requests.get(html_url, timeout=10)
        html = html_resp.text

        og_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if og_match:
            file_url = og_match.group(1)
            if file_url.startswith('//'):
                file_url = 'https:' + file_url
            md5_match = re.search(r'/([a-f0-9]{32})\.[a-z]+', file_url, re.I)
            md5 = md5_match.group(1) if md5_match else None

        meta_keywords = re.search(r'<meta name="keywords" content="([^"]+)"', html, re.I)
        if meta_keywords:
            keywords = meta_keywords.group(1)
            raw_tags = [t.strip() for t in keywords.split(',') if t.strip()]
            filtered_keywords = filter_gelbooru_tags(raw_tags)
            tags = [clean_tag(t) for t in filtered_keywords] if filtered_keywords else None
            if tags and log_callback and lang_dict:
                log_callback(lang_dict['gelbooru_parsed_tags'].format(len(tags)))
                return {
                    'tags': tags,
                    'file_url': file_url,
                    'md5': md5
                }

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
                            return {
                                'tags': tags,
                                'file_url': file_url,
                                'md5': md5
                            }

        return {
            'tags': tags,
            'file_url': file_url,
            'md5': md5
        }
    except Exception as e:
        return {
            'tags': None,
            'file_url': None,
            'md5': None
        }

def get_image_info_from_source(domain, identifier):
    if 'yande.re' in domain:
        post = fetch_yandere_post(identifier)
        if post:
            return {'file_url': post['file_url'], 'md5': post['md5']}
    elif 'gelbooru.com' in domain:
        post = fetch_gelbooru_post(identifier)
        if post:
            return {'file_url': post['file_url'], 'md5': post['md5']}
    elif 'konachan.com' in domain or 'konachan.net' in domain:
        post = fetch_konachan_post(domain, identifier)
        if post:
            return {'file_url': post['file_url'], 'md5': post['md5']}
    return {'file_url': None, 'md5': None}

def search_on_danbooru_by_md5(md5):
    url = f"https://danbooru.donmai.us/posts.json?tags=md5:{md5}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data and len(data) > 0:
            return data[0].get('id')
    except:
        pass
    return None

def search_on_danbooru_by_iqdb(image_url):
    try:
        img_resp = requests.get(image_url, stream=True, timeout=15)
        if img_resp.status_code != 200:
            return None
        files = {'file': ('image.jpg', img_resp.content, 'image/jpeg')}
        iqdb_resp = requests.post('https://iqdb.org/', files=files, timeout=20)
        if iqdb_resp.status_code != 200:
            return None
        pattern = r'danbooru\.donmai\.us/posts/(\d+)'
        matches = re.findall(pattern, iqdb_resp.text)
        if matches:
            return matches[0]
    except:
        pass
    return None

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
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if isinstance(data, dict) and 'post' in data:
            posts = data['post']
        elif isinstance(data, list):
            posts = data
        else:
            posts = []
        if posts:
            return posts[0].get('id')
    except:
        pass
    return None

def search_on_gelbooru_by_iqdb(image_url):
    try:
        img_resp = requests.get(image_url, stream=True, timeout=15)
        if img_resp.status_code != 200:
            return None
        files = {'file': ('image.jpg', img_resp.content, 'image/jpeg')}
        iqdb_resp = requests.post('https://iqdb.org/', files=files, timeout=20)
        if iqdb_resp.status_code != 200:
            return None
        pattern = r'gelbooru\.com/index\.php\?page=post&s=view&id=(\d+)'
        matches = re.findall(pattern, iqdb_resp.text)
        if matches:
            return matches[0]
    except:
        pass
    return None

def get_image_hash(image_url, hash_size=8):
    try:
        headers = {}
        if 'gelbooru.com' in image_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://gelbooru.com/'
            }
        resp = requests.get(image_url, headers=headers, timeout=10)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        img = img.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
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
    except Exception as e:
        print(f"Ошибка вычисления хеша для {image_url}: {e}")
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
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(", ".join(tags))
            f.write(f"\n\nВсего тегов: {len(tags)}")
            f.write(f"\n\nSource: {source_url}")
            if danbooru_url and danbooru_url != source_url:
                f.write(f"\nDanbooru: {danbooru_url}")
            if gelbooru_url and gelbooru_url != source_url:
                f.write(f"\nGelbooru: {gelbooru_url}")
        return full_path
    except Exception as e:
        raise e

def merge_all_tags(save_folder, log_callback, lang_dict):
    pattern = os.path.join(save_folder, "tags_*_clean.txt")
    tag_files = glob.glob(pattern)

    if not tag_files:
        log_callback(lang_dict['merge_no_files'])
        return

    log_callback(lang_dict['merge_start'])
    output_filename = os.path.join(save_folder, "all_tags_combined.txt")

    file_count = 0
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for filename in sorted(tag_files):
            try:
                with open(filename, 'r', encoding='utf-8') as infile:
                    first_line = infile.readline().strip()
                    if first_line:
                        outfile.write(first_line + '\n\n')
                        file_count += 1
                        log_callback(f"  + {os.path.basename(filename)}")
                    else:
                        log_callback(f"  ⚠️ {os.path.basename(filename)} (empty)")
            except Exception as e:
                log_callback(f"  ❌ Error with {os.path.basename(filename)}: {e}")

    log_callback(lang_dict['merge_done'].format(os.path.basename(output_filename)))

class TagExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x800")
        self.title("Tag Extractor")
        self.resizable(True, True)

        self.current_lang = tk.StringVar(value='ru')
        self.save_folder = tk.StringVar(value=tempfile.gettempdir())

        self.create_widgets()

        self.current_image_url = None
        self.preview_image = None

        try:
            loc = locale.getlocale(locale.LC_CTYPE)[0]
            if loc:
                sys_lang = loc[:2]
            else:
                sys_lang = 'en'
        except:
            sys_lang = 'en'
        if sys_lang not in ['ru', 'en']:
            sys_lang = 'en'
        self.current_lang.set(sys_lang)
        self.update_language()

        self.user_choice_event = threading.Event()
        self.user_choice_result = None

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding="5")
        top_frame.pack(fill=tk.X)

        self.lang_label = ttk.Label(top_frame, text=LANG['ru']['lang_label'])
        self.lang_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        self.lang_combo = ttk.Combobox(top_frame, textvariable=self.current_lang, values=['ru', 'en'], state='readonly', width=5)
        self.lang_combo.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.lang_combo.bind('<<ComboboxSelected>>', self.on_lang_change)

        self.folder_btn = ttk.Button(top_frame, text=LANG['ru']['folder_btn'], command=self.select_folder)
        self.folder_btn.grid(row=0, column=2, padx=5)

        self.folder_label = ttk.Label(top_frame, text="", foreground="blue")
        self.folder_label.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.update_folder_label()

        url_frame = ttk.Frame(self, padding="5")
        url_frame.pack(fill=tk.X)

        self.url_label = ttk.Label(url_frame, text=LANG['ru']['url_label'])
        self.url_label.pack(side=tk.LEFT)

        self.url_entry = ttk.Entry(url_frame, font=('TkDefaultFont', 10))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.paste_btn = ttk.Button(url_frame, text=LANG['ru']['paste_btn'],
                                    command=lambda: self.paste_text(self.url_entry))
        self.paste_btn.pack(side=tk.LEFT, padx=2)

        self.clear_entry_btn = ttk.Button(url_frame, text=LANG['ru']['clear_btn_entry'],
                                          command=lambda: self.url_entry.delete(0, tk.END))
        self.clear_entry_btn.pack(side=tk.LEFT, padx=2)

        self.create_context_menu(self.url_entry)

        self.url_entry.bind('<Return>', lambda e: self.process_url_thread())

        self.url_entry.bind('<Control-KeyPress>', self.on_url_ctrl_key)

        btn_frame = ttk.Frame(self, padding="5")
        btn_frame.pack(fill=tk.X)

        self.process_btn = ttk.Button(btn_frame, text=LANG['ru']['process_btn'], command=self.process_url_thread)
        self.process_btn.pack(side=tk.LEFT, padx=2)

        self.merge_btn = ttk.Button(btn_frame, text=LANG['ru']['merge_btn'], command=self.merge_tags_thread)
        self.merge_btn.pack(side=tk.LEFT, padx=2)

        self.clear_btn = ttk.Button(btn_frame, text=LANG['ru']['clear_btn'], command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=2)

        self.exit_btn = ttk.Button(btn_frame, text=LANG['ru']['exit_btn'], command=self.quit)
        self.exit_btn.pack(side=tk.LEFT, padx=2)

        main_panel = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(main_panel)
        right_frame = ttk.Frame(main_panel, width=400)

        main_panel.add(left_frame, weight=1)
        main_panel.add(right_frame, weight=1)

        log_frame = ttk.Frame(left_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20, bg='#ffffff', fg='#000000', insertbackground='black')
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text.bind('<Control-KeyPress>', self.on_log_ctrl_key)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.preview_label = ttk.Label(right_frame, text=LANG['ru']['preview_not_available'], anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar()
        self.status_var.set(LANG['ru']['status_ready'])
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Вставить", command=lambda: self.paste_text(widget))
        menu.add_separator()
        menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)
        widget.bind("<Button-3>", show_menu)

    def on_url_ctrl_key(self, event):
        if event.keycode == 67:
            self.copy_text(self.url_entry)
        elif event.keycode == 86:
            self.paste_text(self.url_entry)
        elif event.keycode == 88:
            self.cut_text(self.url_entry)
        return "break"

    def on_log_ctrl_key(self, event):
        if event.keycode == 67:
            self.copy_text(self.log_text)
        return "break"

    def paste_text(self, widget):
        try:
            text = widget.clipboard_get()
            if isinstance(widget, tk.Entry):
                widget.insert(tk.INSERT, text)
            else:
                widget.insert(tk.INSERT, text)
        except:
            pass

    def copy_text(self, widget):
        widget.event_generate("<<Copy>>")

    def cut_text(self, widget):
        widget.event_generate("<<Cut>>")

    def update_folder_label(self):
        folder = self.save_folder.get()
        if len(folder) > 50:
            display = "..." + folder[-47:]
        else:
            display = folder
        self.folder_label.config(text=display)

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_folder.get(),
                                         title=LANG[self.current_lang.get()]['select_folder'])
        if folder:
            self.save_folder.set(folder)
            self.update_folder_label()

    def on_lang_change(self, event=None):
        self.update_language()

    def update_language(self):
        lang = self.current_lang.get()
        self.lang_label.config(text=LANG[lang]['lang_label'])
        self.url_label.config(text=LANG[lang]['url_label'])
        self.folder_btn.config(text=LANG[lang]['folder_btn'])
        self.process_btn.config(text=LANG[lang]['process_btn'])
        self.merge_btn.config(text=LANG[lang]['merge_btn'])
        self.clear_btn.config(text=LANG[lang]['clear_btn'])
        self.exit_btn.config(text=LANG[lang]['exit_btn'])
        self.paste_btn.config(text=LANG[lang]['paste_btn'])
        self.clear_entry_btn.config(text=LANG[lang]['clear_btn_entry'])
        self.status_var.set(LANG[lang]['status_ready'])
        if not self.preview_image:
            self.preview_label.config(text=LANG[lang]['preview_not_available'])

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def set_preview(self, image_url):
        self.current_image_url = image_url
        loading_text = LANG[self.current_lang.get()].get('loading', 'Loading...')
        self.preview_label.config(text=loading_text, image='')
        self.preview_image = None

        def load_image():
            try:
                if 'gelbooru.com' in image_url:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://gelbooru.com/'
                    }
                    resp = requests.get(image_url, headers=headers, timeout=10)
                else:
                    resp = requests.get(image_url, timeout=10)
                resp.raise_for_status()
                img_data = resp.content
                pil_image = Image.open(io.BytesIO(img_data))
                pil_image.thumbnail((400, 600))
                self.preview_image = ImageTk.PhotoImage(pil_image)
                self.preview_label.config(image=self.preview_image, text='')
            except Exception as e:
                print(f"Ошибка загрузки предпросмотра: {e}")
                error_text = LANG[self.current_lang.get()]['preview_not_available']
                self.preview_label.config(text=error_text, image='')
                self.preview_image = None

        threading.Thread(target=load_image, daemon=True).start()

    def ask_tag_source(self, sources):
        lang_dict = LANG[self.current_lang.get()]
        dialog = tk.Toplevel(self)
        dialog.title(lang_dict['choose_source_title'])
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (600 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text=lang_dict['choose_source_msg'], wraplength=580).pack(pady=10)

        result = [None]

        def on_choose(source_tuple):
            result[0] = source_tuple
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        col = 0
        max_cols = 3
        thumb_size = (150, 200)

        for src in sources:
            src_type, tags, identifier, img_url = src
            if src_type == 'danbooru':
                btn_text = lang_dict['btn_danbooru'].format(len(tags))
            elif src_type == 'gelbooru':
                btn_text = lang_dict['btn_gelbooru'].format(len(tags))
            else:
                btn_text = lang_dict['btn_source'].format(identifier.capitalize(), len(tags))

            frame = ttk.Frame(main_frame, relief=tk.RAISED, borderwidth=1)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            thumb_label = ttk.Label(frame, text="Загрузка...")
            thumb_label.pack(pady=5)

            def load_thumb(url, label):
                try:
                    headers = {}
                    if 'gelbooru.com' in url:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Referer': 'https://gelbooru.com/'
                        }
                    resp = requests.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()
                    img = Image.open(io.BytesIO(resp.content))
                    img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    label.config(image=photo, text='')
                    label.image = photo
                except Exception as e:
                    label.config(text="Нет превью")

            load_thumb(img_url, thumb_label)

            btn = ttk.Button(frame, text=btn_text, command=lambda s=src: on_choose(s))
            btn.pack(pady=5)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        cancel_btn = ttk.Button(dialog, text=lang_dict['btn_cancel'], command=on_cancel)
        cancel_btn.pack(pady=10)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.wait_window()

        return result[0]

    def process_url_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log(LANG[self.current_lang.get()]['no_url'])
            return
        self.url_entry.delete(0, tk.END)
        thread = threading.Thread(target=self.process_url, args=(url,))
        thread.daemon = True
        thread.start()

    def process_url(self, url):
        lang = self.current_lang.get()
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set(LANG[lang]['processing'])
        self.log(LANG[lang]['processing_url'].format(url))

        try:
            domain, identifier = extract_identifier(url)
            if not domain or not identifier:
                self.log(LANG[lang]['error_extract'])
                return

            file_id = identifier.replace(':', '_')
            domain_slug = domain.replace('.', '_')

            if 'danbooru.donmai.us' in domain:
                self.log(LANG[lang]['direct_request'].format(domain))
                post_data = fetch_danbooru_post(identifier)
                if not post_data or not post_data['tags']:
                    self.log(LANG[lang]['error_no_tags'])
                    return
                tags = post_data['tags']
                if post_data['file_url']:
                    self.set_preview(post_data['file_url'])
                saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                          domain_slug=domain_slug, post_id=file_id)
                self.log(LANG[lang]['saved_tags'].format(len(tags), os.path.basename(saved)))

            elif 'aibooru.online' in domain:
                self.log(LANG[lang]['direct_request'].format(domain))
                post_data = fetch_aibooru_post(identifier)
                if not post_data or not post_data['tags']:
                    self.log(LANG[lang]['error_no_tags'])
                    return
                tags = post_data['tags']
                if post_data['file_url']:
                    self.set_preview(post_data['file_url'])
                saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                          domain_slug=domain_slug, post_id=file_id)
                self.log(LANG[lang]['saved_tags'].format(len(tags), os.path.basename(saved)))

            elif 'konachan.com' in domain or 'konachan.net' in domain:
                self.log(LANG[lang]['source_info'].format(domain, identifier))
                info = get_image_info_from_source(domain, identifier)
                source_image_url = info.get('file_url')
                if source_image_url:
                    self.set_preview(source_image_url)
                else:
                    self.log(LANG[lang]['preview_fail'])

                md5 = info.get('md5')
                file_url = info.get('file_url')
                konachan_tags = None
                direct_post = fetch_konachan_post(domain, identifier)
                if direct_post:
                    konachan_tags = direct_post['tags']

                danbooru_id = None
                db_post = None
                danbooru_image_url = None
                if md5:
                    self.log(LANG[lang]['search_md5'])
                    danbooru_id = search_on_danbooru_by_md5(md5)
                    if danbooru_id:
                        self.log(LANG[lang]['found_md5'])
                        db_post = fetch_danbooru_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('file_url')

                if not danbooru_id and file_url:
                    self.log(LANG[lang]['search_iqdb'])
                    danbooru_id = search_on_danbooru_by_iqdb(file_url)
                    if danbooru_id:
                        self.log(LANG[lang]['found_iqdb'])
                        db_post = fetch_danbooru_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('file_url')

                self.log(LANG[lang]['search_gelbooru'])
                gelbooru_id = None
                gelbooru_post = None
                gelbooru_image_url = None
                if md5:
                    gelbooru_id = search_on_gelbooru_by_md5(md5)
                    if gelbooru_id:
                        self.log(LANG[lang]['found_gelbooru'])
                        gelbooru_post = fetch_gelbooru_post(gelbooru_id)
                        if gelbooru_post:
                            gelbooru_image_url = gelbooru_post.get('file_url')
                if not gelbooru_id and file_url:
                    gelbooru_id = search_on_gelbooru_by_iqdb(file_url)
                    if gelbooru_id:
                        self.log(LANG[lang]['found_gelbooru'])
                        gelbooru_post = fetch_gelbooru_post(gelbooru_id)
                        if gelbooru_post:
                            gelbooru_image_url = gelbooru_post.get('file_url')

                sources = []
                sources.append(('source', konachan_tags, 'Konachan', source_image_url))
                if db_post and db_post.get('tags'):
                    sources.append(('danbooru', db_post['tags'], danbooru_id, danbooru_image_url))
                if gelbooru_post and gelbooru_post.get('tags'):
                    sources.append(('gelbooru', gelbooru_post['tags'], gelbooru_id, gelbooru_image_url))

                if db_post and db_post.get('tags') and source_image_url and danbooru_image_url:
                    if md5 is None or db_post.get('md5') != md5:
                        self.log(LANG[lang]['comparing_images'])
                        if compare_images_by_hash(source_image_url, danbooru_image_url):
                            self.log(LANG[lang]['images_match'].format('?'))
                            sources = [('danbooru', db_post['tags'], danbooru_id, danbooru_image_url)]
                        else:
                            self.log(LANG[lang]['images_differ'])

                if len(sources) == 1:
                    src = sources[0]
                    src_type, tags, identifier, img_url = src
                    danbooru_url = None
                    gelbooru_url = None
                    if src_type == 'danbooru':
                        danbooru_url = f"https://danbooru.donmai.us/posts/{identifier}"
                        if img_url:
                            self.set_preview(img_url)
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  danbooru_url=danbooru_url,
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
                    elif src_type == 'gelbooru':
                        gelbooru_url = f"https://gelbooru.com/index.php?page=post&s=view&id={identifier}"
                        if img_url:
                            self.set_preview(img_url)
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  gelbooru_url=gelbooru_url,
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_gelbooru'].format(len(tags), os.path.basename(saved)))
                    else:
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_source'].format(len(tags), 'Konachan', os.path.basename(saved)))
                else:
                    self.user_choice_event.clear()
                    self.after(0, lambda: self.ask_tag_source_and_continue(sources, url, domain_slug, file_id, lang))
                    self.user_choice_event.wait()
                    choice = self.user_choice_result
                    if choice:
                        src_type, tags, identifier, img_url = choice
                        danbooru_url = None
                        gelbooru_url = None
                        if src_type == 'danbooru':
                            danbooru_url = f"https://danbooru.donmai.us/posts/{identifier}"
                            if img_url:
                                self.set_preview(img_url)
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      danbooru_url=danbooru_url,
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
                        elif src_type == 'gelbooru':
                            gelbooru_url = f"https://gelbooru.com/index.php?page=post&s=view&id={identifier}"
                            if img_url:
                                self.set_preview(img_url)
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      gelbooru_url=gelbooru_url,
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_gelbooru'].format(len(tags), os.path.basename(saved)))
                        else:
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_source'].format(len(tags), 'Konachan', os.path.basename(saved)))
                    else:
                        saved = save_tags_to_file(konachan_tags, url, self.save_folder.get(),
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_source'].format(len(konachan_tags), 'Konachan', os.path.basename(saved)))

            elif 'yande.re' in domain:
                self.log(LANG[lang]['source_info'].format(domain, identifier))
                info = get_image_info_from_source(domain, identifier)
                source_image_url = info.get('file_url')
                if source_image_url:
                    self.set_preview(source_image_url)
                else:
                    self.log(LANG[lang]['preview_fail'])

                md5 = info.get('md5')
                file_url = info.get('file_url')
                yandere_tags = None
                direct_post = fetch_yandere_post(identifier)
                if direct_post:
                    yandere_tags = direct_post['tags']

                danbooru_id = None
                db_post = None
                danbooru_image_url = None
                if md5:
                    self.log(LANG[lang]['search_md5'])
                    danbooru_id = search_on_danbooru_by_md5(md5)
                    if danbooru_id:
                        self.log(LANG[lang]['found_md5'])
                        db_post = fetch_danbooru_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('file_url')

                if not danbooru_id and file_url:
                    self.log(LANG[lang]['search_iqdb'])
                    danbooru_id = search_on_danbooru_by_iqdb(file_url)
                    if danbooru_id:
                        self.log(LANG[lang]['found_iqdb'])
                        db_post = fetch_danbooru_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('file_url')

                self.log(LANG[lang]['search_gelbooru'])
                gelbooru_id = None
                gelbooru_post = None
                gelbooru_image_url = None
                if md5:
                    gelbooru_id = search_on_gelbooru_by_md5(md5)
                    if gelbooru_id:
                        self.log(LANG[lang]['found_gelbooru'])
                        gelbooru_post = fetch_gelbooru_post(gelbooru_id)
                        if gelbooru_post:
                            gelbooru_image_url = gelbooru_post.get('file_url')
                if not gelbooru_id and file_url:
                    gelbooru_id = search_on_gelbooru_by_iqdb(file_url)
                    if gelbooru_id:
                        self.log(LANG[lang]['found_gelbooru'])
                        gelbooru_post = fetch_gelbooru_post(gelbooru_id)
                        if gelbooru_post:
                            gelbooru_image_url = gelbooru_post.get('file_url')

                sources = []
                sources.append(('source', yandere_tags, 'Yande.re', source_image_url))
                if db_post and db_post.get('tags'):
                    sources.append(('danbooru', db_post['tags'], danbooru_id, danbooru_image_url))
                if gelbooru_post and gelbooru_post.get('tags'):
                    sources.append(('gelbooru', gelbooru_post['tags'], gelbooru_id, gelbooru_image_url))

                if db_post and db_post.get('tags') and source_image_url and danbooru_image_url:
                    if md5 is None or db_post.get('md5') != md5:
                        self.log(LANG[lang]['comparing_images'])
                        if compare_images_by_hash(source_image_url, danbooru_image_url):
                            self.log(LANG[lang]['images_match'].format('?'))
                            sources = [('danbooru', db_post['tags'], danbooru_id, danbooru_image_url)]
                        else:
                            self.log(LANG[lang]['images_differ'])

                if len(sources) == 1:
                    src = sources[0]
                    src_type, tags, identifier, img_url = src
                    danbooru_url = None
                    gelbooru_url = None
                    if src_type == 'danbooru':
                        danbooru_url = f"https://danbooru.donmai.us/posts/{identifier}"
                        if img_url:
                            self.set_preview(img_url)
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  danbooru_url=danbooru_url,
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
                    elif src_type == 'gelbooru':
                        gelbooru_url = f"https://gelbooru.com/index.php?page=post&s=view&id={identifier}"
                        if img_url:
                            self.set_preview(img_url)
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  gelbooru_url=gelbooru_url,
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_gelbooru'].format(len(tags), os.path.basename(saved)))
                    else:
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_source'].format(len(tags), 'Yande.re', os.path.basename(saved)))
                else:
                    self.user_choice_event.clear()
                    self.after(0, lambda: self.ask_tag_source_and_continue(sources, url, domain_slug, file_id, lang))
                    self.user_choice_event.wait()
                    choice = self.user_choice_result
                    if choice:
                        src_type, tags, identifier, img_url = choice
                        danbooru_url = None
                        gelbooru_url = None
                        if src_type == 'danbooru':
                            danbooru_url = f"https://danbooru.donmai.us/posts/{identifier}"
                            if img_url:
                                self.set_preview(img_url)
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      danbooru_url=danbooru_url,
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
                        elif src_type == 'gelbooru':
                            gelbooru_url = f"https://gelbooru.com/index.php?page=post&s=view&id={identifier}"
                            if img_url:
                                self.set_preview(img_url)
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      gelbooru_url=gelbooru_url,
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_gelbooru'].format(len(tags), os.path.basename(saved)))
                        else:
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_source'].format(len(tags), 'Yande.re', os.path.basename(saved)))
                    else:
                        saved = save_tags_to_file(yandere_tags, url, self.save_folder.get(),
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_source'].format(len(yandere_tags), 'Yande.re', os.path.basename(saved)))

            elif 'gelbooru.com' in domain:
                self.log(LANG[lang]['source_info'].format(domain, identifier))
                post_data = fetch_gelbooru_post(identifier, log_callback=self.log, lang_dict=LANG[lang])
                source_image_url = post_data.get('file_url') if post_data else None
                if source_image_url:
                    self.set_preview(source_image_url)
                else:
                    self.log(LANG[lang]['preview_fail'])

                md5 = post_data.get('md5') if post_data else None
                file_url = post_data.get('file_url') if post_data else None
                gelbooru_tags = post_data.get('tags') if post_data else None

                danbooru_id = None
                db_post = None
                danbooru_image_url = None
                if md5:
                    self.log(LANG[lang]['search_md5'])
                    danbooru_id = search_on_danbooru_by_md5(md5)
                    if danbooru_id:
                        self.log(LANG[lang]['found_md5'])
                        db_post = fetch_danbooru_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('file_url')

                if not danbooru_id and file_url:
                    self.log(LANG[lang]['search_iqdb'])
                    danbooru_id = search_on_danbooru_by_iqdb(file_url)
                    if danbooru_id:
                        self.log(LANG[lang]['found_iqdb'])
                        db_post = fetch_danbooru_post(danbooru_id)
                        if db_post:
                            danbooru_image_url = db_post.get('file_url')

                sources = []
                sources.append(('source', gelbooru_tags, 'Gelbooru', source_image_url))
                if db_post and db_post.get('tags'):
                    sources.append(('danbooru', db_post['tags'], danbooru_id, danbooru_image_url))

                if db_post and db_post.get('tags') and source_image_url and danbooru_image_url:
                    if md5 is None or db_post.get('md5') != md5:
                        self.log(LANG[lang]['comparing_images'])
                        if compare_images_by_hash(source_image_url, danbooru_image_url):
                            self.log(LANG[lang]['images_match'].format('?'))
                            sources = [('danbooru', db_post['tags'], danbooru_id, danbooru_image_url)]

                if len(sources) == 1:
                    src = sources[0]
                    src_type, tags, identifier, img_url = src
                    danbooru_url = None
                    gelbooru_url = None
                    if src_type == 'danbooru':
                        danbooru_url = f"https://danbooru.donmai.us/posts/{identifier}"
                        if img_url:
                            self.set_preview(img_url)
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  danbooru_url=danbooru_url,
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
                    else:
                        saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_source'].format(len(tags), 'Gelbooru', os.path.basename(saved)))
                else:
                    self.user_choice_event.clear()
                    self.after(0, lambda: self.ask_tag_source_and_continue(sources, url, domain_slug, file_id, lang))
                    self.user_choice_event.wait()
                    choice = self.user_choice_result
                    if choice:
                        src_type, tags, identifier, img_url = choice
                        danbooru_url = None
                        gelbooru_url = None
                        if src_type == 'danbooru':
                            danbooru_url = f"https://danbooru.donmai.us/posts/{identifier}"
                            if img_url:
                                self.set_preview(img_url)
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      danbooru_url=danbooru_url,
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_danbooru'].format(len(tags), os.path.basename(saved)))
                        else:
                            saved = save_tags_to_file(tags, url, self.save_folder.get(),
                                                      domain_slug=domain_slug, post_id=file_id)
                            self.log(LANG[lang]['saved_from_source'].format(len(tags), 'Gelbooru', os.path.basename(saved)))
                    else:
                        saved = save_tags_to_file(gelbooru_tags, url, self.save_folder.get(),
                                                  domain_slug=domain_slug, post_id=file_id)
                        self.log(LANG[lang]['saved_from_source'].format(len(gelbooru_tags), 'Gelbooru', os.path.basename(saved)))
            else:
                self.log(LANG[lang]['unsupported_domain'].format(domain))
        except Exception as e:
            self.log(LANG[lang]['error_exception'].format(str(e)))
        finally:
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set(LANG[lang]['status_ready'])

    def ask_tag_source_and_continue(self, sources, url, domain_slug, file_id, lang):
        choice = self.ask_tag_source(sources)
        self.user_choice_result = choice
        self.user_choice_event.set()

    def merge_tags_thread(self):
        thread = threading.Thread(target=self.merge_tags)
        thread.daemon = True
        thread.start()

    def merge_tags(self):
        lang = self.current_lang.get()
        self.merge_btn.config(state=tk.DISABLED)
        self.status_var.set(LANG[lang]['processing'])
        try:
            merge_all_tags(self.save_folder.get(), self.log, LANG[lang])
        except Exception as e:
            self.log(LANG[lang]['error_exception'].format(str(e)))
        finally:
            self.merge_btn.config(state=tk.NORMAL)
            self.status_var.set(LANG[lang]['status_ready'])

if __name__ == "__main__":
    app = TagExtractorApp()
    app.mainloop()
