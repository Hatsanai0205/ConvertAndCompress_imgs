import os
from flask import Flask, request, send_file
from PIL import Image
import zipfile
import io

app = Flask(__name__)

# สร้างโฟลเดอร์สำหรับเก็บไฟล์ที่อัปโหลด
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# กำหนดให้ Flask ใช้โฟลเดอร์นี้ในการอัปโหลดไฟล์
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ฟังก์ชันในการลดขนาดไฟล์ JPG
def compress_jpg(img, quality=85):
    jpg_io = io.BytesIO()
    img.save(jpg_io, 'JPEG', quality=quality, optimize=True)
    jpg_io.seek(0)
    return jpg_io

# ฟังก์ชันในการแปลง PNG เป็น JPG
def convert_png_to_jpg(png_file):
    img = Image.open(png_file)
    img = img.convert('RGB')  # แปลงเป็น RGB ก่อนบันทึกเป็น JPG
    jpg_io = compress_jpg(img, quality=85)  # ลดขนาด JPG
    return jpg_io

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    # ตรวจสอบว่าเป็นไฟล์ ZIP หรือไฟล์ PNG/JPG เดี่ยวๆ
    if 'zipfile' in request.files:
        file = request.files['zipfile']
        
        if not file.filename.endswith('.zip'):
            return 'The file is not a ZIP file', 400
        
        # สร้างไฟล์ ZIP ที่จะบรรจุไฟล์ JPG ที่แปลงแล้ว
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # แกะไฟล์ ZIP ที่ผู้ใช้ส่งมา
            with zipfile.ZipFile(file, 'r') as uploaded_zip:
                # วนรอบไฟล์ใน ZIP
                for zip_file in uploaded_zip.namelist():
                    # ตรวจสอบว่าไฟล์เป็น PNG หรือ JPG
                    if zip_file.endswith('.png'):
                        with uploaded_zip.open(zip_file) as img_file:
                            jpg_io = convert_png_to_jpg(img_file)  # แปลง PNG เป็น JPG
                            zipf.writestr(zip_file.rsplit('.', 1)[0] + '.jpg', jpg_io.read())  # เพิ่ม JPG ลงใน ZIP
                    elif zip_file.endswith('.jpg') or zip_file.endswith('.jpeg'):
                        with uploaded_zip.open(zip_file) as img_file:
                            img = Image.open(img_file)
                            jpg_io = compress_jpg(img, quality=85)  # ลดขนาด JPG
                            zipf.writestr(zip_file, jpg_io.read())  # เพิ่ม JPG ที่ลดขนาดแล้วลงใน ZIP
        
        zip_io.seek(0)
        return send_file(zip_io, as_attachment=True, download_name='compressed_images.zip', mimetype='application/zip')

    # ถ้าเป็นไฟล์ PNG หรือ JPG เดี่ยวๆ
    if 'image' in request.files:
        file = request.files['image']
        
        if file.filename.endswith('.png'):
            # ถ้าเป็น PNG, แปลงเป็น JPG
            jpg_io = convert_png_to_jpg(file)
            return send_file(jpg_io, as_attachment=True, download_name='converted_image.jpg', mimetype='image/jpeg')
        
        elif file.filename.endswith('.jpg') or file.filename.endswith('.jpeg'):
            # ถ้าเป็น JPG, ลดขนาด
            img = Image.open(file)
            jpg_io = compress_jpg(img, quality=85)
            return send_file(jpg_io, as_attachment=True, download_name='compressed_image.jpg', mimetype='image/jpeg')

    return 'No file part', 400

if __name__ == '__main__':
    app.run(debug=True)
