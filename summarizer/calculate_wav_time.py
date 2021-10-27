import glob
import librosa
import datetime

def main():
  inputkeys = ["19bc34cd-feee-4ffa-afdb-1901b1d24f90_길이삭", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_김다연-5", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_노유정-3", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_이기쁨-6", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_최진영-4", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_한동훈-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_6 박준석", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_박준석-6", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_송재엽-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_장경석-4", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_황정석-5", "4499b593-365b-407d-a143-00533e7bce42_김동훈-6", "4499b593-365b-407d-a143-00533e7bce42_김윤정-3", "4499b593-365b-407d-a143-00533e7bce42_김현정-4", "4499b593-365b-407d-a143-00533e7bce42_염주선 2", "4499b593-365b-407d-a143-00533e7bce42_이주원-5", "4499b593-365b-407d-a143-00533e7bce42_전승민-1"]

  print(len(inputkeys))
  
  tot_totdur = 0
  for inputkey in inputkeys:
    totdur = 0
    try:
      with open("ignore_"+inputkey+".txt", 'r') as ig:
        ignorenames = ig.read()
      ignorenames = ignorenames.split(",")
    except:
      ignorenames = []
    
    ignorenames = ["./wav/"+ig for ig in ignorenames]
    # print(ignorenames)
    
    infiles = sorted(glob.glob("./wav/"+inputkey+"_*.*"))
    
    for infile in infiles:
      if infile in ignorenames:
        # print(infile)
        continue
      else:
        dur = librosa.get_duration(filename=infile)
        # print(dur)
        totdur += dur
        tot_totdur += dur
    print(inputkey+" - totdur: ", totdur, " || ", str(datetime.timedelta(seconds=totdur)))

  print("tot_totdur: ", tot_totdur, " || ", str(datetime.timedelta(seconds=tot_totdur)))

  
  
  
  

if __name__ == '__main__':
  main()

