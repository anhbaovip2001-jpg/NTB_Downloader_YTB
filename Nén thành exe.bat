@echo off
echo ========================================
echo   Building YouTube Channel Downloader
echo ========================================
echo.

REM Đường dẫn Python của bạn
set PYTHON="C:/Users/Admin/AppData/Local/Python/pythoncore-3.14-64/python.exe"

REM Cài đặt các thư viện cần thiết
echo [1/2] Installing requirements...
%PYTHON% -m pip install pyinstaller pillow requests --quiet

echo.
echo [2/2] Building exe...
%PYTHON% -m PyInstaller --onefile --windowed --icon=icon.ico --name="YouTubeChannelDownloader" --clean youtube_channel_downloader.py

echo.
echo ========================================
echo   Build completed!
echo   Check the 'dist' folder for the exe
echo ========================================
echo.

REM Copy các file cần thiết vào thư mục dist
if exist "dist\YouTubeChannelDownloader.exe" (
    echo Copying required files to dist folder...
    copy "yt-dlp.exe" "dist\" 2>nul
    copy "ffmpeg.exe" "dist\" 2>nul
    copy "icon.ico" "dist\" 2>nul
    echo Done!
)

pause