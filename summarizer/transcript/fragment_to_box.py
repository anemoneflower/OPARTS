import glob
import librosa
def update_time(time, timedic):
  parse = time.split(":")
  timedic['m'] = int(parse[0])
  timedic['s'] = int(parse[1])

def main():
  inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]

  for inputkey in inputkeys:
    # ORIGINAL
    fragmentname = "fragment_original_timestamp_transcript_"+inputkey+".txt"
    boxname = "box_original_timestamp_transcript_"+inputkey+".txt"
    outputname = "fbox/fbox_original_transcript_"+inputkey+".txt"

    # FILTERING + BOOSTING
    # fragmentname = "09_timestamp_transcript_"+inputkey+".txt"
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

