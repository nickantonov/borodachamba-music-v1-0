# Borodachamba Music v1.0

Теплый консольный MP3/аудио-плеер в духе htop и Linux TUI программ 90-х.

## Документация

- Краткий гайд: этот `README.md`
- Подробный пользовательский мануал: `USER_MANUAL.md`
- История изменений релиза: `CHANGELOG.md`
- Подготовка релиз-пака: `RELEASE.md`

## Скриншоты

- `docs/screenshots/main-ui-1.png`
- `docs/screenshots/main-ui-2.png`

## Запуск

```bash
python borodachamba_player.py
```

Можно сразу передать папку или файл:

```bash
python borodachamba_player.py ~/Music
python borodachamba_player.py ~/Music/track.mp3
```

## Зависимости

- `python`
- `ffplay`
- `ffprobe`

Они обычно входят в пакет FFmpeg.

## Управление

- `o` - открыть браузер файлов
- `Enter` - играть выбранный трек; в браузере: `./` добавляет текущую папку целиком, папка открывается, файл добавляется
- `a` - добавить выбранный файл/папку целиком
- `Space` - play/pause; в браузере добавить выбранный файл/папку и сразу играть
- `Insert` - отметить/снять отметку с файла или папки в браузере; `a` и `Space` работают со всеми отмеченными
- В Windows в браузере доступны записи `DRV`, чтобы быстро переходить на другой диск (например флешка `E:`)
- `g` в браузере - быстрый переход/переключение между дисками (`DRV`)
- `s` - stop
- `n` / `p` - следующий / предыдущий трек
- `Left` / `Right` - перемотка -5s / +5s
- `r` - repeat (`all/one/off`)
- `h` - shuffle on/off
- `m` - mute on/off
- `u` - resume autoplay on/off
- `v` - смена визуализации (10 стилей)
- `N` - nostalgia profile (`off/cassette/cassette deck/reel tape/vinyl`)
- `i` - окно About
- `+` / `-` - громкость
- `<` / `>` - тон
- `x` - смена DSP режима (`stereo/echo/chorus/reverb/phaser/flanger`)
- `[` / `]` - уровень DSP (0..12)
- `b` - bass boost on/off
- `B` - увеличить bass boost (+2 dB)
- `e` / `E` - следующий / предыдущий EQ пресет
- `0..4` - быстрый выбор EQ пресета (`0 flat`, `1 rock`, `2 jazz`, `3 vocal`, `4 bass boost`)
- `t` / `F8` - следующая цветовая схема
- `F7` - предыдущая цветовая схема
- `w` - сохранить плейлист
- `l` - загрузить плейлист
- `d` - сбросить DSP цепочку (mode/level/bass)
- `D` или `Delete` - удалить трек из плейлиста
- `c` - очистить плейлист
- `q` / `Esc` - выйти или закрыть браузер

## License

Проект распространяется как open-source под лицензией `GPL-3.0-only`.
Полный текст лицензии: `LICENSE`.

## Сохранение сессии

- При закрытии автоматически сохраняются настройки, плейлист, последний трек и позиция
- При следующем запуске состояние восстанавливается автоматически

Файлы: `~/.config/borodachamba-player/config.json` и `~/.config/borodachamba-player/playlist.m3u`.

## Portable build

- Windows: `build_portable_windows.bat`
- Linux: `build_portable_linux.sh`

## Copyright

Borodachamba Studio open-source by Nick Antonov (2000-2026)
