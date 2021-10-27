import glob
import librosa
def main():
    ### result 다시뽑기 ###
    inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]
    
    output_key = "box_boost"
    # "box"
    # "box_original"
    # "fragment_original"
    merged = True
    for inputkey in inputkeys:
      # with open("test_box_"+inputkey+".txt", 'r') as ig:
      with open("test_"+output_key+"_"+inputkey+".txt", 'r') as ig:
        sttresult = ig.readlines()
        # print(sttresult)
      transdict = {}
      curstamp = 0
      curstart = 0

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
            # DESIGN: START
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
            transdict[curstamp]["temp"].append(ig)
            # print("2: ", transdict)
            # print(ig)
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
              leftover = transdict[curstamp]["temp"][0]
              transdict[curstamp][curstart].append(transdict[curstamp]["temp"][1])
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
        # print(transdict)
        ##### 녹음파일 조각 #####
      
      with open("transcript/"+output_key+"_timestamp_transcript_"+inputkey+".txt", 'a') as rf:
        ### SAVE INTO FILE AFTER SORT
        totdur = 0
        curdur = 0
        for key in sorted(transdict):
          innerdict = transdict[key]
          for k in innerdict:
            if k == 'temp' :
              continue
            elif k == 'dur' :
              totdur += curdur
              curdur = innerdict[k]
              # rf.write(str(curdur) +"/" + str(totdur))
              continue
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


if __name__ == '__main__':
    main()

