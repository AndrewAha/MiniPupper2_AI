import pyaudio
import wave
import time

CHUNK = 1024

wf = wave.open('output.wav', 'rb')

p = pyaudio.PyAudio()
start_time = time.time()

# open stream
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                input_device_index=0,
                output=True)

# read data
data = wf.readframes(CHUNK)
print("start play")

# play stream
while True:
    stream.write(data)
    data = wf.readframes(CHUNK)
    if time.time() - start_time > 5:
      break
    
# stop stream
stream.stop_stream()
stream.close()

# close PyAudio
p.terminate()
wf.close()
