"""
================================
SERVICE A - หลัก Backend Service
================================
บทบาท: 
  - เป็น main service ที่เก็บข้อมูล (Database กรณีนี้เป็น JSON)
  - ให้บริการผ่าน 2 โปรโตคล: gRPC และ REST API
  - รับ request จาก Service B (gRPC) และ Service C (REST)
  - ส่งข้อมูลหนังกลับไปในรูปแบบที่กำหนด

พอร์ต:
  - gRPC: 50051 (สำหรับ Service B เรียกใช้)
  - REST: 8000 (สำหรับ Service C เรียกใช้)
"""

import grpc
from concurrent import futures
import threading
from fastapi import FastAPI
import uvicorn
import json
import os

# ========== นำเข้า Libraries ที่สำคัญ ==========
# - grpc: สำหรับสร้าง gRPC Server
# - concurrent.futures: Thread Pool สำหรับ gRPC Server
# - threading: ใช้สร้าง Thread แยกสำหรับรันทั้ง gRPC และ REST พร้อมกัน
# - FastAPI: Framework สำหรับสร้าง REST API
# - uvicorn: Web server ที่รัน FastAPI
# - json: อ่านและจัดการไฟล์ JSON
# - os: จัดการ path ของไฟล์

# นำเข้าไฟล์ที่สร้างจากการ Compile protobuf
# user_pb2: ประกอบด้วย message class (UserRequest, UserResponse)
# user_pb2_grpc: ประกอบด้วย Service class (UserServiceServicer, UserServiceStub)
import user_pb2
import user_pb2_grpc

# ========== สร้าง FastAPI Instance ==========
# เป็น object หลักที่ใช้ในการจัดการ REST API routes
app = FastAPI()

# ========== ฟังก์ชันช่วย: อ่านข้อมูลจากไฟล์ JSON ==========
def load_movies_db():
    """
    ฟังก์ชนี้มีหน้าที่:
      1. อ่านไฟล์ movies.json จากโฟลเดอร์ service_a
      2. ดึง list ของหนังทั้งหมด
      3. คืนค่าเป็น list ของ dictionary
    
    ถ้าอ่านไฟล์ไม่สำเร็จ:
      - ปรินท์ข้อความข้อผิดพลาด
      - คืนค่าเป็น list ว่าง []
    
    Returns:
        list: รายชื่อหนัง หรือ [] หากเกิดข้อผิดพลาด
    """
    file_path = os.path.join(os.path.dirname(__file__), "movies.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("movies", [])
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

# ========== gRPC SERVER IMPLEMENTATION ==========
# ส่วนนี้รองรับการสื่อสารกับ Service B ผ่าน gRPC

class UserService(user_pb2_grpc.UserServiceServicer):
    """
    คลาสนี้ implement gRPC Service ตามที่กำหนดไว้ใน user.proto
    
    ทำหน้าที่:
      - ตอบสนองต่อ gRPC request จาก Service B
      - ค้นหาข้อมูลหนังตามรหัสที่ส่งมา
      - ส่งคืนข้อมูลในรูปแบบ UserResponse
    """
    
    def GetUser(self, request, context):
        """
        gRPC method สำหรับดึงข้อมูลหนัง
        
        Args:
            request (user_pb2.UserRequest): 
              - มีฟิลด์ user_id ที่ใช้ค้นหาหนัง
            context: gRPC context object (ใช้สำหรับจัดการ error, metadata)
        
        Returns:
            user_pb2.UserResponse: ประกอบด้วย
              - user_name: ชื่อหนัง (title)
              - email: ผู้กำกับ (director)
              - is_active: สถานะ (ไม่ใช้จริง แต่คืนค่า True เสมอ)
        
        Logic:
          1. โหลดข้อมูลหนังทั้งหมด
          2. ค้นหาหนังที่มี movie_id ตรงกับ user_id ที่ส่งมา
          3. ถ้าเจอ: ส่งข้อมูลหนังกลับ
          4. ถ้าไม่เจอ: ส่งข้อความ "Movie Not Found"
        """
        movies = load_movies_db()
        
        # ใช้ next() เพื่อค้นหาหนังแรกที่ match กับ movie_id
        # str() ใช้เพื่อแปลง type ให้เหมือนกัน (int ↔ string)
        movie = next((m for m in movies if str(m["movie_id"]) == str(request.user_id)), None)
        
        if movie:
            # ส่งข้อมูลหนังในรูปแบบ UserResponse protobuf
            return user_pb2.UserResponse(
                user_name=movie["title"],
                email=f"Director: {movie['director']}",
                is_active=True
            )
        # ถ้าไม่พบหนัง ให้ส่งข้อความข้อผิดพลาด
        return user_pb2.UserResponse(user_name="Movie Not Found")

def run_grpc():
    """
    ฟังก์ชันนี้มีหน้าที่รัน gRPC Server
    
    ขั้นตอน:
      1. สร้าง gRPC server ที่มี thread pool จำนวน 10 thread
      2. ลงทะเบียน UserService ไปยัง server
      3. เปิด port 50051 (Insecure: ไม่มี SSL/TLS)
      4. เริ่ม server และรอ request
    
    Note:
      - insecure_port: ไม่มีการเข้ารหัส (สำหรับ local/development)
      - [::] : ฟังบนทุก network interface (IPv4 + IPv6)
      - daemon=True: Thread จะถูกหยุดเมื่อ main program ปิด
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Server is running on port 50051...")
    server.start()
    server.wait_for_termination()

# ========== REST API IMPLEMENTATION ==========
# ส่วนนี้รองรับการสื่อสารกับ Service C ผ่าน HTTP/REST

@app.get("/movies")
def get_all_movies_rest():
    """
    REST Endpoint สำหรับดึงข้อมูลหนังทั้งหมด
    
    URL: http://service_a:8000/movies
    Method: GET
    Response: List ของ object หนังทั้งหมด
    
    ใช้โดย: Service C อาจจะใช้เพื่อแสดงหนังทั้งหมด
    """
    return load_movies_db()

@app.get("/user/{user_id}")
def get_movie_rest(user_id: str):
    """
    REST Endpoint สำหรับดึงข้อมูลหนังตาม ID
    
    URL: http://service_a:8000/user/{user_id}
    Method: GET
    Parameter: user_id (string) - รหัสหนัง
    
    Response:
      - ถ้าเจอ: object ของหนังที่ต้องการ
      - ถ้าไม่เจอ: {"error": "Movie Not Found"}
    
    ใช้โดย: Service C เรียกเพื่อดึงข้อมูลหนังตาม ID
    """
    movies = load_movies_db()
    movie = next((m for m in movies if str(m["movie_id"]) == user_id), None)
    return movie if movie else {"error": "Movie Not Found"}

# ========== MAIN ENTRY POINT ==========
if __name__ == "__main__":
    # เริ่มต้นส่วน gRPC
    # สร้าง daemon thread เพื่อรัน gRPC Server
    # daemon=True หมายความว่า thread จะปิดโดยอัตโนมัติเมื่อ main thread ปิด
    threading.Thread(target=run_grpc, daemon=True).start()
    
    # เริ่มต้นส่วน REST API
    # ใช้ uvicorn ในการรัน FastAPI server บนพอร์ต 8000
    # host="0.0.0.0" ให้เชื่อมต่อจากที่ใด ก็ได้
    # port=8000 เปิด port 8000 สำหรับ REST API
    print("REST API is running on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)