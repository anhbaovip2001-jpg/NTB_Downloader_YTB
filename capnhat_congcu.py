# update_tools.py
# Chạy file này trong thư mục chứa yt-dlp.exe và ffmpeg.exe (không tạo thư mục con).
# Python 3.8+ khuyến nghị.

import os
import sys
import json
import time
import shutil
import zipfile
import platform
import subprocess
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))

YTDLP_CANDIDATES = ["yt-dlp.exe", "yt-dlp"]  # hỗ trợ trường hợp bạn đặt tên không có .exe
FFMPEG_EXE = "ffmpeg.exe"
FFPROBE_EXE = "ffprobe.exe"
FFPLAY_EXE = "ffplay.exe"

# URL ổn định cho yt-dlp (Windows exe)
YTDLP_DIRECT_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

# Ưu tiên lấy ffmpeg từ GitHub API (BtbN), fallback sang gyan.dev nếu lỗi
BTBN_LATEST_API = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
GYAN_ESSENTIALS_ZIP = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def log(msg: str) -> None:
    print(msg, flush=True)


def is_windows() -> bool:
    return os.name == "nt"


def pick_arch_tag() -> str:
    # Windows đa số là 64-bit
    arch, _ = platform.architecture()
    return "win64" if "64" in arch else "win32"


def safe_remove(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        raise RuntimeError(f"Không xoá được file: {path} | Lỗi: {e}")


def download_file(url: str, dest_path: str, desc: str = "") -> None:
    tmp_path = dest_path + ".download"
    safe_remove(tmp_path)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
    }
    req = urllib.request.Request(url, headers=headers)

    log(f"⬇️  Tải {desc or os.path.basename(dest_path)} ...")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = resp.headers.get("Content-Length")
            total = int(total) if total and total.isdigit() else None

            downloaded = 0
            last_print = 0.0
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_print >= 0.2:
                        last_print = now
                        if total:
                            pct = downloaded * 100.0 / total
                            log(f"   ... {pct:6.2f}% ({downloaded/1024/1024:.2f} MB)")
                        else:
                            log(f"   ... {downloaded/1024/1024:.2f} MB")
    except urllib.error.URLError as e:
        safe_remove(tmp_path)
        raise RuntimeError(f"Tải thất bại: {url}\nLỗi mạng: {e}")
    except Exception as e:
        safe_remove(tmp_path)
        raise RuntimeError(f"Tải thất bại: {url}\nLỗi: {e}")

    # Đổi tên sang file thật (tránh file dở dang)
    safe_remove(dest_path)
    os.replace(tmp_path, dest_path)
    log("✅ Tải xong.")


def run_cmd(cmd, cwd=None) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, "Không tìm thấy file để chạy."
    except Exception as e:
        return 1, f"Lỗi khi chạy lệnh: {e}"


def find_existing_ytdlp() -> str | None:
    for name in YTDLP_CANDIDATES:
        path = os.path.join(HERE, name)
        if os.path.isfile(path):
            return path
    return None


def ensure_ytdlp() -> str:
    path = find_existing_ytdlp()

    # Nếu đã có: thử tự cập nhật
    if path:
        log(f"🔧 Đã có yt-dlp: {os.path.basename(path)} -> thử tự cập nhật (-U)")
        code, out = run_cmd([path, "-U"], cwd=HERE)

        # Có bản yt-dlp sẽ trả code=0, nhưng cũng có trường hợp trả khác 0 dù đã tải.
        # Ta kiểm tra lại bằng --version.
        vcode, vout = run_cmd([path, "--version"], cwd=HERE)
        if vcode == 0 and vout:
            log(f"✅ yt-dlp phiên bản: {vout}")
        else:
            log("⚠️  Không đọc được phiên bản yt-dlp sau khi cập nhật.")
            if out:
                log(out)
        return path

    # Nếu chưa có: tải về
    log("📌 Chưa có yt-dlp -> tải mới.")
    dest = os.path.join(HERE, "yt-dlp.exe" if is_windows() else "yt-dlp")
    download_file(YTDLP_DIRECT_URL, dest, desc="yt-dlp.exe")
    if is_windows():
        # Trên Windows không cần chmod
        pass
    else:
        try:
            os.chmod(dest, 0o755)
        except Exception:
            pass

    vcode, vout = run_cmd([dest, "--version"], cwd=HERE)
    if vcode == 0 and vout:
        log(f"✅ yt-dlp phiên bản: {vout}")
    return dest


def github_latest_ffmpeg_zip_url() -> tuple[str, str]:
    """
    Trả về (url, filename) của gói zip phù hợp từ BtbN.
    Ưu tiên bản 'gpl' (tĩnh), nếu không có thì lấy 'gpl-shared'.
    """
    arch = pick_arch_tag()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github+json",
    }
    req = urllib.request.Request(BTBN_LATEST_API, headers=headers)

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))

    assets = data.get("assets", []) or []

    # Ưu tiên thứ tự:
    preferred_names = [
        f"ffmpeg-master-latest-{arch}-gpl.zip",
        f"ffmpeg-master-latest-{arch}-gpl-shared.zip",
        f"ffmpeg-master-latest-{arch}.zip",
    ]

    # Tạo map nhanh theo tên
    by_name = {a.get("name", ""): a for a in assets if a.get("name")}

    for name in preferred_names:
        a = by_name.get(name)
        if a and a.get("browser_download_url"):
            return a["browser_download_url"], name

    # Nếu không khớp đúng tên: thử tìm gần đúng
    lower_assets = [(a.get("name", ""), a.get("browser_download_url", "")) for a in assets]
    for nm, url in lower_assets:
        if url and nm.lower().endswith(".zip") and arch in nm.lower() and "gpl" in nm.lower() and "ffmpeg" in nm.lower():
            return url, nm

    raise RuntimeError("Không tìm thấy gói ffmpeg zip phù hợp từ BtbN (GitHub).")


