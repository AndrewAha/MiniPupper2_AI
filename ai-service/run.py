import json
import os
from dotenv import load_dotenv
import base64
import pyaudio
import time
import collections
import webrtcvad
import logging
import wave
import re
import logging
from dotenv import load_dotenv
import webrtcvad
import sys
import time
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.stt_api import *
#from api.tts_api import *
from api.deepseek_api import create_conversation
from api.media_api import *
from api.move_api import *
import threading

think_end = False
speaking = True
response = None

move_cmd_functions = {
                 "action": init_movement,
                 "sit": squat,
                 "move forwards": move_forward,
                 "move backwards": move_backward,
                 "move left": move_left,
                 "move right": move_right,
                 "look down": look_down,
                 "look left": look_left,
                 "look upper left": look_upperleft,
                 "look lower left": look_leftlower,
                 "look right": look_right,
                 "look upper right": look_upperright,
                 "look lower right": look_rightlower,
                 "dance": dance,
             }

def think_gif():
    player = init_gifplayer("../think_gif/")
    while not think_end:
        show_gif(player)

def speaking_gif():
    player = init_gifplayer("../speaking_gif/")
    while speaking:
        show_gif(player)

def ai_text_response(conversation, input_text):
    print("ai_text_response start!")
    ms_start = int(time.time() * 1000)

    result = conversation.invoke(input=input_text)
    print(f"ai_text_response response: {result}")
    result = result['response']
    print(f"text response: {result}")
    ms_end = int(time.time() * 1000)
    print(f"ai_text_response end, delay = {ms_end - ms_start}ms")
    global response
    global think_end
    response =  result
    think_end = True

def tts():
    global response
    global speaking
    text = response
    # 填写平台申请的appid, access_token以及cluster
    appid = os.environ["appid"]
    access_token = os.environ["access_token"]
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
    speaking = False

def main():
    load_dotenv("../.env")
    global response
    global think_end
    global speaking
    conversation = create_conversation()
    move_api_map = {
        "init": init_movement,
        "lower": lower_body,
        "raise": raise_body,
        "left roll": left_body,
        "right roll": right_body,
        "trot": trot,
        "trot1": trot_duration,
        "squat": squat,
        "forward": move_forward,
        "backward": move_backward,
        "left": move_left,
        "right": move_right,
        # "bow": bow,
        "look up": look_up,
        "look down": look_down,
        "look left": look_left,
        "look upper left": look_upperleft,
        "look lower left": look_leftlower,
        "look right": look_right,
        "look upper right": look_upperright,
        "look lower right": look_rightlower,
        "dance": dance,
    }

    print("AI started!")
    while True:
   
        user_input = stt()
        user_input = ''.join(user_input)
        print(user_input)
        
        if "结束" in user_input:
            break
        
        if not user_input:
            logging.debug(f"no input!")
        elif "向上看" in user_input:
            # movement_queue.put("look up")
            move_cmd_functions["look up"]()
        elif "跳舞" in user_input or "dance" in user_input:
            #movement_queue.put(move_key)
            # movement_queue.put("dance")
            move_cmd_functions["dance"]()
            # output_text_queue.put("好的")
        elif "坐下" in user_input :
            # movement_queue.put(move_key)
            move_cmd_functions["sit"]()
            # output_text_queue.put("好的")
        elif "走路" in user_input or "走" in user_input or "向前走" in user_input or "行" in user_input:
            # movement_queue.put("move forwards")
            move_cmd_functions["move forwards"]()
            # output_text_queue.put("好的")
        elif "action" in user_input :
            move_cmd_functions["aciton"]()
            # output_text_queue.put("action initing")
            
        #这是原ai_app.py的特判
        # elif move_key:
            # movement_queue.put(move_key)
            # move_cmd_functions[move_key]()
            # output_text_queue.put(f"好的, 我会{move_key}")
        # elif not ai_on:
        #     logging.info(f"ai is not on, do not use gemini")
        #     stt_queue.put(True)
        #     time.sleep(0.5)
        #     google_api.stop_speech_to_text(stream)
        #     time.sleep(0.5)
        #     continue
        elif "游戏" in user_input or "做游戏" in user_input or "玩游戏" in user_input:
            #movement_queue.put("trot")
            move_cmd_functions["trot"]()
            # output_text_queue.put(GAME_TEXT)
        # elif lang:
        #     logging.debug(f"switch language: {lang}")
        #     user_input += f", Please reply in {lang}."
        #     input_text_queue.put(user_input)
        #     stt_queue.put(False)
        # else:
        #     logging.debug(f"put voice text to input queue: {user_input}")
        #     input_text_queue.put(user_input)
        #     stt_queue.put(False)
        time.sleep(0.5)
        # google_api.stop_speech_to_text(stream)
        time.sleep(0.5)
        
        deepseek_task = threading.Thread(target=ai_text_response, args=(conversation, user_input))
        deepseek_task.start()

        think_end = False
        th_gif_thread = threading.Thread(target=think_gif)
        th_gif_thread.start()

        deepseek_task.join()
        th_gif_thread.join()

        print(response)

        speaking = True

        tts_task = threading.Thread(target=tts)
        tts_task.start()

        sp_gif_thread = threading.Thread(target=speaking_gif)
        sp_gif_thread.start()

        tts_task.join()
        sp_gif_thread.join()

        
    print("AI end!")

        
    stream.stop_stream()
    stream.close()
    audio.terminate()

if __name__ == "__main__":
    main()

