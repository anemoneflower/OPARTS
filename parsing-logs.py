# Parsing log data from the meeting logs.
# @input argument: roomname

import os
import argparse
import glob
import matplotlib.pyplot as plt
from numpy import inf

from numbers import Number
import statistics
import datetime

import csv


def toggle_pair(data):
    # print("Toggle Pair")
    # print(data)
    if not data:
        return [[], []]
    time = sorted(list(data.keys()))
    result = [[], []]
    prevt = 0
    prevk = data[0]
    index = 0 if prevk == "SUMMARY" else 1
    for t in time:
        key = data[t]
        if key == prevk:
            continue
        result[index].append((prevt, t-prevt))
        prevt = t
        prevk = key
        index = 0 if index == 1 else 1
    result[index].append((prevt, TIMELIMIT-prevt))
    return result


def on_off_focus(data):
    onkey = 'WINDOW-FOCUS-ON'
    offkey = 'WINDOW-FOCUS-OFF'

    if not data:
        return []
    time = sorted(list(data.keys()))
    if data[time[0]] == offkey:
        print("**ERROR::::", time[0], offkey)
    if data[time[-1]] == onkey:
        data[TIMELIMIT] = offkey
        time.append(TIMELIMIT)

    prevt = -1
    prevk = offkey

    results = [[], []]
    for t in time:
        key = data[t]
        if key == prevk:
            continue
        elif key == onkey:
            if prevt > 0:
                results[1].append((prevt, t))
            prevt = t
            prevk = onkey
        else:
            results[0].append((prevt, t))
            prevt = t
            prevk = offkey
    return results


def on_off_pair(data, onkey, offkey):
    # print("on_off_pair", onkey, offkey)
    # print(data)
    if not data:
        return []
    time = sorted(list(data.keys()))
    if data[time[0]] == offkey:
        print("**ERROR::::", time[0], offkey)
    if data[time[-1]] == onkey:
        data[TIMELIMIT] = offkey
        time.append(TIMELIMIT)

    prevt = -1
    prevk = offkey

    results = []
    for t in time:
        key = data[t]
        if key == prevk:
            continue
        if key == onkey:
            prevt = t
            prevk = onkey
        else:
            results.append((prevt, t-prevt))
            prevk = offkey
    return results


def speech_pair_on_off(data):
    ONs = {**data[0], **data[1]}
    OFFs = {**data[2], **data[3]}

    onKeys = sorted(list(ONs.keys()))
    offKeys = sorted(list(OFFs.keys()))

    if not onKeys and not offKeys:
        return []

    for on in onKeys:
        ONs[on] = True
    if(onKeys[0] < 0):
        ONs[0] = True

    for off in offKeys:
        OFFs[off] = False
    if(onKeys[-1] > offKeys[-1]):
        OFFs[TIMELIMIT] = False

    onoff = {**ONs, **OFFs}
    # print("onoff", onoff)
    # print(len(onoff))

    allkeys = sorted(list(onoff.keys()))
    # print(allkeys, len(allkeys))

    if len(ONs) == 0 or len(OFFs) == 0:
        return []

    results = []

    pre = allkeys[0]
    for idx, key in enumerate(allkeys):
        # print(key, idx, onoff[key])
        if onoff[key] == onoff[pre]:
            # print("---", key, idx, onoff[key])
            continue
        if onoff[pre]:
            results.extend([(pre, key-pre)])
        pre = key
    return results


