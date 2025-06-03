# -*- coding: utf-8 -*-
import json
from tencentcloud.common.common_client import CommonClient
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
import os
from dotenv import load_dotenv
import base64
import pyaudio
import time
import collections
import webrtcvad
import wave
import re

def init_tencent_cred():
    APPID = os.environ["APPID"]
    SECRET_ID = os.environ["SecretId"]
    SECRET_KEY = os.environ["SecretKey"]
    #init
    cred = credential.Credential(SECRET_ID, SECRET_KEY)
    # 使用临时密钥示例
    # cred = credential.Credential("SecretId", "SecretKey", "Token")
    httpProfile = HttpProfile()
    httpProfile.endpoint = "asr.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    return clientProfile, cred


def is_silence(data, vad, RATE):
    """Checks if a given audio frame is silence."""
    try:
        return not vad.is_speech(data, RATE)
    except Exception as e:
        # This can happen if the frame length is incorrect for VAD
        print(f"Error in VAD: {e}")
        return True # Assume silence on error to be safe


def tencent_stt(clientProfile, cred, audio_data):
    print("STT started")
    start_ms = time.time() * 1000
    
    # 转换为 Base64
    base64_string = base64.b64encode(audio_data).decode("utf-8")
    
    params = {
        "EngineModelType": "16k_zh",
        "ChannelNum": 1,
        "ResTextFormat": 2,
        "SourceType": 1,
        "Data": base64_string  # 确保 base64_string 是有效的 Base64 编码
    }
    
    params = json.dumps(params, ensure_ascii=False)
    common_client = CommonClient("asr", "2019-06-14", cred, "ap-guangzhou", profile=clientProfile)
    request = common_client.call_json("CreateRecTask", json.loads(params))

    params = {
        "TaskId": request["Response"]["Data"]["TaskId"],
        }
    params = json.dumps(params, ensure_ascii=False)
    response = common_client.call_json("DescribeTaskStatus", json.loads(params))
    
    while response["Response"]["Data"]["Status"] != 2:
        response = common_client.call_json("DescribeTaskStatus", json.loads(params))
    end_ms = time.time() * 1000
    print(f"time delay: {end_ms - start_ms}ms")
    #print(response["Response"]["Data"]["Result"])
    result = re.sub(r'\[.*?\]', '', response["Response"]["Data"]["Result"])  # 非贪婪匹配
    #print(result)
    return result

def stt(clientProfile, cred, audio, stream, vad, FRAMES_FOR_SILENCE, FRAME_SIZE, CHANNELS, FORMAT, SILENCE_THRESHOLD_SECONDS, WAVE_OUTPUT_FILENAME, RATE):
    frames = []
    silence_buffer = collections.deque([True] * FRAMES_FOR_SILENCE, maxlen=FRAMES_FOR_SILENCE)
    currently_silent_period = True
    
    while True:
        try:
            frame_data = stream.read(FRAME_SIZE, exception_on_overflow=False)
        except IOError as e:
            if e.errno == pyaudio.paInputOverflowed:
                print("Input overflowed. Skipping frame.")
                continue
            else:
                raise

        if len(frame_data) != FRAME_SIZE * CHANNELS * pyaudio.get_sample_size(FORMAT):
            print(f"Warning: Incorrect frame size received. Expected {FRAME_SIZE * CHANNELS * 2}, got {len(frame_data)}")
            continue
        
        frame_is_silent = is_silence(frame_data, vad, RATE)
        silence_buffer.append(frame_is_silent)
        frames.append(frame_data)
        
        # Check if all frames in the buffer are silent
        if all(silence_buffer):
            if not currently_silent_period:
                print(f"\nDetected {SILENCE_THRESHOLD_SECONDS} seconds of continuous silence.")
                currently_silent_period = True
                break
        else:
            if currently_silent_period:
                print("Speech detected.")
                currently_silent_period = False

            

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    # 读取 WAV 文件
    with open("output.wav", "rb") as audio_file:
        audio_bytes = audio_file.read()
    #audio_bytes = b''.join(frames)

    return tencent_stt(clientProfile, cred, audio_bytes)

    
        

if __name__ == "__main__":
    load_dotenv("../.env")
    clientProfile, cred = init_tencent_cred()
    WAVE_OUTPUT_FILENAME = "output.wav"

    # 录音参数
    FORMAT = pyaudio.paInt16  # 16位PCM
    CHANNELS = 1              # 单声道
    RATE = 16000              # 16kHz采样率
    FRAME_DURATION_MS = 30   # Duration of each audio frame in ms (10, 20, or 30 ms)
    FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000) # Number of samples per frame
    VAD_AGGRESSIVENESS = 3   # VAD aggressiveness (0-3, 3 is most aggressive filtering non-speech)
    SILENCE_THRESHOLD_SECONDS = 1.5 # Duration of silence to detect (in seconds)
    # Calculate the number of frames needed for the silence threshold
    FRAMES_FOR_SILENCE = int(SILENCE_THRESHOLD_SECONDS * 1000 / FRAME_DURATION_MS)

    # 初始化PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=FRAME_SIZE)
    
    vad = webrtcvad.Vad()
    vad.set_mode(VAD_AGGRESSIVENESS)
   
    stt(clientProfile, cred, stream, vad, FRAMES_FOR_SILENCE, FRAME_SIZE, CHANNELS, FORMAT, SILENCE_THRESHOLD_SECONDS, WAVE_OUTPUT_FILENAME, RATE)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()


    
