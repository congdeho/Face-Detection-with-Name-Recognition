# 🎓 Hệ thống Điểm danh Học sinh - Face Recognition

## 📋 Tổng quan
Hệ thống điểm danh học sinh tự động sử dụng công nghệ nhận diện khuôn mặt (Face Recognition), được phát triển bằng Python với giao diện đồ họa thân thiện.

## ✨ Tính năng chính

### 👥 Quản lý Học sinh
- ➕ Thêm/sửa/xóa thông tin học sinh
- 📸 Thu thập và quản lý ảnh khuôn mặt
- 🏫 Quản lý lớp học và khóa học
- 🔍 Tìm kiếm và lọc học sinh

### ✅ Điểm danh Tự động
- 🎯 Nhận diện khuôn mặt realtime qua webcam
- ⏰ Ghi nhận thời gian vào/ra tự động
- 👤 Xử lý nhiều khuôn mặt cùng lúc
- 🎚️ Điều chỉnh độ tin cậy nhận diện

### 📊 Báo cáo & Thống kê
- 📈 Báo cáo điểm danh theo ngày/tháng
- 📋 Thống kê tỷ lệ vắng mặt
- 📄 Xuất báo cáo Excel/PDF
- 📊 Biểu đồ trực quan

### 💾 Quản lý Dữ liệu
- 🗄️ Database SQLite tích hợp
- 🔄 Backup và restore dữ liệu
- 🔒 Bảo mật thông tin học sinh
- 📱 Giao diện thân thiện

## 🏗️ Kiến trúc Hệ thống

```
📁 attendance_system/
├── 📁 core/                    # Modules cốt lõi
│   ├── face_recognizer.py      # Engine nhận diện khuôn mặt
│   ├── face_trainer.py         # Training model
│   └── face_detector.py        # Phát hiện khuôn mặt
├── 📁 database/               # Lớp dữ liệu
│   └── models.py              # Quản lý database
├── 📁 gui/                    # Giao diện người dùng
│   └── main_app.py            # GUI chính
├── 📁 utils/                  # Tiện ích
│   ├── config.py              # Cấu hình
│   └── report_generator.py    # Tạo báo cáo
├── 📁 data/                   # Dữ liệu
│   ├── attendance.db          # Database chính
│   └── 📁 students/           # Ảnh học sinh
└── main.py                    # File khởi chạy
```

## 🚀 Cài đặt và Sử dụng

### Bước 1: Cài đặt Python Dependencies
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi chạy Ứng dụng
```bash
cd attendance_system
python main.py
```

### Bước 3: Thiết lập Ban đầu
1. **Tạo Lớp học**: Vào tab "Cài đặt" → Thêm lớp học mới
2. **Thêm Học sinh**: Vào tab "Quản lý Học sinh" → Thêm thông tin học sinh
3. **Thu thập Ảnh**: Chọn học sinh → Click "Thu thập Ảnh" → Chụp 50-100 ảnh
4. **Training Model**: Chạy `02_face_training_fixed.py` để train model
5. **Bắt đầu Điểm danh**: Vào tab "Điểm danh" → Tạo phiên điểm danh

## 📱 Hướng dẫn Sử dụng

### Quản lý Học sinh
1. Mở tab **"👥 Quản lý Học sinh"**
2. Chọn lớp học từ dropdown
3. Điền thông tin học sinh: Mã HS, Họ tên, Email, SĐT
4. Click **"➕ Thêm Học sinh"**

### Thu thập Ảnh Training
1. Chọn học sinh trong danh sách
2. Click **"📸 Thu thập Ảnh"**
3. Webcam sẽ mở → Chụp 50-100 ảnh từ nhiều góc độ
4. Ảnh được lưu tự động vào thư mục `dataset/`

### Điểm danh Tự động
1. Mở tab **"✅ Điểm danh"**
2. Nhập tên phiên và chọn lớp
3. Click **"🚀 Bắt đầu Điểm danh"**
4. Webcam sẽ nhận diện và ghi nhận tự động
5. Click **"⏹️ Kết thúc"** khi hoàn tất

