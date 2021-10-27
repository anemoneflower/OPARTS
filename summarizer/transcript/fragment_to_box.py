import glob
import librosa
def update_time(time, timedic):
  parse = time.split(":")
  timedic['m'] = int(parse[0])
  timedic['s'] = int(parse[1])

def main():
  inputkeys = ["19bc34cd-feee-4ffa-afdb-1901b1d24f90_길이삭", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_김다연-5", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_노유정-3", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_이기쁨-6", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_최진영-4", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_한동훈-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_박준석-6", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_송재엽-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_장경석-4", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_황정석-5", "4499b593-365b-407d-a143-00533e7bce42_김동훈-6", "4499b593-365b-407d-a143-00533e7bce42_김윤정-3", "4499b593-365b-407d-a143-00533e7bce42_김현정-4", "4499b593-365b-407d-a143-00533e7bce42_염주선 2", "4499b593-365b-407d-a143-00533e7bce42_이주원-5", "4499b593-365b-407d-a143-00533e7bce42_전승민-1"]

  for inputkey in inputkeys:
    # ORIGINAL
    fragmentname = "fragment_original_timestamp_transcript_"+inputkey+".txt"
    boxname = "box_original_timestamp_transcript_"+inputkey+".txt"
    outputname = "fbox/fbox_original_transcript_"+inputkey+".txt"

    # FILTERING + BOOSTING
    # fragmentname = "09timestamp_transcript_"+inputkey+".txt"
    # boxname = "box_boost_timestamp_transcript_"+inputkey+".txt"
    # outputname = "fbox/fbox_filter_boost_transcript_"+inputkey+".txt"
    
    print(outputname)
    with open(fragmentname, 'r') as ig:
      fragresult = ig.readlines()
    with open(boxname, 'r') as ig:
      boxresult = ig.readlines()

    with open(outputname, 'a') as rf:
      rf.write(fragresult[0])
    fragidx = 1
    boxstart = {'m': 0, 's': 0}
    boxend = {'m': 0, 's': 0}
    fragstart = {'m': 0, 's': 0}
    fragend = {'m': 0, 's': 0}
    
    endStamp = ""

    for boxidx, boxline in enumerate(boxresult):
      if boxline[0] == '(': # e.g., (72180, 1:12) SPEECH-START
        boxparse = boxline.split(', ')[1].split(') ')
        boxtime = boxparse[0] # e.g., 1:12
        boxtag = boxparse[1].strip() # e.g., SPEECH-START
        # print("boxtag", boxtag)
        if boxtag == "SPEECH-START":
          update_time(boxtime, boxstart)
          # print("boxstart", boxstart)
        else:
          update_time(boxtime, boxend)
          # print("boxend", boxend)
          # process fragment
          startStamp = False
          while fragend['m'] < boxend['m'] or (fragend['m'] == boxend['m'] and fragend['s'] < boxend['s']):
            if fragidx==len(fragresult):
              break
            fragline = fragresult[fragidx]
            if fragline[0] == '(':
              fragparse = fragline.split(', ')[1].split(') ')
              fragtime = fragparse[0] # e.g., 1:12
              fragtag = fragparse[1].strip() # e.g., SPEECH-START
              # print("fragtag", fragtag)
              if fragtag == "SPEECH-START":
                update_time(fragtime, fragstart)
                # print("fragstart", fragstart)
                if fragstart['m'] == fragend['m'] and fragstart['s'] == fragend['s']:
                  fragidx += 1
                  # print("startfragidx", fragidx)
                  startStamp = True
                  continue
                if fragstart['m'] < boxstart['m'] or (fragstart['m'] == boxstart['m'] and fragstart['s'] < boxstart['s']):
                  while fragend['m'] < boxstart['m'] or (fragend['m'] == boxstart['m'] and fragend['s'] < boxstart['s']):
                    if fragidx==len(fragresult):
                      break
                    fragline = fragresult[fragidx]
                    if fragline[0] == '(':
                      fragparse = fragline.split(', ')[1].split(') ')
                      fragtime = fragparse[0] # e.g., 1:12
                      fragtag = fragparse[1].strip() # e.g., SPEECH-START
                      # print("fragtag", fragtag)
                      if fragtag == "SPEECH-START":
                        update_time(fragtime, fragstart)
                        # print("_fragstart", fragstart)
                        if fragstart['m'] == fragend['m'] and fragstart['s'] == fragend['s']:
                          fragidx += 1
                          # print("fragidx2", fragidx)
                          # print(fragstart, fragend, boxstart, boxend)
                          continue
                        if endStamp:
                          # print("_[PRINT] ", endStamp)
                          with open(outputname, 'a') as rf:
                            rf.write(endStamp)
                          endStamp = ""
                        if fragstart['m'] > boxend['m'] or (fragstart['m'] == boxend['m'] and fragstart['s'] > boxend['s']):
                          break                            
                        if not startStamp:
                          # print("_[PRINT] ", fragline)
                          with open(outputname, 'a') as rf:
                            rf.write(fragline)
                      else: # fragtag == "SPEECH-END"
                        update_time(fragtime, fragend)
                        # print("_fragend", fragend)
                        
                        endStamp = fragline
                        
                      fragidx += 1
                      # print("fragidx3", fragidx)
                    else:
                      # print("_[PRINT] ", fragline)
                      with open(outputname, 'a') as rf:
                        rf.write(fragline)
                      fragidx += 1
                      # print("fragidx4", fragidx)
                  continue
                elif fragstart['m'] > boxend['m'] or (fragstart['m'] == boxend['m'] and fragstart['s'] > boxend['s']):
                  break
                elif not startStamp:
                  if endStamp:
                    # print("[PRINT] ", endStamp)
                    with open(outputname, 'a') as rf:
                      rf.write(endStamp)
                    endStamp = ""
                  # print("[PRINT] ", fragline)
                  with open(outputname, 'a') as rf:
                    rf.write(fragline)
                  startStamp = True
                fragidx += 1
                # print("fragidx5", fragidx)
              else:
                update_time(fragtime, fragend)
                # print("fragend", fragend)
                endStamp = fragline
                fragidx += 1
                # print("fragidx6", fragidx)
            else:
              # print("[PRINT] ", fragline)
              with open(outputname, 'a') as rf:
                rf.write(fragline)
              fragidx += 1
              # print("fragidx7", fragidx)
    # print("[PRINT] ", fragline)  
    with open(outputname, 'a') as rf:
      rf.write(fragline)

if __name__ == '__main__':
    main()

