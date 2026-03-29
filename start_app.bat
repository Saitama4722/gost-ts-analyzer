@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem Корень проекта
cd /d "%~dp0" || (
  echo Не удалось перейти в каталог проекта.
  pause
  exit /b 1
)

echo ==========================================
echo Запуск gost-ts-analyzer
echo ==========================================

rem Поиск Python: .venv -> venv -> system python
set "PYTHON="
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON if exist "%~dp0venv\Scripts\python.exe" set "PYTHON=%~dp0venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"

rem Проверка Python
"%PYTHON%" -c "import sys; print(sys.version)" >nul 2>&1
if errorlevel 1 (
  echo Python не найден.
  echo Установите Python или создайте .venv / venv в папке проекта.
  pause
  exit /b 1
)

rem Проверка uvicorn
"%PYTHON%" -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
  echo Не найден пакет uvicorn.
  echo Установите зависимости: pip install -r requirements.txt
  echo При использовании .venv или venv установите пакеты в это окружение.
  pause
  exit /b 1
)

rem Проверка curl
where curl >nul 2>&1
if errorlevel 1 (
  echo В системе не найден curl.
  echo Для запуска требуется curl.exe из Windows 10/11.
  pause
  exit /b 1
)

echo Поиск свободного порта...
set "PORT="
call :bind_test 8000
if defined PORT goto have_port
call :bind_test 8765
if defined PORT goto have_port

for /L %%n in (8001,1,8100) do (
  if not defined PORT if not %%n equ 8765 call :bind_test %%n
)

:have_port
if not defined PORT (
  echo Не удалось найти свободный порт в диапазоне 8000–8100
  pause
  exit /b 1
)

echo Выбран порт: %PORT%
echo Запуск сервера...

start "gost-ts-analyzer-server" /b "%PYTHON%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port %PORT%
if errorlevel 1 (
  echo Не удалось запустить сервер.
  echo Проверьте зависимости и конфигурацию проекта.
  pause
  exit /b 1
)

echo Ожидание готовности...

set "READY="
for /L %%i in (1,1,60) do (
  curl -s -f "http://127.0.0.1:%PORT%/api/health" >nul 2>&1
  if not errorlevel 1 (
    set "READY=1"
    goto open_browser
  )
  timeout /t 1 /nobreak >nul
)

if not defined READY (
  echo Сервер не ответил вовремя.
  echo Проверьте сообщения об ошибках выше.
  pause
  exit /b 1
)

:open_browser
echo Открытие сайта в браузере...
start "" "http://127.0.0.1:%PORT%"

echo.
echo Сайт запущен: http://127.0.0.1:%PORT%
echo Не закрывайте это окно, пока работаете с приложением.
echo Чтобы остановить сервер, просто закройте это окно.
echo.

:keep_alive
timeout /t 60 /nobreak >nul
goto keep_alive

:bind_test
"%PYTHON%" -c "import socket;s=socket.socket();s.bind(('127.0.0.1',%1));s.close()" >nul 2>&1
if not errorlevel 1 set "PORT=%1"
exit /b 0
