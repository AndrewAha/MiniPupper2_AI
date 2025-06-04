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
        
        response = ai_text_response(conversation=conversation, input_text=user_input)
        print(response)
        
        tts(response)
        
    print("AI end!")

        
    stream.stop_stream()
    stream.close()
    audio.terminate()

if __name__ == "__main__":
    main()
