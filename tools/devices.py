import pyaudio

p = pyaudio.PyAudio()

print("可用音频设备列表:")
for i in range(p.get_device_count()):
    dev_info = p.get_device_info_by_index(i)
    print(f"  索引 {i}: {dev_info['name']}")
    print(f"    最大输入声道数: {dev_info['maxInputChannels']}")
    print(f"    最大输出声道数: {dev_info['maxOutputChannels']}")
    print(f"    默认采样率: {dev_info['defaultSampleRate']}")

# 获取默认输入设备信息
default_input_device_info = p.get_default_input_device_info()
print(f"\n默认输入设备索引: {default_input_device_info['index']}")
print(f"默认输入设备名称: {default_input_device_info['name']}")

# 获取默认输出设备信息
default_output_device_info = p.get_default_output_device_info()
print(f"\n默认输出设备索引: {default_output_device_info['index']}")
print(f"默认输出设备名称: {default_output_device_info['name']}")

p.terminate()