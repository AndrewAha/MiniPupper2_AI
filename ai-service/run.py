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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.stt_api import *
from api.tts_api import *
from api.deepseek_api import *
from api.media_api import *
import threading

think_end = False
response = None

def think_gif():
    player = init_gifplayer("../think_gif/")
    while not think_end:
        show_gif(player)


def ai_text_response(conversation, input_text):
    logging.debug("ai_text_response start!")
    ms_start = int(time.time() * 1000)

    result = conversation.invoke(input=input_text)
    logging.debug(f"ai_text_response response: {result}")
    result = result['response']
    logging.debug(f"text response: {result}")
    ms_end = int(time.time() * 1000)
    logging.debug(f"ai_text_response end, delay = {ms_end - ms_start}ms")
    response =  result
    think_end = True

def main():
    load_dotenv("../.env")
    
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
        
        tts(response)

        
    print("AI end!")

        
    stream.stop_stream()
    stream.close()
    audio.terminate()

if __name__ == "__main__":
    main()
