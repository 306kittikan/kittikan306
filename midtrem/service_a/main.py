import grpc
from concurrent import futures
import threading
from fastapi import FastAPI
import uvicorn
import json
import os

# มั่นใจว่ามีไฟล์เหล่านี้จากการ gen proto
import user_pb2
import user_pb2_grpc

# สร้าง instance ของ FastAPI
app = FastAPI()

# --- ฟังก์ชันอ่านข้อมูลจาก JSON ---
# --- ฟังก์ชันอ่านข้อมูลจาก JSON ---
def load_movies_db():
    """
    อ่านข้อมูลหนังจากไฟล์ movies.json
    """
    file_path = os.path.join(os.path.dirname(__file__), "movies.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("movies", [])
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

# --- gRPC Logic (สำหรับ Service B) ---
# --- gRPC Logic (สำหรับ Service B) ---
class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        """
        รับ request จาก gRPC Client (Service B)
        ค้นหาหนังตาม user_id (ใช้เป็น movie_id)
        ส่งคืน title, director, is_active
        """
        movies = load_movies_db()
        # ค้นหาหนังตาม movie_id (เทียบเท่า user_id ในตัวอย่างเก่า)
        movie = next((m for m in movies if str(m["movie_id"]) == str(request.user_id)), None)
        
        if movie:
            # ส่งข้อมูล title กลับไปในฟิลด์ user_name (เพื่อให้เข้ากับ proto เดิม)
            return user_pb2.UserResponse(
                user_name=movie["title"],
                email=f"Director: {movie['director']}",
                is_active=True
            )
        return user_pb2.UserResponse(user_name="Movie Not Found")

def run_grpc():
    """
    ฟังก์ชันสำหรับรัน gRPC Server
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Server is running on port 50051...")
    server.start()
    server.wait_for_termination()

# --- REST Logic (สำหรับ Service C) ---
# --- REST Logic (สำหรับ Service C) ---
@app.get("/movies")
def get_all_movies_rest():
    """
    Endpoint สำหรับดึงข้อมูลหนังทั้งหมด (REST API)
    """
    return load_movies_db()

@app.get("/user/{user_id}") # เปลี่ยนเป็นดึงข้อมูลหนังตาม ID
def get_movie_rest(user_id: str):
    """
    Endpoint สำหรับดึงข้อมูลหนังตาม ID (REST API)
    """
    movies = load_movies_db()
    movie = next((m for m in movies if str(m["movie_id"]) == user_id), None)
    return movie if movie else {"error": "Movie Not Found"}

if __name__ == "__main__":
    # แยก Thread รัน gRPC Server (Port 50051)
    threading.Thread(target=run_grpc, daemon=True).start()
    
    # รัน REST API (Port 8000)
    print("REST API is running on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)