def extract_exes_from_zip(zip_path: str, target_dir: str) -> dict:
    """
    Giải nén đúng các file exe cần thiết từ zip và chép thẳng vào target_dir (không tạo thư mục con).
    Trả về dict {ten_file: duong_dan}
    """
    want = {FFMPEG_EXE.lower(), FFPROBE_EXE.lower(), FFPLAY_EXE.lower()}
    extracted = {}

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()

        for member in names:
            base = os.path.basename(member)
            if not base:
                continue
            base_l = base.lower()
            if base_l in want and member.lower().endswith(".exe"):
                dest = os.path.join(target_dir, base)
                # Chép đè an toàn: ghi ra file tạm trước
                tmp = dest + ".new"
                safe_remove(tmp)
                with z.open(member, "r") as src, open(tmp, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                safe_remove(dest)
                os.replace(tmp, dest)
                extracted[base] = dest

    if FFMPEG_EXE not in extracted:
        raise RuntimeError("Giải nén không thấy ffmpeg.exe trong gói zip (cấu trúc gói có thể đã thay đổi).")

    return extracted


def ensure_ffmpeg() -> dict:
    """
    Tải/cập nhật ffmpeg (và ffprobe/ffplay nếu có), lưu thẳng tại thư mục HERE.
    """
    log("🔧 Cập nhật ffmpeg...")

    zip_tmp = os.path.join(HERE, "_ffmpeg_update.zip")
    safe_remove(zip_tmp)

    # 1) Thử tải từ BtbN (GitHub)
    try:
        url, name = github_latest_ffmpeg_zip_url()
        log(f"📌 Nguồn: BtbN (GitHub) | Gói: {name}")
        download_file(url, zip_tmp, desc=name)
    except Exception as e:
        log("⚠️  Không tải được từ BtbN (GitHub). Chuyển sang nguồn dự phòng.")
        log(f"   Chi tiết: {e}")
        log("📌 Nguồn dự phòng: gyan.dev | Gói: essentials")
        download_file(GYAN_ESSENTIALS_ZIP, zip_tmp, desc="ffmpeg-release-essentials.zip")

    # 2) Giải nén đúng exe, chép thẳng vào HERE
    extracted = extract_exes_from_zip(zip_tmp, HERE)

    # 3) Dọn file zip tạm
    safe_remove(zip_tmp)

    # 4) In phiên bản
    ffmpeg_path = extracted.get(FFMPEG_EXE) or os.path.join(HERE, FFMPEG_EXE)
    code, out = run_cmd([ffmpeg_path, "-version"], cwd=HERE)
    if code == 0 and out:
        first_line = out.splitlines()[0].strip()
        log(f"✅ ffmpeg: {first_line}")
    else:
        log("⚠️  Đã chép ffmpeg.exe nhưng không chạy được để đọc phiên bản. Hãy thử chạy bằng tay.")
        if out:
            log(out)

    return extracted


def main() -> int:
    log("======================================")
    log("CẬP NHẬT yt-dlp + ffmpeg (cùng thư mục)")
    log("======================================")
    log(f"📁 Thư mục: {HERE}")

    if not is_windows():
        log("⚠️  Script này tối ưu cho Windows (vì dùng .exe). Bạn vẫn có thể thử, nhưng có thể cần chỉnh thêm.")

    # Nhắc người dùng đóng chương trình đang dùng ffmpeg/yt-dlp để tránh bị khoá file
    log("📌 Lưu ý: nếu đang có chương trình dùng ffmpeg/yt-dlp, hãy đóng trước để tránh lỗi ghi đè.")

    try:
        ytdlp_path = ensure_ytdlp()
    except Exception as e:
        log(f"❌ Lỗi khi cập nhật yt-dlp: {e}")
        ytdlp_path = None

    try:
        extracted = ensure_ffmpeg()
    except Exception as e:
        log(f"❌ Lỗi khi cập nhật ffmpeg: {e}")
        extracted = {}

    log("======================================")
    log("KẾT QUẢ")
    log("======================================")
    if ytdlp_path:
        log(f"✅ yt-dlp: {os.path.basename(ytdlp_path)}")
    else:
        log("❌ yt-dlp: thất bại")

    if os.path.exists(os.path.join(HERE, FFMPEG_EXE)):
        log(f"✅ ffmpeg: {FFMPEG_EXE}")
    else:
        log("❌ ffmpeg: thất bại")

    if extracted:
        extra = [k for k in extracted.keys() if k.lower() != FFMPEG_EXE.lower()]
        if extra:
            log("➕ Có thêm: " + ", ".join(extra))

    log("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
