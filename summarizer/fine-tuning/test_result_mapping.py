import os
import glob
def to_anony(key):
  rem = key.split('_')[1]
  
  if rem == '길이삭':
    newrem = '1'
  elif rem == '6 박준석':
    newrem = '6'
  else:
    newrem = rem[-1]
  
  return key.replace(rem, newrem)

def get_naver_result(files):
  naver_boost_result = {}
  for file in files:
    filename = file.split('/')[2].split('_')
    filename = filename[4]+"_"+filename[5].split(".")[0]

    naver_boost_result[filename] = {}
    with open(file, 'r') as f:
      text = f.readlines()
    
    curfragkey = ''
    for trans in text:
      if trans == '\n':
        continue
      if trans[:7] == 'FRAGKEY':
        curfragkey = trans[10:].strip()
        naver_boost_result[filename][curfragkey] = []
      elif trans[0] != '(':
        naver_boost_result[filename][curfragkey].append(trans)
      else:
        continue

  return naver_boost_result

def main():
  # dir_path = '/mnt/1tb/eugene123/ai-moderator/summarizer/fine-tuning/model1'

  # naver_boost_files = sorted(glob.glob("../anontrans/frag_boost_timestamp_trans_*"))
  naver_files = glob.glob("../transcript/1020demo_*")

  naver_stt = get_naver_result(naver_files)
  print(naver_stt.keys())
  print(naver_files)
  
  for filename in naver_stt:
    username = filename.split("_")[1]

    model1_path = "../1020demo/"+username+"/model_1/"+filename+"_"
    model2_path = "../1020demo/"+username+"/model_2/"+filename+"_"

    fragcnt = len(naver_stt[filename].keys())
    for idx, fragkey in enumerate(naver_stt[filename].keys()):
      with open(model1_path+fragkey+".txt", 'r') as f:
        model1_tr = f.readlines()
      with open(model2_path+fragkey+".txt", 'r') as f:
        model2_tr = f.readlines()
      print(len(model1_tr), len(model2_tr), fragkey)

      naver_result = ""
      for tr in naver_stt[filename][fragkey]:
        naver_result += tr.strip() + ' '

      trained_result = ""
      for tr in model1_tr:
        trained_result += tr.strip() + ' '

      original_result = ""
      for tr in model2_tr:
        original_result += tr.strip() + ' '

      matching_wav = filename+"_"+fragkey+".wav"

      print(username, str(idx)+"/"+str(fragcnt), matching_wav)
      print(naver_result, trained_result, original_result)

      with open("../1020demo/mapping/"+username+"_result_mapping.txt", "a") as rm:
        rm.write(matching_wav+"\n")
        # rm.write("human_labeled::: "+human_result+"\n")
        rm.write("naver_model::::: "+naver_result+"\n")
        rm.write("trained_model::: "+trained_result+"\n")
        rm.write("original_model:: "+original_result+"\n")
        rm.write("\n")

##### quaility test
  # trained_files = sorted(glob.glob("./txt_lexical_user-tts_original/model_1/*"))
  # print(len(trained_files))

  # original_path = "./txt_lexical_user-tts_original/model_2/"
  # human_path = "./Human-labeled_transcription(normalized)/"

  # for idx, file in enumerate(trained_files):
  #   filename = file.split("/")[3]
  #   matching_wav = filename.split(".")[0]+".wav"

  #   with open(file, 'r') as f:
  #     trained_tr = f.readlines()

  #   with open(original_path+filename, 'r') as f:
  #     original_tr = f.readlines()

  #   with open(human_path+filename, 'r') as f:
  #     human_tr = f.readlines()

  #   anonname = to_anony(filename).split("_")
  #   naverkey = anonname[0]+"_"+anonname[1]
  #   naverfrag = anonname[2].split('.')[0]
  #   naver_result = ""
  #   for tr in naver_boost_result[naverkey][naverfrag]:
  #     naver_result += tr.strip() + ' '

  #   trained_result = ""
  #   for tr in trained_tr:
  #     trained_result += tr.strip() + ' '

  #   original_result = ""
  #   for tr in original_tr:
  #     original_result += tr.strip() + ' '

  #   human_result = ""
  #   for tr in human_tr:
  #     human_result += tr.strip() + ' '

  #   print(idx, file, filename, matching_wav)
  #   print(trained_result, original_result, human_result, naver_result)

  #   with open("result_mapping.txt", "a") as rm:
  #     rm.write(matching_wav+"\n")
  #     rm.write("human_labeled::: "+human_result+"\n")
  #     rm.write("naver_model::::: "+naver_result+"\n")
  #     rm.write("trained_model::: "+trained_result+"\n")
  #     rm.write("original_model:: "+original_result+"\n")
  #     rm.write("\n")

if __name__ == "__main__":
  main();