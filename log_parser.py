import os
import glob
import matplotlib.pyplot as plt
from numpy import inf

from numbers import Number
import statistics
import datetime

import csv
import pandas as pd
from IPython.display import display


class UserData:
    pairactions = ["WINDOW-FOCUS-OFF", "WINDOW-FOCUS-ON", "VIDEO-ON", "VIDEO-OFF",
                   "AUDIO-ON", "AUDIO-OFF", "OPEN-SUBTASK", "CLOSE-SUBTASK", "TOGGLE-MODE"]

    def __init__(self, roomname, roomid, username, filename, timelimit=1800000, starttime=-1):
        self.roomname = roomname
        self.roomid = roomid
        self.username = username
        self.filename = filename
        # TODO: fix filename
        self.speechfilename = "./moderator/logs/{}_{}/{}.txt".format(
            self.roomname, self.roomid, username)
        self.TIMELIMIT = timelimit
        self.STARTTIME = starttime
        self.mintime = None
        self.maxtime = 0

        # Parse usernumber: PO - Trans mode, PE - Summary mode
        self.defaultMode = "SUMMARY" if len(username.split(
            "-")) > 1 and int(username.split("-")[-1]) % 2 == 0 else "TRANSCRIPT"

        self.normaldata = {"SCROLL-UP": {}, "SCROLL-DOWN": {}, "CLICK-SCROLL-DOWN-BUTTON": {}, "SEARCH-TRENDINGWORDS": {}, "SUMMARY-FOR-KEYWORD": {}, "CLICK-HIDE-SUMMARY": {}, "CLICK-SEE-SUMMARY": {}, "CLICK-HIDE-FULL-TEXT": {},
                         "CLICK-SEE-FULL-TEXT": {}, "START-EDIT-MESSAGE": {}, "UPDATE-PARAGRAPH-MESSAGEBOX": {}, "FINISH-EDIT-PARAGRAPH": {}, "CANCEL-EDIT-PARAGRAPH": {}, "UPDATE-SUMMARY-MESSAGEBOX": {}, "FINISH-EDIT-SUMMARY": {}, "CANCEL-EDIT-SUMMARY": {}, 'SPEECH-START': {}, 'SPEECH-START-M': {}, 'SPEECH-END': {}, 'SPEECH-END-M': {}}  # TODO: remove speech later
        self.log_pairdata = {"window": {}, "video": {}, "audio": {},
                             "subtask": {}, "mode": {}, "speech": {}}
        self.pairdata = {"window": [], "video": [], "audio": [],
                         "subtask": [], "mode": [], "speech": []}
        self.focus_on_off = []

    def toggle_pair(self):
        data = self.log_pairdata["mode"]
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
        result[index].append((prevt, self.TIMELIMIT-prevt))
        return result

    def pair_edit_start_finish_or_cancel(self, start, finish, cancel):
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

    def find_edit_msg_pair(self, start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm, isBoth=False):
        start_pgh = {}
        start_smm = {}
        for time in start_msgs:
            if start_msgs[time]['TYPE'] == "paragraph":
                start_pgh[time] = start_msgs[time]
            else:
                start_smm[time] = start_msgs[time]

        finish_pgh_data, cancel_pgh_data = self.pair_edit_start_finish_or_cancel(
            start_pgh, finish_pgh, cancel_pgh)
        finish_smm_data, cancel_smm_data = self.pair_edit_start_finish_or_cancel(
            start_smm, finish_smm, cancel_smm)

        if isBoth:
            return finish_pgh_data+cancel_pgh_data, finish_smm_data+cancel_smm_data

        return finish_pgh_data, cancel_pgh_data, finish_smm_data, cancel_smm_data

    def on_off_pair(self, data, onkey, offkey):
        # print("on_off_pair", onkey, offkey)
        # print(data)
        if not data:
            return []
        time = sorted(list(data.keys()))
        if data[time[0]] == offkey:
            print("**ERROR::::", time[0], offkey)
        if data[time[-1]] == onkey:
            data[self.TIMELIMIT] = offkey
            time.append(self.TIMELIMIT)

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

    def speech_pair_on_off(self, data):
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
            OFFs[self.TIMELIMIT] = False

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

    def on_off_focus(self, data):
        onkey = 'WINDOW-FOCUS-ON'
        offkey = 'WINDOW-FOCUS-OFF'

        if not data:
            return []
        time = sorted(list(data.keys()))
        if data[time[0]] == offkey:
            print("**ERROR::::", time[0], offkey)
        if data[time[-1]] == onkey:
            data[self.TIMELIMIT] = offkey
            time.append(self.TIMELIMIT)

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

    def calculate_pairdata(self):
        # self.pairdata = {"window": [], "video": [], "audio": [],
        #  "subtask": [], "mode": [], "speech": []}
        ### SUBTASK ###
        self.pairdata["subtask"] = self.on_off_pair(
            self.log_pairdata["subtask"], "OPEN-SUBTASK", "CLOSE-SUBTASK")

        ### ON/OFF - AUDIO/VIDEO/FOCUS ###
        self.pairdata["audio"] = self.on_off_pair(
            self.log_pairdata["audio"], 'AUDIO-ON', 'AUDIO-OFF')
        self.pairdata["video"] = self.on_off_pair(
            self.log_pairdata["video"], 'VIDEO-ON', 'VIDEO-OFF')
        self.pairdata["window"] = self.on_off_pair(self.log_pairdata["window"],
                                                   'WINDOW-FOCUS-ON', 'WINDOW-FOCUS-OFF')

        ### SPEECH START/END LOG ###
        self.pairdata["speech"] = self.speech_pair_on_off([self.normaldata[x] if x in self.normaldata else {} for x in [
            'SPEECH-START', 'SPEECH-START-M', 'SPEECH-END', 'SPEECH-END-M']])

        self.pairdata["mode"] = self.toggle_pair()

        self.focus_on_off = self.on_off_focus(self.log_pairdata["window"])

        # print(self.pairdata)

    def print_pairdata(self):
        for pairtype, content in self.pairdata.items():
            print(pairtype)
            print(content)

    def draw_overall_plot(self, path, is_system, is_multitask):
        normaldata = self.normaldata
        xbar = 500
        ybar = 1
        ### EDIT MESSAGES (PARAGRAPH OR SUMMARY) ###
        # TODO: fix
        start_msgs, finish_pgh, cancel_pgh, finish_smm, cancel_smm = [normaldata[x] if x in normaldata else {} for x in [
            "START-EDIT-MESSAGE",  "FINISH-EDIT-PARAGRAPH", "CANCEL-EDIT-PARAGRAPH", "FINISH-EDIT-SUMMARY", "CANCEL-EDIT-SUMMARY"]]
        finish_pgh_data, cancel_pgh_data, finish_smm_data, cancel_smm_data = self.find_edit_msg_pair(
            start_msgs, cancel_pgh, finish_pgh, cancel_smm, finish_smm)

        ### TOGGLE ###
        toggles = self.pairdata["mode"]

        ### HIDE/SHOW & SCROLL & SEARCH TRENDINGWORDS ###
        hideshow = ["CLICK-HIDE-SUMMARY", "CLICK-SEE-SUMMARY",
                    "CLICK-HIDE-FULL-TEXT", "CLICK-SEE-FULL-TEXT"]
        scroll = ["SCROLL-UP", "SCROLL-DOWN", "CLICK-SCROLL-DOWN-BUTTON"]
        trending = ["SEARCH-TRENDINGWORDS", "SUMMARY-FOR-KEYWORD"]
        datadict = {}
        for action in hideshow + scroll + trending:
            if action not in normaldata:
                times = []
            else:
                times = normaldata[action].keys()
            actiontime = [(time, xbar) for time in times]
            datadict[action] = actiontime

        ### SUBTASK ###
        subtask = self.pairdata["subtask"]

        ### ON/OFF - AUDIO/VIDEO/FOCUS ###
        audio = self.pairdata["audio"]
        video = self.pairdata["video"]
        focus = self.pairdata["window"]

        ### SPEECH START/END LOG ###
        speechs = self.pairdata["speech"]

        ############### GENERATE OVERALL PLOT ###############
        if is_system:
            fig, ax = plt.subplots(figsize=(15, 10))
        else:
            fig, ax = plt.subplots(figsize=(12, 3))
        ax.grid(True, color='#DDDDDD')
        ax.set_axisbelow(True)

        idx = 0

        labels = []

        if is_system:
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
            ax.broken_barh([(0, self.maxtime)], (2*idx, ybar), color='#FFFFFF')
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
            ax.broken_barh([(0, self.maxtime)], (2*idx, ybar), color='#FFFFFF')
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
            ax.broken_barh([(0, self.maxtime)], (2*idx, ybar), color='#FFFFFF')
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
            ax.broken_barh([(0, self.maxtime)], (2*idx, ybar), color='#FFFFFF')
            idx += 1  # EMPTY BAR
            labels.extend([" "])

        if is_multitask:
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
                no_focus.append((time[0], self.TIMELIMIT - time[0]))
        # print("no_focus", no_focus)
        ax.broken_barh(no_focus, (0, 2*(idx+2)),
                       zorder=-2, color='#ffe8ed')
        ax.broken_barh(focus, (0, 2*(idx+2)), zorder=-2, color='#e6f7ff')

        yticks = [2*i+0.5 for i in range(idx)]

        ax.set_yticks(yticks)
        ax.set_yticklabels(labels)

        ax.set_ylim(-1, 2*(idx))
        ax.set_xlim(0, (int(self.maxtime/60/1000)+0.5)*60*1000)
        ax.set_xticks([i*60*1000 for i in range(int(self.maxtime/60/1000)+1)])
        ax.set_xticklabels([str(i)
                           for i in range(int(self.maxtime/60/1000)+1)])

        plt.suptitle("[{}] OVERALL - {}".format(self.roomname, self.username),
                     fontsize=16, fontweight="bold")
        if is_system:
            plt.title(
                "FOCUS(ON-blue/OFF-red) || MODE(SUMMARY-green/TRANSCRIPT-violet)", fontweight="bold")
        else:
            plt.title(
                "FOCUS(ON-blue/OFF-red)", fontweight="bold")

        plt.tight_layout()

        pngfilename = path + \
            "/overall-{}-{}.png".format(self.roomname, self.username)
        plt.savefig(pngfilename)
        print("GENERATED FILE: "+pngfilename)

        # return on off data
        self.on_off_focus(self.log_pairdata["window"])

        ############### GENERATE SUBTASK PLOT ###############
        # TODO