def pair_edit_start_finish_or_cancel(start, finish, cancel):
    inputs = {}

    for time in start:
        timestamp = start[time]['TIMESTAMP']
        if timestamp not in inputs:
            inputs[timestamp] = {'START': [],
                                 'FINISH': [], 'CANCEL': [], 'BOTH': []}
        inputs[timestamp]['START'].append(time)

    for time in finish:
        timestamp = finish[time]['TIMESTAMP']
        inputs[timestamp]['FINISH'].append(time)
        inputs[timestamp]['BOTH'].append(time)

    for time in cancel:
        timestamp = cancel[time]['TIMESTAMP']
        inputs[timestamp]['CANCEL'].append(time)
        inputs[timestamp]['BOTH'].append(time)

    finish_results = []
    cancel_results = []
    for timestamp in inputs:
        while len(inputs[timestamp]['START']) > 0:
            if len(inputs[timestamp]['BOTH']) == 0:
                break

            start = min(inputs[timestamp]['START'])
            inputs[timestamp]['START'].remove(start)
            end = min(inputs[timestamp]['BOTH'])
            inputs[timestamp]['BOTH'].remove(end)

            if end in inputs[timestamp]['FINISH']:
                finish_results.append((start, end-start))
            else:
                cancel_results.append((start, end-start))
    return finish_results, cancel_results


def find_edit_msg_pair(start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm, isBoth=False):
    start_pgh = {}
    start_smm = {}
    for time in start_msgs:
        if start_msgs[time]['TYPE'] == "paragraph":
            start_pgh[time] = start_msgs[time]
        else:
            start_smm[time] = start_msgs[time]

    finish_pgh_data, cancel_pgh_data = pair_edit_start_finish_or_cancel(
        start_pgh, finish_pgh, cancel_pgh)
    finish_smm_data, cancel_smm_data = pair_edit_start_finish_or_cancel(
        start_smm, finish_smm, cancel_smm)

    if isBoth:
        return finish_pgh_data+cancel_pgh_data, finish_smm_data+cancel_smm_data

    return finish_pgh_data, cancel_pgh_data, finish_smm_data, cancel_smm_data


#############################################################################################################
### PARSE ARGUMENTS ###
parser = argparse.ArgumentParser()
parser.add_argument("roomname", type=str)
parser.add_argument("-t", type=float, default=30)
args = parser.parse_args()

# Get roomname from agrument
roomname = args.roomname
TIMELIMIT = int(args.t*60*1000)
print("MEETING DURATION: {}min - TIMELIMIT is {}".format(args.t, TIMELIMIT))

# Parse Roomname
multitask = roomname.split('_')[1] == "M"
system = roomname.split('_')[2] == "S"

logfiles = glob.glob("./media-server/logs/"+roomname+"_*")

print("AVAILABLE LOGS FOR ROOM <{}>:".format(roomname), logfiles)
index = int(input("Enter index: "))

# Parse roomid
roomid = logfiles[index].split("/")[3].split("_")[-1]
print("ROOM ID:", roomid)

logfiles = glob.glob("./media-server/logs/"+roomname+"_"+roomid+"/*")
print("LOG FILE LIST:", logfiles)

# Generate Log Directory
path = "./analysis/{}_{}".format(roomname, roomid)
# path가 파일이면?
try:
    if not os.path.exists(path):
        os.makedirs(path)
except OSError:
    print('Error: Creating directory '+path)

### Calculate Delay ###
#####
delays = {}
# Keyword
with open("./moderator/delays/{}_{}/KeyExt.txt".format(roomname, roomid), 'r') as f:
    delay_k = f.readlines()
delay_k = [float(d.split(":")[-1].split("}")[0]) for d in delay_k]
delays['keyword'] = statistics.mean(delay_k)

# Silence
with open("./moderator/delays/{}_{}/Silence.txt".format(roomname, roomid), 'r') as f:
    delay_sil = f.readlines()
delay_sil = [float(d.split(":")[-1].split("}")[0]) for d in delay_sil]
delays['silence'] = statistics.mean(delay_sil)

# Summary
with open("./moderator/delays/{}_{}/Sum.txt".format(roomname, roomid), 'r') as f:
    delay_sum = f.readlines()
delay_sum = [float(d.split(":")[-1].split("}")[0]) for d in delay_sum]
delays['summary'] = statistics.mean(delay_sum)

# Speech End Detect
endDetect = []

# Focus out
focusout = {}

### Get starttime ###
try:
    with open("./moderator/logs/{}_{}/STARTCLOCK.txt".format(roomname, roomid), 'r') as f:
        starttime = int(f.readline())
