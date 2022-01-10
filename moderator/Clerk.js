// Clerk.js
// Defines Clerk class that keeps track of last "paragraph" in each room.
// Clerk also interacts with the summary server.

const axios = require("axios");
const config = require("./config");

// Read and write logs
const fs = require("fs");
const getLastLine = require("./fileTools.js").getLastLine;
const { time } = require("console");

const summaryHost = config.summaryHost_1;
const remoteHost = config.summaryHost_2;

const keywordPorts = summaryHost + config.keywordPorts;
const summarizerPorts = config.summarizerPorts_1;
const remotePorts = config.summarizerPorts_2;
const localPortCnt = summarizerPorts.length;
const remotePortCnt = remotePorts.length;
const sumPortCnt = localPortCnt + remotePortCnt;

const sttPorts = config.sttPorts;
const sttPortCnt = sttPorts.length;

const sttNumKeys = config.numKeys;

let summarizerHosts = [];
for (i = 0; i < localPortCnt; i++) {
  summarizerHosts.push(summaryHost + summarizerPorts[i]);
}
for (i = 0; i < remotePortCnt; i++) {
  summarizerHosts.push(remoteHost + remotePorts[i]);
}

let sttHosts = [];
for (i = 0; i < sttPortCnt; i++) {
  sttHosts.push(summaryHost + sttPorts[i]);
}

let keyword_trends = {};

