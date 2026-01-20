"""
================================
SERVICE C - REST Client Service
================================
บทบาท:
  - เป็น Client Service ที่เชื่อมต่อไปยัง Service A ผ่าน REST API
  - รับ request จาก end-user/browser ผ่าน REST API
  - แปลง request และส่งไปยัง Service A ผ่าน HTTP GET
  - ส่งคืนผลลัพธ์ให้ผู้ใช้

พอร์ต:
  - REST API: 8002 (ผู้ใช้เรียก endpoint นี้)
  - HTTP Client: เชื่อมต่อไปยัง Service A บน port 8000

สัญญาณการสื่อสาร:
  - Client (User) → Service C (REST) → Service A (REST) → Client

ความแตกต่างจาก Service B:
  - Service B ใช้ gRPC สำหรับติดต่อ Service A
  - Service C ใช้ REST (HTTP) สำหรับติดต่อ Service A
"""

from fastapi import FastAPI
import requests
import uvicorn

# ========== สร้าง FastAPI Instance ==========
# เป็น object หลักที่ใช้ในการจัดการ REST API routes
app = FastAPI()

@app.get("/user/{user_id}")
def get_user_via_rest(user_id: str):
    """
    REST Endpoint สำหรับดึงข้อมูลผู้ใช้ (หรือหนัง)
    
    ขั้นตอนการทำงาน:
      1. รับ user_id จาก URL path
      2. ส่ง HTTP GET request ไปยัง Service A
      3. รอรับ response จาก Service A
      4. ส่งคืนข้อมูลให้ผู้ใช้ในรูปแบบ JSON
    
    URL: http://service_c:8002/user/{user_id}
    Method: GET
    Parameter: user_id (string) - รหัสของหนังที่ต้องการ
    
    Response:
      {
        "source": "Data from Service A via REST",
        "details": {
          "movie_id": 1,
          "title": "ชื่อหนัง",
          "director": "ผู้กำกับ",
          ...
        }
      }
    
    Args:
        user_id (str): รหัสหนังที่ต้องการค้นหา
    
    Returns:
        dict: ข้อมูลหนังที่ได้จาก Service A ผ่าน REST API
    """
    
    # ========== ส่ง HTTP Request ไปยัง Service A ==========
    # ปรินท์ข้อมูล debug เพื่อติดตามการทำงาน
    print(f"Requesting data for user_id: {user_id} from Service A")
    
    # requests.get(): ส่ง HTTP GET request
    # f"http://service_a:8000/user/{user_id}":
    #   - 'http': โปรโตคล HTTP
    #   - 'service_a': ชื่อ service ตามใน docker-compose.yml
    #   - 8000: port ที่ Service A เปิด REST API
    #   - /user/{user_id}: endpoint ที่จะเรียก
    response = requests.get(f"http://service_a:8000/user/{user_id}")
    
    # แปลง response body เป็น JSON dictionary
    data = response.json()
    
    # ========== ส่งผลลัพธ์กลับไปยัง Client ==========
    # เอาข้อมูลจาก Service A มาห่อด้วย metadata ที่ระบุว่ามาจากไหน
    return {
        "source": "Data from Service A via REST",
        "details": data
    }

# ========== MAIN ENTRY POINT ==========
if __name__ == "__main__":
    # เริ่มต้น FastAPI server ด้วย uvicorn
    # host="0.0.0.0": ให้เชื่อมต่อจากที่ใด ก็ได้
    # port=8002: เปิด port 8002 สำหรับ REST API
    # 
    # ผู้ใช้จะเรียกใช้ผ่าน: http://service_c:8002/user/1
    uvicorn.run(app, host="0.0.0.0", port=8002)