from fastapi import FastAPI
import grpc
import user_pb2
import user_pb2_grpc
import uvicorn  # เพิ่มการ import uvicorn

app = FastAPI()

@app.get("/user/{user_id}")
def get_user_via_grpc(user_id: int):
    """
    รับ Request จาก Browser/Client ผ่าน REST API
    แล้วส่งต่อ Request ไปยัง Service A ผ่าน gRPC
    """
    # เชื่อมต่อไปยัง service_a พอร์ต 50051 (ชื่อ service_a ต้องตรงกับใน docker-compose)
    # insecure_channel คือการเชื่อมต่อแบบไม่มี SSL/TLS
    with grpc.insecure_channel('service_a:50051') as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        # เรียกใช้คำสั่ง GetUser แบบ Synchronous ไปยัง Service A
        response = stub.GetUser(user_pb2.UserRequest(user_id=user_id))
    
    # ส่งผลลัพธ์ที่ได้จาก gRPC กลับไปยัง Client
    return {
        "source": "Data from Service A via gRPC",
        "user_name": response.user_name,
        "email": response.email
    }

# --- ส่วนที่เพิ่มเข้าไปเพื่อให้ Container ไม่ปิดตัวเอง ---
if __name__ == "__main__":
    # รันบนพอร์ต 8001 ตามที่กำหนดไว้ในไฟล์ docker-compose.yml
    uvicorn.run(app, host="0.0.0.0", port=8001)