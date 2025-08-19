# testvue

## Як запустити локально

### Backend

<img width="621" height="133" alt="image" src="https://github.com/user-attachments/assets/0ec34930-4b77-45d6-a2dc-d5b05d03d4e6" />

http://127.0.0.1:8000/test_rtp - лінка для тесту RTP


```bash
python -m venv venv
.\venv\Scripts\activate   # для Windows

pip install -r requirements.txt
uvicorn main:app --reload
