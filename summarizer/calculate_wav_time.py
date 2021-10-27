import glob
import librosa
import datetime

def main():
  inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]
  
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

