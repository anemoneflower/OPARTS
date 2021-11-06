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

def convert_and_split(input, output):
    command = ['ffmpeg', '-i', input, '-c:a', 'pcm_f32le', output]
    subprocess.run(command,stdout=subprocess.PIPE,stdin=subprocess.PIPE)

class ClovaSpeechClient:
  def __init__(self, invoke_url, secret):
    self.invoke_url = invoke_url
    self.secret = secret
    
  def req_upload(self, file, completion, callback=None, userdata=None, forbiddens=None, boostings=None, sttEnable=True,
      wordAlignment=True, fullText=True, script='', diarization=None, keywordExtraction=None, groupByAudio=False):
    if boostings:
      boostings = [{"words": ""}]      
    
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

def run_stt(keyIdx, inputkey, outputkey, filenames, ignorenames, convert, merged, boost, filt):
  sttresult = []
  len_wavfiles = len(filenames)
  for i, filename in enumerate(filenames):
    sp = filename.split('_')
    roomID = sp[0]
    user = sp[1]
    if not merged:
      startTimestamp = int(sp[2].split('.')[0])
      print(str(i)+"/"+str(len_wavfiles), roomID, user, startTimestamp)
    
    if filename in ignorenames:
      sttresult.append("IGNORE:::"+filename+"\n")
      with open("temp_"+outputkey+"_"+roomID+"_"+user+'.txt', 'a') as f:
        f.write("IGNORE:::"+filename+"\n")
        print("IGNORE:::"+filename+"\n")
      continue

    # Convert file type from webm to wav
    if merged:
      wavfile = "./"+filename
    elif convert:
      inputfile = "../moderator/webm/"+filename
      wavfile = "./post_wav/"+roomID+"_"+user+"_"+str(startTimestamp)+".wav"
      convert_and_split(inputfile, wavfile)
    else:
      wavfile = "./wav/"+roomID+"_"+user+"_"+str(startTimestamp)+".wav"
    
    # Run Naver STT for given audio file
    sttime = int(time())

    # boosting on
    if boost:
      stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=wavfile, completion='sync', boostings=True)
    else:
      stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=wavfile, completion='sync')
    ####### 시간측정용
    endtime = int(time())
    

    transcript = json.loads(stt_res.text)
    print(transcript)
    print(endtime-sttime)
    ####### 시간측정용
    if transcript['text']=='':
      with open("ignore_"+inputkey+".txt", 'a') as ff:
        ff.write(filename+",")
      sttresult.append("IGNORE:::"+filename+"\n")
      with open("temp_"+outputkey+"_"+roomID+"_"+user+'.txt', 'a') as f:
        f.write("IGNORE:::"+filename+"\n")
        print("IGNORE:::"+filename+"\n")
      continue
    
    print(transcript['segments'])
    speech_timestamp = transcript['segments'];
    seg_start = 0;
    seg_end = 0;
    # speechLog = {}
    with open("temp_"+outputkey+"_"+roomID+"_"+user+'.txt', 'a') as f:
      if not merged:
        f.write("\n"+roomID+"_"+user+"_"+str(startTimestamp)+".wav\n")
        sttresult.append(roomID+"_"+user+"_"+str(startTimestamp)+".wav\n")
      for seg in speech_timestamp:
        # print(seg['start'], seg['end'])
        if seg['text'] == '': 
          continue

        if filt and seg['text'] in [
          '엄마', '아빠', '오빠',
          '쯧', '습', '이씨', '허허', '아', '아휴', '아우', '아흠', '에', '오', '음', '아 아', '음 음', '흑', '흠', '흠흠', '허허허', '으흠', '하아', '흐흠', '에휴', '이', '허어', '이보게', '아', '어허', '아유', '어허허허허허허허', '허', '흐흐', '흐흐흐', '흐흐흐흐', '흐흐', 
          '아이고', '아이', '이런', 
          '아마 실행되고 있는 브라우저는 다른 책을 치지 마세요.', '아이 데이터가 실행되고 있는 브라우저는 다른 탭을 끼지 마세요.', '아이 메이저가 진행되고 있는 브라우저는 다른 태도에 그치지 마세요.', '아이 데이터가 되고 있는 브라우저를 다른 탭을 주지 마세요.', '아이들이 저희가 진행되고 있는 브라우저는 다른 책을 쓰지 마세요.', '아이 데이터가 실행되고 있는 버가우자는 다른 탭을 짓지 마세요.', '아이들이 저는 책임지고 있는 브라우저는 다른 책을 기지 마세요.']:
          f.write("SKIP:::"+seg['text']+"\n")
          sttresult.append("SKIP:::"+seg['text']+"\n")
          continue
        f.write(seg['text']+"\n")
        sttresult.append(seg['text']+"\n")
        if merged:
          startTimestamp = 0
        if startTimestamp + seg['start'] != seg_end :
          if seg_end != 0:
            # speechLog[seg_end] = 
            f.write("(" + str(seg_end) + ") SPEECH-END\n")
            sttresult.append("(" + str(seg_end) + ") SPEECH-END\n")
            with open("result_"+outputkey+"_"+inputkey+".txt", 'a') as rf:
              rf.write("(" + str(seg_end) + ") SPEECH-END\n")
            # print("speechLog:: ", speechLog)
          seg_start = startTimestamp + seg['start']
          # speechLog[seg_start] = 
          f.write("(" + str(seg_start) + ") SPEECH-START\n")
          sttresult.append("(" + str(seg_start) + ") SPEECH-START\n")
          with open("result_"+outputkey+"_"+inputkey+".txt", 'a') as rf:
            rf.write("(" + str(seg_start) + ") SPEECH-START\n")
          
        seg_end = startTimestamp + seg['end']

      if seg_end != 0:
        f.write("(" + str(seg_end) + ") SPEECH-END\n")
        sttresult.append("(" + str(seg_end) + ") SPEECH-END\n")
        with open("result_"+outputkey+"_"+inputkey+".txt", 'a') as rf:
          rf.write("(" + str(seg_end) + ") SPEECH-END\n")

  # print(sttresult)
  return sttresult

