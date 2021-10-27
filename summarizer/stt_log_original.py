from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Text
from urllib.parse import parse_qs
from IPython.display import display

import subprocess
import json
import requests

from time import time

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
  # "68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3",
    inputkeys = [ "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]

    for idx, inputkey in enumerate(inputkeys):
      keyIdx = 1
      print(inputkey, keyIdx)      
      
      merged = False
      output_key = "fragment_original"

      if merged:
        filenames = [inputkey+'_merged.wav']
      else:
        filenames = [g.split('/')[2] for g in glob.glob("./wav/"+inputkey+"_*.*")]
        print(len(filenames))

  #### IGNORE FILES IF RERUN
      if not merged:
        try:
          with open("ignore_"+inputkey+".txt", 'r') as ig:
            ignorenames = ig.read()
            # print(ignorenames)
          ignorenames = ignorenames.split(",")
          print(ignorenames, len(ignorenames))
        except:
          ignorenames = []
          print(ignorenames)
      else:
        ignorenames = []

      for i, filename in enumerate(filenames):        
        sp = filename.split('_')
        roomID = sp[0]
        user = sp[1]
        if not merged:
          startTimestamp = int(sp[2][:-4])
          print(i, roomID, user, startTimestamp)
        
        if filename in ignorenames:
          with open("test_"+output_key+"_"+roomID+"_"+user+'.txt', 'a') as f:
            f.write("IGNORE:::"+filename+"\n")
            print("IGNORE:::"+filename+"\n")
          continue

        # Convert file type from webm to wav
        if merged:
          outputfile = "./"+filename
        else: 
          outputfile = "./wav/"+roomID+"_"+user+"_"+str(startTimestamp)+".wav"
          
        
        # Run Naver STT for given audio file
        sttime = int(time())
        stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=outputfile, completion='sync')

        # boosting on
        # stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=outputfile, completion='sync', boostings=True)
        ####### 시간측정용
        endtime = int(time())
        

        transcript = json.loads(stt_res.text)
        print(transcript)
        print(endtime-sttime)
        ####### 시간측정용
        if transcript['text']=='':
          with open("ignore_"+inputkey+".txt", 'a') as ff:
            ff.write(filename+",")
          with open("test_"+output_key+"_"+roomID+"_"+user+'.txt', 'a') as f:
            f.write("IGNORE:::"+filename+"\n")
            print("IGNORE:::"+filename+"\n")
          continue
        
        print(transcript['segments'])
        speech_timestamp = transcript['segments'];
        seg_start = 0;
        seg_end = 0;
        # speechLog = {}
        with open("test_"+output_key+"_"+roomID+"_"+user+'.txt', 'a') as f:
          if not merged:
            f.write("\n"+roomID+"_"+user+"_"+str(startTimestamp)+".wav\n")
          for seg in speech_timestamp:
            # print(seg['start'], seg['end'])
            if seg['text'] == '': 
              continue

            f.write(seg['text']+"\n")
            print(seg['text']+"\n")
            if merged:
              startTimestamp = 0
            if startTimestamp + seg['start'] != seg_end :
              if seg_end != 0:
                # speechLog[seg_end] = 
                f.write("(" + str(seg_end) + ") SPEECH-END\n")
                print("(" + str(seg_end) + ") SPEECH-END\n")
                with open("result_"+output_key+"_"+inputkey+".txt", 'a') as rf:
                  rf.write("(" + str(seg_end) + ") SPEECH-END\n")
                # print("speechLog:: ", speechLog)
              seg_start = startTimestamp + seg['start']
              # speechLog[seg_start] = 
              f.write("(" + str(seg_start) + ") SPEECH-START\n")
              print("(" + str(seg_start) + ") SPEECH-START\n")
              with open("result_"+output_key+"_"+inputkey+".txt", 'a') as rf:
                rf.write("(" + str(seg_start) + ") SPEECH-START\n")
              
            seg_end = startTimestamp + seg['end']

            # print("speechLog:: ", speechLog)
            # print()
          
          # speechLog[seg_end] = 
          if seg_end != 0:
            f.write("(" + str(seg_end) + ") SPEECH-END\n")
            print("(" + str(seg_end) + ") SPEECH-END\n")
            with open("result_"+output_key+"_"+inputkey+".txt", 'a') as rf:
              rf.write("(" + str(seg_end) + ") SPEECH-END\n")

          # print(speechLog)
          
        #   # Design: save log to file

if __name__ == '__main__':
    main()



