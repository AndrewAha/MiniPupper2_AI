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
    
    print("Cred init")
    clientProfile, cred = init_tencent_cred()
    WAVE_OUTPUT_FILENAME = "output.wav"

    # 录音参数
    FORMAT = pyaudio.paInt16  # 16位PCM
    CHANNELS = 1              # 单声道
    RATE = 16000              # 16kHz采样率
    FRAME_DURATION_MS = 30   # Duration of each audio frame in ms (10, 20, or 30 ms)
    FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000) # Number of samples per frame
    VAD_AGGRESSIVENESS = 3   # VAD aggressiveness (0-3, 3 is most aggressive filtering non-speech)
    SILENCE_THRESHOLD_SECONDS = 1.0 # Duration of silence to detect (in seconds)
    # Calculate the number of frames needed for the silence threshold
    FRAMES_FOR_SILENCE = int(SILENCE_THRESHOLD_SECONDS * 1000 / FRAME_DURATION_MS)
    

    # 初始化PyAudio
    print("Audio init started!")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=FRAME_SIZE)
    
    vad = webrtcvad.Vad()
    vad.set_mode(VAD_AGGRESSIVENESS)
    
    conversation = create_conversation()

    print("AI started!")
    while True:
   
        user_input = stt(clientProfile, cred, audio, stream, vad, FRAMES_FOR_SILENCE, FRAME_SIZE, CHANNELS, FORMAT, SILENCE_THRESHOLD_SECONDS, WAVE_OUTPUT_FILENAME, RATE)
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