class Parser:
    def __init__(self, roomname, roomid, duration, plot):
        self.roomname = roomname
        self.roomid = roomid
        self.TIMELIMIT = int(duration*60*1000)
        self.STARTTIME = -1
        self.is_multitask = roomname.split('_')[1] == "M"
        self.is_system = roomname.split('_')[2] == "S"
        self.toggle_actions = {}
        self.delays = {'keyword': -1, 'silence': -
                       1, 'summary': -1, 'transcript': -1}
        # Speech End Detect
        self.endDetect = []
        # Focus out
        self.focusout = {}
        self.users = []
        self.draw = plot

        # TODO: Move to other class
        self.mode_statistics = None

    def readfile(self, filepath):
        try:
            with open(filepath, 'r') as f:
                contents = f.readlines()
        except:
            print("[ERROR] File path error: {} does not exist".format(filepath))
            contents = []
        return contents

    def calculate_delay(self, delaypath, delaytype):
        if delaytype == "keyword":
            delayfilename = "KeyExt.txt"
        elif delaytype == "silence":
            delayfilename = "Silence.txt"
        elif delaytype == "summary":
            delayfilename = "Sum.txt"
        else:
            print("[Error] delay type error: {}".format(delaytype))

        delay = self.readfile(delaypath + delayfilename)
        delay = [float(d.split(":")[-1].split("}")[0]) for d in delay]
        self.delays[delaytype] = statistics.mean(delay)
        # print("delay", delaytype, delay)

    def parse_system_log(self, user, loglines, issystem):
        # print(self.STARTTIME, self.TIMELIMIT)
        starttime = self.STARTTIME
        pairlogs = user.log_pairdata

        joinmsgline = 0
        joinmsgidx = 4

        videocond = False
        audiocond = False
        focuscond = True
        modecond = user.defaultMode
        for idx, line in enumerate(loglines):
            # print(idx, line)
            # PASS WITH JOINED MSG
            if "joined" in line and "User" in line:
                joinmsgline = idx
                joinmsgidx = joinmsgline+4

                time = int(line.split(")")[0].replace("(", ""))
                user.mintime = time if user.mintime == None else user.mintime
                time = time - starttime

                if time < 0:
                    focuscond = True
                else:
                    pairlogs[time] = "WINDOW-FOCUS-ON"
            if idx <= joinmsgidx and idx >= joinmsgline:
                continue

            # PARSE ACTION
            params = line.split(")")[-1].strip()
            action = params.split("/")[0]

            # PARSE TIME
            time = int(line.split(")")[0].replace("(", ""))
            user.mintime = time if user.mintime == None else user.mintime
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
            if time > self.TIMELIMIT:
                continue

            if user.maxtime < time + starttime:
                user.maxtime = time + starttime

            if action in ["SPEECH-RECOGNIZED", "CURRENT-MSG-BOXES", "CREATE-MSGBOX"] or "GET-POSITION-OF-MOUSE" in action:
                continue

            if action in user.pairactions:
                parseaction = action.split("-")
                if parseaction[0] == "WINDOW":
                    pairlogs["window"][time] = action
                elif parseaction[0] == "VIDEO":
                    pairlogs["video"][time] = action
                elif parseaction[0] == "AUDIO":
                    pairlogs["audio"][time] = action
                elif parseaction[1] == "SUBTASK":
                    pairlogs["subtask"][time] = action
                else:
                    pairlogs["mode"][time] = params.split(
                        "/")[1].split("=")[1]
            elif '/' in params:
                try:
                    user.normaldata[action][time] = {arg.split("=")[0]: arg.split(
                        "=")[1] for arg in params.split("/")[1:]}
                except:
                    # case SEARCH-TRENDINGWORDS/RETURN
                    user.normaldata[action][time] = {}
            elif action == "Exit":
                pairlogs["audio"][time] = "AUDIO-OFF"
                pairlogs["video"][time] = "VIDEO-OFF"
                pairlogs["window"][time] = "WINDOW-FOCUS-OFF"
                pairlogs["window"][time] = user.defaultMode
            else:
                try:
                    user.normaldata[action][time] = {}
                except:
                    print("Action Key error::", action, params)

        if videocond:
            pairlogs["video"][0] = "VIDEO-ON"
        if audiocond:
            pairlogs["audio"][0] = "AUDIO-ON"
        if focuscond:
            pairlogs["window"][0] = "WINDOW-FOCUS-ON"
        if issystem:
            pairlogs["mode"][0] = modecond

        user.log_pairdata = pairlogs
        # print(pairlogs)

    def parse_speech_log(self, user, sttlines):
        starttime = self.STARTTIME
        mintime = user.mintime

        endDetect = []
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
            if time > self.TIMELIMIT:
                continue

            if user.maxtime < time + starttime:
                user.maxtime = time + starttime

            params = line.split(")")[-1].strip()
            action = params.split("/")[0]
            # pairdata["speech"][time] = action

            if action not in user.normaldata:
                user.normaldata[action] = {}
            user.normaldata[action][time] = {arg.split("=")[0]: arg.split(
                "=")[1] for arg in params.split("/")[1:]}
        return endDetect

    def parse_user_logs(self, user):
        # Read logs
        loglines = self.readfile(user.filename)
        sttlines = self.readfile(user.speechfilename)

        # TODO: move to class
        # Parse starttime
        self.STARTTIME = int(loglines[0].split(")")[0].replace(
            "(", "")) if self.STARTTIME == -1 else self.STARTTIME
        # print("starttime:", starttime)

        self.parse_system_log(user, loglines, self.is_system)
        endDetect = self.parse_speech_log(user, sttlines)
        self.endDetect.append(endDetect)

        # print("---USERDATA---\n", normaldata)
        user.maxtime = user.maxtime-self.STARTTIME
        print("STARTTIME", self.STARTTIME, "ENDTIME",
              self.STARTTIME+self.TIMELIMIT)

    def parse_logs(self):
        logfiles = glob.glob("./media-server/logs/" +
                             self.roomname+"_"+self.roomid+"/*")
        print("LOG FILE LIST:", logfiles)

        # Generate Log Directory
        path = "./analysis/{}_{}".format(self.roomname, self.roomid)
        # TODO: path가 파일이면?
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print('Error: Creating directory '+path)

        # TODO: path 고치기
        delaypath = "./moderator/delays/{}_{}/".format(
            self.roomname, self.roomid)
        for key in ["keyword", "silence", "summary"]:
            self.calculate_delay(delaypath, key)

        ### Get starttime ###
        try:
            with open("./moderator/logs/{}_{}/STARTCLOCK.txt".format(self.roomname, self.roomid), 'r') as f:
                self.STARTTIME = int(f.readline())
        except:
            self.STARTTIME = -1

        # TODO: move path
        outdir = "./analysis/{}_{}".format(self.roomname, self.roomid)

        ### ITERATE FOR EACH USERS ###
        for filename in logfiles:
            # Check if this is user's log file
            # os.path.walk | rsplit // split 여러 번
            if filename.split("/")[-1] == self.roomname+".txt":
                continue
            if "subtask" in filename.split("/")[-1].split("_"):
                continue

            print("*"*50)
            # Parse username
            username = filename.split("/")[-1][:-4]
            print("USERNAME:", username)

            if username == "cpsAdmin":
                continue
            if "Junyoung" in username or "junyoung" in username:
                continue

            user = UserData(self.roomname, self.roomid,
                           username, filename, self.TIMELIMIT)
            self.parse_user_logs(user)

            user.calculate_pairdata()
            # user.print_pairdata()
            if self.draw:
                self.focusout[user.name] = user.draw_overall_plot(
                    outdir, self.is_system, self.is_multitask)

            self.users.append(user)

        # TODO: 아래 내용 함수로 옮기기
        # # SAVE DELAY
        # self.delays['transcript'] = statistics.mean(self.endDetect)
        # with open(outdir+"/delay_logs.txt", 'w') as f:
        #     for (case, value) in self.delays.items():
        #         f.write("{}: {}\n".format(case, value))

        # # print(self.focusout)
        # for (username, values) in self.focusout.items():
        #     with open(outdir+"/focusout_"+username+".csv", 'w', newline='') as f:
        #         writer = csv.writer(f)
        #         writer.writerow(['Focus ON']+values[0])
        #         writer.writerow(['Focus OFF']+values[1])

