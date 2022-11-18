from numbers import Number
import statistics
import datetime
with open("cpsAdmin.txt", 'r') as ig:
  sttLog = ig.readlines()

endDetect = []
for i, log in enumerate(sttLog):
  if log.split(') ')[1] == "SPEECH-END\n":
    print(log, sttLog[i-1])
    lastgen = datetime.datetime.fromtimestamp(float(log.split(') ')[0][1:-1])/100)
    endsig = datetime.datetime.fromtimestamp(float(sttLog[i-1].split(') ')[0][1:-1])/100)
    print(lastgen, endsig)
    endDetect.append((lastgen - endsig).total_seconds())
    
print(endDetect)
print(statistics.mean(endDetect))
  