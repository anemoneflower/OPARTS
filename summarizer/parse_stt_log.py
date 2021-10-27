import glob
import librosa
def main():
    ### result 다시뽑기 ###
    inputkeys = ["19bc34cd-feee-4ffa-afdb-1901b1d24f90_길이삭", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_김다연-5", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_노유정-3", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_이기쁨-6", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_최진영-4", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_한동훈-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_박준석-6", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_송재엽-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_장경석-4", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_황정석-5", "4499b593-365b-407d-a143-00533e7bce42_김동훈-6", "4499b593-365b-407d-a143-00533e7bce42_김윤정-3", "4499b593-365b-407d-a143-00533e7bce42_김현정-4", "4499b593-365b-407d-a143-00533e7bce42_염주선 2", "4499b593-365b-407d-a143-00533e7bce42_이주원-5", "4499b593-365b-407d-a143-00533e7bce42_전승민-1"]
    
    output_key = "fragment_original"
    merged = False
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