class RoomData:
    def __init__(self, roomname, roomid, userList):
        self.name = roomname
        self.id = roomid
        self.users = userList
        

class ParsedData:
    def __init__(self, dataType):
        self.type = dataType
        self.users = []
        self.mode_statistics = pd.DataFrame()

    def add_users(self, userList):
        self.users.extend(userList)

    def calculate_speech(self):
        print("\n{:-^50}".format(" Calculate speech: {} ".format(self.type)))
        speech_statistics = {user.username: sum(
            pair[1] for pair in user.pairdata["speech"]) for user in self.users}
        total_speech = sum(speech_statistics.values())
        print("TOTAL SPEECH DURATION: {} minutes".format(total_speech/60000))
        for username, duration in sorted(speech_statistics.items(), key=lambda item: item[1], reverse=True):
            print("- {:20}: {:10.3%} ({:.1f} min.)".format(username,
                  duration/total_speech, duration/60000))

    def get_mode_statistics(self):
        mode_statistics = {user.username: [user.defaultMode, sum(pair[1] for pair in user.pairdata["mode"][0])/user.TIMELIMIT, sum(
            pair[1] for pair in user.pairdata["mode"][1])/user.TIMELIMIT, len(user.normaldata["CLICK-SEE-FULL-TEXT"]), len(user.normaldata["CLICK-SEE-SUMMARY"])] for user in self.users}
        mode_df = pd.DataFrame(data=[[item[0]] + (["SUMMARY", "{:.2%}".format(item[1]), item[3], "TRANSCRIPT", "{:.2%}".format(item[2]), item[4], item[0] == "SUMMARY"] if item[1] > item[2] else ["TRANSCRIPT", "{:.2%}".format(
            item[2]), item[4], "SUMMARY", "{:.2%}".format(item[1]), item[3], item[0] == "TRANSCRIPT"]) for item in mode_statistics.values()], columns=["Default", "1st", "%(1st)", "Click(1st)", "2nd", "%(2nd)", "Click(2nd)", "Stay"], index=mode_statistics.keys()).sort_index(key=lambda x: x.str[-1])
        self.mode_statistics = mode_df

    def calculate_mode(self):
        # TODO: Remove later
        mode_statistics = {user.username: [user.defaultMode, sum(pair[1] for pair in user.pairdata["mode"][0])/user.TIMELIMIT, sum(
            pair[1] for pair in user.pairdata["mode"][1])/user.TIMELIMIT, len(user.normaldata["CLICK-SEE-FULL-TEXT"]), len(user.normaldata["CLICK-SEE-SUMMARY"])] for user in self.users}

        # for user in self.users:
        #     sum_dur, trans_dur = sum(pair[1] for pair in user.pairdata["mode"][0])/self.TIMELIMIT, sum(pair[1] for pair in user.pairdata["mode"][1])/self.TIMELIMIT
        #     user.mode_statistics = {"Default": user.defaultMode, "1st": "SUMMARY", "%(1st)": sum_dur, "Click(1st)":len(user.normaldata["CLICK-SEE-FULL-TEXT"]), "2nd": "TRANSCRIPT", "%(2nd)": trans_dur, "Click(2nd)":len(user.normaldata["CLICK-SEE-SUMMARY"]), "Stay":user.defaultMode == "SUMMARY"} if sum_dur > trans_dur else {"Default": user.defaultMode, "1st": "TRANSCRIPT", "%(1st)": trans_dur, "Click(1st)":len(user.normaldata["CLICK-SEE-SUMMARY"]), "2nd": "SUMMARY", "%(2nd)": sum_dur, "Click(2nd)":len(user.normaldata["CLICK-SEE-FULL-TEXT"]), "Stay":user.defaultMode == "TRANSCRIPT"}

        # # mode_df = pd.DataFrame([ms["Default"], ms["1st"], ms["%(1st)"], ms["Click(1st)"], ms["2nd"], ms["%(2nd)"], ms["Click(2nd)"], ms["Stay"] for user.mode_statistics in self.users])
        # mode_df = pd.DataFrame([user.mode_statistics for user in self.users], index = [user.username for user in self.users])

        if self.mode_statistics.empty:
            self.get_mode_statistics()
        mode_df = self.mode_statistics

        first_mode = mode_df.groupby(['1st']).count()
        sum_to_trans, trans_to_sum = mode_df[(mode_df["Default"] == "SUMMARY") & (
            mode_df.Stay == False)], mode_df[(mode_df["Default"] == "TRANSCRIPT") & (mode_df.Stay == False)]
        total_count, sum_count, trans_count = len(
            mode_df), first_mode.iloc[0][0], first_mode.iloc[1][0]
        full_click_count, sum_click_count = sum(item[3] for item in mode_statistics.values(
        )), sum(item[4] for item in mode_statistics.values())

        # Print analysis result
        print("\n{:-^50}".format(" Calculate mode: {} ".format(self.type)))
        display(mode_df)
        print("-"*30)
        print("* TOTAL PARTICIPANTS: {}".format(total_count))
        print("* MODE COUNT: SUMMARY [{} ({:.2%})] | TRANSCRIPT [{} ({:.2%})]".format(
            sum_count, sum_count/total_count, trans_count, trans_count/total_count))
        print("* MODE CHANGE [{} participant(s) ({:.2%})]".format(len(sum_to_trans) +
              len(trans_to_sum), (len(sum_to_trans) + len(trans_to_sum))/total_count))
        if not sum_to_trans.empty:
            print("[SUMMARY -> TRANSCRIPT]: total {} ({:.2%})".format(
                len(sum_to_trans), len(sum_to_trans)/total_count))
            display(sum_to_trans)
        if not trans_to_sum.empty:
            print("[TRANSCRIPT -> SUMMARY]: total {} ({:.2%})".format(
                len(trans_to_sum), len(trans_to_sum)/total_count))
            display(trans_to_sum)
        print("* BUTTON CLICK: FULL-SCRIPT({}) | SUMMARY({})".format(full_click_count, sum_click_count))

    def calculate_scroll_log(self):
        if self.mode_statistics.empty:
            self.get_mode_statistics()
        scroll_df = pd.DataFrame([[user.defaultMode, len(user.normaldata["SCROLL-UP"]), len(user.normaldata["SCROLL-DOWN"]), len(user.normaldata["CLICK-SCROLL-DOWN-BUTTON"])]
                                 for user in self.users], columns=["Default", "Scroll UP", "Scroll DOWN", "Scroll BUTTON"], index=[user.username for user in self.users]).sort_index(key=lambda x: x.str[-1])
        scroll_df = scroll_df.join(self.mode_statistics["1st"])
        temp_col = scroll_df.pop("1st")
        scroll_df.insert(1, "1st", temp_col)

        sum_scroll_df, trans_scroll_df = scroll_df[scroll_df['Default']
                                                   == 'SUMMARY'], scroll_df[scroll_df['Default'] == 'TRANSCRIPT']
        sum_up_cnt, sum_down_cnt, sum_btn_cnt = sum(sum_scroll_df["Scroll UP"]), sum(
            sum_scroll_df["Scroll DOWN"]), sum(sum_scroll_df["Scroll BUTTON"])
        trans_up_cnt, trans_down_cnt, trans_btn_cnt = sum(trans_scroll_df["Scroll UP"]), sum(
            trans_scroll_df["Scroll DOWN"]), sum(trans_scroll_df["Scroll BUTTON"])
        up_cnt, down_cnt, btn_cnt = sum(scroll_df["Scroll UP"]), sum(
            scroll_df["Scroll DOWN"]), sum(scroll_df["Scroll BUTTON"])
        total_cnt = up_cnt + down_cnt + btn_cnt
        sum_total_cnt, trans_total_cnt = sum_up_cnt + sum_down_cnt + \
            sum_btn_cnt, trans_up_cnt + trans_down_cnt + trans_btn_cnt

        # Print analysis result
        print("\n{:-^50}".format(" Calculate scroll log: {} ".format(self.type)))
        print("* TOTAL SCROLL {} | UP {} ({:.2%}) | DOWN {} ({:.2%}) | BTN {} ({:.2%})".format(total_cnt,
              up_cnt, up_cnt/total_cnt, down_cnt, down_cnt/total_cnt, btn_cnt, btn_cnt/total_cnt))
        print("* [SUMMARY MODE] TOTAL SCROLL {} | UP {} ({:.2%}) | DOWN {} ({:.2%}) | BTN {} ({:.2%})".format(sum_total_cnt,
              sum_up_cnt, sum_up_cnt/sum_total_cnt, sum_down_cnt, sum_down_cnt/sum_total_cnt, sum_btn_cnt, sum_btn_cnt/sum_total_cnt))
        display(scroll_df[scroll_df['1st'] == 'SUMMARY'])
        print("* [TRANSCRIPT MODE] TOTAL SCROLL {} | UP {} ({:.2%}) | DOWN {} ({:.2%}) | BTN {} ({:.2%})".format(trans_total_cnt, trans_up_cnt,
              trans_up_cnt/trans_total_cnt, trans_down_cnt, trans_down_cnt/trans_total_cnt, trans_btn_cnt, trans_btn_cnt/trans_total_cnt))
        display(scroll_df[scroll_df['1st'] == 'TRANSCRIPT'])

    def calculate_focus_log(self):
        focus_df = pd.DataFrame([[len(user.focus_on_off[1]), sum(dur for start, dur in user.pairdata["window"])/60000]for user in self.users], columns=[
                                "# Focus Out", "Focus In Duration"], index=[user.username for user in self.users]).sort_index(key=lambda x: x.str[-1])

        # Print analysis result
        print("\n{:-^50}".format(" Calculate focus log: {} ".format(self.type)))
        display(focus_df)
        print(
            "* Avg Focus Out Count: {:.2f}".format(sum(focus_df["# Focus Out"])/len(self.users)))
        print("* Avg Focus In Duration: {:.2f} min".format(
            sum(focus_df["Focus In Duration"])/len(self.users)))


