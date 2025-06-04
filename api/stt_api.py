# For prerequisites running the following sample, visit https://help.aliyun.com/zh/model-studio/getting-started/first-api-call-to-qwen
import os
import signal  # for keyboard events handling (press "Ctrl+C" to terminate recording and translation)
import sys

import dashscope
import pyaudio
from dashscope.audio.asr import *
from dotenv import load_dotenv
import webrtcvad
import collections

mic = None
stream = None

# Set recording parameters
sample_rate = 16000  # sampling rate (Hz)
channels = 1  # mono channel
dtype = 'int16'  # data type
format_pcm = 'pcm'  # the format of the audio data
block_size = 480  # number of frames per buffer

texts = ['']


def init_dashscope_api_key():
    """
        Set your DashScope API-key. More information:
        https://github.com/aliyun/alibabacloud-bailian-speech-demo/blob/master/PREREQUISITES.md
    """

    if 'DASHSCOPE_API_KEY' in os.environ:
        dashscope.api_key = os.environ[
            'DASHSCOPE_API_KEY']  # load API-key from environment variable DASHSCOPE_API_KEY
    else:
        dashscope.api_key = '<your-dashscope-api-key>'  # set API-key manually


# Real-time speech recognition callback
class Callback(RecognitionCallback):
    def on_open(self) -> None:
        global mic
        global stream
        print('RecognitionCallback open.')
        mic = pyaudio.PyAudio()
        stream = mic.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=16000,
                          input=True)

    def on_close(self) -> None:
        global mic
        global stream
        print('RecognitionCallback close.')
        stream.stop_stream()
        stream.close()
        mic.terminate()
        stream = None
        mic = None

    def on_complete(self) -> None:
        print('RecognitionCallback completed.')  # translation completed

    def on_error(self, message) -> None:
        print('RecognitionCallback task_id: ', message.request_id)
        print('RecognitionCallback error: ', message.message)
        # Stop and close the audio stream if it is running
        if 'stream' in globals() and stream.active:
            stream.stop()
            stream.close()
        # Forcefully exit the program
        sys.exit(1)

    def on_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        if 'text' in sentence:
            print('RecognitionCallback text: ', sentence['text'])
            texts[len(texts)-1] = sentence['text']
            if RecognitionResult.is_sentence_end(sentence):
                print(
                    'RecognitionCallback sentence end, request_id:%s, usage:%s'
                    % (result.get_request_id(), result.get_usage(sentence)))
                texts.append('')


def signal_handler(sig, frame):
    print('Ctrl+C pressed, stop translation ...')
    # Stop translation
    recognition.stop()
    print('Translation stopped.')
    print(
        '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
        .format(
            recognition.get_last_request_id(),
            recognition.get_first_package_delay(),
            recognition.get_last_package_delay(),
        ))
    print(texts)
    # Forcefully exit the program
    sys.exit(0)

def is_silence(data, vad, RATE):
    """Checks if a given audio frame is silence."""
    try:
        return not vad.is_speech(data, RATE)
    except Exception as e:
        # This can happen if the frame length is incorrect for VAD
        print(f"Error in VAD: {e}")
        return True # Assume silence on error to be safe

def stt():
    global texts
    texts = ['']
    load_dotenv("../.env")
    init_dashscope_api_key()
    print('Initializing ...')

    # Create the translation callback
    callback = Callback()

    # Call recognition service by async mode, you can customize the recognition parameters, like model, format,
    # sample_rate For more information, please refer to https://help.aliyun.com/document_detail/2712536.html
    recognition = Recognition(
        model='paraformer-realtime-v2',
        # 'paraformer-realtime-v1'、'paraformer-realtime-8k-v1'
        format=format_pcm,
        # 'pcm'、'wav'、'opus'、'speex'、'aac'、'amr', you can check the supported formats in the document
        sample_rate=sample_rate,
        # support 8000, 16000
        semantic_punctuation_enabled=False,
        callback=callback)

    # Start translation
    recognition.start()

    signal.signal(signal.SIGINT, signal_handler)
    print("Press 'Ctrl+C' to stop recording and translation...")
    # Create a keyboard listener until "Ctrl+C" is pressed
    RATE = 16000              # 16kHz采样率
    FRAME_DURATION_MS = 30   # Duration of each audio frame in ms (10, 20, or 30 ms)
    FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000) # Number of samples per frame
    VAD_AGGRESSIVENESS = 3   # VAD aggressiveness (0-3, 3 is most aggressive filtering non-speech)
    SILENCE_THRESHOLD_SECONDS = 1.5 # Duration of silence to detect (in seconds)
    # Calculate the number of frames needed for the silence threshold
    FRAMES_FOR_SILENCE = int(SILENCE_THRESHOLD_SECONDS * 1000 / FRAME_DURATION_MS)
    vad = webrtcvad.Vad()
    vad.set_mode(VAD_AGGRESSIVENESS)
    silence_buffer = collections.deque([True] * FRAMES_FOR_SILENCE, maxlen=FRAMES_FOR_SILENCE)
    currently_silent_period = True
    print("STT started")
    
    while True:
        if stream:
            data = stream.read(480, exception_on_overflow=False)
            silence_buffer.append(is_silence(data, vad, RATE))
                    
            # Check if all frames in the buffer are silent

            if all(silence_buffer) and texts != ['']:
                if not currently_silent_period:
                    print(f"\nDetected {SILENCE_THRESHOLD_SECONDS} seconds of continuous silence.")
                    currently_silent_period = True
                    break
            else:
                if currently_silent_period:
                    print("Speech detected.")
                    currently_silent_period = False
                    
            recognition.send_audio_frame(data)
        else:
            break

    
    
    recognition.stop()
    print("STT end")
    print(texts)
    return texts

# main function
if __name__ == '__main__':
    
    while(True):
        stt()
