import json
import math
import sys
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pororo import Pororo
summ_abstractive = Pororo(task="summarization", model="abstractive", lang="ko")
summ_extractive = Pororo(task="summarization", model="extractive", lang="ko")
summ_bullet = Pororo(task="summarization", model="bullet", lang="ko")

def pororo_abstractive_model(input_txt):
    try :
        summary = summ_abstractive(input_txt)
        if len(summary) > len(input_txt)*0.9:
            print("INVALID proro_ab:::", input_txt)
            return ""
    except:
        return ""
    return summary

def pororo_extractive_model(input_txt):
    try: 
        summary = summ_extractive(input_txt)
    except:
        return ""
    return summary
    
def pororo_bullet_model(input_txt):
  try: 
    summary = summ_bullet(input_txt)
  except:
    return ""
  return summary

##### Data #####
# message1118: `moderator/logs/8904fb9e-19f3-4ba6-882b-96eb3ac9e4de.txt`
with open('message1118.json') as j:
  message1118 = json.load(j)
# message1123: `moderator/logs/8b5723af-fb55-465c-90f0-7c0f2d8a4098.txt`
with open('message1123.json') as j:
  message1123 = json.load(j)
# message1125: `moderator/logs/cd084e3c-33a2-4f8b-b0d7-f04d36d7a2f5.txt`
with open('message1125.json') as j:
  message1125 = json.load(j)
# message1127: `moderator/logs/88d32b28-f4cb-4a83-80cb-fc7b98dd91d5.txt`
with open('message1127.json') as j:
  message1127 = json.load(j)
  
  
# # note1118_1, 2: `media-server/logs/1118_UserTest_8904fb9e-19f3-4ba6-882b-96eb3ac9e4de`
# with open('note1118_1.txt') as t:
#   note1118_1 = t.readlines()
# with open('note1118_2.txt') as t:
#   note1118_2 = t.readlines()
# # note1123_1, 2: `media-server/logs/1123_UserTest_8b5723af-fb55-465c-90f0-7c0f2d8a4098`
# with open('note1123_1.txt') as t:
#   note1123_1 = t.readlines()
# with open('note1123_2.txt') as t:
#   note1123_2 = t.readlines()
# # note1125_1, 2: `media-server/logs/1125_UserTest_cd084e3c-33a2-4f8b-b0d7-f04d36d7a2f5`
# with open('note1125_1.txt') as t:
#   note1125_1 = t.readlines()
# with open('note1125_2.txt') as t:
#   note1125_2 = t.readlines()
# # note1127_1, 2: `media-server/logs/1127_UserTest_88d32b28-f4cb-4a83-80cb-fc7b98dd91d5`
# with open('note1127_1.txt') as t:
#   note1127_1 = t.readlines()
# with open('note1127_2.txt') as t:
#   note1127_2 = t.readlines()
# ### note 2 2등분
# note2_2_1117 = ['반대-4: 셧다운제로 인해 게임 이용 시간이 16~20분이 감소하는 효과를 볼 수 있었으나, 이는 굉장히 미미한 효과라고 볼 수 있음 찬성-1: 게임에 대한 중독장애는 도박, 알코올 등 특정 행동을 반복하는 것에 도움이 된다고 할 수 있음. 게임은 특히 interactive한 놀이문화로 청소년에게 높은 중독성을 보일 수 있음. 반대-3: 게임 규제는 게임 별 규제가 아니라 특정 시간만 규제 하므로 효용성이 떨어짐. 또한 게임규제가 가져오는 사이드-이펙트가 문제가 있음. 셧다운제 때문에 국제대회에서 게임을 망친 대표적인 사례가 있음. 반대-4(이어서): 게임이 국가에서 중요한 위상을 가지게 되면서 게임과 관련된 유명인이 등장하기도 하며 글로벌한 유명인이 생기기도 하였음. 찬성-2: 국가경쟁력과 연결된다는 말은 비약이 있음. 청소년은 특히 중독에 빠지기 쉽고 올바르게 결정하기 어려움. 프로게이머와 같은 직업과는 연결되기 어려움. 반대-4: 프로게이머는 주 활동 연령층이 다른 직업에 비해 굉장히 어림. 셧다운제의 청소년 규제는 이런 커리어에 큰 걸림돌이 됨. 찬성-2: 셧다운제로 규제되는 시간은 굉장히 적음. 오히려 올바른 생활양식을 유도함. 이는 최소한의 규제라고 볼 수 있음. 반대-4: 미국의 예시: 게임중독의 문제는 가정에서 해결할 문제라고 제시하며 게임별로 가이드라인을 만들 것을 권고. 중국 또한 가정의 문제로 인식하고 있음. 찬성-1: 이는 최근에 가정 단위에서의 규제가 쉽게 이루어지기 어렵다고 인식했기 때문에 법적인 규제를 통해 해결하려는 움직임을 보였음. 반대-4: 이는 근거 부족이라고 생각함.', '찬성-2: 게임산업은 굉장히 큰 산업임에 동의하나, 그럼에도 게임중독에 대한 장치가 없다면 이는 모순되는 문제라고 생각함. 반대-4: 사회적 문제가 심할 수 있다는 것에 동의하나, 한국과 같은 방식으로 문제를 해결하고자 하는 나라는 우리나라가 유일함. 반대-3: 청소년 프로게이머는 셧다운제에서 예외적으로 제외한다는 기사를 보았음. 이는 셧다운제의 문제를 정부차원에서 인지하고 있을 뿐 아니라 청소년 프로게이머에게 예외를 두는 것은 그 자체로 문제가 있음을 인정하는 바와 같음. 찬성-1: 이것은 크게 모순되는 것은 아님. 업이 되는 순간 예외를 두고 적용하는 것은 당연한 수순임. 셧다운제 자체가 문제가 아니라, 좀 더 실용적인 법안이 되도록 수정해야 함. 최후변론 -- 찬성-1: 게임은 굉장히 재미있으나 게임을 보다 올바르게 즐길 수 있는 방법을 제시하는 것이 필요함. 반대-3: 게임규제가 실행된지 꽤 오래되었으나 실효성이 있다고 보기 어려움. 완화 또는 적극적인 개선이 필요함.']

