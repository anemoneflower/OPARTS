import os
import argparse

######################################################################################
#####################   PARSE LOGS
######################################################################################

################### ARGUMENT
parser = argparse.ArgumentParser()
parser.add_argument("username", type=str)
parser.add_argument("roomname", type=str)
parser.add_argument("--starttime", type=int, default=-1)
args = parser.parse_args()

username = args.username 
roomname = args.roomname 
############################


filename = "./media-server/logs/{}_{}*".format(roomname, username)
filename = "./media-server/logs/"+"pilot/"+"{}-{}*".format(roomname, username) # For Pilot Test

# READ LOGS
with os.popen("ls "+filename+" -t") as stream:
    logfile = stream.read().split()[-1]

print("LOGFILE", logfile)
with open(logfile, "r") as f:
    lines = f.readlines()

# PARSE LINES
starttime = int(lines[0].split(")")[0].replace("(", "")) if args.starttime==-1 else args.starttime
userdata = {}; mintime = None
joinmsgline = 0; joinmsgidx = 4
for idx, line in enumerate(lines):
    
    # PASS WITH JOINED MSG
    if "joined" in line and "User" in line:
        joinmsgline = idx
        joinmsgidx = joinmsgline+4
    if idx <= joinmsgidx and idx >= joinmsgline:
        continue
    
    # PARSE TIME
    time = int(line.split(")")[0].replace("(", "")); mintime = time if mintime==None else mintime; maxtime = time
    time = time - starttime

    # MEETING STARTED
    if time < 0 :
        continue

    # UNTIL 20 MIN AFTER MEETING STARTED
    if time > 20*60*1000:
        break

    params = line.split(")")[-1].strip()
    action = params.split("/")[0]

    if action not in userdata:
        userdata[action]={}
    userdata[action][time] = {arg.split("=")[0]:arg.split("=")[1] for arg in params.split("/")[1:]}
maxtime = maxtime-starttime
print("STARTTIME", starttime, "ENDTIME", starttime+20*60*1000)

# CHECK
'''
for key in userdata:
    print(key, userdata[key])
'''

'''
checklist = ["START-EDIT-MESSAGE", "UPDATE-PARAGRAPH-MESSAGEBOX", "FINISH-EDIT-PARAGRAPH", "CANCLE-EDIT-PARAGRAPH"] 
checklist = ["PIN-BOX", "UNPIN-BOX", "CLICK-PIN" ]
checklist = ['PIN-DROPDOWN-PIN-OPEN', 'PIN-DROPDOWN-CLOSE']
for key in checklist:
    if key in userdata:
        keys = userdata[key].keys()
        print(key, [i+starttime for i in keys])
'''

######################################################################################
#####################   DRAW GRAPH
######################################################################################
import matplotlib.pyplot as plt 
from numpy import inf

def pair_on_off (data):
    ONs = data[0]; OFFs = data[1]

    ONs = sorted(list(ONs.keys()))
    OFFs = sorted(list(OFFs.keys()))

    if len(ONs) == 0 or len(OFFs) == 0:
        return []

    results = []
    if OFFs[0] < ONs[0]:
        results = [(0,OFFs[0])]
        OFFs.pop(0)
    results.extend([(on, off-on) for on, off in zip(ONs, OFFs)])

    return results

def pair_edit_start_finish_or_cancel(start, finish, cancel):
    inputs={ }

    for time in start:
        timestamp = start[time]['TIMESTAMP']
        if timestamp not in inputs:
            inputs[timestamp] = {'START': [], 'FINISH': [], 'CANCEL': [], 'BOTH': []}
        inputs[timestamp]['START'].append(time)

    for time in finish:
        timestamp = finish[time]['TIMESTAMP']
        inputs[timestamp]['FINISH'].append(time)
        inputs[timestamp]['BOTH'].append(time)

    for time in cancel:
        timestamp = cancel[time]['TIMESTAMP']
        inputs[timestamp]['CANCEL'].append(time)
        inputs[timestamp]['BOTH'].append(time)

    finish_results=[]; cancel_results=[]
    for timestamp in inputs:
        while len(inputs[timestamp]['START']) > 0:
            if len(inputs[timestamp]['BOTH']) == 0:
                break

            start = min(inputs[timestamp]['START']); inputs[timestamp]['START'].remove(start)
            end = min(inputs[timestamp]['BOTH']); inputs[timestamp]['BOTH'].remove(end)

            if end in inputs[timestamp]['FINISH']:
                finish_results.append((start, end-start))
            else:
                cancel_results.append((start, end-start))

    return finish_results, cancel_results