module.exports = class Clerk {
  constructor (io, room_id, room_name) {
    this.io = io;
    this.room_id = room_id;
    this.room_name = room_name;

    this.paragraph = "";
    this.speakerId = null;
    this.speakerName = null;
    this.switchTimeout = null;

    // Timestamp records when a new paragraph started.
    // It can be used to identify a paragraph uniquely.
    this.timestamp = null;

    /**
     * Paragraph dictionary which saves transcript results.
     * For each key(== timestamp), every element includes contents below.
     * - ms stt result
     * - naver stt result
     * - summarizer result
     * - edit transcript log {timestamp: (editor, content, summary elements)}
     * - edit summary log {timestamp: (editor, content)}
     */
    this.paragraphs = {};

    // Set PORT for STT and Summarizer.
    this.summarizerPorts = summarizerHosts;
    this.sttPorts = sttHosts;
    this.sumPortCnt = sumPortCnt;
    this.sttPortCnt = sttPortCnt;
    this.sttKeyCnt = sttNumKeys;

    this.keywordPorts = keywordPorts;

    this.requestSTTIdx = 0;
    this.sttKeyIdx = 0;
    this.requestSumIdx = 0;
  }

  restoreParagraphs() {
    const fileName = "./logs/" + this.room_name + "_" + this.room_id + "/transcript.txt";
    fs.access(fileName, fs.F_OK, (err) => {
      if (err) {
        console.log("No previous conversation");

        // read Default-Conversation
        const defaultfileName = "./logs/default-transcript/Default-Conversation_College.txt";
        fs.access(defaultfileName, fs.F_OK, (err) => {
          if (err) {
            console.log("No default conversation");
            return;
          }

          // File exists
          const minLineLength = 1;
          getLastLine(defaultfileName, minLineLength)
            .then((lastLine) => {
              let past_paragraphs = JSON.parse(lastLine);
              this.paragraphs = past_paragraphs;
              this.io.sockets.to(this.room_id).emit("restore", this.paragraphs);
              this.addRoomLog();
            })
            .catch((err) => {
              console.error(err);
            });
        });

        return;
      }

      // File exists
      const minLineLength = 1;
      getLastLine(fileName, minLineLength)
        .then((lastLine) => {
          console.log("[Clerk.js] Restore past paragraphs");
          // console.log(JSON.parse(lastLine))
          let past_paragraphs = JSON.parse(lastLine);
          this.paragraphs = past_paragraphs;
          this.io.sockets.to(this.room_id).emit("restore", this.paragraphs);
        })
        .catch((err) => {
          console.error(err);
        });
    });

    const clockfilename = "./logs/" + this.room_name + "_" + this.room_id + "/STARTCLOCK.txt";
    fs.access(clockfilename, fs.F_OK, (err) => {
      if (err) {
        console.log("NO CLOCK FILE");
        return;
      }

      // File exists
      const minLineLength = 1;
      getLastLine(clockfilename, minLineLength)
        .then((lastLine) => {
          let starttime = new Date(parseInt(lastLine));

          this.io.sockets.to(this.room_id).emit("startTimer", starttime);

          console.log("RESTORE CLOCK", starttime);
        })
        .catch((err) => {
          console.error(err);
        });
    });
  }

  /**
   * Construct a new paragraph dictionary entry for given timestamp and speaker information.
   */
  addNewParagraph(speakerId, speakerName, timestamp) {
    this.paragraphs[timestamp] = {
      speakerID: speakerId,
      speakerName: speakerName,
      ms: [],
      sum: {},
      editTrans: {},
      editSum: {},
      pinned: false,
    };
  }

  /**
   * Return timestamp for messagebox.
   * Split if
   *  1) stacked MS list has length > 10
   *  2-1) other speaker has MS list length > 3 after speech start
   *  2-2) other speaker has MS speech length > 15 after speech start
   * 
   * @param {string} speakerId 
   * @param {string} speakerName 
   * @param {list[timestamp]} timestamps 
   * @param {bool} isLast 
   * @returns {timestamp, bool, timestamp} timestamp, isLast, newTimestamp
   */
  getMsgTimestamp(speakerId, speakerName, timestamps, isLast) {
    if (!timestamps) {
      console.log(
        "################ invalidtimestamp!",
        speakerId,
        speakerName,
        timestamps,
        isLast
      );
      let v = null;
      return { v, v, v };
    }
    let ts = timestamps[0];

    // console.log(">>> (Debug) getMsgTimestamp function")
    // console.log(">>> (Debug) timestamps:", timestamps);

    if (!(ts in this.paragraphs)) {
      console.log("[NEW MSGBOX(" + speakerName + ")] ts, isLast", ts, isLast);
      this.addNewParagraph(speakerId, speakerName, ts);
      return { ts, isLast, ts };
    }

    let newTimestamp = 0;
    let otherTimestamp = 0;
    let newLast = ts;
    for (var t in this.paragraphs) {
      t = Number(t);
      // console.log(">>> (Debug) t:", t)
      if (timestamps.includes(t)) {
        newTimestamp = t;
      } else if (t > ts) {
        // console.log(">>> (Debug) newTimestamp, t, ts:", newTimestamp, t, ts);
        if ((this.paragraphs[t]["ms"].length > 3) || (this.paragraphs[t]["ms"].join('').length > 15)) {
          // console.log(">>> (Debug) Update othertimestamp to t:", t);
          otherTimestamp = t;
        }
      }
    }

    if (newTimestamp) {
      ts = newTimestamp;
    }

    // console.log(">>> (Debug) paragraphs:", this.paragraphs[ts]["ms"]);
    // console.log(">>> (Debug) otherTimestamp, ts, isLast:", otherTimestamp, ts, isLast);
    if (this.paragraphs[ts]["ms"].length > 10) {
      console.log("[SPLIT MSGBOX(" + speakerName + ")] Long speech");
      isLast = true;
      newLast = timestamps[timestamps.length - 1];
      this.addNewParagraph(speakerId, speakerName, newLast);
    }
    else if (otherTimestamp > ts && !isLast) {
      isLast = true;
      newLast = timestamps[timestamps.length - 1];
      console.log("[SPLIT MSGBOX(" + speakerName + ")] Other's speech");
      this.addNewParagraph(speakerId, speakerName, newLast);
    }

    return { ts, isLast, newLast };
  }

  /**
   * Temporarily display transcript returned from MS STT.
   */
  async tempParagraph(speakerId, speakerName, transcript, timestamp) {
    // Save transcript
    this.paragraphs[timestamp]["ms"].push(transcript);

    let tempTranscript = this.paragraphs[timestamp]["ms"].join(' ');

    // Show message box
    this.publishTranscript(tempTranscript, speakerName, timestamp);

    this.requestKeyword(
      speakerId, speakerName,
      this.paragraphs[timestamp]["ms"].join(" "),
      timestamp, 1
    );
  }

  /**
   * Broadcasts a transcript to the room.
   */
  publishTranscript(transcript, name, timestamp) {
    this.addRoomLog();
    this.io.sockets
      .to(this.room_id)
      .emit("transcript", transcript, name, timestamp);
  }

  /**
   * Request Keyword from given paragraph. Broadcasts the result.
   * Call this function for every temporal STT results.
   */
  requestKeyword(speakerId, speakerName, paragraph, timestamp, requestTrial) {
    if (!paragraph) {
      paragraph = this.paragraphs[timestamp]["ms"].join(" ");
    }

    let unit = 3;
    if (paragraph.split(".").length % unit != 1) return;

    let host = this.keywordPorts;
    let requestStart = Date.now()
    let requestStartTime = new Date(requestStart).toTimeString().split(' ')[0]
    console.log("-----requestKeyword(" + speakerName + ")-----")
    console.log("HOST: ", host)
    console.log("requestTrial: ", requestTrial)
    console.log("requestStart: ", requestStartTime)
    console.log("timestamp: ", new Date(Number(timestamp)))
    console.log("---requestKeyword(" + speakerName + ") start...");

    axios
      .post(
        host,
        {
          type: "requestKeyword",
          user: speakerId,
          content: paragraph,
        },
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      )
      .then((response) => {
        let requestSuccess = Date.now()
        console.log("-----requestKeyword(" + speakerName + ") at " + requestStartTime + " success-----")
        console.log("requestSuccess: ", new Date(requestSuccess).toTimeString().split(' ')[0])
        console.log("Time spent: ", (requestSuccess - requestStart) / 1000)

        // add time delay log
        this.addDelLog(timestamp, (requestSuccess - requestStart) / 1000, "KeyExt")


        let summary, summaryArr;
        if (response.status === 200) {
          summary = response.data;
        }
        let keywordList = summary.split("@@@@@CD@@@@@AX@@@@@");
        console.log("[Keyword result(" + speakerName + ")]", keywordList)

        this.io.sockets
          .to(this.room_id)
          .emit("keyword", keywordList, speakerName, timestamp);
      })
      .catch((e) => {
        console.log("-----requestKeyword(" + speakerName + ") ERROR-----")
        if (requestTrial < 5) {
          console.log("Try requestKeyword again...");
          this.requestKeyword(speakerId, speakerName, paragraph, timestamp, requestTrial + 1)
        }
        else {
          console.log("Too many failed requests in requestKeyword(" + speakerName + "): use empty keyword");

          let keywordList = [];

          this.io.sockets
            .to(this.room_id)
            .emit("keyword", keywordList, speakerName, timestamp);
        }
      });
  }

  /**
   * Requests for a summary for the current paragraph, then
   * broadcasts the result with given confidence level.
   */
  requestSummary(speakerId, speakerName, timestamp, requestTrial) {
    let paragraph = this.paragraphs[timestamp]["ms"].join(' ');
    if (!paragraph) {
      console.log("-----requestSummary(ERROR) - no paragraph for timestamp: ", timestamp);
    }

    let idx = this.requestSumIdx;
    this.requestSumIdx = ++this.requestSumIdx % this.sumPortCnt;
    let host = this.summarizerPorts[idx];

    let requestStart = Date.now()
    let requestStartTime = new Date(requestStart).toTimeString().split(' ')[0]
    console.log("-----requestSummary(" + speakerName + '_' + speakerId + ")-----")
    console.log("HOST: ", host)
    console.log("this.requestSumIdx: ", this.requestSumIdx)
    console.log("requestTrial: ", requestTrial)
    console.log("requestStart: ", requestStartTime)
    console.log("---requestSummary(" + speakerName + ") start...")

    if (paragraph.split(" ")[0].length == 0) return;

    axios
      .post(
        host,
        {
          type: "requestSummary",
          user: speakerId,
          content: paragraph,
        },
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      )
      .then((response) => {
        let requestSuccess = Date.now()
        console.log("-----requestSummary(" + speakerName + ") at " + requestStartTime + " success-----")
        console.log("requestSuccess: ", new Date(requestSuccess).toTimeString().split(' ')[0])
        console.log("Time spent: ", (requestSuccess - requestStart) / 1000)

        // add time delay log
        this.addDelLog(timestamp, (requestSuccess - requestStart) / 1000, "Sum")

        let summary, summaryArr;
        if (response.status === 200) {
          summary = response.data;
        }

        let confArr = [1, 1]; //Math.random();
        // No summary: just emit the paragraph with an indication that
        // it is not a summary (confidence === -1).
        if (!summary) {
          summaryArr = [paragraph, paragraph, "", ""];
          confArr = [0, 0];
        }
        else {
          console.log("[Summarizer result(" + speakerName + ")]", summary);

          // Parse returned summary
          let summary_text = summary.split("@@@@@CF@@@@@")[0];
          const confidence_score = summary.split("@@@@@CF@@@@@")[1].split(', ').map(Number)
          console.log(confidence_score);
          confArr = confidence_score;

          // summaryArr: [Abstractive, Extractive, Keywords]
          summaryArr = summary_text.split("@@@@@AB@@@@@EX@@@@@");

          // Calculate trending keywords
          let top10_trending = [];
          var trending_sort = [];
          let new_keywords = summaryArr[2].split("@@@@@CD@@@@@AX@@@@@");
          for (var key in keyword_trends) {
            keyword_trends[key] *= 0.8;
          }
          let i = 5;
          for (key of new_keywords) {
            if (key in keyword_trends) {
              keyword_trends[key] += i;
            } else {
              keyword_trends[key] = i;
            }
            i--;
          }
          for (var key in keyword_trends) {
            trending_sort.push([key, keyword_trends[key]]);
          }
          trending_sort.sort(function (a, b) {
            return b[1] - a[1];
          });
          for (key of trending_sort.slice(0, 5)) {
            if (key[1] > 3) {
              top10_trending.push(key[0]);
            }
          }
          // summaryArr[3]: Trending keywords
          summaryArr.push(top10_trending.join("@@@@@CD@@@@@AX@@@@@"));
        }

        // Update room conversation log
        this.paragraphs[timestamp]["sum"] = {
          summaryArr: summaryArr,
          confArr: confArr,
        };
        this.addRoomLog();

        this.io.sockets
          .to(this.room_id)
          .emit("summary", summaryArr, confArr, speakerName, timestamp);
      })
      .catch((e) => {
        console.log("-----requestSummary(" + speakerName + ") ERROR-----")
        if (requestTrial < 5) {
          console.log("Try requestSummary again...");
          this.requestSummary(speakerId, speakerName, timestamp, requestTrial + 1)
        }
        else {
          console.log("Too many failed requests in requestSummary(" + speakerName + "): use default summary");
          let summaryArr = [paragraph, paragraph, "", ""];
          let confArr = [0, 0];

          this.io.sockets
            .to(this.room_id)
            .emit("summary", summaryArr, confArr, speakerName, timestamp);
        }
      });
  }

  updateParagraph(paragraph, timestamp, editor, editTimestamp, requestTrial) {
    let idx = this.requestSumIdx;
    this.requestSumIdx = ++this.requestSumIdx % this.sumPortCnt;
    let host = this.summarizerPorts[idx];

    let requestStartTime = new Date(Date.now()).toTimeString().split(' ')[0]
    console.log("-----updateParagraph(" + editor + ")-----");
    console.log("HOST: ", host)
    console.log("this.requestSumIdx: ", this.requestSumIdx)
    console.log("requestTrial: ", requestTrial)
    console.log("requestStartTime: ", requestStartTime)
    console.log("---updateParagraph(" + editor + ") request start...");

    axios
      .post(
        host,
        {
          type: "requestSummary",
          user: editor,
          content: paragraph,
        },
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      )
      .then((response) => {
        console.log("-----request updateParagraph(" + editor + ") at " + requestStartTime + " success-----")
        let summary, summaryArr;
        if (response.status === 200) {
          summary = response.data;
        }

        let confArr = [1, 1]; //Math.random();
        // No summary: just emit the paragraph with an indication that
        // it is not a summary (confidence === -1).
        if (!summary) {
          summaryArr = [paragraph, paragraph, "", ""];
          confArr = [0, 0];
        }
        else {
          console.log("[Summarizer result(" + editor + ")]", summary);

          // Parse returned summary
          let summary_text = summary.split("@@@@@CF@@@@@")[0];
          const confidence_score = parseFloat(summary.split("@@@@@CF@@@@@")[1]);
          confArr[0] = confidence_score;

          // summaryArr: [Abstractive, Extractive, Keywords, Trending Keywords]
          summaryArr = summary_text.split("@@@@@AB@@@@@EX@@@@@");
        }

        // Update room conversation log: content and summary
        let checkTimeStamp = timestamp.toString().split("@@@");
        if (checkTimeStamp[0] !== "summary-for-keyword") {
          this.paragraphs[timestamp]["editTrans"][editTimestamp] = {
            editor: editor,
            content: paragraph,
            sum: [summaryArr, confArr],
          };
          this.addRoomLog();
        }

        this.io.sockets
          .to(this.room_id)
          .emit("updateParagraph", paragraph, summaryArr, confArr, timestamp, editTimestamp);
      })
      .catch((e) => {
        console.log("-----request updateParagraph(" + editor + ") ERROR-----")
        if (requestTrial < 5) {
          console.log("Try updateParagraph again...");
          this.updateParagraph(paragraph, timestamp, editor, editTimestamp, requestTrial + 1)
        }
        else {
          console.log("Too many failed requests in updateParagraph(" + editor + "): use default summary");
          let summaryArr = [paragraph, paragraph, "", ""];
          let confArr = [0, 0];

          this.io.sockets
            .to(this.room_id)
            .emit("updateParagraph", paragraph, summaryArr, confArr, timestamp, editTimestamp);
        }
      });
  }

  updateSummary(type, content, timestamp, editTimestamp) {
    // console.log("CLERK:: ", type, content, timestamp, editTimestamp)
    if (type == "summary") {
      this.paragraphs[timestamp]["editSum"][editTimestamp] = {
        content: content,
      };
      this.addRoomLog();
    } else if (type == "pin") {
      if (this.paragraphs[timestamp]["pinned"]) {
        this.paragraphs[timestamp]["pinned"] = false;
      } else {
        this.paragraphs[timestamp]["pinned"] = true;
      }
    }
    this.io.sockets
      .to(this.room_id)
      .emit("updateSummary", type, content, timestamp, editTimestamp);
  }

  updateNotePad(content, userkey, updateTimestamp) {
    // console.log("Clerk.js", content, userkey);
    this.io.sockets.to(this.room_id).emit("updateNotePad", content, userkey, updateTimestamp);
  }

  startTimer(date) {
    console.log("DATE", date);

    const clockfilename = "./logs/" + this.room_name + "_" + this.room_id + "/STARTCLOCK.txt";
    fs.access(clockfilename, fs.F_OK, (err) => {
      if (err) {
        fs.appendFile(clockfilename, date.toString(), function (err) {
          if (err) throw err;
          console.log("[Log] Add timer log");
        });

        this.io.sockets.to(this.room_id).emit("startTimer", date);
        return;
      }
    });
  }

  /**
   * Save paragraph log on server.
   */
  addRoomLog() {
    const dir = 'logs/' + this.room_name + '_' + this.room_id;
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, {
        recursive: true
      });
    }

    // Construct new log file for room
    fs.appendFile(
      dir + "/transcript.txt",
      JSON.stringify(this.paragraphs) + "\n",
      function (err) {
        if (err) throw err;
        console.log("[Log] Add paragraph log");
      }
    );
  }

  addDelLog(ts, del, type) {
    const dir = 'delays/' + this.room_name + '_' + this.room_id;
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, {
        recursive: true
      });
    }

    let tmpJS = {}
    tmpJS[ts] = del
    fs.appendFile(
      dir + "/" + type + ".txt",
      JSON.stringify(tmpJS) + "\n",
      function (err) {
        if (err) throw err;
        console.log("[Log] Add " + type + " delay log")
      }
    )
  }
};