# with open('1127_data.json') as j:
#   data1127 = json.load(j)

startclock_1118 = 1637237599261
startclock_1123 = 1637641027777
startclock_1125 = 1637838218898
startclock_1127 = 1637990031445
endclock_1118 = startclock_1118 + 1800000
endclock_1123 = startclock_1123 + 1800000
endclock_1125 = startclock_1125 + 1800000
endclock_1127 = startclock_1127 + 1800000

def preprocessing(msg, start, end):
    original = []
    summary = []
    dict_len = len(msg)
    cnt = -1
    
    for timestamp, log in msg.items():
        cnt += 1
        # print("parsing original transcript and summary: ", cnt, '/' , dict_len)
        timestamp = int(timestamp)
        if timestamp > start and timestamp < end:
            if log['speakerName'] in ['cpsAdmin','이하연']:
                continue

            tempsum = [0, '']
            temptrans = ''
            hasSummary = True
            if len(log["editTrans"]) == 0:
                # print("No editTrans")
                if len(log["naver"]) != 0:
                    temptrans = log["naver"][0]
                else:
                    temptrans = ' '.join(log["ms"])
                
                if len(log["sum"]) == 0:
                    hasSummary = False
                else:
                    tempsum = [0, log["sum"]["summaryArr"][0]]
            else:
                # print("EditTrans")
                edittime = list(log["editTrans"])[-1]
                temptrans = log["editTrans"][edittime]["content"]
                tempsum = [int(edittime), log["editTrans"][edittime]["sum"][0][0]]
            
            if len(log["editSum"]) != 0:
                # print("EditSum")
                edittime = list(log["editSum"])[-1]
                if tempsum[0] < int(edittime):
                    tempsum = [int(edittime), log["editSum"][edittime]["content"]]
            
            if not temptrans:
                continue
            if tempsum[0] != 0 and not tempsum[1]:
                continue

            original.append(temptrans)
            summary.append(tempsum[1])
    return [original, summary]

# result = preprocessing(message1127, startclock_1127, endclock_1127)
# original = result[0]
# summary = result[1]
# len_ori = len(original)
# len_sum = len(summary)

# result = preprocessing(message1118, startclock_1118, endclock_1118)
# original = result[0]
# summary = result[1]
# len_ori = len(original)
# len_sum = len(summary)

# result = preprocessing(message1123, startclock_1123, endclock_1123)
# original = result[0]
# summary = result[1]
# len_ori = len(original)
# len_sum = len(summary)

