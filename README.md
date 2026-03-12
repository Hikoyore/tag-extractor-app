# Tag Extractor App

A GUI application to extract tags from image posts on booru-style sites (Gelbooru, Danbooru, Konachan, Yande.re, Aibooru). It automatically searches for the same image on Danbooru and Gelbooru, compares images visually (via perceptual hash), and lets you choose the best tag source when multiple are found.

## Features
- Extracts tags from:
  - Gelbooru
  - Danbooru
  - Konachan / Konachan.net
  - Yande.re
  - Aibooru
- Searches for the same image on Danbooru and Gelbooru using:
  - MD5 hash (exact match)
  - IQDB (reverse image search)
- Compares images visually (dhash) when MD5 differs – automatically selects Danbooru if images match.
- If multiple sources are available, displays a dialog with preview thumbnails and tag counts for manual choice.
- Saves tags to a text file with source URLs (includes Danbooru/Gelbooru links if selected).
- Bilingual interface (Russian/English) – language can be switched on the fly.
- Preview panel shows the currently selected image.
- Merges all saved tag files into one combined file.

## Requirements
- Python 3.6+
- Libraries (all are standard except Pillow):
  - `tkinter` (usually included with Python)
  - `requests`
  - `Pillow` (PIL)
  - `locale`, `threading`, `re`, `glob`, `urllib`, `io`, `tempfile` (built-in)

Install missing libraries with pip:
```bash
pip install requests Pillow
```

No additional libraries needed for image hashing – it’s implemented from scratch.

How to Use

1. Run the script:
   ```bash
   python TagExtractorApp.py
   ```
2. Select a save folder (where tag files will be stored).
3. Paste a post URL from any supported site into the input field and press Enter or click "Extract tags".
4. The program will:
   · Fetch tags from the original site.
   · Search Danbooru and Gelbooru by MD5 and IQDB.
   · Compare images if needed.
   · If multiple sources are found, a dialog with thumbnails will appear – choose the preferred one.
5. Tags are saved as tags_<domain>_<post_id>_clean.txt in the chosen folder.
6. Use "Merge all tags" to combine all saved tag files into all_tags_combined.txt.

Language

Click the language dropdown (top left) to switch between Russian and English. The interface updates immediately.

Logging

All actions are logged in the left panel – you can see what the program is doing at every step.

Notes

· For Gelbooru, tags are filtered to remove garbage (like "imageboard-") and correctly handle the "imageboard- 1girl" case.
· For Konachan and Yande.re, the program also searches Gelbooru if Danbooru is not found.
· Image comparison uses a custom dhash implementation with a threshold of 5 (you can adjust in the code).
· IQDB searches may occasionally return wrong posts; the visual comparison and manual dialog help avoid mistakes.

# Tag Extractor App

Программа с графическим интерфейсом для извлечения тегов из постов на booru-сайтах (Gelbooru, Danbooru, Konachan, Yande.re, Aibooru). Автоматически ищет то же изображение на Danbooru и Gelbooru, сравнивает изображения визуально (через perceptual hash) и позволяет выбрать лучший источник тегов, если их несколько.

## Возможности
- Извлекает теги с:
  - Gelbooru
  - Danbooru
  - Konachan / Konachan.net
  - Yande.re
  - Aibooru
- Ищет то же изображение на Danbooru и Gelbooru с помощью:
  - MD5-хеша (точное совпадение)
  - IQDB (обратный поиск по изображению)
- Сравнивает изображения визуально (dhash), если MD5 различаются – автоматически выбирает Danbooru при совпадении.
- Если доступно несколько источников, показывает диалог с миниатюрами и количеством тегов для ручного выбора.
- Сохраняет теги в текстовый файл с указанием исходных URL (если выбран Danbooru/Gelbooru, добавляет соответствующую ссылку).
- Двуязычный интерфейс (русский/английский) – язык можно переключать на лету.
- Панель предпросмотра показывает текущее изображение.
- Объединяет все сохранённые файлы тегов в один общий файл.

## Требования
- Python 3.6+
- Библиотеки (все стандартные, кроме Pillow):
  - `tkinter` (обычно идёт с Python)
  - `requests`
  - `Pillow` (PIL)
  - `locale`, `threading`, `re`, `glob`, `urllib`, `io`, `tempfile` (встроенные)

Установите недостающие библиотеки через pip:
```bash
pip install requests Pillow
```

Дополнительные библиотеки для хеширования не требуются – реализация сделана с нуля.

Как использовать

1. Запустите скрипт:
   ```bash
   python TagExtractorApp.py 
   ```
2. Выберите папку для сохранения (где будут храниться файлы с тегами).
3. Вставьте URL поста с любого поддерживаемого сайта в поле ввода и нажмите Enter или кнопку «Извлечь теги».
4. Программа:
   · Получит теги с исходного сайта.
   · Выполнит поиск на Danbooru и Gelbooru по MD5 и IQDB.
   · При необходимости сравнит изображения.
   · Если найдено несколько источников, появится диалог с миниатюрами – выберите предпочтительный.
5. Теги сохраняются как tags_<домен>_<ID_поста>_clean.txt в выбранной папке.
6. Используйте кнопку «Объединить все теги», чтобы объединить все сохранённые файлы в all_tags_combined.txt.

Язык

Нажмите выпадающий список языка (слева вверху) для переключения между русским и английским. Интерфейс обновится мгновенно.

Логирование

Все действия записываются в левой панели – вы всегда видите, что делает программа.

Примечания

· Для Gelbooru теги фильтруются, чтобы удалить мусор (например, "imageboard-") и корректно обрабатывается случай "imageboard- 1girl".
· Для Konachan и Yande.re программа также ищет на Gelbooru, если Danbooru не найден.
· Сравнение изображений использует собственную реализацию dhash с порогом 5 (можно изменить в коде).
· Поиск через IQDB иногда может возвращать ошибочные посты; визуальное сравнение и ручной диалог помогают избежать ошибок.
```
