@echo off
setlocal

python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :fail

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --noconfirm --clean --onefile --name "BorodachambaMusic_v1_0" borodachamba_player.py
if errorlevel 1 goto :fail

echo Portable build ready: dist\BorodachambaMusic_v1_0.exe
exit /b 0

:fail
echo Build failed
exit /b 1