def save_stt(inputkey, outputkey, convert, merged):
  with open("temp_"+outputkey+"_"+inputkey+".txt", 'r') as ig:
    sttresult = ig.readlines()
  transdict = {}
  curstamp = 0
  curstart = 0
  
  if convert:
    dirpath = 'post_wav/'
  else:
    dirpath = 'wav/'

  ##### merged #####
  if merged:
    transdict[0] = {"temp": [], "dur": 0}
    for i, ig in enumerate(sttresult):
      if ig=='\n':
        continue          
      if ig[0] != '(':
        if curstart and (transdict[curstamp]["temp"] != []):
          transdict[curstamp][curstart] += transdict[curstamp]["temp"]
          transdict[curstamp]["temp"] = []
        if ig[:4] == "SKIP":
          continue
        transdict[curstamp]["temp"].append(ig)
        
      elif ig[-4:] == 'END\n':
        transdict[curstamp]["temp"].append(ig)
      else:
        leftover = None
        if curstart:
          leftover = transdict[curstamp]["temp"][0]
          transdict[curstamp][curstart].append(transdict[curstamp]["temp"][1])
          transdict[curstamp]["temp"] = []

        curstart = ig.split(') ')[0][1:]
        # print("curstart:: ", curstart)

        if leftover:
          ig = [ig, leftover]
        else:
          ig = [ig]
        transdict[curstamp][curstart] = ig + transdict[curstamp]["temp"]
        transdict[curstamp]["temp"] = []
        # print("4: ", transdict)
        # rf.write(ig)
    if curstart:
      transdict[curstamp][curstart] += transdict[curstamp]["temp"]
      transdict[curstamp]["temp"] = []
    ##### Merged #####
  else:
    ##### 녹음파일 조각 #####
    for i, line in enumerate(sttresult):
      print(line)
      print(line.split('.'))
      
      if line[:4] == 'IGNO':
        sp = line.split('_')
        startTimestamp = int(sp[2].split('.')[0])
        print("IGNO: startTimestamp - ", startTimestamp)
        
        dur = librosa.get_duration(filename=dirpath+line[9:-1].split('.')[0]+'.wav')
        transdict[startTimestamp] = {"dur": dur}
        continue
        
      if line=='\n':
        continue
      if line[-4:] == 'wav\n':
        sp = line.split('_')
        roomID = sp[0]
        user = sp[1]
        startTimestamp = int(sp[2].split('.')[0])
        print(roomID, user, startTimestamp)
        
        dur = librosa.get_duration(filename=dirpath+line[:-1])
        # print(dur)

        if curstamp and curstart:
          # print(curstamp, curstart)
          transdict[curstamp][curstart] += transdict[curstamp]["temp"]
          transdict[curstamp]["temp"] = []
        curstamp = startTimestamp
        curstart = 0
        transdict[curstamp] = {"temp": [], "dur": dur}
        # print("1: ", transdict)
      elif line[0] != '(':
        if curstart and (transdict[curstamp]["temp"] != []):
          transdict[curstamp][curstart] += transdict[curstamp]["temp"]
          transdict[curstamp]["temp"] = []
        if line[:4] == "SKIP":
          continue
        transdict[curstamp]["temp"].append(line)
        # print("2: ", transdict)
        # print(line)
      elif line[-4:] == 'END\n':
        # print(line)
        # transdict[curstamp][curstart].append(line)
        transdict[curstamp]["temp"].append(line)
        # print("3: ", transdict)
      else:
        leftover = None
        if curstart:
          # print(transdict[curstamp]["temp"])
          leftover = transdict[curstamp]["temp"][0]
          transdict[curstamp][curstart].append(transdict[curstamp]["temp"][1])
          transdict[curstamp]["temp"] = []

        curstart = line[1:14]
        # print("curstart ", curstart)
        if leftover:
          line = [line, leftover]
        else:
          line = [line]
        transdict[curstamp][curstart] = line + transdict[curstamp]["temp"]
        transdict[curstamp]["temp"] = []
        # print("4: ", transdict)
        # rf.write(line)
    if curstamp and curstart:
      # print(curstamp, curstart)
      transdict[curstamp][curstart] += transdict[curstamp]["temp"]
      transdict[curstamp]["temp"] = []
    # print(transdict)
    ##### 녹음파일 조각 #####
  
  with open("transcript/"+outputkey+"_timestamp_fragkey_"+inputkey+".txt", 'a') as rf:
    ### SAVE INTO FILE AFTER SORT
    fragkeys = []
    totdur = 0
    curdur = 0
    for key in sorted(transdict):
      innerdict = transdict[key]
      fragkey = ""
      if len(innerdict.keys()) > 1:
        fragkey = "\nFRAGKEY:: "+str(key)+'\n'
        fragkeys.append(str(key))
      for k in innerdict:
        if k == 'temp' :
          continue
        elif k == 'dur' :
          totdur += curdur
          curdur = innerdict[k]
          # rf.write(str(curdur) +"/" + str(totdur))
          continue
        if fragkey:
          # print(fragkey)
          rf.write(fragkey)
          fragkey = ""    
        for trans in innerdict[k]:
          if trans[0]=='(':
            if merged:
              time = trans.split(') ')[0][1:]
              millis = int(time)
            else:
              time = trans.split(') ')[0][1:14]
              millis = int(time)-int(key)+ totdur*1000
            # print(time)
            seconds=int((millis/1000)%60)
            minutes=int((millis/(1000*60))%60)
            trans = trans.replace(time, time+", "+str(minutes)+":"+str(seconds))
            # print(seconds, minutes, trans)
          # print(trans)
          rf.write(trans)
    return fragkeys

