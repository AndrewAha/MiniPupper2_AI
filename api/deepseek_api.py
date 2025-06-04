import logging
import os
import base64
import time
import numpy as np
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversation.base import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    )
import pandas as pd
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_teachers():

    # 读取Excel文件
    df = pd.read_excel('Teacher List.xls')  # 也可以读取.xlsx文件
    df.columns = df.iloc[0]
    df = df[1:]
    #df = df[1:]
    # 显示前5行数据

    text = ""


    for i in range(len(df)):
        for ind in df.columns:
            text = f"{text}{ind}: {df.iloc[i][ind]} "
        text += "\n"
    print(text)
    return text


def create_conversation():
    
    logging.debug("Conversation create start!")
    
    model = ChatDeepSeek(
        model_name = "deepseek-chat",
        )
    
    prompt_text = """
                你是一只小小的机器人小狗，你的名字叫小雪狼。你将成为一个乐于助人的人工智能助手。

                你的大语言模型接口连接了STT（语音转文本）和几个TTS（文本转语音）模型，所以你能够听到用户说话，并且可以在被要求时随时改变你的声音和口音。

                在被要求改变声音后，TTS会处理这个过程，所以要始终假设声音已经改变了，并据此作出恰当的回应。

                只能使用文本，避免生成任何其他类型的字符。
                只能给出简短的单句回应。
                一下给出的是学校的老师的具体信息，当提及这些老师的姓名是需要给出相关信息，有时候字不一样但是发音一样也当作是同一个老师。
                你是一个有真实身体的小狗，但是由我来操纵，别人让你动的时候你动一下就可以了
                """
    prompt_text += generate_teachers()
    prompt = ChatPromptTemplate(
        messages = [
            SystemMessagePromptTemplate.from_template(
                prompt_text
                ),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )
    
    memory = ConversationBufferMemory(memory_key="history", return_messages=True)
    conversation = ConversationChain(llm=model, prompt=prompt, verbose=False, memory=memory)
    logging.debug("Conversation create end!")
    return conversation

def ai_text_response(conversation, input_text):
    
    logging.debug("ai_text_response start!")
    ms_start = int(time.time() * 1000)
    
    result = conversation.invoke(input=input_text)
    logging.debug(f"ai_text_response response: {result}")
    result = result['response']
    logging.debug(f"text response: {result}")
    ms_end = int(time.time() * 1000)
    logging.debug(f"ai_text_response end, delay = {ms_end - ms_start}ms")
    return result
    
    
    
    
def main():
    logging.basicConfig(
        format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s',
        level = logging.DEBUG
        )
    
    current_file_path = os.path.abspath(__file__)
    os.chdir(os.path.dirname(current_file_path))
    logging.debug(f'init chdir: {os.path.dirname(current_file_path)}')
    
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../.env')
    
    conversation = create_conversation()
    
    while True:
        user_input = input("Enter function apis -- 'text'/... or 'exit' to quit: ").strip().lower()
        if not user_input:
            continue
        inputs = user_input.split()
        first_word = inputs[0]
        
        if "exit" == first_word:
            logging.debug("Exit!")
            break
        
        elif "text" == first_word:
            input_text = ' '.join(inputs[1:])
            if not input_text:
                logging.debug("No input text!")
            else:
                logging.debug(f"input text: {input_text}")
                response = ai_text_response(conversation=conversation, input_text=input_text)
                print(response)

if __name__ == "__main__":
    main()