def find_edit_msg_pair(start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm, isBoth=False):

    # START-EDIT-MESSAGE
    #{1628682273386: {'TYPE': 'absum', 'TIMESTAMP': '1628135388083'}, 1628682282081: {'TYPE': 'paragraph', 'TIMESTAMP': '1628135388083'}, 1628682295816: {'TYPE': 'paragraph', 'TIMESTAMP': '1628135356660'}, 1628682300271: {'TYPE': 'absum', 'TIMESTAMP': '1628135356660'}, 1628682318485: {'TYPE': 'paragraph', 'TIMESTAMP': '1628135356660'}}    
    # FINISH-EDIT-PARAGRAPH
    #{1628682286000: {'TYPE': 'paragraph', 'MSG': '성진', 'TIMESTAMP': '1628135388083'}, 1628682298695: {'TYPE': 'paragraph', 'MSG': '영현', 'TIMESTAMP': '1628135356660'}, 1628682321507: {'TYPE': 'paragraph', 'MSG': '영현', 'TIMESTAMP': '1628135356660'}}

    start_pgh= {}; start_smm= {}
    for time in start_msgs:
        if start_msgs[time]['TYPE'] == "paragraph":
            start_pgh[time] = start_msgs[time]
        else:
            start_smm[time] = start_msgs[time]

    finish_pgh_data, cancel_pgh_data = pair_edit_start_finish_or_cancel(start_pgh, finish_pgh, cancel_pgh)
    finish_smm_data, cancel_smm_data = pair_edit_start_finish_or_cancel(start_smm, finish_smm, cancel_smm)

    if isBoth:
        return finish_pgh_data+cancel_pgh_data, finish_smm_data+cancel_smm_data 

    return finish_pgh_data, cancel_pgh_data, finish_smm_data, cancel_smm_data 

###########

all_actions = ["WINDOW-FOCUS-OFF", "WINDOW-FOCUS-ON", "VIDEO-ON", "VIDEO-OFF", "AUDIO-ON", "AUDIO-OFF",
    #"CLICK-INVITE-BUTTON", 
    "CLICK-SEARCH-BUTTON", "CLICK-SHOW-ALL-BUTTON", "CLICK-SCROLL-DOWN-BUTTON",  
    " ",
    "OPEN-MAP", "OPEN-SUBTASK", #"SUBTASK-ANSWER", "SAVE-TEMP-ANSWERS", 
    " ",
    "SCROLL-UP", "SCROLL-DOWN", "SUMMARY-FOR-KEYWORD", 
    " ",
    "UPDATE-PARAGRAPH-MESSAGEBOX", "FINISH-EDIT-PARAGRAPH", "CANCLE-EDIT-PARAGRAPH", 
    "UPDATE-SUMMARY-MESSAGEBOX", "FINISH-EDIT-SUMMARY", "CANCLE-EDIT-SUMMARY", 
    "ADD-KEYWORD", "DELETE-KEYWORD", "SEARCH-WORD",  
    " ",
    "ADD-FAVORITE", "DELETE-FAVORITE", "SEARCH-FAVORITE",
    " ", 
    "PIN-BOX",  "UNPIN-BOX", "CLICK-PIN", 
    " ",
    "CLICK-HIDE-FULL-TEXT", "CLICK-SEE-FULL-TEXT",  
    'PIN-DROPDOWN-PIN-OPEN', 'PIN-DROPDOWN-CLOSE',
    "START-EDIT-MESSAGE"]

actions = [ "START-EDIT-MESSAGE",
    "UPDATE-PARAGRAPH-MESSAGEBOX", "FINISH-EDIT-PARAGRAPH", "CANCLE-EDIT-PARAGRAPH",
    "UPDATE-SUMMARY-MESSAGEBOX", "FINISH-EDIT-SUMMARY", "CANCLE-EDIT-SUMMARY",
    "WINDOW-FOCUS-OFF", "WINDOW-FOCUS-ON", "VIDEO-ON", "VIDEO-OFF", "AUDIO-ON", "AUDIO-OFF",
    'PIN-DROPDOWN-PIN-OPEN', 'PIN-DROPDOWN-CLOSE',
    ]
last_actions = list(filter(lambda x: x not in actions, all_actions)) # Actions not in actions

fig, ax = plt.subplots(figsize=(12,10))
ax.grid(True, color='#DDDDDD')
ax.set_axisbelow(True)

xbar = 500
ybar = 1

for idx, action in enumerate(last_actions):

    # EMPTY LINE
    if action not in userdata:
        if action == " ":   
            ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF')
        continue
    
    
    times = userdata[action].keys()
    actiontime = [(time, xbar) for time in times]

    ax.broken_barh(actiontime, (2*idx, ybar), zorder = 10)