except:
    starttime = -1

### ITERATE FOR EACH USERS ###
for filename in logfiles:
    # Check if this is user's log file
    # os.path.walk | rsplit // split 여러 번
    if filename.split("/")[-1] == roomname+".txt":
        continue
    if "subtask" in filename.split("/")[-1].split("_"):
        continue

    print("********************************")
    # Parse username
    username = filename.split("/")[-1][:-4]
    print("USERNAME:", username)

    if username == "cpsAdmin":
        continue
    if "Junyoung" in username or "junyoung" in username:
        continue

    # Parse usernumber: PO - Trans mode
    if len(username.split("-")) > 1 and int(username.split("-")[-1]) % 2 == 0:
        defaultmode = "SUMMARY"
    else:
        defaultmode = "TRANSCRIPT"

    speechfilename = "./moderator/logs/{}_{}/{}.txt".format(
        roomname, roomid, username)
    # print("speechfilename:", speechfilename)

    # Read logs
    with open(filename, "r") as f:
        lines = f.readlines()
    try:
        with open(speechfilename, "r") as f:
            sttlines = f.readlines()
    except:
        print("No speech from this user!!")
        sttlines = []

    # Parse starttime
    starttime = int(lines[0].split(")")[0].replace(
        "(", "")) if starttime == -1 else starttime
    # print("starttime:", starttime)

    userdata = {"SCROLL-UP": {}, "SCROLL-DOWN": {}, "CLICK-SCROLL-DOWN-BUTTON": {}, "SEARCH-TRENDINGWORDS": {}, "SUMMARY-FOR-KEYWORD": {}, "CLICK-HIDE-SUMMARY": {}, "CLICK-SEE-SUMMARY": {}, "CLICK-HIDE-FULL-TEXT": {},
                "CLICK-SEE-FULL-TEXT": {}, "START-EDIT-MESSAGE": {}, "UPDATE-PARAGRAPH-MESSAGEBOX": {}, "FINISH-EDIT-PARAGRAPH": {}, "CANCEL-EDIT-PARAGRAPH": {}, "UPDATE-SUMMARY-MESSAGEBOX": {}, "FINISH-EDIT-SUMMARY": {}, "CANCEL-EDIT-SUMMARY": {}, 'SPEECH-START': {}, 'SPEECH-START-M': {}, 'SPEECH-END': {}, 'SPEECH-END-M': {}}  # TODO: remove speech later
    pairdata = {"window": {}, "video": {}, "audio": {},
                "subtask": {}, "mode": {}, "speech": {}}
    pairactions = ["WINDOW-FOCUS-OFF", "WINDOW-FOCUS-ON", "VIDEO-ON", "VIDEO-OFF",
                   "AUDIO-ON", "AUDIO-OFF", "OPEN-SUBTASK", "CLOSE-SUBTASK", "TOGGLE-MODE"]

    mintime = None
    maxtime = 0

    joinmsgline = 0
    joinmsgidx = 4

    videocond = False
    audiocond = False
    focuscond = True
    modecond = defaultmode
    for idx, line in enumerate(lines):
        # PASS WITH JOINED MSG
        if "joined" in line and "User" in line:
            joinmsgline = idx
            joinmsgidx = joinmsgline+4

            time = int(line.split(")")[0].replace("(", ""))
            mintime = time if mintime == None else mintime
            time = time - starttime

            if time < 0:
                focuscond = True
            else:
                pairdata[time] = "WINDOW-FOCUS-ON"
        if idx <= joinmsgidx and idx >= joinmsgline:
            continue

        # PARSE ACTION
        params = line.split(")")[-1].strip()
        action = params.split("/")[0]

        # PARSE TIME
        time = int(line.split(")")[0].replace("(", ""))
        mintime = time if mintime == None else mintime
        time = time - starttime

        # MEETING STARTED
        if time < 0:
            # check window
            if action in ["WINDOW-FOCUS-OFF", "Exit"]:
                focuscond = False
            elif action == "WINDOW-FOCUS-ON":
                focuscond = True

            # check video
            elif action == "VIDEO-ON":
                videocond = True
            elif action in ["VIDEO-OFF", "Exit"]:
                videocond = False

            # check audio
            elif action == "AUDIO-ON":
                audiocond = True
            elif action in ["AUDIO-OFF", "Exit"]:
                audiocond = False

            # check mode
            elif action == "TOGGLE-MODE":
                modecond = params.split("/")[1].split("=")[1]

            continue

        # UNTIL 30 MIN AFTER MEETING STARTED
        if time > TIMELIMIT:
            continue

        if maxtime < time + starttime:
            maxtime = time + starttime

        if action in ["SPEECH-RECOGNIZED", "CURRENT-MSG-BOXES", "CREATE-MSGBOX"] or "GET-POSITION-OF-MOUSE" in action:
            continue

        if action in pairactions:
            parseaction = action.split("-")
            if parseaction[0] == "WINDOW":
                pairdata["window"][time] = action
            elif parseaction[0] == "VIDEO":
                pairdata["video"][time] = action
            elif parseaction[0] == "AUDIO":
                pairdata["audio"][time] = action
            elif parseaction[1] == "SUBTASK":
                pairdata["subtask"][time] = action
            else:
                pairdata["mode"][time] = params.split("/")[1].split("=")[1]
        elif '/' in params:
            try:
                userdata[action][time] = {arg.split("=")[0]: arg.split(
                    "=")[1] for arg in params.split("/")[1:]}
            except:
                # case SEARCH-TRENDINGWORDS/RETURN
                userdata[action][time] = {}
        elif action == "Exit":
            pairdata["audio"][time] = "AUDIO-OFF"
            pairdata["video"][time] = "VIDEO-OFF"
            pairdata["window"][time] = "WINDOW-FOCUS-OFF"
            pairdata["window"][time] = defaultmode
        else:
            try:
                userdata[action][time] = {}
            except:
                print("Action Key error::", action, params)

    if videocond:
        pairdata["video"][0] = "VIDEO-ON"
    if audiocond:
        pairdata["audio"][0] = "AUDIO-ON"
    if focuscond:
        pairdata["window"][0] = "WINDOW-FOCUS-ON"
    if system:
        pairdata["mode"][0] = modecond

    for idx, line in enumerate(sttlines):
        # PARSE TIME
        time = int(line.split(")")[0].replace("(", ""))
        mintime = time if mintime == None else mintime
        time = time - starttime

        if line.split(') ')[1] == "SPEECH-END\n" or line.split(') ')[1] == "SPEECH-END-M\n":
            lastgen = datetime.datetime.fromtimestamp(
                float(line.split(') ')[0][1:-1])/100)
            endsig = datetime.datetime.fromtimestamp(
                float(sttlines[idx-1].split(') ')[0][1:-1])/100)
            # print(lastgen, endsig)
            endDetect.append((lastgen - endsig).total_seconds())

        # MEETING STARTED
        if time < 0:
            continue

        # UNTIL 20 MIN AFTER MEETING STARTED
        if time > TIMELIMIT:
            continue

        if maxtime < time + starttime:
            maxtime = time + starttime

        params = line.split(")")[-1].strip()
        action = params.split("/")[0]
        # pairdata["speech"][time] = action

        if action not in userdata:
            userdata[action] = {}
        userdata[action][time] = {arg.split("=")[0]: arg.split(
            "=")[1] for arg in params.split("/")[1:]}
    # print("---USERDATA---\n", userdata)
    maxtime = maxtime-starttime
    print("STARTTIME", starttime, "ENDTIME", starttime+TIMELIMIT)

    ############### LOG DATAS FOR PLOT ###############
    xbar = 500
    ybar = 1
    ### EDIT MESSAGES (PARAGRAPH OR SUMMARY) ###
    start_msgs, finish_pgh, cancel_pgh, finish_smm, cancel_smm = [userdata[x] if x in userdata else {} for x in [
        "START-EDIT-MESSAGE",  "FINISH-EDIT-PARAGRAPH", "CANCEL-EDIT-PARAGRAPH", "FINISH-EDIT-SUMMARY", "CANCEL-EDIT-SUMMARY"]]
    finish_pgh_data, cancel_pgh_data, finish_smm_data, cancel_smm_data = find_edit_msg_pair(
        start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm)

    ### TOGGLE ###
    toggles = toggle_pair(pairdata["mode"])

    ### HIDE/SHOW & SCROLL & SEARCH TRENDINGWORDS ###
    hideshow = ["CLICK-HIDE-SUMMARY", "CLICK-SEE-SUMMARY",
                "CLICK-HIDE-FULL-TEXT", "CLICK-SEE-FULL-TEXT"]
    scroll = ["SCROLL-UP", "SCROLL-DOWN", "CLICK-SCROLL-DOWN-BUTTON"]
    trending = ["SEARCH-TRENDINGWORDS", "SUMMARY-FOR-KEYWORD"]
    datadict = {}
    for action in hideshow + scroll + trending:
        if action not in userdata:
            times = []
        else:
            times = userdata[action].keys()
        actiontime = [(time, xbar) for time in times]
        datadict[action] = actiontime

    ### SUBTASK ###
    subtask = on_off_pair(pairdata["subtask"], "OPEN-SUBTASK", "CLOSE-SUBTASK")

    ### ON/OFF - AUDIO/VIDEO/FOCUS ###
    audio = on_off_pair(pairdata["audio"], 'AUDIO-ON', 'AUDIO-OFF')
    video = on_off_pair(pairdata["video"], 'VIDEO-ON', 'VIDEO-OFF')
    focus = on_off_pair(pairdata["window"],
                        'WINDOW-FOCUS-ON', 'WINDOW-FOCUS-OFF')
    ##
    focusout[username] = on_off_focus(pairdata["window"])

    ### SPEECH START/END LOG ###
    speechs = speech_pair_on_off([userdata[x] if x in userdata else {} for x in [
                                 'SPEECH-START', 'SPEECH-START-M', 'SPEECH-END', 'SPEECH-END-M']])
    

    print("window")
    print(focus)
    print("video")
    print(video)
    print("audio")
    print(audio)
    print("subtask")
    print(subtask)
    print("mode")
    print(toggles)
    print("speech")
    print(speechs)
    
    ############### GENERATE OVERALL PLOT ###############
    if system:
        fig, ax = plt.subplots(figsize=(15, 10))
    else:
        fig, ax = plt.subplots(figsize=(12, 3))
    ax.grid(True, color='#DDDDDD')
    ax.set_axisbelow(True)

    idx = 0

    labels = []

    if system:
        # EDIT MESSAGES (PARAGRAPH OR SUMMARY)
        ax.broken_barh(finish_pgh_data, (2*idx, ybar), zorder=10)
        idx += 1
        ax.broken_barh(cancel_pgh_data, (2*idx, ybar), zorder=10)
        idx += 1
        ax.broken_barh(finish_smm_data, (2*idx, ybar), zorder=10)
        idx += 1
        ax.broken_barh(cancel_smm_data, (2*idx, ybar), zorder=10)
        idx += 1
        labels.extend(['EDIT-PARAGRAPH', 'CANCEL-PGH',
                      'EDIT-SUMMARY', 'CANCEL-SMM'])

        # TOGGLE MODE INDEX
        ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF')
        idx += 1  # EMPTY BAR
        toggles.append(idx)  # save mode index
        labels.extend([" "])  # , 'MODE(G-SUM/B-TRANS)'])

        # HIDE/SHOW
        for action in hideshow:
            actiontime = datadict[action]
            if action[-1] == "T":
                ax.broken_barh(actiontime, (2*idx, ybar),
                               zorder=10, color='#462875')
                idx += 1
            else:
                ax.broken_barh(actiontime, (2*idx, ybar),
                               zorder=10, color='#146627')
                idx += 1
        labels.extend([name.split("CLICK-")[-1] for name in hideshow])

        # DRAW TOGGLE
        ystart, yend = 2*toggles[-1], 2*(idx-toggles[-1])-1
        ax.broken_barh(toggles[0], (ystart, yend),
                       zorder=1, color='#658a6d')  # Summary
        ax.broken_barh(toggles[1], (ystart, yend),
                       zorder=1, color='#8c97ba')  # Trans

        # SCOLL
        ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF')
        idx += 1  # EMPTY BAR
        toggles.append(idx)
        for action in scroll:
            actiontime = datadict[action]
            ax.broken_barh(actiontime, (2*idx, ybar),
                           zorder=10, color='#262670')
            idx += 1
        labels.extend([" "] + scroll)

        # DRAW TOGGLE
        ystart, yend = 2*toggles[-1], 2*(idx-toggles[-1])-1
        ax.broken_barh(toggles[0], (ystart, yend),
                       zorder=1, color='#658a6d')  # Summary
        ax.broken_barh(toggles[1], (ystart, yend),
                       zorder=1, color='#8c97ba')  # Trans

        # SEARCH TRENDINGWORDS
        ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF')
        idx += 1  # EMPTY BAR
        toggles.append(idx)
        for action in trending:
            actiontime = datadict[action]
            ax.broken_barh(actiontime, (2*idx, ybar),
                           zorder=10, color='#262670')
            idx += 1
        labels.extend([" "] + trending)

        # DRAW TOGGLE
        ystart, yend = 2*toggles[-1], 2*(idx-toggles[-1])-1
        ax.broken_barh(toggles[0], (ystart, yend),
                       zorder=1, color='#658a6d')  # 7fb58c')  # Summary
        ax.broken_barh(toggles[1], (ystart, yend),
                       zorder=1, color='#8c97ba')  # Trans
        ax.broken_barh([(0, maxtime)], (2*idx, ybar), color='#FFFFFF')
        idx += 1  # EMPTY BAR
        labels.extend([" "])

    if multitask:
        # SUBTASK
        ax.broken_barh(subtask, (2*idx, ybar), zorder=10)
        idx += 1
        labels.extend(['SUBTASK'])

    # SPEECH && AUDIO && VIDEO
    ax.broken_barh(speechs, (2*idx, ybar), zorder=10)
    ax.broken_barh(audio, (2*idx, ybar), color='#b8d7f2')
    idx += 1
    ax.broken_barh(video, (2*idx, ybar))
    idx += 1
    labels.extend(['SPEECH(AUDIO-ON)', 'VIDEO-ON'])

    # TOTAL COLORED GRID  -> FOCUS OFF
    no_focus = []
    if focus[0][0] != 0:
        no_focus = [(0, focus[0][0])]
    if len(focus) > 1:
        end_focus = focus[0][0] + focus[0][1]
        for time in focus[1:]:
            no_focus.append((end_focus, time[0]-end_focus))
            end_focus = time[0] + time[1]
        if time[0]:
            no_focus.append((time[0], TIMELIMIT - time[0]))
    # print("no_focus", no_focus)
    ax.broken_barh(no_focus, (0, 2*(idx+2)), zorder=-2, color='#ffe8ed')
    ax.broken_barh(focus, (0, 2*(idx+2)), zorder=-2, color='#e6f7ff')

    yticks = [2*i+0.5 for i in range(idx)]

    ax.set_yticks(yticks)
    ax.set_yticklabels(labels)

    ax.set_ylim(-1, 2*(idx))
    ax.set_xlim(0, (int(maxtime/60/1000)+0.5)*60*1000)
    ax.set_xticks([i*60*1000 for i in range(int(maxtime/60/1000)+1)])
    ax.set_xticklabels([str(i) for i in range(int(maxtime/60/1000)+1)])

    plt.suptitle("[{}] OVERALL - {}".format(roomname, username),
                 fontsize=16, fontweight="bold")
    if system:
        plt.title(
            "FOCUS(ON-blue/OFF-red) || MODE(SUMMARY-green/TRANSCRIPT-violet)", fontweight="bold")
    else:
        plt.title(
            "FOCUS(ON-blue/OFF-red)", fontweight="bold")

    plt.tight_layout()

    pngfilename = path+"/overall-{}-{}.png".format(username, roomname)
    # plt.savefig(pngfilename)
    # print("GENERATED FILE: "+pngfilename)

    ############### GENERATE SUBTASK PLOT ###############
    # TODO


