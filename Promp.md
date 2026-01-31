hãy giúp tôi tạo một code py giúp tải dữ liệu từ 1 kênh youtube bằng ytdlp và ffmeg.
tôi sẽ gửi đường dẫn 1 kênh yotube cụ thể , tool sẽ quét toàn bộ video từ kênh yotube đó bằng API YOUTUBE V3.

Dữ liệu cần tải về bằng yt-dlp và ffmeg:
tải video
tải âm thanh
tải tiêu đề
tải thumnail

tôi có thể tải các dữ liệu trên riêng lẻ hoặc theo bộ ( chỉ âm thanh hoặc toàn bộ video , tiêu đề, thumnail, âm thanh.
tôi có thể lọc để tải video về theo:
tải video theo khoảng thời gian
tải video theo thời lượng
tải video theo view

setting được luồng tải cùng lúc
có thể thêm cookie, api
hiện lên UI để tôi nhập thông số dễ dàng

- không gom tệp tải về vào thư mục riêng cho từng video, để trực tiếp ở thư mục người dùng setting
- tên tệp để ở định dạng : Ngày tháng năm đăng tải_id video (ví dụ: 20251227_cpnTKFEHa74)
- tệp tiêu đề đuôi mặc định phải là txt
- tệp tiêu đề chỉ chứa tiêu đề không chứa gì khác
- tệp video tải về phải là mp4 , h264, tôi có thể tùy chình FPS nhưng mặc định là 30fps
- tệp ảnh tải về phải là định dạng jpg ( nếu là định dạng webp phải tiến hành chuyển đổi qua jpg thực sự, chứ không chỉ là đổi đuôi file)
- tôi có thể tùy chọn kích thước ảnh tải về, nếu file tải về chưa phù hợp phải tiến hành fix kích thước

Thư mục : tôi sẽ để chung tool cùng với công cụ ffmeg và yt dlp