def select_roomid(roomname, rooms, index=-1):
    print("AVAILABLE LOGS FOR ROOM <{}>:".format(roomname))
    for i, room in enumerate(rooms):
        print("Index [{}]:{}".format(i, room))

    if index == -1:
        index = int(input("- Enter index: "))
    else:
        print("- Use default index 0")

    # Parse roomid
    roomid = rooms[index].split("_")[-1]
    print("ROOM ID:", roomid)
    return roomid


def main():
    ### PARSE ARGUMENTS ###
    import argparse
    argParser = argparse.ArgumentParser()
    # argParser.add_argument("roomname", type=str, default=None)
    argParser.add_argument("-time", type=float, default=30)
    argParser.add_argument("-p", type=bool, default=False)
    argParser.add_argument("-type", type=str, default=None)
    args = argParser.parse_args()

    # Get roomname from agrument
    # roomnames = [args.roomname]
    # parsedResult = ParsedData(args.type if args.type else args.roomname)

    # for roomname in roomnames:
    #     rooms = [room for room in os.listdir(
    #         "./media-server/logs/") if room.startswith(roomname + "_")]
    #     roomid = select_roomid(roomname, rooms)

    #     logParser = Parser(roomname, roomid, args.time, args.p)
    #     logParser.parse_logs()
    #     parsedResult.add_users(logParser.users)

    # print("*"*50)
    # # 회의 별 총 발화 시간 및 각 참여자 점유율
    # parsedResult.calculate_speech()
    # parsedResult.calculate_mode()
    # parsedResult.calculate_scroll_log()
    # parsedResult.calculate_focus_log()

    # room_BN = ["0315_N_B_Game", "O316_N_B_College"]
    # room_SN = ["0315_N_S_College", "0316_N_S_Game"]
    room_BN = ["0316_N_B_College"]
    room_SN = ["0316_N_S_Game"]
    room_BM = ["0317_M_B_Game", "0318_M_B_College"]
    room_SM = ["0317_M_S_College", "0318_M_S_Game"]

    BNResult = ParsedData("Base Normal")
    SNResult = ParsedData("System Normal")
    BMResult = ParsedData("Base Multitask")
    SMResult = ParsedData("System multitask")
    OverallResult = ParsedData("Overall")
    BaseResult = ParsedData("Base Overall")
    SysResult = ParsedData("System Overall")
    groupResults = {"BN": (room_BN, BNResult), "SN": (
        room_SN, SNResult), "BM": (room_BM, BMResult), "SM": (room_SM, SMResult)}

    for roomtype, (roomnames, analyizer) in groupResults.items():
        print("{:*^50}".format(roomtype))
        for roomname in roomnames:
            print("{:-^30} [{}]".format(roomname, analyizer.type))
            rooms = [room for room in os.listdir(
                "./media-server/logs/") if room.startswith(roomname+"_")]
            roomid = select_roomid(roomname, rooms, 0)

            if roomname == "0316_N_S_Game":
                args.time = 28.5
            logParser = Parser(roomname, roomid, args.time, args.p)
            logParser.parse_logs()

            analyizer.add_users(logParser.users)
            # if roomtype == "BN":
            #     BNResult.add_users(logParser.users)
            # elif roomtype == "SN":
            #     SNResult.add_users(logParser.users)
            # elif roomtype == "BM":
            #     BMResult.add_users(logParser.users)
            # elif roomtype == "SM":
            #     SMResult.add_users(logParser.users)
            # else:
            #     print("ERROR")

            # analyizer.add_users(logParser.users)
            # for user in logParser.users:
            #     print(user.username)
            # print("++++")
            # for user in SMResult.users:
            #     print(user.username)
            # print("&&&&")

            if roomtype[0] == "B":
                BaseResult.add_users(logParser.users)
            else:
                SysResult.add_users(logParser.users)
            OverallResult.add_users(logParser.users)

    # for user in BMResult.users:
    #     print(user.username)
    # print("---")
    # for user in SMResult.users:
    #     print(user.username)

    while True:
        print("*"*50)
        option = int(input(
            "Insert type option[1. Overall, 2. System, 3. Baseline, 4. BN, 5. SN, 6. BM, 7. SM, 0. Exit]: "))

        if option == 1:
            resultData = OverallResult
        elif option == 2:
            resultData = SysResult
        elif option == 3:
            resultData = BaseResult
        elif option == 4:
            resultData = BNResult
        elif option == 5:
            resultData = SNResult
        elif option == 6:
            resultData = BMResult
        elif option == 7:
            resultData = SMResult
        elif option == 0:
            break
        else:
            print("Type option ERROR!!")
            continue

        while True:
            if option not in [3, 4, 6]:
                action = int(input(
                    "[{}] Insert action option[1. speech, 2. mode, 3. scroll, 4. focus, 0. exit]: ".format(resultData.type)))
            else:
                action = int(input(
                    "[{}] Insert action option[1. speech, 4. focus, 0. exit]: ".format(resultData.type)))

            if action == 1:
                resultData.calculate_speech()
            elif action == 2 and option not in [1, 3, 4, 6]:
                resultData.calculate_mode()
            elif action == 3 and option not in [1, 3, 4, 6]:
                resultData.calculate_scroll_log()
            elif action == 4:
                resultData.calculate_focus_log()
            elif action == 0:
                break
            else:
                print("Action option ERROR!!")
                continue


if __name__ == "__main__":
    main()
