import os
import glob
def to_anony(key):
  rem = key.split('_')[1]
  
  newrem = rem[-1]
  
  return key.replace(rem, newrem)

def main():
  # dir_path = '/mnt/1tb/eugene123/ai-moderator/summarizer/fine-tuning/model1'

  naver_boost_files = sorted(glob.glob("../anontrans/frag_boost_timestamp_trans_*"))
  naver_boost_result = {}
  for file in naver_boost_files:
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

  trained_files = sorted(glob.glob("./txt_lexical_user-tts_original/model_1/*"))
  print(len(trained_files))

  original_path = "./txt_lexical_user-tts_original/model_2/"
  human_path = "./Human-labeled_transcription(normalized)/"

  for idx, file in enumerate(trained_files):
    filename = file.split("/")[3]
    matching_wav = filename.split(".")[0]+".wav"

    with open(file, 'r') as f:
      trained_tr = f.readlines()

    with open(original_path+filename, 'r') as f:
      original_tr = f.readlines()

    with open(human_path+filename, 'r') as f:
      human_tr = f.readlines()

    anonname = to_anony(filename).split("_")
    naverkey = anonname[0]+"_"+anonname[1]
    naverfrag = anonname[2].split('.')[0]
    try:
      naver_tr = naver_boost_result[naverkey][naverfrag]
    except:
      naver_tr = []
    
    naver_result = ""
    for tr in naver_tr:
      naver_result += tr.strip() + ' '

    trained_result = ""
    for tr in trained_tr:
      trained_result += tr.strip() + ' '

    original_result = ""
    for tr in original_tr:
      original_result += tr.strip() + ' '

    human_result = ""
    for tr in human_tr:
      human_result += tr.strip() + ' '

    print(idx, file, filename, matching_wav)
    print(trained_result, original_result, human_result, naver_result)

    with open("result_mapping.txt", "a") as rm:
      rm.write(matching_wav+"\n")
      rm.write("human_labeled::: "+human_result+"\n")
      rm.write("naver_model::::: "+naver_result+"\n")
      rm.write("trained_model::: "+trained_result+"\n")
      rm.write("original_model:: "+original_result+"\n")
      rm.write("\n")

if __name__ == "__main__":
  main();