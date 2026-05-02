# Release Pack Guide

Инструкция для подготовки релиз-пака Borodachamba Music v1.0.

## 1) Что должно быть в релизе

- Бинарник:
  - Windows: `BorodachambaMusic_v1_0.exe`
  - Linux: `BorodachambaMusic_v1_0`
- Документация:
  - `README.md`
  - `USER_MANUAL.md`
  - `CHANGELOG.md`
- Лицензия/брендинг:
  - `Borodachamba Studio - All Rights Reserved`

## 2) Сборка

### Windows

```bat
build_portable_windows.bat
```

### Linux

```bash
chmod +x build_portable_linux.sh
./build_portable_linux.sh
```

## 3) Быстрая проверка перед публикацией

1. Запуск бинарника и открытие UI.
2. Воспроизведение минимум 2-3 треков до конца.
3. Проверка `Space/s/q` и `Ctrl+C` (процессы не должны оставаться).
4. Проверка `x`, `[ ]`, `b/B`, `d`.
5. Проверка `w/l` (плейлист).
6. Проверка перезапуска приложения (восстановление сессии).
7. Проверка окна About (`i`) и ввода ключа (`k`).

## 4) Формирование релиз-пака

Рекомендуемая структура архива:

```text
BorodachambaMusic_v1_0/
  BorodachambaMusic_v1_0(.exe)
  README.md
  USER_MANUAL.md
  CHANGELOG.md
```

## 5) Имя и версия

- Product name: `Borodachamba Music v1.0`
- Version tag: `v1.0.0`
