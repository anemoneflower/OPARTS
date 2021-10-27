import glob
from zipfile import ZipFile
import os

def to_anony(key):
  rem = key.split('_')[1]
  
  newrem = rem[-1]
  
  return key.replace(rem, newrem)

def main():
  inputkeys = ["9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]
    
    # "68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6"]
  # ]
  anonkeys = [to_anony(k) for k in inputkeys]  
  input_name = "finish/frag_boost_timestamp_trans_"
  
  ### total_trans: total_trans[user][timestamp] for all files match input_name
  total_trans = {}
  for anon_idx, anonkey in enumerate(anonkeys):
    with open(input_name + anonkey +".txt", 'r') as tr:
      trans_result = tr.readlines()
    
    inputkey = inputkeys[anon_idx]
    total_trans[inputkey] = {}
    curfragkey = ''
    for trans in trans_result:
      if trans == '\n':
        continue
      if trans[:7] == 'FRAGKEY':
        curfragkey = trans[10:].strip()
        total_trans[inputkey][curfragkey] = []
      elif trans[0] != '(':
        total_trans[inputkey][curfragkey].append(trans)
      else:
        continue
    # print(total_trans)
  
  ### Save total_trans into proper txt file and make zip files
  ##### totlascript_train
  ##### totalscript_test
  ##### wav_list[train]: wav file list which matches with transcript
  ##### wav_list[test]: wav file list which matches with transcript  
  
  print(len(total_trans))
  wav_list = {'train': [], 'test': []}
  is_train = True
  for idx, user in enumerate(total_trans): #inputkeys
    print(idx, user)
    if idx == len(total_trans)-1:
      is_train = False
    # anonuser = to_anony(user)
    trans = total_trans[user]
    print(len(trans))
    print(round(len(trans)/10))
    for tidx, timestamp in enumerate(trans):
      filename = user+'_'+timestamp+'.wav'
      output = filename+'\t'
      for tr in trans[timestamp]:
        output += tr.strip() + ' '
      output = output[:-1] + '\n'
      if is_train and (((idx%2==0) and (tidx < (len(trans) - round(len(trans)/10)))) or ((idx%2==1) and (tidx > round(len(trans)/10)))):
        print("train: ", idx, user, tidx)
        wav_list['train'].append(filename)
        with open("totalscript_train_2.txt", 'a') as ts:
          ts.write(output)
      else:
        print("test: ", idx, user, tidx)
        # wav_list['test'].append(filename)
        # with open("totalscript_test.txt", 'a') as ts:
        #   ts.write(output)
  ### Create zip file for train set and test set each
  with ZipFile('base_wav_transcript_train_2.zip', 'w') as zipObj:
    dir_path = '/mnt/1tb/seoyun/research/ai-moderator/summarizer/wav'
    for dir_path, dir_names, files in os.walk(dir_path):
      # Writing each file into the zip
      for idx, file in enumerate(files):
        if file in wav_list['train']:
          zipObj.write(os.path.join(dir_path, file), file)
    zipObj.write(os.path.join('/mnt/1tb/seoyun/research/ai-moderator/summarizer/anontrans',"totalscript_train_2.txt"), "totalscript_train_2.txt")
  print("base_wav_transcript_train_2.zip")
  
  # with ZipFile('base_wav_transcript_test.zip', 'w') as zipObj:
  #   dir_path = '/mnt/1tb/seoyun/research/ai-moderator/summarizer/wav'
  #   for dir_path, dir_names, files in os.walk(dir_path):
  #     # Writing each file into the zip
  #     for idx, file in enumerate(files):
  #       if file in wav_list['test']:
  #         zipObj.write(os.path.join(dir_path, file), file)
  #   zipObj.write(os.path.join('/mnt/1tb/seoyun/research/ai-moderator/summarizer/anontrans',"totalscript_test.txt"), "totalscript_test.txt")
  # print('base_wav_transcript_test.zip')

if __name__ == "__main__":
  main();