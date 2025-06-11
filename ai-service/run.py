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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.stt_api import *
from api.tts_api import *
from api.deepseek_api import create_conversation
from api.media_api import *
import threading

think_end = False
speaking = True
response = None

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

def main():
    load_dotenv("../.env")
    global response
    global think_end
    global speaking
    conversation = create_conversation()

    print("AI started!")
    while True:
   
        user_input = stt()
        user_input = ''.join(user_input)
        print(user_input)
        
        if "结束" in user_input:
            break
        
        deepseek_task = threading.Thread(target=ai_text_response, args=(conversation, user_input))
        deepseek_task.start()

        think_end = False
        th_gif_thread = threading.Thread(target=think_gif)
        th_gif_thread.start()

        deepseek_task.join()
        th_gif_thread.join()

        print(response)

        speaking = True
        tts_task = threading.Thread(target=tts, args=(response))
        tts_task.start()

        sp_gif_thread = threading.Thread(target=speaking_gif)
        sp_gif_thread.start()

        tts_task.join()
        speaking = False
        sp_gif_thread.join()

        
    print("AI end!")

        
    stream.stop_stream()
    stream.close()
    audio.terminate()

if __name__ == "__main__":
    main()
