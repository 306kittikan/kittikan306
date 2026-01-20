"""
================================
SERVICE B - gRPC Client Service
================================
บทบาท:
  - เป็น Client Service ที่เชื่อมต่อไปยัง Service A ผ่าน gRPC
  - รับ request จาก end-user/browser ผ่าน REST API
  - แปลง request เป็น gRPC format และส่งไปยัง Service A
  - ส่งคืนผลลัพธ์ให้ผู้ใช้

พอร์ต:
  - REST API: 8001 (ผู้ใช้เรียก endpoint นี้)
  - gRPC Client: เชื่อมต่อไปยัง Service A บน port 50051

สัญญาณการสื่อสาร:
  - Client (User) → Service B (REST) → Service A (gRPC) → Client
"""

from fastapi import FastAPI
import grpc
import user_pb2
import user_pb2_grpc
import uvicorn

# ========== สร้าง FastAPI Instance ==========
# เป็น object หลักที่ใช้ในการจัดการ REST API routes
app = FastAPI()

@app.get("/user/{user_id}")
def get_user_via_grpc(user_id: int):
    """
    REST Endpoint สำหรับดึงข้อมูลผู้ใช้ (หรือหนัง)
    
    ขั้นตอนการทำงาน:
      1. รับ user_id จาก URL path
      2. เชื่อมต่อไปยัง Service A ผ่าน gRPC
      3. ส่ง request GetUser ไปยัง Service A
      4. รอรับ response จาก Service A
      5. ส่งคืนข้อมูลให้ผู้ใช้ในรูปแบบ JSON
    
    URL: http://service_b:8001/user/{user_id}
    Method: GET
    Parameter: user_id (integer) - รหัสของหนังที่ต้องการ
    
    Response:
      {
        "source": "Data from Service A via gRPC",
        "user_name": "ชื่อหนัง",
        "email": "ผู้กำกับ"
      }
    
    Args:
        user_id (int): รหัสหนังที่ต้องการค้นหา
    
    Returns:
        dict: ข้อมูลหนังที่ได้จาก Service A ผ่าน gRPC
    """
    
    # ========== สร้างการเชื่อมต่อ gRPC ไปยัง Service A ==========
    # grpc.insecure_channel: เชื่อมต่อแบบไม่มี SSL/TLS (สำหรับ development)
    # 'service_a:50051': 
    #   - 'service_a' = ชื่อ service ตามใน docker-compose.yml
    #   - 50051 = port ที่ Service A เปิด gRPC Server
    # with statement: ทำให้แน่ใจว่าการเชื่อมต่อจะปิดเมื่อเสร็จสิ้น
    with grpc.insecure_channel('service_a:50051') as channel:
        # สร้าง gRPC client stub (proxy) เพื่อเรียกใช้ gRPC service
        # stub นี้ใช้เพื่อเรียกเมธอด GetUser ที่ตั้งไว้ใน Service A
        stub = user_pb2_grpc.UserServiceStub(channel)
        
        # ส่ง request ไปยัง Service A
        # UserRequest(user_id=user_id): สร้าง protobuf message เพื่อส่งไป
        # ฟังก์ชัน GetUser บน Service A จะประมวลผลและส่งคืน response
        response = stub.GetUser(user_pb2.UserRequest(user_id=user_id))
    
    # ========== ส่งผลลัพธ์กลับไปยัง Client ==========
    # แปลง protobuf response ให้เป็น JSON dict เพื่อส่งกลับ REST API
    return {
        "source": "Data from Service A via gRPC",
        "user_name": response.user_name,
        "email": response.email
    }

# ========== MAIN ENTRY POINT ==========
if __name__ == "__main__":
    # เริ่มต้น FastAPI server ด้วย uvicorn
    # host="0.0.0.0": ให้เชื่อมต่อจากที่ใด ก็ได้
    # port=8001: เปิด port 8001 สำหรับ REST API
    # 
    # ผู้ใช้จะเรียกใช้ผ่าน: http://service_b:8001/user/1
    uvicorn.run(app, host="0.0.0.0", port=8001)