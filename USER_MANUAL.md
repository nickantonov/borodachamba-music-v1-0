# Borodachamba Music v1.0 — User Manual

Borodachamba Music v1.0 — консольный аудио-плеер в стиле ретро-деки.

## 1) Быстрый старт

1. Установите Python 3.10+.
2. Установите FFmpeg (должны быть доступны `ffplay` и `ffprobe` в PATH).
3. Запустите:

```bash
python borodachamba_player.py
```

Запуск с музыкой сразу:

```bash
python borodachamba_player.py ~/Music
python borodachamba_player.py ~/Music/track.mp3
```

## 2) Главное окно

- `playlist` — очередь треков.
- `warm cube levels` — ретро-индикатор уровня (кассетный стиль).
- `now` — текущий трек, время, статус, режимы.
- `controls` — горячие клавиши и слайдеры.

## 3) Управление (горячие клавиши)

### Базовое воспроизведение

- `Space` — play/pause
- `Enter` — play выбранного трека
- `s` — stop
- `n` / `p` — следующий / предыдущий
- `Left` / `Right` — перемотка на `-5s / +5s`
- `q` / `Esc` — выход (или закрыть браузер)

### Плейлист

- `o` — открыть файловый браузер
- `a` — добавить текущую папку
- `D` или `Delete` — удалить трек из плейлиста
- `c` — очистить плейлист
- `w` — сохранить плейлист
- `l` — загрузить плейлист

### Режимы проигрывания

- `r` — repeat: `all -> one -> off`
- `h` — shuffle on/off
- `m` — mute on/off
- `u` — resume autoplay on/off
- `v` — смена визуализации (10 стилей)

### Звук и эффекты

- `+` / `-` — громкость
- `<` / `>` — tone
- `x` — DSP mode: `stereo/echo/chorus/reverb/phaser/flanger`
- `[` / `]` — DSP level `0..12`
- `d` — сброс DSP-цепочки (mode/level/bass)
- `b` — bass boost on/off
- `B` — увеличить bass boost (`+2 dB`, до `+18 dB`)
- `e` / `E` — EQ preset вперед/назад
- `0..4` — быстрый выбор EQ preset

### Внешний вид

- `t` / `F8` — следующая тема
- `F7` — предыдущая тема

### Лицензия / About

- `i` — About

## 4) Файловый браузер

- `Insert` — отметить/снять отметку файла/папки
- `a` — добавить отмеченные
- `Space` — добавить и сразу играть
- `Enter`:
  - на `./` — добавить текущую папку рекурсивно
  - на папке — зайти в папку
  - на файле — добавить файл

В Windows в файловом браузере есть пункты `DRV`, через них можно перейти на другой диск (например `D:`/`E:`/USB).

## 5) Автосохранение и восстановление сессии

При выходе сохраняются:

- настройки (theme, volume, tone, DSP, EQ, bass boost, repeat/shuffle/mute)
- плейлист
- последний трек и позиция

При запуске все состояние восстанавливается автоматически.

## 5.1) Стили визуализации

По клавише `v` переключаются 10 стилей:

1. deck flow
2. pacman medusa
3. pixel rain
4. scanner
5. matrix
6. sine wave
7. spark field
8. mirror bars
9. retro fire
10. orbit

Файлы сессии:

- `~/.config/borodachamba-player/config.json`
- `~/.config/borodachamba-player/playlist.m3u`

## 6) Сборка portable

### Windows

```bat
build_portable_windows.bat
```

Результат: `dist/BorodachambaMusic_v1_0.exe`

### Linux

```bash
chmod +x build_portable_linux.sh
./build_portable_linux.sh
```

Результат: `dist/BorodachambaMusic_v1_0`

## 7) Частые проблемы

### Нет звука / ошибка запуска

- Проверьте, что `ffplay` доступен в PATH.
- Проверьте, что файл поддерживаемого формата (`.mp3/.flac/.ogg/.wav/.m4a/.aac/.opus/.wma`).

### Не видны цвета

- Используйте современный терминал (Windows Terminal / Linux terminal с color support).

### Клавиши не реагируют в не-EN раскладке

- Переключать раскладку не обязательно: основные hotkeys нормализуются и должны работать в RU/UA.

## 8) Версия

- Product: `Borodachamba Music v1.0`
- Copyright: `Borodachamba Studio open-source by Nick Antonov (2000-2026)`
- License: `GPL-3.0-only` (GNU GPL v3.0 only)

## 9) Условия open-source

- Можно использовать, изучать, изменять и распространять проект по условиям GNU GPLv3.
- При распространении модифицированных версий необходимо сохранить ту же GPLv3-совместимую лицензию и исходный код.
- Полный юридический текст: файл `LICENSE`.
