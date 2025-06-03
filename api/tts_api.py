#coding=utf-8
import base64
import json
import uuid
import requests
import time
import sounddevice as sd
import soundfile as sf
from io import BytesIO
import os
from dotenv import load_dotenv

def tts(text):
    # 填写平台申请的appid, access_token以及cluster
    appid = os.environ["appid"]
    access_token= os.environ["access_token"]
    cluster = "volcano_tts"


    voice_type = "zh_male_shaonianzixin_moon_bigtts"
    host = "openspeech.bytedance.com"
    api_url = f"https://{host}/api/v1/tts"

    header = {"Authorization": f"Bearer;{access_token}"}

    request_json = {
        "app": {
            "appid": appid,
            "token": "access_token",
            "cluster": cluster
        },
        "user": {
            "uid": "388808087185088"
        },
        "audio": {
            "voice_type": voice_type,
            "encoding": "wav",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson"

        }
    }
    start_ms = time.time() * 1000
    resp = requests.post(api_url, json.dumps(request_json), headers=header)
    print(f"resp body: \n{resp.json().keys()}")
    end_ms = time.time() * 1000
    print(f"{end_ms - start_ms}ms")
    if "data" in resp.json():
        data = resp.json()["data"]
        data = base64.b64decode(data)
        audio_data, sample_rate = sf.read(BytesIO(data))
        sd.play(audio_data, sample_rate)
        sd.wait()  # 等待播放完成
        
    end_ms = time.time() * 1000
    print(f"{end_ms - start_ms}ms")

if __name__ == '__main__':
    try:
        load_dotenv("../.env")
        text = """
        1. 自律：解决问题的第一步 🛠️
        派克认为，自律是解决人生问题的首要工具。它包含四个原则：
        """
        tts(text)

    except Exception as e:
        e.with_traceback()

