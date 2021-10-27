import glob
import librosa
def to_anony(key):
  rem = key.split('_')[1]
  
  newrem = rem[-1]
  
  return key.replace(rem, newrem)


def main():
  inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]

  # output_key = "frag_timestamp_trans_"
  output_key = "frag_boost_timestamp_trans_"
  for inputkey in inputkeys:
    anoninputkey = to_anony(inputkey)
    # with open("test_box_"+inputkey+".txt", 'r') as ig:
    # with open("test_fragment_original_"+inputkey+".txt", 'r') as ig:
    with open("test09_"+inputkey+".txt", 'r') as ig:
      sttresult = ig.readlines()
      # print(sttresult)
    transdict = {}
    curstamp = 0
    curstart = 0

    for i, ig in enumerate(sttresult):
      if ig[:4] == 'IGNO':
        sp = ig.split('_')
        startTimestamp = int(sp[2][:-5])
        
        dur = librosa.get_duration(filename='wav/'+ig[9:-1])
        transdict[startTimestamp] = {"dur": dur}
        continue
        
      if ig=='\n':
        continue

      if ig[-4:] == 'wav\n':
        sp = ig.split('_')
        roomID = sp[0]
        user = sp[1]
        startTimestamp = int(sp[2][:-5])
        print(roomID, user, startTimestamp)

        dur = librosa.get_duration(filename='wav/'+ig[:-1])
        # print(dur)
        if curstamp and curstart:
          # print(curstamp, curstart)
          transdict[curstamp][curstart] += transdict[curstamp]["temp"]
          transdict[curstamp]["temp"] = []
        curstamp = startTimestamp
        curstart = 0
        transdict[curstamp] = {"temp": [], "dur": dur}
        # print("1: ", transdict)
      elif ig[0] != '(':
        if curstart and (transdict[curstamp]["temp"] != []):
          transdict[curstamp][curstart] += transdict[curstamp]["temp"]
          transdict[curstamp]["temp"] = []
        if ig[:4] == "SKIP":
          continue
        if ig.strip() in [
          '엄마', '아빠', '오빠',
          '쯧', '습', '이씨', '허허', '아', '어', '어어', '응', '아니', '아휴', '아우', '아흠', '에', '오', '음', '아 아', '음 음', '흑', '흠', '흠흠', '허허허', '으흠', '하아', '흐흠', '에휴', '이', '허어', '이보게', '아', '어허', '아유', '어허허허허허허허', '허', '하', '흐흐', '흐흐흐', '흐흐흐흐', '흐흐', 
          '아이고', '아이', '이런', 
          '아마 실행되고 있는 브라우저는 다른 책을 치지 마세요.', '아이 데이터가 실행되고 있는 브라우저는 다른 탭을 끼지 마세요.', '아이 메이저가 진행되고 있는 브라우저는 다른 태도에 그치지 마세요.', '아이 데이터가 되고 있는 브라우저를 다른 탭을 주지 마세요.', '아이들이 저희가 진행되고 있는 브라우저는 다른 책을 쓰지 마세요.', '아이 데이터가 실행되고 있는 버가우자는 다른 탭을 짓지 마세요.', '아이들이 저는 책임지고 있는 브라우저는 다른 책을 기지 마세요.', '아이 게이저가 실행되고 있는 브라우저는 다른 탭을 키지 마세요.', '아이게이저가 실행되고 있는 브라우저는 다른 탭을 키지 마세요.', '아이게이저가 실행되고 있는 브라우저는 다른 탭을 아세요.', '아이제이저가 실행되고 있는 브라우저는 다른 태블릿. 피지 마세요.', '라이게이저가 실행되고 있는 브라우저는 다른 탭을 키지 마세요.', '바이 메이저가 실행되고 있는 브라우저는 다른 태을 키지 마세요.', '아이 베이저가 실행이 되는', '바이 게이저가 실행되고 있는 브라우저는 다른 탭을 키지 마세요.', '바이 게이저가 실행되고 있는 브라우저', '아이데이저가 실행되고 있는 브라우저는 다른 탭을 보지 마세요.', '아이 게이저가 실행되고 있는 브라우저는 다른 탭을 두지 마세요.', '와이 게이저가 진행되고 있는 브라우저는 다른 태을 키지 마세요.', '아이데이저가 실행되고 있는 브라우저는 다른 탭을 키지 마세요.', '아이 데이저가 실행되고 있는 브라우저는 다른 탭을 쓰지 마세요.']:
          continue
        transdict[curstamp]["temp"].append(ig)

      elif ig[-4:] == 'END\n':
        # print(ig)
        # transdict[curstamp][curstart].append(ig)
        transdict[curstamp]["temp"].append(ig)
        # print("3: ", transdict)
      else:
        # DESIGN: START
        leftover = None
        if curstart:
          # print(transdict[curstamp]["temp"])
          if(len(transdict[curstamp]["temp"]) == 2):
            leftover = transdict[curstamp]["temp"][0]
            # print(transdict[curstamp]["temp"])
            transdict[curstamp][curstart].append(transdict[curstamp]["temp"][1])
          else:
            transdict[curstamp][curstart].append(transdict[curstamp]["temp"][0])
          transdict[curstamp]["temp"] = []
        curstart = ig[1:14]
        # print("curstart ", curstart)
        if leftover:
          ig = [ig, leftover]
        else:
          ig = [ig]
        transdict[curstamp][curstart] = ig + transdict[curstamp]["temp"]
        transdict[curstamp]["temp"] = []
        # print("4: ", transdict)
        # rf.write(ig)
    if curstamp and curstart:
      # print(curstamp, curstart)
      transdict[curstamp][curstart] += transdict[curstamp]["temp"]
      transdict[curstamp]["temp"] = []

    with open("anontrans/"+output_key+anoninputkey+".txt", 'a') as rf:
      ### SAVE INTO FILE AFTER SORT
      totdur = 0
      curdur = 0
      for key in sorted(transdict):
        innerdict = transdict[key]
        fragkey = ""
        if len(innerdict.keys()) > 1:
          fragkey = "\nFRAGKEY:: "+str(key)+'\n'
        for k in innerdict:
          if k == 'temp' :
            continue
          elif k == 'dur' :
            totdur += curdur
            curdur = innerdict[k]
            # rf.write(str(curdur) +"/" + str(totdur))
            continue
          if not [t for t in innerdict[k] if t[0]!='(']:
            continue
          if fragkey:
            # print(fragkey)
            rf.write(fragkey)
            fragkey = ""          
          for trans in innerdict[k]:
            if trans[0]=='(':
              time = trans.split(') ')[0][1:14]
              millis = int(time)-int(key)+ totdur*1000
              # print(time)
              seconds=int((millis/1000)%60)
              minutes=int((millis/(1000*60))%60)
              trans = trans.replace(time, time+", "+str(minutes)+":"+str(seconds))
              # print(seconds, minutes, trans)
            # print(trans)
            rf.write(trans)

if __name__ == '__main__':
  main()

