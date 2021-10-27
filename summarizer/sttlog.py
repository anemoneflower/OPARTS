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
    # roomID = '68d60d83-5080-4eb0-89f9-2265d3a878f3'
    # user = '김유승-1'
    # startTimestamp = 1629778911964
    
    filenames = [g.split('/')[2] for g in glob.glob("./wav/68d60d83-5080-4eb0-89f9-2265d3a878f3_*")]
    
    # print(filenames, len(filenames))
    # ['68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629778911964.wav', '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629779594507.wav',
    # '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629778941870.wav',  '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629779627114.wav',
    # '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629778975159.wav',  '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629779791180.wav',
    # '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629779465264.wav',  '68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_1629780408453.wav']
    
    # # print(os.path.basename("./wav/68d60d83-5080-4eb0-89f9-2265d3a878f3*"))
    # print(glob.glob("./wav/68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1_*")) 
    
    keyIdx = 0
    
    for filename in filenames:
      sp = filename.split('_')
      roomID = sp[0]
      user = sp[1]
      startTimestamp = int(sp[2][:-4])
      print(roomID, user, startTimestamp)
    
    

      # Convert file type from webm to wav
      # inputfile = "../moderator/webm/"+roomID+"_"+user+"_"+str(startTimestamp)+".webm"
      outputfile = "./wav/"+roomID+"_"+user+"_"+str(startTimestamp)+".wav"
      # convert_and_split(inputfile, outputfile)
      # TODO: remove[debug]
      # print(inputfile +'\n'+ outputfile +'\n'+ "convert file type")
      
      # Run Naver STT for given audio file
      stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=outputfile, completion='sync')
      
      transcript = json.loads(stt_res.text)
      # print(transcript)
      print(transcript['segments'])
      speech_timestamp = transcript['segments'];
      seg_start = 0;
      seg_end = 0;
      # speechLog = {}
      with open(roomID+"_"+user+'.txt', 'a') as f:
        for seg in speech_timestamp:
          print(seg['start'], seg['end'])
          if seg['text'] == '': continue
          if startTimestamp + seg['start'] != seg_end :
            if seg_end != 0:
              # speechLog[seg_end] = 
              f.write("(" + str(seg_end) + ") SPEECH-END\n")
              print("(" + str(seg_end) + ") SPEECH-END\n")
              # print("speechLog:: ", speechLog)
            seg_start = startTimestamp + seg['start']
            # speechLog[seg_start] = 
            f.write("(" + str(seg_start) + ") SPEECH-START\n")
            print("(" + str(seg_start) + ") SPEECH-START\n")
            
          seg_end = startTimestamp + seg['end']
          # print("speechLog:: ", speechLog)
          print()
        
        # speechLog[seg_end] = 
        if seg_end != 0:
          f.write("(" + str(seg_end) + ") SPEECH-END\n")
          print("(" + str(seg_end) + ") SPEECH-END\n")
        # print(speechLog)
        
      #   # Design: save log to file

if __name__ == '__main__':
    main()


