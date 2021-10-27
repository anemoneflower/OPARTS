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
      if boostings:
        boostings = [{"words": "꽃구경, 페스토, 엘에이갈비, 세꼬시, 육회, 술국, 블록팩, 아이스커피, 아몬드봉봉, 리조또, 코엑스, 비빔냉면, 육사시미, 냉면, 돈카츠, 진대감, 부대찌개, 발로나카카오밀크, 잠실역, 평양온면, 숙성지, 감자튀김, 남산골한옥마을, 경치, 순메밀, 시나몬, 블라스트, 큐브케이크, 송파나루길, 이십만원, 칼국수, 해장국, 케일주스, 리코타치즈, 일리터, 도미뱃살, 바이킹스워프, 바이탈피치, 스타필드, 골뱅이무침, 라운지앤바, 디저트, 들꽃마루, 홍차롤, 장어구이, 송파, 키친이공오, 떡볶이, 완자, 된장찌개, 한정식, 봉은사역, 레이디그레이, 바질, 새우돼지고기완자뽀짜이판, 불고기브라더스, 명동거리, 삼합, 콩닭콩닭, 타르타르, 샤인머스캣, 올림픽홀, 물곰, 제로컴플렉스, 빠다, 고관스튜디오, 멜론빙수, 남산서울타워, 레이디스플레져, 엄마는외계인, 명란오일, 서울시립미술관, 시립미술관, 프리미엄, 우롱피치, 플랫화이트, 코돈부루, 딸바, 오프레도, 심층상담, 동묘앞역, 그라놀라, 판메밀, 평양냉면, 육개장, 술밥, 대중음악박물관, 햄버거, 맑은우육탕면, 명태식해, 이호, 딸기밭, 체험관, 세작유자, 엘유사십이, 토로토로, 인터컨티넨탈, 아인슈페너, 캠핑, 베스킨라빈스, 초계국수, 방이역, 아이스링크, 오레오쿠키앤카라멜, 아유베다, 동그랑땡, 별을품은곱창, 펄, 방문자, 라구, 버라이어티팩, 크림치즈, 봉땅, 일술, 크레이프, 시트러스, 결정장애, 백세주, 전복닭죽, 레몬라임, 돌솥밥, 아쿠아리움, 입장료, 샤브샤브, 수란, 보리굴비, 레디팩, 플래터, 강동구청역, 사시미, 어니언, 국립극단 명동예술극장, 메가박스, 어피치, 을밀대, 청와옥, 바닐라빈라떼, 티라미슈, 날치알, 에이드, 참게얼큰탕, 오므라이스, 알도치, 명동, 새우볼, 세이지, 올림픽공원, 바이탈, 로네펠트티하우스, 시청역, 분보남보, 모짜렐라, 하우스, 달빛산책, 돈차슈라멘, 모듬전, 레드파파야티샹그리아, 아퀄리브리엄, 호우섬, 양갈비, 롯데월드몰, 순대국밥, 치맥, 한우바싹불고기, 샐러드, 짜조, 롯데월드, 비네그렛, 마늘빵, 찐만두, 물회, 함박, 뷔페, 라뽂이, 허니레몬, 불닭, 간재미, 우롱티, 깍뚜기, 스포트컵, 주옥, 그릴, 이베리코, 잠실한강공원, 미쉐린, 가브리살, 별별성격카페, 강남역, 정신라멘, 양어깨살, 세트권, 야경, 힐링, 오렌지당근퓨레, 숯불구이, 매직아일랜드, 이탈리아, 가재미, 딸리아뗄레, 비프, 샤롯데씨어터, 와규, 특선, 크앤토, 아보카도, 밀키우롱, 냄비우동, 볶음면, 베리베리스트로베리, 풍납토성, 로즈마리, 먹자골목, 도루묵, 카레라이스, 칵테일, 웨스틴조선호텔, 별마당도서관, 원더플레이스, 해물파전, 아이스죠리퐁, 성곽, 바닐, 묵사발, 한옥마을, 프렌치, 고막, 엔다이브, 브라운버터소스, 요구르트, 미스사이공, 한돈, 새우후라이, 명동지하쇼핑센터, 돈코츠라멘, 얼큰순대국밥, 가이드, 메밀, 라구소스, 충무로역, 한우리, 우동사리, 페퍼민트, 윌도프, 화이트, 컨벤션센터, 약선, 칠아웃, 라즈베리피치, 상하목장, 롯데콘서트홀, 마르셀, 과카몰리, 쭈꾸미, 더블레귤러, 세트, 레몬에이드, 고르곤졸라, 디너, 통전복, 하프갤론, 소마미술관, 명동교자, 잔술, 아이스크림롤, 루카스, 가리비, 화포식당, 아이스모찌, 쌀국수, 꽃놀이, 산들해, 강남면옥, 한성백제박물관, 설문, 아이스마카롱, 바다의왕자, 하동관, 돈까스, 제육, 얼큰수제비, 아란치니, 아메리카노, 허브티, 동대문역사문화공원역, 동역사, 부르리카, 웜, 루이보스 스윗밀크티, 지킬앤하이드, 남대문시장, 파르나스몰, 채끝, 스페셜, 캐모마일, 생선가스, 더블치즈버거, 홍어회무침, 트러플, 아쌈, 코스모스, 마늘칩꿔바육, 명동돈가스, 심리카페, 위례성대로, 패밀리, 소르베, 홍어식해훈제오리, 속초생태집, 초콜렛, 시트론바이탈, 콜드브루, 몽촌토성, 크루통, 가마솥밥, 홈카페, 트리플민초, 스위트, 홍어회, 찹쌀떡, 곤드레나물밥, 정종, 깔라마리, 한성백제역, 베이컨, 김치찌개, 쇼핑, 춘천닭갈비, 타르트, 메뉴판, 샌드위치, 생면빠빠르델레, 접시만두, 쉐프, 밀크티, 파스타, 석촌동고분궁, 런치, 돈부리, 싱글킹, 맷차, 오제, 고봉삼계탕, 곰국수, 유가네닭갈비, 블로그, 분자, 와츄원, 떡갈비, 돌코롬 그린라떼, 과일티, 코로나, 화떡, 연어장, 레몬스카이, 공차, 듀얼, 마주앙, 스파게티니, 돼지불백, 탄지레몬, 반미, 부라타, 왕교자, 숭례문, 체리쥬밀레, 벌교꼬막, 샴피뇽 소테, 치킨카레스프, 분보후에, 곰치, 콜라, 마카다미아, 드립커피, 마린프렌즈권, 화진포막국수, 스파게티, 미즈컨테이너, 양지탕밥, 토스트, 아이리쉬, 한성백제시대, 타로, 뇨끼, 카페라떼, 피크닉, 차돌, 더블주니어, 엔터테인먼트, 명동성당, 큰기와집 한상, 오설록티하우스, 위미 올레 감귤에이드, 곱창전골, 브런치세트, 코스, 히레가스, 테마파크, 까사빠보, 전통혼례, 라자냐, 삼성역, 장미정원, 롯데몰, 로투스, 한방삼계탕, 아이스크림, 스노우화이트, 모르겐타우, 광화문미진, 상황삼계탕, 앙찌, 메뉴, 신세계백화점 본점, 덕수궁, 만두국밥, 클래식, 알리오올리오, 돈육보쌈, 오리가슴, 짬뽕, 모둠순대, 오믈렛, 닭불고기, 쿼터, 간장게장, 국악공연, 맛있는녀석들, 제육쌈밥, 포테이토, 입장권, 맥주, 순대구이, 솔티드 카라멜, 쥬스, 이니스프리 그린카페, 엘유사이, 로스가스, 랍스터, 바베큐, 쭈닭갈비, 석촌호수, 파인트, 시민공원, 스틱바, 크린티라떼, 찰떡콩떡, 황태, 설향딸기, 크로플, 라미옥, 도림, 피넛버터, 숯불, 쯔란오징어튀김, 오레오 쿠키앤크림, 피나콜라다, 마리 앙투아네트, 어리굴젓, 블랙티, 참쌀순대, 밀크폼, 단팥빵, 구운감자, 뉴욕치즈케이크, 라구짜장도삭면, 쑥국도다리, 아이스티, 에스프레소, 북창동, 리뷰, 그린티, 자장면, 민트초콜릿칩, 송파나루공원, 홈메이드, 블랙하가우, 생맥주, 서울식불고기, 평양면옥, 홍만당, 임실치즈, 얼그레이, 크림, 핸드팩, 올림픽로, 포숑, 안심카츠, 한가람, 사케, 꽃등심, 한아람정육식당, 치킨부루, 곤드레, 차이, 스트로베리필즈, 우나기벤토, 영동대교, 하야시, 맷돌"}]
      
      
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
    inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]


    for idx, inputkey in enumerate(inputkeys):
      # inputkey = inputkeys[int(input("UsernameIDX(0~17)"))]
      # inputkey = '773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1'
      # keyIdx = int(input("keyIdx(0~5): "))
      keyIdx = 0
      print(inputkey, keyIdx)      
      # filenames = [g.split('/')[2] for g in glob.glob("./wav/"+inputkey+"_*.*")]
      # filenames = [g.split('/')[2] for g in glob.glob("./wav/"+inputkey)]
      
      # 773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1_1629952268074
      # print(filenames, len(filenames))
      # print(len(filenames))
      filenames = [inputkey+'_merged.wav']
      merged = True

      # print(filenames.index('773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1_1629953370609.wav'))


  #### IGNORE FILES IF RERUN
      if not merged:
        try:
          with open("ignore_"+inputkey+".txt", 'r') as ig:
            ignorenames = ig.read()
            print(ignorenames)
          ignorenames = ignorenames.split(",")
          print(ignorenames, len(ignorenames))
        except:
          ignorenames = []
          print(ignorenames)
      else:
        ignorenames = []

      # Run again only some files
      # ignorenames = []
      # filenames = ["4499b593-365b-407d-a143-00533e7bce42_김윤정-3_1629959812886.wav"]

      # keyIdx = 0
      
      for i, filename in enumerate(filenames):        
        sp = filename.split('_')
        roomID = sp[0]
        user = sp[1]
        if not merged:
          startTimestamp = int(sp[2][:-4])
          print(i, roomID, user, startTimestamp)
        # inputkey = roomID+"_"+user
        
        if filename in ignorenames:
          with open("test_box_boost_"+roomID+"_"+user+'.txt', 'a') as f:
            f.write("IGNORE:::"+filename+"\n")
            print("IGNORE:::"+filename+"\n")
          continue

        # Convert file type from webm to wav
        # outputfile = "./wav/"+roomID+"_"+user+"_"+str(startTimestamp)+".wav"
        outputfile = "./"+filename
        
        # Run Naver STT for given audio file
        sttime = int(time())
        # stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=outputfile, completion='sync')

        # boosting on
        stt_res = ClovaSpeechClient(invoke_url[keyIdx], secret[keyIdx]).req_upload(file=outputfile, completion='sync', boostings=True)
        ####### 시간측정용
        endtime = int(time())
        

        transcript = json.loads(stt_res.text)
        # print(transcript)
        print(endtime-sttime)
        ####### 시간측정용
        if transcript['text']=='':
          with open("ignore_"+inputkey+".txt", 'a') as ff:
            ff.write(filename+",")
          with open("test_box_boost_"+roomID+"_"+user+'.txt', 'a') as f:
            f.write("IGNORE:::"+filename+"\n")
            print("IGNORE:::"+filename+"\n")
          continue
        
        print(transcript['segments'])
        speech_timestamp = transcript['segments'];
        seg_start = 0;
        seg_end = 0;
        # speechLog = {}
        with open("test_box_boost_"+roomID+"_"+user+'.txt', 'a') as f:
          if not merged:
            f.write("\n"+roomID+"_"+user+"_"+str(startTimestamp)+".wav\n")
          for seg in speech_timestamp:
            # print(seg['start'], seg['end'])
            if seg['text'] == '': 
              continue

            if seg['text'] in [
              '엄마', '아빠', '오빠',
              '쯧', '습', '이씨', '허허', '아', '아휴', '아우', '아흠', '에', '오', '음', '아 아', '음 음', '흑', '흠', '흠흠', '허허허', '으흠', '하아', '흐흠', '에휴', '이', '허어', '이보게', '아', '어허', '아유', '어허허허허허허허', '허', '흐흐', '흐흐흐', '흐흐흐흐', '흐흐', 
              '아이고', '아이', '이런', 
              '아마 실행되고 있는 브라우저는 다른 책을 치지 마세요.', '아이 데이터가 실행되고 있는 브라우저는 다른 탭을 끼지 마세요.', '아이 메이저가 진행되고 있는 브라우저는 다른 태도에 그치지 마세요.', '아이 데이터가 되고 있는 브라우저를 다른 탭을 주지 마세요.', '아이들이 저희가 진행되고 있는 브라우저는 다른 책을 쓰지 마세요.', '아이 데이터가 실행되고 있는 버가우자는 다른 탭을 짓지 마세요.', '아이들이 저는 책임지고 있는 브라우저는 다른 책을 기지 마세요.']:
              f.write("SKIP:::"+seg['text']+"\n")
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
                with open("result_box_boost_"+inputkey+".txt", 'a') as rf:
                  rf.write("(" + str(seg_end) + ") SPEECH-END\n")
                # print("speechLog:: ", speechLog)
              seg_start = startTimestamp + seg['start']
              # speechLog[seg_start] = 
              f.write("(" + str(seg_start) + ") SPEECH-START\n")
              print("(" + str(seg_start) + ") SPEECH-START\n")
              with open("result_box_boost_"+inputkey+".txt", 'a') as rf:
                rf.write("(" + str(seg_start) + ") SPEECH-START\n")
              
            seg_end = startTimestamp + seg['end']

            # print("speechLog:: ", speechLog)
            # print()
          
          # speechLog[seg_end] = 
          if seg_end != 0:
            f.write("(" + str(seg_end) + ") SPEECH-END\n")
            print("(" + str(seg_end) + ") SPEECH-END\n")
            with open("result_box_boost_"+inputkey+".txt", 'a') as rf:
              rf.write("(" + str(seg_end) + ") SPEECH-END\n")

          # print(speechLog)
          
        #   # Design: save log to file

if __name__ == '__main__':
    main()



