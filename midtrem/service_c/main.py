from fastapi import FastAPI
import requests
import uvicorn  # เพิ่มการ import uvicorn

app = FastAPI()

@app.get("/user/{user_id}")
def get_user_via_rest(user_id: str):
    """
    รับ Request จาก Browser/Client ผ่าน REST API
    แล้วส่งต่อ Request ไปยัง Service A ผ่าน REST (HTTP GET)
    """
    # เรียกไปที่ service_a พอร์ต 8000 (พอร์ต REST) แบบ Synchronous
    # ใช้ชื่อ 'service_a' ตามที่ตั้งไว้ใน docker-compose
    print(f"Requesting data for user_id: {user_id} from Service A")
    response = requests.get(f"http://service_a:8000/user/{user_id}")
    data = response.json()
    
    # ส่งผลลัพธ์ที่ได้จากการเรียก API กลับไป
    return {
        "source": "Data from Service A via REST",
        "details": data
    }

# --- ส่วนที่เพิ่มเข้าไปเพื่อให้ Server รันค้างไว้ ---
if __name__ == "__main__":
    # รันบนพอร์ต 8002 ตามที่กำหนดใน docker-compose.yml
    uvicorn.run(app, host="0.0.0.0", port=8002)