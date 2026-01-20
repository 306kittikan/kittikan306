FROM python:3.10-slim

WORKDIR /app

# 1. ติดตั้ง dependencies ที่จำเป็น
# ใส่ --no-cache-dir เพื่อประหยัดพื้นที่ และมั่นใจว่าได้ของใหม่
RUN pip install --no-cache-dir fastapi uvicorn grpcio grpcio-tools requests

# 2. คัดลอกไฟล์ทั้งหมดในโฟลเดอร์ของ Service นั้นๆ เข้าไป
COPY . .

# 3. สั่ง Generate gRPC Code ภายใน Container เลย (กันเหนียวถ้าในเครื่องเรายังไม่ได้ gen)
# ถ้า Service ไหนไม่มีไฟล์ .proto คำสั่งนี้จะข้ามไปเอง ไม่พังครับ
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. *.proto || true

# 4. สั่งรัน (ต้องมั่นใจว่าชื่อไฟล์หลักคือ main.py นะครับ)
CMD ["python", "main.py"]