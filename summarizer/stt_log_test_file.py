from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Text
from urllib.parse import parse_qs
from IPython.display import display

import subprocess
import json
import requests

import os
import configparser

config = configparser.ConfigParser()
config.read(os.getcwd().split("ai-moderator")[0]+"ai-moderator"+ os.sep + "summarizer" +os.sep+ 'config.ini', encoding='utf-8')

# Clova Speech invoke URL
invoke_url = config['Clova_STT']['invoke_url'].split('**')
# Clova Speech secret key
secret = config['Clova_STT']['secret'].split('**')

naverKeyLen = len(invoke_url)
naverKeyCnt = 0

class ClovaSpeechClient:
    def __init__(self, invoke_url, secret):
        self.invoke_url = invoke_url
        self.secret = secret
        
    def req_upload(self, file, completion, callback=None, userdata=None, forbiddens=None, boostings=None, sttEnable=True,
                wordAlignment=True, fullText=True, script='', diarization=None, keywordExtraction=None, groupByAudio=False):
        request_body = {
            'language': 'ko-KR',
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'sttEnable': sttEnable,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'script': script,
            'forbiddens': forbiddens,
            'boostings': boostings,
            'diarization': diarization,
            'keywordExtraction': keywordExtraction,
            'groupByAudio': groupByAudio,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        print(self.invoke_url)
        print(json.dumps(request_body).encode('UTF-8'))
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=self.invoke_url + '/recognizer/upload', files=files)
        return response
import glob
def main():
    print("REQUEST::::::STT")
    # inputkey = input("roomid_username: ")
    # keyIdx = int(input("keyIdx(0~5): "))
    # print(inputkey, keyIdx)

    # ### result 다시뽑기 ###
    # inputkey = "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3"

    # with open("test2_"+inputkey+".txt", 'r') as ig:
    #   sttresult = ig.readlines()
    #   print(sttresult)
    # with open("result_"+inputkey+".txt", 'a') as rf:
    #   for ig in sttresult:
    #     if ig[0] == '(':
    #       rf.write(ig)
    # return
    
    
#     filenames = [g.split('/')[2] for g in glob.glob("./wav/"+inputkey+"_*.*")]
#     # 773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1_1629952268074
#     # print(filenames, len(filenames))
#     print(len(filenames))

#     # print(filenames.index('773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1_1629953370609.wav'))


# #### IGNORE FILES IF RERUN
#     try:
#       with open("ignore_"+inputkey+".txt", 'r') as ig:
#         ignorenames = ig.read()
#         print(ignorenames)
#       ignorenames = ignorenames.split(",")
#       print(ignorenames, len(ignorenames))
#     except:
#       ignorenames = []
#       print(ignorenames)

    # Run again only some files
    ignorenames = []
    filenames = ["4499b593-365b-407d-a143-00533e7bce42_김윤정-3_1629959812886.wav"]

    keyIdx = 0
    
    for i, filename in enumerate(filenames):        
      sp = filename.split('_')
      roomID = sp[0]
      user = sp[1]
      startTimestamp = int(sp[2][:-4])
      print(i, roomID, user, startTimestamp)
      inputkey = roomID+"_"+user
      
      if filename in ignorenames:
        with open("test3_"+roomID+"_"+user+'.txt', 'a') as f:
          f.write("IGNORE:::"+filename+"\n")
          print("IGNORE:::"+filename+"\n")
        continue

      # Convert file type from webm to wav
      # inputfile = "../moderator/webm/"+roomID+"_"+user+"_"+str(startTimestamp)+".webm"
      outputfile = "./wav/"+roomID+"_"+user+"_"+str(startTimestamp)+".wav"
      # convert_and_split(inputfile, outputfile)
      # print(inputfile +'\n'+ outputfile +'\n'+ "convert file type")
      
      # Run Naver STT for given audio file
      stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=outputfile, completion='sync')
      
      transcript = json.loads(stt_res.text)
      if transcript['text']=='':
        with open("ignore_"+inputkey+".txt", 'a') as ff:
          ff.write(filename+",")
        with open("test3_"+roomID+"_"+user+'.txt', 'a') as f:
          f.write("IGNORE:::"+filename+"\n")
          print("IGNORE:::"+filename+"\n")
        continue
      
      print(transcript['segments'])
      speech_timestamp = transcript['segments'];
      seg_start = 0;
      seg_end = 0;
      # speechLog = {}
      with open("test3_"+roomID+"_"+user+'.txt', 'a') as f:
        f.write("\n"+roomID+"_"+user+"_"+str(startTimestamp)+".wav\n")
        for seg in speech_timestamp:
          # print(seg['start'], seg['end'])
          if seg['text'] == '': 
            continue

          if seg['text'] in [
            '쯧', '습', '이씨', '허허', '아', '아휴', '아우', '아흠', '에', '오', '음', '아 아', '음 음', '흠', '흠흠', '허허허', '으흠', '하아', '흐흠', '에휴', '이', '허어', '이보게', '아', '어허', '아유', '어허허허허허허허', '허', '아이 데이터가 실행되고 있는 버가우자는 다른 탭을 짓지 마세요.', '흐흐', '흐흐흐', '흐흐흐흐', '아이고', '아이', '이런', '흐흐', '아마 실행되고 있는 브라우저는 다른 책을 치지 마세요.', '아이 데이터가 실행되고 있는 브라우저는 다른 탭을 끼지 마세요.', '흑', '아이 메이저가 진행되고 있는 브라우저는 다른 태도에 그치지 마세요.', '아이 데이터가 되고 있는 브라우저를 다른 탭을 주지 마세요.', '아이들이 저희가 진행되고 있는 브라우저는 다른 책을 쓰지 마세요.', '아이들이 저는 책임지고 있는 브라우저는 다른 책을 기지 마세요.']:
            f.write("SKIP:::"+seg['text']+"\n")
            continue
          f.write(seg['text']+"\n")
          print(seg['text']+"\n")
          if startTimestamp + seg['start'] != seg_end :
            if seg_end != 0:
              # speechLog[seg_end] = 
              f.write("(" + str(seg_end) + ") SPEECH-END\n")
              print("(" + str(seg_end) + ") SPEECH-END\n")
              with open("result1_"+inputkey+".txt", 'a') as rf:
                rf.write("(" + str(seg_end) + ") SPEECH-END\n")
              # print("speechLog:: ", speechLog)
            seg_start = startTimestamp + seg['start']
            # speechLog[seg_start] = 
            f.write("(" + str(seg_start) + ") SPEECH-START\n")
            print("(" + str(seg_start) + ") SPEECH-START\n")
            with open("result1_"+inputkey+".txt", 'a') as rf:
              rf.write("(" + str(seg_start) + ") SPEECH-START\n")
            
          seg_end = startTimestamp + seg['end']

          # print("speechLog:: ", speechLog)
          # print()
        
        # speechLog[seg_end] = 
        if seg_end != 0:
          f.write("(" + str(seg_end) + ") SPEECH-END\n")
          print("(" + str(seg_end) + ") SPEECH-END\n")
          with open("result1_"+inputkey+".txt", 'a') as rf:
            rf.write("(" + str(seg_end) + ") SPEECH-END\n")

        # print(speechLog)
        
      #   # Design: save log to file

if __name__ == '__main__':
    main()



