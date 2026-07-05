# Tag Extractor App

![Иллюстрация к проекту](https://github.com/Hikoyore/tag-extractor-app/blob/main/preview/preview.png)

Tag Extractor - это десктопное приложение на Python с графическим интерфейсом (Tkinter), предназначенное для извлечения тегов с различных booru-сайтов. Программа анализирует ссылку на пост или изображение, получает теги из первоисточника и при необходимости ищет более полные теги через Danbooru или Gelbooru, используя MD5-хеш или сервис IQDB. Результат сохраняется в текстовый файл. Также поддерживается объединение всех ранее сохранённых тегов в один файл.

## Особенности

- **Мультиязычный интерфейс** (русский / английский) - автоматически определяется язык системы, можно переключить вручную.
- **Извлечение тегов** из URL поста или изображения с booru-сайтов.
- **Поиск по MD5** - если у изображения есть MD5, программа пытается найти соответствующий пост на Danbooru или Gelbooru.
- **Поиск через IQDB** - если MD5 недоступен, выполняется поиск по картинке через iqdb.org.
- **Сравнение изображений** - при обнаружении нескольких источников (например, Konachan и Danbooru) программа может визуально сравнить изображения (по хешу разницы) и предложить выбрать наиболее подходящие теги.
- **Предпросмотр изображения** - загружает и показывает превью изображения из поста.
- **Сохранение тегов** в текстовый файл с информацией об источнике.
- **Объединение всех файлов тегов** в один общий файл.
- **Удобный интерфейс** с контекстным меню, горячими клавишами (Ctrl+C, Ctrl+V) и возможностью очистки полей ввода.

## Требования

- Python 3.7 или выше
- Библиотеки: `Pillow` (для работы с изображениями), `tkinter` (обычно входит в стандартную поставку Python)

Установите зависимости командой:

```bash
pip install Pillow
```

## Поддерживаемые сайты
- Danbooru (danbooru.donmai.us)
- Gelbooru (gelbooru.com)
- Konachan (konachan.com, konachan.net)
- Yande.re (yande.re)
- AIBooru (aibooru.online)

Ссылки могут быть как на страницу поста, так и напрямую на изображение (если в URL есть MD5 или ID).

## Формат сохраняемого файла
Пример содержимого файла `tags_danbooru_donmai_us_123456_clean.txt`:
```
1girl, ahoge, blush, long hair, school uniform, solo, ...
Всего тегов: 27

Source: https://danbooru.donmai.us/posts/123456
Danbooru: https://danbooru.donmai.us/posts/123456
```
_________________________________________________________________________

# Tag Extractor App

Tag Extractor is a Python desktop application with a GUI (Tkinter) designed to extract tags from various booru sites. The program analyzes a link to a post or image, retrieves tags from the original source, and if necessary, searches for more complete tags via Danbooru or Gelbooru using the MD5 hash or the IQDB service. The result is saved to a text file. Merging all previously saved tags into a single file is also supported.

## Features

- **Multilingual interface** (Russian / English) - automatically detects the system language, can be switched manually.
- **Tag extraction** from a post or image URL on booru sites.
- **MD5 search** - if the image has an MD5, the program attempts to find the corresponding post on Danbooru or Gelbooru.
- **IQDB search** - if MD5 is unavailable, it performs an image search via iqdb.org.
- **Image comparison** - when multiple sources are found (e.g., Konachan and Danbooru), the program can visually compare the images (using a difference hash) and suggest the most suitable tags.
- **Image preview** - loads and displays a preview of the image from the post.
- **Tag saving** to a text file with source information.
- **Merging all tag files** into one combined file.
- **User-friendly interface** with context menus, hotkeys (Ctrl+C, Ctrl+V), and the ability to clear input fields.

## Requirements

- Python 3.7 or higher
- Libraries: `Pillow` (for image handling), `tkinter` (usually included with Python)

Install the dependencies with:

```bash
pip install Pillow
```

## Supported Sites
- Danbooru (danbooru.donmai.us)
- Gelbooru (gelbooru.com)
- Konachan (konachan.com, konachan.net)
- Yande.re (yande.re)
- AIBooru (aibooru.online)

Links can be either to a post page or directly to an image (if the URL contains an MD5 or ID).

## Saved File Format
Example content of `tags_danbooru_donmai_us_123456_clean.txt`:
```
1girl, ahoge, blush, long hair, school uniform, solo, ...
Total tags: 27

Source: https://danbooru.donmai.us/posts/123456
Danbooru: https://danbooru.donmai.us/posts/123456
```
