from statistics import stdev, mean

with open("../moderator/logs/0118Test_a4d5775b-d4e8-433e-a428-53b64c39c3eb/test.txt", 'r') as f:
  speech_0118 = f.readlines()

recog_delay = []

for idx, line in enumerate(speech_0118):
  if line.split(') ')[1] in ["SPEECH-END\n", "SPEECH-END-M\n"]:
    last_recog = speech_0118[idx-1].split(') ')[0][1:]
    end_stamp = line.split(') ')[0][1:]
    print(last_recog, end_stamp)

    recog_delay.append(int(end_stamp) - int(last_recog))
    
print(recog_delay)

print([d/1000 for d in recog_delay])
print(mean([d/1000 for d in recog_delay]))
  