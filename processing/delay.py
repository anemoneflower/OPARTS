from statistics import stdev, mean

with open('moderator_1127.txt') as f:
  moderator_1127 = f.readlines()
  
with open('moderator_1125.txt') as f:
  moderator_1125 = f.readlines()

with open('moderator_1122.txt') as f:
  moderator_1122 = f.readlines()
  
with open('moderator_1118.txt') as f:
  moderator_1118 = f.readlines()
  
def parse_delay(input_data, stt_array, sum_array):
  for i in range(len(input_data)):
    line = input_data[i]
    if '-----requestSTT(' in line:
      if 'cpsAdmin' in line:
        continue
      if '하연' in line:
        continue
      if 'success' in line:
        # print('---STT---')
        # print(line.strip())
        i = i+2
        line = input_data[i]
        # print(float(line.split('Time spent:  ')[1].strip()))
        stt_array.append(float(line.split('Time spent:  ')[1].strip()))
        
    if '-----requestSummary(' in line:
      if 'cpsAdmin' in line:
        continue
      if 'success' in line:
        # print('---Summary---')
        # print(line.strip())
        i = i+2
        line = input_data[i]
        # print(float(line.split('Time spent:  ')[1].strip()))
        sum_array.append(float(line.split('Time spent:  ')[1].strip()))
  return stt_array, sum_array

stt_delay_1127 = []
sum_delay_1127 = []
stt_delay_1127, sum_delay_1127 = parse_delay(moderator_1127, stt_delay_1127, sum_delay_1127)

stt_delay_1125 = []
sum_delay_1125 = []
stt_delay_1125, sum_delay_1125 = parse_delay(moderator_1125, stt_delay_1125, sum_delay_1125)

stt_delay_1122 = []
sum_delay_1122 = []
stt_delay_1122, sum_delay_1122 = parse_delay(moderator_1122, stt_delay_1122, sum_delay_1122)

stt_delay_1118 = []
sum_delay_1118 = []
stt_delay_1118, sum_delay_1118 = parse_delay(moderator_1118, stt_delay_1118, sum_delay_1118)


stt_delay_len_1127 = len(stt_delay_1127)
print('---STT result 11/27---')
print('stt_delay_len_1127: ', stt_delay_len_1127)
print('mean: ', mean(stt_delay_1127))
print('stdev: ', stdev(stt_delay_1127))
print()

stt_delay_len_1125 = len(stt_delay_1125)
print('---STT result 11/25---')
print('stt_delay_len_1125: ', stt_delay_len_1125)
print('mean: ', mean(stt_delay_1125))
print('stdev: ', stdev(stt_delay_1125))
print()

stt_delay_len_1122 = len(stt_delay_1122)
print('---STT result 11/22---')
print('stt_delay_len_1122: ', stt_delay_len_1122)
print('mean: ', mean(stt_delay_1122))
print('stdev: ', stdev(stt_delay_1122))
print()

stt_delay_len_1118 = len(stt_delay_1118)
print('---STT result 11/18---')
print('stt_delay_len_1118: ', stt_delay_len_1118)
print('mean: ', mean(stt_delay_1118))
print('stdev: ', stdev(stt_delay_1118))
print()


sum_delay_len_1127 = len(sum_delay_1127)
print('---Summary result 11/27---')
print('sum_delay_len_1127: ', sum_delay_len_1127)
print('mean: ', mean(sum_delay_1127))
print('stdev: ', stdev(sum_delay_1127))
print()

sum_delay_len_1125 = len(sum_delay_1125)
print('---Summary result 11/25---')
print('sum_delay_len_1125: ', sum_delay_len_1125)
print('mean: ', mean(sum_delay_1125))
print('stdev: ', stdev(sum_delay_1125))
print()

sum_delay_len_1122 = len(sum_delay_1122)
print('---Summary result 11/22---')
print('sum_delay_len_1122: ', sum_delay_len_1122)
print('mean: ', mean(sum_delay_1122))
print('stdev: ', stdev(sum_delay_1122))
print()

sum_delay_len_1118 = len(sum_delay_1118)
print('---Summary result 11/18---')
print('sum_delay_len_1118: ', sum_delay_len_1118)
print('mean: ', mean(sum_delay_1118))
print('stdev: ', stdev(sum_delay_1118))
print()


print('---STT result overall---')
overall_stt = stt_delay_1118 + stt_delay_1122 + stt_delay_1125 + stt_delay_1127
print('stt_delay_len: ', len(overall_stt))
print('mean: ', mean(overall_stt))
print('stdev: ', stdev(overall_stt))
print()

print('---Summary result overall---')
overall_sum = sum_delay_1118 + sum_delay_1122 + sum_delay_1125 + sum_delay_1127
print('sum_delay_len: ', len(overall_sum))
print('mean: ', mean(overall_sum))
print('stdev: ', stdev(overall_sum))
print()