def make_zip(zipfilename, dirpath, inputkey, fragkeys):
  with ZipFile(zipfilename+'_'+inputkey+'.zip', 'w') as zipObj:
    for fragkey in fragkeys:
      filename = inputkey +'_' + fragkey + '.wav'
      zipObj.write(os.path.join(dirpath, filename), filename)

import glob
import librosa
from zipfile import ZipFile
def main():
  test_1101 = ["eed48de1-983f-47d8-9944-ed2b71483b76_seoyun"]#, 
  # test_1101_whole = ["wholeeed48de1-983f-47d8-9944-ed2b71483b76_seoyun"]
  inputkeys = test_1101
  
  # convert = True
  convert = False
  merged = False
  boost = False
  filt = False
  outputkey = "1101test_whole_naver"

  for idx, inputkey in enumerate(inputkeys):
    keyIdx = 0
    print(inputkey, keyIdx)

  #### Run STT from files
    if merged:
      filenames = [inputkey+'_merged.wav']
    elif convert:
      filenames = [g.split('/')[3] for g in glob.glob("../moderator/webm/"+inputkey+"_*.*")]

    else:
      filenames = [g.split('/')[2] for g in glob.glob("./wav/"+inputkey+"_*.*")]

    #### IGNORE FILES
    if not merged:
      try:
        with open("ignore_"+inputkey+".txt", 'r') as ig:
          ignorenames = ig.read()
          # print(ignorenames)
        ignorenames = ignorenames.split(",")
        print("ignorenames: ", ignorenames, len(ignorenames))
      except:
        ignorenames = []
        print(ignorenames)
    else:
      ignorenames = []

    ## run stt
    sttime = int(time())
    sttresult = run_stt(keyIdx, inputkey, outputkey, filenames, ignorenames, convert, merged, boost, filt)
    endtime = int(time())
    print("RUN STT TIME DELAY:::", endtime-sttime, ':', endtime, '-', sttime)
    print(sttresult)

    # 완성된 sttresult 파일로 저장
    fragkeys = save_stt(inputkey, outputkey, convert, merged)
    print(fragkeys)

    # MS 돌리기 위한 wav zip파일 생성
    zipfilename = outputkey
    if convert:
      dirpath = '/mnt/1tb/seoyun/research/ai-moderator/summarizer/post_wav'
    else:
      dirpath = '/mnt/1tb/seoyun/research/ai-moderator/summarizer/wav'
    make_zip(zipfilename, dirpath, inputkey, fragkeys)

if __name__ == '__main__':
  main()