# EDIT MESSAGES (PARAGRAPH OR SUMMARY)
start_msgs, finish_pgh, cancel_pgh, finish_smm, cancel_smm = [userdata[x] if x in userdata else {} for x in ["START-EDIT-MESSAGE",  "FINISH-EDIT-PARAGRAPH", "CANCEL-EDIT-PARAGRAPH", "FINISH-EDIT-SUMMARY", "CANCEL-EDIT-SUMMARY"] ]

isBoth = True
if isBoth:
    edit_pgh_data, edit_smm_data = find_edit_msg_pair(start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm, isBoth)
    
    idx+=1; ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF') ## EMPTY BAR
    idx+=1; ax.broken_barh(edit_pgh_data, (2*idx, ybar), zorder = 10)
    idx+=1; ax.broken_barh(edit_smm_data, (2*idx, ybar), zorder = 10)
    edit_labels = ['EDIT-PARAGRAPH', 'EDIT-SUMMARY']    

else:
    finish_pgh_data, cancel_pgh_data, finish_smm_data, cancel_smm_data  = find_edit_msg_pair(start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm)

    idx+=1; ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF') ## EMPTY BAR
    idx+=1; ax.broken_barh(finish_pgh_data, (2*idx, ybar), zorder = 10)
    idx+=1; ax.broken_barh(cancel_pgh_data, (2*idx, ybar), zorder = 10)
    idx+=1; ax.broken_barh(finish_smm_data, (2*idx, ybar), zorder = 10)
    idx+=1; ax.broken_barh(cancel_smm_data, (2*idx, ybar), zorder = 10)
    edit_labels = ['EDIT-PARAGRAPH', 'CANCEL-PGH', 'EDIT-SUMMARY', 'CANCEL-SMM']    


# ON/OFF - AUDIO/VIDEO/FOCUS
audio = pair_on_off([userdata[x] if x in userdata else {} for x in ['AUDIO-ON', 'AUDIO-OFF']])
video = pair_on_off([userdata[x] if x in userdata else {} for x in ['VIDEO-ON', 'VIDEO-OFF']])
focus = pair_on_off([userdata[x] if x in userdata else {} for x in ['WINDOW-FOCUS-ON', 'WINDOW-FOCUS-OFF']])
pins = pair_on_off([userdata[x] if x in userdata else {} for x in ['PIN-DROPDOWN-PIN-OPEN', 'PIN-DROPDOWN-CLOSE']])

idx+=1; ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF') ## EMPTY BAR
idx+=1; ax.broken_barh(audio, (2*idx, ybar))
idx+=1; ax.broken_barh(video, (2*idx, ybar))
idx+=1; ax.broken_barh(focus, (2*idx, ybar))
idx+=1; ax.broken_barh(pins, (2*idx, ybar))

# TOTAL COLORED GRID  -> FOCUS OFF
no_focus = []
if len(focus) > 1:
    end_focus = focus[0][0] + focus[0][1]
    for time in focus[1:]:
        no_focus.append((end_focus, time[0]-end_focus))
        end_focus = time[0]+ time[1]
    if time[0]:
        no_focus.append((time[0], 20*60*1000 - time[0]))
print(no_focus)
ax.broken_barh(no_focus, (0, 2*(idx+2)), zorder = -1, color='#ffe8ed')
ax.broken_barh(focus, (0, 2*(idx+2)), zorder = -1, color='#e6f7ff')

#Edit_labels = ['EDIT-PARAGRAPH', 'CANCEL-PGH', 'EDIT-SUMMARY', 'CANCEL-SMM']
labels =[name.split("CLICK-")[-1] for name in last_actions+[" ",] +edit_labels+ [ " ", 'AUDIO-ON', 'VIDEO-ON', 'FOCUS-ON', 'PIN-DROPDOWN']]
yticks = [2*i+0.5 for i in range(idx+1)]

ax.set_yticks(yticks)
ax.set_yticklabels(labels)


ax.set_ylim(-1, 2*(idx+1))
ax.set_xlim(0, (int(maxtime/60/1000)+0.5)*60*1000 )
ax.set_xticks([i*60*1000 for i in range(int(maxtime/60/1000)+1)])
ax.set_xticklabels([str(i) for i in range(int(maxtime/60/1000)+1)])

plt.title("USER[{}]-{}".format(username, roomname))
plt.tight_layout()

pngfilename = "./user-log-analysis-{}-{}.png".format(username, roomname) 
plt.savefig(pngfilename)
print(pngfilename)