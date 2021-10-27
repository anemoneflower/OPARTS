import glob
from zipfile import ZipFile
import os

def to_anony(key):
  rem = key.split('_')[1]
  
  if rem == '길이삭':
    newrem = '1'
  elif rem == '6 박준석':
    newrem = '6'
  else:
    newrem = rem[-1]
  
  return key.replace(rem, newrem)

# def main():
#   dir_path = '/mnt/1tb/eugene123/ai-moderator/summarizer/wav'
#   for dir_path, dir_names, files in os.walk(dir_path):
#     # Writing each file into the zip
#     for file in files:
#       # print(file.split("_")[1])
#       if file.split("_")[1] == '6 박준석':
#         print(file)
#         print(file.replace('6 박준석', '박준석-6'))
#         os.rename(dir_path+"/"+file, dir_path+"/"+file.replace('6 박준석', '박준석-6'))

def main():
  inputkeys = ["19bc34cd-feee-4ffa-afdb-1901b1d24f90_길이삭", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_김다연-5", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_노유정-3", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_이기쁨-6", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_최진영-4", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_한동훈-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_박준석-6", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_송재엽-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_장경석-4", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_황정석-5", "4499b593-365b-407d-a143-00533e7bce42_김동훈-6", "4499b593-365b-407d-a143-00533e7bce42_김윤정-3", "4499b593-365b-407d-a143-00533e7bce42_김현정-4", "4499b593-365b-407d-a143-00533e7bce42_염주선 2", "4499b593-365b-407d-a143-00533e7bce42_이주원-5", "4499b593-365b-407d-a143-00533e7bce42_전승민-1"]
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
        with open("totalscript_train.txt", 'a') as ts:
          ts.write(output)
      else:
        print("test: ", idx, user, tidx)
        wav_list['test'].append(filename)
        with open("totalscript_test.txt", 'a') as ts:
          ts.write(output)
  ### Create zip file for train set and test set each
  with ZipFile('system_wav_transcript_train.zip', 'w') as zipObj:
    dir_path = '/mnt/1tb/eugene123/ai-moderator/summarizer/wav'
    for dir_path, dir_names, files in os.walk(dir_path):
      # Writing each file into the zip
      for idx, file in enumerate(files):
        if file in wav_list['train']:
          zipObj.write(os.path.join(dir_path, file), file)
    zipObj.write(os.path.join('/mnt/1tb/eugene123/ai-moderator/summarizer/anontrans',"totalscript_train.txt"), "totalscript_train.txt")
  print("system_wav_transcript_train.zip")
  
  with ZipFile('system_wav_transcript_test.zip', 'w') as zipObj:
    dir_path = '/mnt/1tb/eugene123/ai-moderator/summarizer/wav'
    for dir_path, dir_names, files in os.walk(dir_path):
      # Writing each file into the zip
      for idx, file in enumerate(files):
        if file in wav_list['test']:
          zipObj.write(os.path.join(dir_path, file), file)
    zipObj.write(os.path.join('/mnt/1tb/eugene123/ai-moderator/summarizer/anontrans',"totalscript_test.txt"), "totalscript_test.txt")
  print('system_wav_transcript_test.zip')

if __name__ == "__main__":
  main();