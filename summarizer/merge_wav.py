import glob
import wave
import sox    

def to_anony(key):
  rem = key.split('_')[1]
  
  if rem == '길이삭':
    newrem = '1'
  elif rem == '6 박준석':
    newrem = '6-1'
  elif rem == '박준석-6':
    newrem = '6-2'
  else:
    newrem = rem[-1]
  
  return key.replace(rem, newrem)

def main():
    ### result 다시뽑기 ###
    inputkeys = ["19bc34cd-feee-4ffa-afdb-1901b1d24f90_길이삭", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_김다연-5", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_노유정-3", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_이기쁨-6", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_최진영-4", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_한동훈-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_6 박준석", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_박준석-6", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_송재엽-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_장경석-4", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_황정석-5", "4499b593-365b-407d-a143-00533e7bce42_김동훈-6", "4499b593-365b-407d-a143-00533e7bce42_김윤정-3", "4499b593-365b-407d-a143-00533e7bce42_김현정-4", "4499b593-365b-407d-a143-00533e7bce42_염주선 2", "4499b593-365b-407d-a143-00533e7bce42_이주원-5", "4499b593-365b-407d-a143-00533e7bce42_전승민-1"]

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