result = preprocessing(message1125, startclock_1125, endclock_1125)
original = result[0]
summary = result[1]
len_ori = len(original)
len_sum = len(summary)

## 1127 note 1 : 259
### summary 2등분
# len_sum_2 = math.floor(len_sum/2)
# print(len_sum_2)
# summary_2 = [summary[:len_sum_2], summary[len_sum_2:]]
# summary_2 = [' '.join(summ) for summ in summary_2]

### summary 9등분
len_sum_9 = math.floor(len_sum/9)
print(len_sum_9)
summary_9 = [summary[:len_sum_9], summary[len_sum_9:len_sum_9*2], summary[len_sum_9*2:len_sum_9*3], summary[len_sum_9*3:len_sum_9*4], summary[len_sum_9*4:len_sum_9*5], summary[len_sum_9*5:len_sum_9*6], summary[len_sum_9*6:len_sum_9*7], summary[len_sum_9*7:len_sum_9*8], summary[len_sum_9*8:]]
summary_9 = [' '.join(summ) for summ in summary_9]

### summary 8등분
len_sum_8 = math.floor(len_sum/8)
print(len_sum_8)
summary_8 = [summary[:len_sum_8], summary[len_sum_8:len_sum_8*2], summary[len_sum_8*2:len_sum_8*3], summary[len_sum_8*3:len_sum_8*4], summary[len_sum_8*4:len_sum_8*5], summary[len_sum_8*5:len_sum_8*6], summary[len_sum_8*6:len_sum_8*7], summary[len_sum_8*7:]]
summary_8 = [' '.join(summ) for summ in summary_8]

### summary 7등분
len_sum_7 = math.floor(len_sum/7)
print(len_sum_7)
summary_7 = [summary[:len_sum_7], summary[len_sum_7:len_sum_7*2], summary[len_sum_7*2:len_sum_7*3], summary[len_sum_7*3:len_sum_7*4], summary[len_sum_7*4:len_sum_7*5], summary[len_sum_7*5:len_sum_7*6], summary[len_sum_7*6:]]
summary_7 = [' '.join(summ) for summ in summary_7]

### summary 6등분
len_sum_6 = math.floor(len_sum/6)
print(len_sum_6)
summary_6 = [summary[:len_sum_6], summary[len_sum_6:len_sum_6*2], summary[len_sum_6*2:len_sum_6*3], summary[len_sum_6*3:len_sum_6*4], summary[len_sum_6*4:len_sum_6*5], summary[len_sum_6*5:]]
summary_6 = [' '.join(summ) for summ in summary_6]

### summary 5등분
len_sum_5 = math.floor(len_sum/5)
print(len_sum_5)
summary_5 = [summary[:len_sum_5], summary[len_sum_5:len_sum_5*2], summary[len_sum_5*2:len_sum_5*3], summary[len_sum_5*3:len_sum_5*4], summary[len_sum_5*4:]]
summary_5 = [' '.join(summ) for summ in summary_5]

### summary 4등분
len_sum_4 = math.floor(len_sum/4)
print(len_sum_4)
summary_4 = [summary[:len_sum_4], summary[len_sum_4:len_sum_4*2], summary[len_sum_4*2:len_sum_4*3], summary[len_sum_4*3:]]
summary_4 = [' '.join(summ) for summ in summary_4]


def sum_all_pororo(txt):
  models = [pororo_abstractive_model, pororo_extractive_model, pororo_bullet_model]
  sums = []
  for model in models:
    summary = model(txt)
    sums.append(summary)
  return sums

def sum_list(sumlist):
  listlen = len(sumlist)
  ab = []
  ex = []
  bu = []
  for idx, txt in enumerate(sumlist):
    print(idx , '/', listlen)
    sums = sum_all_pororo(txt)
    ab.append(sums[0])
    ex.append(sums[1])
    bu += sums[2]
  print(ab)
  print(ex)
  print(bu)


# print("summary_2 ---")
# sum_list(summary_2)

# print("note2_2 ---")
# sum_list(note2_2)

print("summary_9 ---")
sum_list(summary_9)

# print("summary_8 ---")
# sum_list(summary_8)

# print("summary_7 ---")
# sum_list(summary_7)

# print("summary_6 ---")
# sum_list(summary_6)

# print("summary_5 ---")
# sum_list(summary_5)

# print("summary_4 ---")
# sum_list(summary_4)
    