# # SAVE DELAY
# delays['transcript'] = statistics.mean(endDetect)
# with open(path+"/delay_logs.txt", 'w') as f:
#     for (case, value) in delays.items():
#         f.write("{}: {}\n".format(case, value))

# print(focusout)
# for (username, values) in focusout.items():
#     with open(path+"/focusout_"+username+".csv", 'w', newline='') as f:
#         writer = csv.writer(f)
#         writer.writerow(['Focus ON']+values[0])
#         writer.writerow(['Focus OFF']+values[1])
################################# ACTIONS #################################
# all_actions = ["WINDOW-FOCUS-OFF", "WINDOW-FOCUS-ON", "VIDEO-ON", "VIDEO-OFF", "AUDIO-ON", "AUDIO-OFF",
#     "SPEECH-START", "SPEECH-END",
#     "SPEECH-START-M", "SPEECH-END-M",
#     #"CLICK-INVITE-BUTTON",
#     # "CLICK-SEARCH-BUTTON", "CLICK-SHOW-ALL-BUTTON",
#     "CLICK-SCROLL-DOWN-BUTTON",
#     " ",
#     "OPEN-SUBTASK", "CLOSE-SUBTASK", #"SUBTASK-ANSWER", "SAVE-TEMP-ANSWERS",
#     " ",
#     "SCROLL-UP", "SCROLL-DOWN", "SUMMARY-FOR-KEYWORD",
#     " ",
#     "UPDATE-PARAGRAPH-MESSAGEBOX", "FINISH-EDIT-PARAGRAPH", "CANCEL-EDIT-PARAGRAPH",
#     "UPDATE-SUMMARY-MESSAGEBOX", "FINISH-EDIT-SUMMARY", "CANCEL-EDIT-SUMMARY",
#     "SEARCH-TRENDINGWORDS",
#     "TOGGLE-MODE",
#     # "ADD-KEYWORD", "DELETE-KEYWORD", "SEARCH-WORD",
#     # "ADD-FAVORITE", "DELETE-FAVORITE", "SEARCH-FAVORITE",
#     # "PIN-BOX",  "UNPIN-BOX", "CLICK-PIN",
#     "CURRENT-MSG-BOXES",
#     "CLICK-HIDE-SUMMARY", "CLICK-SEE-SUMMARY",
#     "CLICK-HIDE-FULL-TEXT", "CLICK-SEE-FULL-TEXT",
#     # 'PIN-DROPDOWN-PIN-OPEN', 'PIN-DROPDOWN-CLOSE',
#     "START-EDIT-MESSAGE"]

# actions = [ "START-EDIT-MESSAGE",
#     "UPDATE-PARAGRAPH-MESSAGEBOX", "FINISH-EDIT-PARAGRAPH", "CANCEL-EDIT-PARAGRAPH",
#     "UPDATE-SUMMARY-MESSAGEBOX", "FINISH-EDIT-SUMMARY", "CANCEL-EDIT-SUMMARY",
#     "WINDOW-FOCUS-OFF", "WINDOW-FOCUS-ON", "VIDEO-ON", "VIDEO-OFF", "AUDIO-ON", "AUDIO-OFF",
#     "SPEECH-START", "SPEECH-END", "SPEECH-START-M", "SPEECH-END-M",
#     "TOGGLE-MODE",
#     "CLICK-HIDE-SUMMARY", "CLICK-SEE-SUMMARY",
#     "CLICK-HIDE-FULL-TEXT", "CLICK-SEE-FULL-TEXT",
#     # "CLICK-SCROLL-DOWN-BUTTON",  "SCROLL-UP", "SCROLL-DOWN",
#     ]
