import glob
import wave
import sox    

def to_anony(key):
  rem = key.split('_')[1]
  
  newrem = rem[-1]
  
  return key.replace(rem, newrem)

def main():
    inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]

    anony = True

    for inputkey in inputkeys:
      infiles = sorted(glob.glob("./wav/"+inputkey+"_*.*"))
      if anony:
        inputkey = "anonwav/"+to_anony(inputkey)
      outputname = inputkey + "_merged.wav"
      print(inputkey, len(infiles))
      
      cbn=sox.Combiner()
      data = []

      cbn.build(infiles, outputname, 'concatenate')
      # for infile in infiles:
      #   print(infile)
      #   w = wave.open(infile, 'rb')
      #   data.append( [w.getparams(), w.readframes(w.getnframes())] )
      #   w.close()
      
      # output = wave.open(outfile, 'wb')
      # output.setparams(data[0][0])
      # for i in range(len(data)):
      #     output.writeframes(data[i][1])
      # output.close()

if __name__ == '__main__':
    main()