### Xem Báo cáo
1. Mở tab **"📊 Báo cáo"**
2. Chọn loại báo cáo: Ngày/Tháng/Học kỳ
3. Chọn lớp học và khoảng thời gian
4. Click **"📋 Tạo Báo cáo"** → Xuất Excel/PDF

## 🔧 Cấu hình Nâng cao

### Điều chỉnh Độ tin cậy Nhận diện
Sửa file `attendance_system/utils/config.py`:
```python
CONFIDENCE_THRESHOLD = 60  # Tăng để giảm false positive
```

### Thay đổi Camera
```python
CAMERA_ID = 0  # 0 = camera mặc định, 1 = camera ngoài
```

### Cấu hình Database
```python
DATABASE_PATH = "attendance_system/data/attendance.db"
```

## 📊 Database Schema

### Bảng Classes (Lớp học)
- `id`: ID tự động
- `class_name`: Tên lớp
- `class_code`: Mã lớp  
- `description`: Mô tả

### Bảng Students (Học sinh)
- `id`: ID tự động
- `student_id`: Mã học sinh
- `full_name`: Họ và tên
- `class_id`: ID lớp học
- `email`, `phone`: Thông tin liên hệ

### Bảng Attendance_Sessions (Phiên điểm danh)
- `id`: ID phiên
- `session_name`: Tên phiên
- `class_id`: ID lớp
- `session_date`: Ngày điểm danh
- `start_time`, `end_time`: Thời gian

### Bảng Attendance_Records (Bản ghi điểm danh)
- `id`: ID bản ghi
- `session_id`: ID phiên
- `student_id`: ID học sinh
- `check_in_time`: Thời gian vào
- `check_out_time`: Thời gian ra
- `status`: Trạng thái (present/absent/late)
- `confidence_score`: Độ tin cậy

## 🛠️ Yêu cầu Hệ thống

### Phần cứng
- **CPU**: Intel i3 hoặc tương đương
- **RAM**: 4GB trở lên
- **Webcam**: HD 720p hoặc cao hơn
- **Ổ cứng**: 2GB dung lượng trống

### Phần mềm
- **OS**: Windows 10/11, macOS, Ubuntu 18.04+
- **Python**: 3.8 trở lên
- **Webcam drivers**: Đã cài đặt

## 🔍 Troubleshooting

### Lỗi Camera không hoạt động
```bash
# Kiểm tra camera
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Lỗi Import Module
```bash
# Cài đặt lại dependencies
pip install --upgrade -r requirements.txt
```

### Lỗi Nhận diện kém
1. Thu thập thêm ảnh training (100+ ảnh/người)
2. Đảm bảo ánh sáng đủ khi chụp
3. Chụp từ nhiều góc độ khác nhau
4. Giảm `CONFIDENCE_THRESHOLD` trong config

### Lỗi Database
```bash
# Reset database
rm attendance_system/data/attendance.db
python attendance_system/database/models.py
```

## 📈 Roadmap Phát triển

### Version 2.0 (Kế hoạch)
- 🌐 **Web Interface**: Giao diện web responsive
- 📱 **Mobile App**: Ứng dụng di động
- ☁️ **Cloud Sync**: Đồng bộ dữ liệu cloud
- 🤖 **AI Enhancement**: Cải thiện thuật toán AI
- 🔔 **Notifications**: Thông báo realtime
- 📧 **Email Reports**: Gửi báo cáo tự động

### Version 2.1 (Tương lai)
- 🎭 **Mask Detection**: Nhận diện với khẩu trang
- 🌡️ **Temperature Check**: Đo thân nhiệt tích hợp
- 🔊 **Voice Alerts**: Thông báo bằng giọng nói
- 📍 **Location Tracking**: Theo dõi vị trí

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng:
1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - Xem file `LICENSE` để biết chi tiết.

## 📞 Hỗ trợ

- **Email**: support@attendance-system.com
- **GitHub Issues**: [Create Issue](https://github.com/your-repo/issues)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

**🎓 Được phát triển với ❤️ cho giáo dục Việt Nam**