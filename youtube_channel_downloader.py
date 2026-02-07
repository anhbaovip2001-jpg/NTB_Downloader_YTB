"""
YouTube Channel Downloader Tool
Sử dụng YouTube Data API v3, yt-dlp và ffmpeg
Author: GitHub Copilot
Version: 2.2
"""

import os
import sys
import subprocess
import json

# ==================== Xác định đường dẫn cho PyInstaller ====================
def get_base_path():
    """Lấy đường dẫn gốc, hỗ trợ cả khi chạy từ .py và .exe"""
    if getattr(sys, 'frozen', False):
        # Chạy từ file .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Chạy từ file .py
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# ==================== Tự động cài đặt thư viện ====================
def install_requirements():
    """Tự động cài đặt các thư viện cần thiết (chỉ khi chạy từ .py)"""
    if getattr(sys, 'frozen', False):
        return  # Không cần cài đặt khi chạy từ .exe
        
    required = ['Pillow', 'requests']
    
    for package in required:
        try:
            if package == 'Pillow':
                __import__('PIL')
            else:
                __import__(package)
        except ImportError:
            print(f"Đang cài đặt {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ Đã cài đặt {package}")

install_requirements()

# ==================== Import thư viện ====================
import io
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import requests
from PIL import Image


class YouTubeChannelDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Channel Downloader v2.2")
        self.root.geometry("950x850")
        self.root.resizable(True, True)
        
        # Đường dẫn tools
        self.base_path = BASE_PATH
        self.ytdlp_path = os.path.join(self.base_path, "yt-dlp.exe")
        self.ffmpeg_path = os.path.join(self.base_path, "ffmpeg.exe")
        self.settings_file = os.path.join(self.base_path, "settings.json")
        self.icon_path = os.path.join(self.base_path, "icon.ico")
        
        # Set icon cho window
        self.set_window_icon()
        
        # Kiểm tra nếu không có .exe thì dùng command line (Linux/Mac)
        if not os.path.exists(self.ytdlp_path):
            self.ytdlp_path = "yt-dlp"
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "ffmpeg"
        
        self.videos = []
        self.is_downloading = False
        self.download_executor = None
        
        # Optimize: Reuse requests session for connection pooling
        self.session = requests.Session()
        
        self.setup_ui()
        self.load_settings()
        
        # Lưu settings khi đóng app
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def set_window_icon(self):
        """Set icon cho cửa sổ"""
        try:
            if os.path.exists(self.icon_path):
                self.root.iconbitmap(self.icon_path)
        except Exception:
            pass  # Bỏ qua nếu không set được icon
            
    def get_default_settings(self):
        """Trả về settings mặc định"""
        return {
            'api_key': '',
            'cookie_file': '',
            'channel_url': '',
            'download_video': True,
            'download_audio': False,
            'download_thumbnail': False,
            'download_title': False,
            'video_quality': '1080p',
            'video_fps': '30',
            'audio_format': 'mp3',
            'audio_bitrate': '320k',
            'thumb_size': 'maxres (1280x720)',
            'thumb_width': '1280',
            'thumb_height': '720',
            'use_date_filter': False,
            'date_from': '2020-01-01',
            'date_to': datetime.now().strftime("%Y-%m-%d"),
            'use_duration_filter': False,
            'duration_min': '0',
            'duration_max': '999',
            'use_view_filter': False,
            'view_min': '0',
            'view_max': '999999999',
            'thread_count': '3',
            'output_dir': os.path.join(self.base_path, "downloads")
        }
        
    def load_settings(self):
        """Load settings từ file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # Apply settings
                defaults = self.get_default_settings()
                
                self.api_key_var.set(settings.get('api_key', defaults['api_key']))
                self.cookie_var.set(settings.get('cookie_file', defaults['cookie_file']))
                self.channel_url_var.set(settings.get('channel_url', defaults['channel_url']))
                
                self.download_video_var.set(settings.get('download_video', defaults['download_video']))
                self.download_audio_var.set(settings.get('download_audio', defaults['download_audio']))
                self.download_thumbnail_var.set(settings.get('download_thumbnail', defaults['download_thumbnail']))
                self.download_title_var.set(settings.get('download_title', defaults['download_title']))
                
                self.video_quality_var.set(settings.get('video_quality', defaults['video_quality']))
                self.video_fps_var.set(settings.get('video_fps', defaults['video_fps']))
                self.audio_format_var.set(settings.get('audio_format', defaults['audio_format']))
                self.audio_bitrate_var.set(settings.get('audio_bitrate', defaults['audio_bitrate']))
                
                self.thumb_size_var.set(settings.get('thumb_size', defaults['thumb_size']))
                self.thumb_width_var.set(settings.get('thumb_width', defaults['thumb_width']))
                self.thumb_height_var.set(settings.get('thumb_height', defaults['thumb_height']))
                
                self.use_date_filter.set(settings.get('use_date_filter', defaults['use_date_filter']))
                self.date_from_var.set(settings.get('date_from', defaults['date_from']))
                self.date_to_var.set(settings.get('date_to', defaults['date_to']))
                
                self.use_duration_filter.set(settings.get('use_duration_filter', defaults['use_duration_filter']))
                self.duration_min_var.set(settings.get('duration_min', defaults['duration_min']))
                self.duration_max_var.set(settings.get('duration_max', defaults['duration_max']))
                
                self.use_view_filter.set(settings.get('use_view_filter', defaults['use_view_filter']))
                self.view_min_var.set(settings.get('view_min', defaults['view_min']))
                self.view_max_var.set(settings.get('view_max', defaults['view_max']))
                
                self.thread_count_var.set(settings.get('thread_count', defaults['thread_count']))
                self.output_dir_var.set(settings.get('output_dir', defaults['output_dir']))
                
                # Update custom thumbnail UI if needed
                self.on_thumb_size_change()
                
                self.log("✅ Đã load settings từ lần sử dụng trước")
        except Exception as e:
            self.log(f"⚠️ Không thể load settings: {str(e)}")
            
    def save_settings(self):
        """Lưu settings vào file"""
        try:
            settings = {
                'api_key': self.api_key_var.get(),
                'cookie_file': self.cookie_var.get(),
                'channel_url': self.channel_url_var.get(),
                'download_video': self.download_video_var.get(),
                'download_audio': self.download_audio_var.get(),
                'download_thumbnail': self.download_thumbnail_var.get(),
                'download_title': self.download_title_var.get(),
                'video_quality': self.video_quality_var.get(),
                'video_fps': self.video_fps_var.get(),
                'audio_format': self.audio_format_var.get(),
                'audio_bitrate': self.audio_bitrate_var.get(),
                'thumb_size': self.thumb_size_var.get(),
                'thumb_width': self.thumb_width_var.get(),
                'thumb_height': self.thumb_height_var.get(),
                'use_date_filter': self.use_date_filter.get(),
                'date_from': self.date_from_var.get(),
                'date_to': self.date_to_var.get(),
                'use_duration_filter': self.use_duration_filter.get(),
                'duration_min': self.duration_min_var.get(),
                'duration_max': self.duration_max_var.get(),
                'use_view_filter': self.use_view_filter.get(),
                'view_min': self.view_min_var.get(),
                'view_max': self.view_max_var.get(),
                'thread_count': self.thread_count_var.get(),
                'output_dir': self.output_dir_var.get()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Không thể lưu settings: {str(e)}")
            
    def on_closing(self):
        """Xử lý khi đóng app"""
        self.save_settings()
        # Close requests session to free resources
        if hasattr(self, 'session'):
            self.session.close()
        self.root.destroy()
        
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Main container với scrollbar
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ==================== API & Cookie Settings ====================
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Cài đặt API & Cookie", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # API Key
        api_row = ttk.Frame(settings_frame)
        api_row.pack(fill=tk.X, pady=2)
        ttk.Label(api_row, text="YouTube API Key:", width=18).pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(api_row, textvariable=self.api_key_var, width=55, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        self.show_api_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(api_row, text="Hiện", variable=self.show_api_var, 
                       command=self.toggle_api_visibility).pack(side=tk.LEFT)
        
        # Cookie file
        cookie_row = ttk.Frame(settings_frame)
        cookie_row.pack(fill=tk.X, pady=2)
        ttk.Label(cookie_row, text="Cookie File:", width=18).pack(side=tk.LEFT)
        self.cookie_var = tk.StringVar()
        ttk.Entry(cookie_row, textvariable=self.cookie_var, width=55).pack(side=tk.LEFT, padx=5)
        ttk.Button(cookie_row, text="Browse", command=self.browse_cookie).pack(side=tk.LEFT)
        
        # ==================== Channel URL ====================
        channel_frame = ttk.LabelFrame(main_frame, text="📺 Kênh YouTube", padding="10")
        channel_frame.pack(fill=tk.X, pady=5)
        
        channel_row = ttk.Frame(channel_frame)
        channel_row.pack(fill=tk.X)
        ttk.Label(channel_row, text="URL Kênh:", width=18).pack(side=tk.LEFT)
        self.channel_url_var = tk.StringVar()
        ttk.Entry(channel_row, textvariable=self.channel_url_var, width=55).pack(side=tk.LEFT, padx=5)
        ttk.Button(channel_row, text="🔍 Quét Video", command=self.scan_channel).pack(side=tk.LEFT, padx=5)
        
        # ==================== Download Options ====================
        options_frame = ttk.LabelFrame(main_frame, text="📥 Tùy chọn tải", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Download type checkboxes
        type_frame = ttk.Frame(options_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Loại tải:").pack(side=tk.LEFT)
        
        self.download_video_var = tk.BooleanVar(value=True)
        self.download_audio_var = tk.BooleanVar(value=False)
        self.download_thumbnail_var = tk.BooleanVar(value=False)
        self.download_title_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(type_frame, text="🎬 Video (MP4/H264)", 
                       variable=self.download_video_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(type_frame, text="🎵 Âm thanh", 
                       variable=self.download_audio_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(type_frame, text="🖼️ Thumbnail (JPG)", 
                       variable=self.download_thumbnail_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(type_frame, text="📝 Tiêu đề (TXT)", 
                       variable=self.download_title_var).pack(side=tk.LEFT, padx=10)
        
        # Quick select buttons
        quick_frame = ttk.Frame(options_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(quick_frame, text="Chỉ Âm thanh", command=self.select_audio_only).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Tất cả", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="Bỏ chọn", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        
        # ==================== Quality Settings ====================
        quality_frame = ttk.LabelFrame(main_frame, text="🎯 Cài đặt chất lượng", padding="10")
        quality_frame.pack(fill=tk.X, pady=5)
        
        # Video quality row
        video_quality_row = ttk.Frame(quality_frame)
        video_quality_row.pack(fill=tk.X, pady=3)
        
        ttk.Label(video_quality_row, text="Chất lượng Video:", width=18).pack(side=tk.LEFT)
        self.video_quality_var = tk.StringVar(value="1080p")
        quality_combo = ttk.Combobox(video_quality_row, textvariable=self.video_quality_var, 
                                     values=["best", "1080p", "720p", "480p", "360p"], width=10, state="readonly")
        quality_combo.pack(side=tk.LEFT, padx=5)
        
        # FPS setting
        ttk.Label(video_quality_row, text="FPS:", width=6).pack(side=tk.LEFT, padx=10)
        self.video_fps_var = tk.StringVar(value="30")
        fps_combo = ttk.Combobox(video_quality_row, textvariable=self.video_fps_var,
                                 values=["original", "24", "25", "30", "60"], width=8, state="readonly")
        fps_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(video_quality_row, text="(MP4/H264)", foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # Audio format row
        audio_format_row = ttk.Frame(quality_frame)
        audio_format_row.pack(fill=tk.X, pady=3)
        
        ttk.Label(audio_format_row, text="Định dạng Audio:", width=18).pack(side=tk.LEFT)
        self.audio_format_var = tk.StringVar(value="mp3")
        audio_combo = ttk.Combobox(audio_format_row, textvariable=self.audio_format_var,
                                   values=["mp3", "m4a", "wav", "flac", "aac"], width=10, state="readonly")
        audio_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(audio_format_row, text="Bitrate:", width=8).pack(side=tk.LEFT, padx=10)
        self.audio_bitrate_var = tk.StringVar(value="320k")
        bitrate_combo = ttk.Combobox(audio_format_row, textvariable=self.audio_bitrate_var,
                                     values=["128k", "192k", "256k", "320k"], width=8, state="readonly")
        bitrate_combo.pack(side=tk.LEFT, padx=5)
        
        # Thumbnail settings row
        thumb_row = ttk.Frame(quality_frame)
        thumb_row.pack(fill=tk.X, pady=3)
        
        ttk.Label(thumb_row, text="Kích thước Thumbnail:", width=18).pack(side=tk.LEFT)
        self.thumb_size_var = tk.StringVar(value="maxres (1280x720)")
        thumb_combo = ttk.Combobox(thumb_row, textvariable=self.thumb_size_var,
                                   values=["maxres (1280x720)", "high (480x360)", 
                                          "medium (320x180)", "default (120x90)", "custom"],
                                   width=18, state="readonly")
        thumb_combo.pack(side=tk.LEFT, padx=5)
        thumb_combo.bind("<<ComboboxSelected>>", self.on_thumb_size_change)
        
        # Custom thumbnail size frame
        self.custom_thumb_frame = ttk.Frame(thumb_row)
        self.custom_thumb_frame.pack(side=tk.LEFT, padx=10)
        
        self.thumb_width_var = tk.StringVar(value="1280")
        self.thumb_height_var = tk.StringVar(value="720")
        
        # ==================== Filter Options ====================
        filter_frame = ttk.LabelFrame(main_frame, text="🔧 Bộ lọc Video", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Date filter
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, pady=3)
        
        self.use_date_filter = tk.BooleanVar(value=False)
        ttk.Checkbutton(date_frame, text="Lọc theo ngày đăng:", 
                       variable=self.use_date_filter, width=20).pack(side=tk.LEFT)
        
        ttk.Label(date_frame, text="Từ:").pack(side=tk.LEFT, padx=5)
        self.date_from_var = tk.StringVar(value="2020-01-01")
        ttk.Entry(date_frame, textvariable=self.date_from_var, width=12).pack(side=tk.LEFT)
        
        ttk.Label(date_frame, text="Đến:").pack(side=tk.LEFT, padx=5)
        self.date_to_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.date_to_var, width=12).pack(side=tk.LEFT)
        
        ttk.Label(date_frame, text="(YYYY-MM-DD)", foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # Duration filter
        duration_frame = ttk.Frame(filter_frame)
        duration_frame.pack(fill=tk.X, pady=3)
        
        self.use_duration_filter = tk.BooleanVar(value=False)
        ttk.Checkbutton(duration_frame, text="Lọc theo thời lượng:", 
                       variable=self.use_duration_filter, width=20).pack(side=tk.LEFT)
        
        ttk.Label(duration_frame, text="Từ:").pack(side=tk.LEFT, padx=5)
        self.duration_min_var = tk.StringVar(value="0")
        ttk.Entry(duration_frame, textvariable=self.duration_min_var, width=8).pack(side=tk.LEFT)
        
        ttk.Label(duration_frame, text="Đến:").pack(side=tk.LEFT, padx=5)
        self.duration_max_var = tk.StringVar(value="999")
        ttk.Entry(duration_frame, textvariable=self.duration_max_var, width=8).pack(side=tk.LEFT)
        
        ttk.Label(duration_frame, text="(phút)", foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # View filter
        view_frame = ttk.Frame(filter_frame)
        view_frame.pack(fill=tk.X, pady=3)
        
        self.use_view_filter = tk.BooleanVar(value=False)
        ttk.Checkbutton(view_frame, text="Lọc theo lượt xem:", 
                       variable=self.use_view_filter, width=20).pack(side=tk.LEFT)
        
        ttk.Label(view_frame, text="Từ:").pack(side=tk.LEFT, padx=5)
        self.view_min_var = tk.StringVar(value="0")
        ttk.Entry(view_frame, textvariable=self.view_min_var, width=12).pack(side=tk.LEFT)
        
        ttk.Label(view_frame, text="Đến:").pack(side=tk.LEFT, padx=5)
        self.view_max_var = tk.StringVar(value="999999999")
        ttk.Entry(view_frame, textvariable=self.view_max_var, width=12).pack(side=tk.LEFT)
        
        # ==================== Thread & Output Settings ====================
        output_frame = ttk.LabelFrame(main_frame, text="📁 Cài đặt xuất", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        # Thread count
        thread_row = ttk.Frame(output_frame)
        thread_row.pack(fill=tk.X, pady=3)
        
        ttk.Label(thread_row, text="Số luồng tải:", width=18).pack(side=tk.LEFT)
        self.thread_count_var = tk.StringVar(value="3")
        thread_spinbox = ttk.Spinbox(thread_row, from_=1, to=10, 
                                     textvariable=self.thread_count_var, width=5)
        thread_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(thread_row, text="(1-10 luồng song song)", 
                 foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # Output directory
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X, pady=3)
        
        ttk.Label(output_row, text="Thư mục lưu:", width=18).pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar(value=os.path.join(self.base_path, "downloads"))
        ttk.Entry(output_row, textvariable=self.output_dir_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_row, text="Browse", command=self.browse_output).pack(side=tk.LEFT, padx=5)
        
        # Filename format info
        format_row = ttk.Frame(output_frame)
        format_row.pack(fill=tk.X, pady=3)
        ttk.Label(format_row, text="Định dạng tên file:", width=18).pack(side=tk.LEFT)
        ttk.Label(format_row, text="YYYYMMDD_videoID (VD: 20251227_cpnTKFEHa74.mp4)", 
                 foreground="blue").pack(side=tk.LEFT)
        
        # ==================== Control Buttons ====================
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.download_btn = ttk.Button(control_frame, text="⬇️ Bắt đầu tải", 
                                       command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Dừng tải", 
                                   command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="🗑️ Xóa log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📂 Mở thư mục", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Lưu Settings", command=self.save_settings_manual).pack(side=tk.LEFT, padx=5)
        
        # Video count label
        self.video_count_label = ttk.Label(control_frame, text="Video: 0 | Sau lọc: 0")
        self.video_count_label.pack(side=tk.RIGHT, padx=10)
        
        # ==================== Progress ====================
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        self.progress_label = ttk.Label(progress_frame, text="Sẵn sàng")
        self.progress_label.pack()
        
        # ==================== Log Area ====================
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    # ==================== UI Helper Methods ====================
    
    def save_settings_manual(self):
        """Lưu settings thủ công"""
        self.save_settings()
        self.log("💾 Đã lưu settings!")
    
    def toggle_api_visibility(self):
        """Hiện/ẩn API key"""
        if self.show_api_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
            
    def on_thumb_size_change(self, event=None):
        """Xử lý khi thay đổi kích thước thumbnail"""
        for child in self.custom_thumb_frame.winfo_children():
            child.destroy()
            
        if self.thumb_size_var.get() == "custom":
            ttk.Label(self.custom_thumb_frame, text="W:").pack(side=tk.LEFT)
            ttk.Entry(self.custom_thumb_frame, textvariable=self.thumb_width_var, width=6).pack(side=tk.LEFT, padx=2)
            ttk.Label(self.custom_thumb_frame, text="H:").pack(side=tk.LEFT, padx=5)
            ttk.Entry(self.custom_thumb_frame, textvariable=self.thumb_height_var, width=6).pack(side=tk.LEFT, padx=2)
            
    def browse_cookie(self):
        """Chọn file cookie"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.cookie_var.set(filename)
            
    def browse_output(self):
        """Chọn thư mục xuất"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
            
    def open_output_folder(self):
        """Mở thư mục xuất"""
        output_dir = self.output_dir_var.get()
        if os.path.exists(output_dir):
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                subprocess.run(['open', output_dir])
            else:
                subprocess.run(['xdg-open', output_dir])
        else:
            messagebox.showwarning("Cảnh báo", "Thư mục chưa tồn tại!")
            
    def select_audio_only(self):
        """Chỉ chọn audio"""
        self.download_video_var.set(False)
        self.download_audio_var.set(True)
        self.download_thumbnail_var.set(False)
        self.download_title_var.set(False)
        
    def select_all(self):
        """Chọn tất cả"""
        self.download_video_var.set(True)
        self.download_audio_var.set(True)
        self.download_thumbnail_var.set(True)
        self.download_title_var.set(True)
        
    def deselect_all(self):
        """Bỏ chọn tất cả"""
        self.download_video_var.set(False)
        self.download_audio_var.set(False)
        self.download_thumbnail_var.set(False)
        self.download_title_var.set(False)
        
    def log(self, message):
        """Ghi log"""
        def _log():
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _log)
        
    def clear_log(self):
        """Xóa log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    # ==================== YouTube API Methods ====================
    
    def extract_channel_id(self, url):
        """Trích xuất Channel ID từ URL"""
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), pattern
        return None, None
        
    def get_channel_id_from_handle(self, handle, api_key):
        """Lấy Channel ID từ handle (@username)"""
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': handle,
            'type': 'channel',
            'key': api_key
        }
        response = self.session.get(url, params=params)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['snippet']['channelId']
        return None
        
    def get_channel_uploads_playlist(self, channel_id, api_key):
        """Lấy playlist ID chứa tất cả video của kênh"""
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'contentDetails',
            'id': channel_id,
            'key': api_key
        }
        response = self.session.get(url, params=params)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return None
        
    def get_all_videos(self, playlist_id, api_key):
        """Lấy tất cả video từ playlist"""
        videos = []
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        next_page_token = None
        
        while True:
            params = {
                'part': 'snippet,contentDetails',
                'playlistId': playlist_id,
                'maxResults': 50,
                'key': api_key
            }
            if next_page_token:
                params['pageToken'] = next_page_token
                
            response = self.session.get(url, params=params)
            data = response.json()
            
            if 'error' in data:
                self.log(f"❌ API Error: {data['error']['message']}")
                break
                
            if 'items' in data:
                for item in data['items']:
                    video_id = item['contentDetails']['videoId']
                    thumbnails = item['snippet'].get('thumbnails', {})
                    videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnails': thumbnails
                    })
                    
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
                
            self.log(f"📊 Đã quét {len(videos)} video...")
            
        return videos
        
    def get_video_details(self, video_ids, api_key):
        """Lấy thông tin chi tiết video (duration, views)"""
        details = {}
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'contentDetails,statistics',
                'id': ','.join(batch),
                'key': api_key
            }
            response = self.session.get(url, params=params)
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    duration_str = item['contentDetails']['duration']
                    duration_seconds = self.parse_duration(duration_str)
                    view_count = int(item['statistics'].get('viewCount', 0))
                    details[item['id']] = {
                        'duration': duration_seconds,
                        'views': view_count
                    }
        return details
        
    def parse_duration(self, duration_str):
        """Parse ISO 8601 duration to seconds"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
        
    def scan_channel(self):
        """Quét tất cả video từ kênh"""
        api_key = self.api_key_var.get().strip()
        channel_url = self.channel_url_var.get().strip()
        
        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập YouTube API Key!")
            return
            
        if not channel_url:
            messagebox.showerror("Lỗi", "Vui lòng nhập URL kênh YouTube!")
            return
            
        threading.Thread(target=self._scan_channel_thread, daemon=True).start()
        
    def _scan_channel_thread(self):
        """Thread quét kênh"""
        try:
            api_key = self.api_key_var.get().strip()
            channel_url = self.channel_url_var.get().strip()
            
            self.log("🔍 Đang phân tích URL kênh...")
            
            identifier, pattern = self.extract_channel_id(channel_url)
            if not identifier:
                self.log("❌ Không thể phân tích URL kênh!")
                return
                
            if 'channel/' in pattern:
                channel_id = identifier
            else:
                self.log(f"🔎 Đang tìm Channel ID cho: {identifier}")
                channel_id = self.get_channel_id_from_handle(identifier, api_key)
                
            if not channel_id:
                self.log("❌ Không tìm thấy Channel ID!")
                return
                
            self.log(f"✅ Channel ID: {channel_id}")
            
            playlist_id = self.get_channel_uploads_playlist(channel_id, api_key)
            if not playlist_id:
                self.log("❌ Không tìm thấy playlist uploads!")
                return
                
            self.log(f"📁 Uploads Playlist: {playlist_id}")
            self.log("📥 Đang quét video từ kênh...")
            
            videos = self.get_all_videos(playlist_id, api_key)
            
            if not videos:
                self.log("❌ Không tìm thấy video nào!")
                return
                
            self.log("📊 Đang lấy thông tin chi tiết video...")
            video_ids = [v['id'] for v in videos]
            details = self.get_video_details(video_ids, api_key)
            
            for video in videos:
                if video['id'] in details:
                    video.update(details[video['id']])
                else:
                    video['duration'] = 0
                    video['views'] = 0
                    
            self.videos = videos
            filtered_count = len(self.filter_videos())
            
            self.root.after(0, lambda: self.video_count_label.config(
                text=f"Video: {len(videos)} | Sau lọc: {filtered_count}"
            ))
            self.log(f"✅ Hoàn tất! Tìm thấy {len(videos)} video.")
            
        except Exception as e:
            self.log(f"❌ Lỗi: {str(e)}")
            
    # ==================== Filter Methods ====================
    
    def filter_videos(self):
        """Lọc video theo các tiêu chí"""
        filtered = self.videos.copy()
        
        if self.use_date_filter.get():
            try:
                date_from = datetime.strptime(self.date_from_var.get(), "%Y-%m-%d")
                date_to = datetime.strptime(self.date_to_var.get(), "%Y-%m-%d")
                filtered = [
                    v for v in filtered 
                    if date_from <= datetime.strptime(v['published_at'][:10], "%Y-%m-%d") <= date_to
                ]
            except ValueError:
                self.log("⚠️ Lỗi định dạng ngày! Sử dụng YYYY-MM-DD")
                
        if self.use_duration_filter.get():
            try:
                min_duration = float(self.duration_min_var.get()) * 60
                max_duration = float(self.duration_max_var.get()) * 60
                filtered = [
                    v for v in filtered 
                    if min_duration <= v.get('duration', 0) <= max_duration
                ]
            except ValueError:
                self.log("⚠️ Lỗi định dạng thời lượng!")
                
        if self.use_view_filter.get():
            try:
                min_views = int(self.view_min_var.get())
                max_views = int(self.view_max_var.get())
                filtered = [
                    v for v in filtered 
                    if min_views <= v.get('views', 0) <= max_views
                ]
            except ValueError:
                self.log("⚠️ Lỗi định dạng lượt xem!")
                
        return filtered
        
    # ==================== Download Methods ====================
    
    def get_filename_base(self, video):
        """Tạo tên file theo định dạng: YYYYMMDD_videoID"""
        published_date = video['published_at'][:10].replace('-', '')
        video_id = video['id']
        return f"{published_date}_{video_id}"
        
    def get_target_thumbnail_size(self):
        """Lấy kích thước thumbnail mục tiêu"""
        size_map = {
            "maxres (1280x720)": (1280, 720),
            "high (480x360)": (480, 360),
            "medium (320x180)": (320, 180),
            "default (120x90)": (120, 90),
        }
        
        selected = self.thumb_size_var.get()
        
        if selected == "custom":
            try:
                width = int(self.thumb_width_var.get())
                height = int(self.thumb_height_var.get())
                return (width, height)
            except ValueError:
                return (1280, 720)
        
        return size_map.get(selected, (1280, 720))
        
    def get_thumbnail_url(self, video):
        """Lấy URL thumbnail phù hợp nhất"""
        thumbnails = video.get('thumbnails', {})
        priority = ['maxres', 'standard', 'high', 'medium', 'default']
        
        for quality in priority:
            if quality in thumbnails and thumbnails[quality].get('url'):
                return thumbnails[quality]['url']
                
        return None
        
    def download_and_convert_thumbnail(self, video, output_dir, filename_base):
        """Tải và chuyển đổi thumbnail sang JPG với kích thước mong muốn"""
        try:
            thumb_url = self.get_thumbnail_url(video)
            if not thumb_url:
                self.log(f"⚠️ Không tìm thấy thumbnail cho {filename_base}")
                return False
                
            # Use session for connection pooling (faster)
            response = self.session.get(thumb_url, timeout=30)
            if response.status_code != 200:
                self.log(f"⚠️ Không thể tải thumbnail: HTTP {response.status_code}")
                return False
                
            img = Image.open(io.BytesIO(response.content))
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            target_size = self.get_target_thumbnail_size()
            if img.size != target_size:
                # Use BILINEAR for faster processing, LANCZOS is CPU-intensive
                img = img.resize(target_size, Image.Resampling.BILINEAR)
                
            output_path = os.path.join(output_dir, f"{filename_base}.jpg")
            # Use lower quality JPEG for faster saving and smaller file size
            img.save(output_path, 'JPEG', quality=85, optimize=False)
            
            return True
            
        except Exception as e:
            self.log(f"⚠️ Lỗi xử lý thumbnail: {str(e)}")
            return False
            
    def start_download(self):
        """Bắt đầu tải"""
        if not self.videos:
            messagebox.showerror("Lỗi", "Vui lòng quét kênh trước!")
            return
            
        if not any([self.download_video_var.get(), self.download_audio_var.get(),
                    self.download_thumbnail_var.get(), self.download_title_var.get()]):
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất một loại nội dung để tải!")
            return
            
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=self._download_thread, daemon=True).start()
        
    def stop_download(self):
        """Dừng tải"""
        self.is_downloading = False
        self.log("⏹️ Đang dừng tải...")
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def _download_thread(self):
        """Thread tải xuống"""
        try:
            filtered_videos = self.filter_videos()
            self.log(f"📊 Số video cần tải: {len(filtered_videos)}")
            
            if not filtered_videos:
                self.log("❌ Không có video nào phù hợp với bộ lọc!")
                return
                
            output_dir = self.output_dir_var.get()
            os.makedirs(output_dir, exist_ok=True)
            
            thread_count = int(self.thread_count_var.get())
            total = len(filtered_videos)
            completed = 0
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                self.download_executor = executor
                futures = {
                    executor.submit(self.download_single_video, video, output_dir): video 
                    for video in filtered_videos
                }
                
                for future in as_completed(futures):
                    if not self.is_downloading:
                        break
                        
                    video = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        self.log(f"❌ Lỗi tải {video['id']}: {str(e)}")
                        
                    completed += 1
                    progress = (completed / total) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda c=completed, t=total: 
                                   self.progress_label.config(text=f"Đã tải: {c}/{t}"))
                    
            if self.is_downloading:
                self.log("✅ Hoàn tất tải xuống!")
            else:
                self.log("⏹️ Đã dừng tải!")
                
        except Exception as e:
            self.log(f"❌ Lỗi: {str(e)}")
        finally:
            self.is_downloading = False
            self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            
    def download_single_video(self, video, output_dir):
        """Tải một video với các tùy chọn đã chọn"""
        if not self.is_downloading:
            return
            
        video_id = video['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        filename_base = self.get_filename_base(video)
        
        self.log(f"📥 Đang tải: {filename_base}")
        
        # Build yt-dlp command base
        base_cmd = [self.ytdlp_path]
        
        # Add cookie if specified
        cookie_file = self.cookie_var.get().strip()
        if cookie_file and os.path.exists(cookie_file):
            base_cmd.extend(['--cookies', cookie_file])
            
        # Add ffmpeg location
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path) if os.path.exists(self.ffmpeg_path) else None
        if ffmpeg_dir:
            base_cmd.extend(['--ffmpeg-location', ffmpeg_dir])
            
        # ========== Download Video (MP4/H264 với FPS tùy chọn) ==========
        if self.download_video_var.get():
            quality = self.video_quality_var.get()
            fps = self.video_fps_var.get()
            
            if quality == "best":
                format_str = "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            else:
                height = quality.replace('p', '')
                format_str = f"bestvideo[height<={height}][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best"
            
            output_file = os.path.join(output_dir, f'{filename_base}.mp4')
            
            # Optimize: Use stream copy when possible to avoid CPU-intensive re-encoding
            if fps == "original":
                # Use copy codec to avoid re-encoding (much faster, less CPU)
                ffmpeg_args = '-c:v copy -c:a copy'
            else:
                # Only re-encode when FPS conversion is needed
                ffmpeg_args = f'-c:v libx264 -preset ultrafast -r {fps} -c:a aac'
            
            cmd = base_cmd + [
                '-f', format_str,
                '-o', output_file,
                '--merge-output-format', 'mp4',
                '--postprocessor-args', f'ffmpeg:{ffmpeg_args}',
                '--no-playlist',
                # Performance optimizations for faster downloads
                '--concurrent-fragments', '4',
                '--buffer-size', '16K',
                '--http-chunk-size', '10M',
                video_url
            ]
            self._run_command(cmd, f"Video {filename_base}")
            
        # ========== Download Audio ==========
        if self.download_audio_var.get():
            audio_format = self.audio_format_var.get()
            audio_bitrate = self.audio_bitrate_var.get()
            
            output_file = os.path.join(output_dir, f'{filename_base}.{audio_format}')
            
            cmd = base_cmd + [
                '-x',
                '--audio-format', audio_format,
                '--audio-quality', audio_bitrate,
                '-o', output_file,
                '--no-playlist',
                # Performance optimizations
                '--concurrent-fragments', '4',
                '--buffer-size', '16K',
                video_url
            ]
            self._run_command(cmd, f"Audio {filename_base}")
            
        # ========== Download Thumbnail (JPG với kích thước tùy chọn) ==========
        if self.download_thumbnail_var.get():
            success = self.download_and_convert_thumbnail(video, output_dir, filename_base)
            if success:
                self.log(f"🖼️ Đã tải thumbnail: {filename_base}.jpg")
                    
        # ========== Save Title (TXT - chỉ chứa tiêu đề) ==========
        if self.download_title_var.get():
            title_path = os.path.join(output_dir, f'{filename_base}.txt')
            with open(title_path, 'w', encoding='utf-8') as f:
                f.write(video['title'])
            self.log(f"📝 Đã lưu tiêu đề: {filename_base}.txt")
                
    def _run_command(self, cmd, description=""):
        """Chạy command và capture output"""
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )
            # Increase timeout to 30 minutes for large files
            stdout, stderr = process.communicate(timeout=1800)
            
            if process.returncode == 0:
                self.log(f"✅ {description} - Thành công")
            else:
                error_msg = stderr[:200] if stderr else "Unknown error"
                self.log(f"⚠️ {description} - Lỗi: {error_msg}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            self.log(f"⚠️ {description} - Timeout (quá 30 phút)")
        except Exception as e:
            self.log(f"❌ {description} - Command error: {str(e)}")


def main():
    root = tk.Tk()
    app = YouTubeChannelDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()