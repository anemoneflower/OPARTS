/**
 * audioFileHandler.js
 * Defines event listeners for transcripting and summarizing user audio streams.
 * References:
 * https://docs.microsoft.com/ko-kr/azure/cognitive-services/speech-service/get-started-speech-to-text?tabs=windowsinstall&pivots=programming-language-nodejs
*/

const { Writable } = require("stream");
const { clerks } = require("./global");

const fs = require("fs");

const axios = require("axios");
const config = require("./config");

// Microsoft Azure Speech
const sdk = require("microsoft-cognitiveservices-speech-sdk");
const { subKey, servReg } = require("./config");
const { time } = require("console");
const speechConfig = sdk.SpeechConfig.fromSubscription(subKey, servReg);
speechConfig.speechRecognitionLanguage = "en-US";

module.exports = function (io, socket) {
  // Variables for using Microsoft Azure STT service
  let pushStream = null;
  let audioConfig = null;
  let recognizer = null;
  const { room_id, room_name, user_name } = socket.handshake.query;
  let logDir = 'logs/' + room_name + '_' + room_id;

  /**
   * Dictionary for logging timestamp
   * 
   * key: timestamp from "startRecognition" socket message
   * value: { "init": time when `startContinuousRecognitionAsync` function started,
   *          "startLogs": [ [start recognition timestamp, recognizied timestamps], ... ]
   *          "endLogs": end recognition timestamps }
   */
  let timestamps = {};

  // Current timestamp section for MS STT
  let curTimestamp = 0;

  // Current record timestamp
  let curRecordTimestamp = 0;

  // Mark speech already end
  let speechEnd = true;

  // Mark recognition end 
  let endRecognition = true;

  /**
   * Audio file lists from each user
   * 
   * key: timestamp from "streamAudioData" socket message
   * value: filename(string) used to access file
   */
  let audiofiles = [];

  let interval = null;
  let currentInterval = 0;

  let silencePort = config.summaryHost_1 + config.silencePort;

  /**
   * @param {String} type: "startLogs" or "endLogs"
   * @returns Last element of corresponding type in timestamps[curTimestamp]
   */
  function getLastTimestamp(type) {
    let len = timestamps[curTimestamp][type].length
    if (len == 0) {
      return 0
    }
    return timestamps[curTimestamp][type][len - 1]
  }

  //* Send audio stream into microsoft STT server
  /**
   * Callback to be called when a response (transcript) arrives from API.
   * @param {RecognitionResult} data: Recognition result from recognizer.recognized function
   */
  const speechCallback = async (data) => {
    let clerk = clerks.get(room_id);

    let transcript = data.text;
    let timestamp = getLastTimestamp("startLogs");

    if (timestamp) {
      timestamps[curTimestamp]["startLogs"][timestamps[curTimestamp]["startLogs"].length - 1].push(Date.now())
      timestamp = getLastTimestamp("startLogs");
    }

    // Clerk accumulates these full sentences ("final" results)
    console.log(`${new Date(Number(timestamp[0]))}(${user_name}): ${transcript}`);

    // Calculate current timestamp
    let { ts, isLast, newLast } = await clerk.getMsgTimestamp(socket.id, user_name, timestamp, false);
    if (!ts) return;

    // Split audio file when split message box
    if (isLast) {
      // console.log("ts vs timestamp: ", ts, timestamp, new Date(Number(ts)))
      restartRecord(newLast, ts, isLast);
    }

    // Update temporary messagebox
    clerk.tempParagraph(socket.id, user_name, transcript, ts);
  };

  /**
   * Send socket message to start recording new audio file and finish current recording.
   * @param {Number} startTimestamp: timestamp for mark new audio file's timestamp
   * @param {Number} timestamp: timestamp for finished speech
   * @param {Boolean} isLast: check if this is finished speech
   */
  function restartRecord(startTimestamp, timestamp, isLast) {
    if (endRecognition) {
      isLast = true;
      speechEnd = true;
    }

    // start new recording signal
    socket.emit("startNewRecord", startTimestamp);

    // stop recording signal
    socket.emit("stopCurrentRecord");

    // request Summary
    if (isLast) {
      try {
        clerks.get(room_id).requestSummary(socket.id, user_name, timestamp, 1);
      }
      catch (e) {
        console.log("[RESTART RECORD] ERR: ", e)
      }
    }

    curRecordTimestamp = startTimestamp;
  }

  /**
   * Start audio recognition stream using recognizer and setup related event handlers.
   */
  function startStream() {
    // Create audioConfig for get audio input for stream
    pushStream = sdk.AudioInputStream.createPushStream();
    audioConfig = sdk.AudioConfig.fromStreamInput(
      pushStream,
      sdk.AudioStreamFormat.getDefaultInputFormat()
    );

    // Define recognizer
    // Document: https://docs.microsoft.com/ko-kr/javascript/api/microsoft-cognitiveservices-speech-sdk/speechrecognizer?view=azure-node-latest#recognized
    recognizer = new sdk.SpeechRecognizer(speechConfig, audioConfig);

    // The event recognized signals that a final recognition result is received.
    // TODO: Leave recognized log at server
    recognizer.recognized = (s, e) => {
      if (e.result.reason === sdk.ResultReason.NoMatch) {
        const noMatchDetail = sdk.NoMatchDetails.fromResult(e.result);
        console.log(
          "    (recognized NoMatch)  Reason: " + sdk.NoMatchReason[noMatchDetail.reason]
        );
      } else {
        if (e.result.reason !== sdk.ResultReason.RecognizedSpeech) {
          console.log(
            "ERROR: Speech was cancelled or could not be recognized. Ensure your microphone is working properly."
          );
        } else {
          if (e.result.text == '') {
            console.log(
              "    (recognized Speech)  empty speech"
            );
            return;
          }
          let recogTime = Date.now();
          if (speechEnd) {
            const startTime = Date.now();
            console.log("  ", new Date(startTime).toTimeString().split(' ')[0], "Speech Start Manually Detected from user <", user_name, ">\n startTime: ", startTime);

            speechStartHandler(startTime, true);
          }

          speechCallback(e.result);
          fs.appendFile(logDir + '/' + user_name + '.txt', "(" + (recogTime).toString() + ") SPEECH-RECOGNIZED\n", function (err) {
            if (err) console.log(err);
            console.log('[RECOG] log saved at ', recogTime);
          });
        }
      }
    };

    // Event handler for speech stopped events.
    recognizer.speechEndDetected = (s, e) => {
      const endTime = Date.now();
      console.log("  ", new Date(endTime).toTimeString().split(' ')[0], "Speech End Detected from user <", user_name, ">");
      // console.log(e)

      if (speechEnd) {
        console.log("    Already processed speech!")
        return;
      }

      speechEndHandler(endTime, false);
    };

    // Event handler for speech started events.
    // TODO: Leave speech start detected log at server
    recognizer.speechStartDetected = (s, e) => {
      if (!speechEnd) {
        console.log("  ", new Date().toTimeString().split(' ')[0], "Speech Start Detected (Duplicate) from user <", user_name, ">",);
        return;
      }
      // Save speech start timestamp
      const startTime = Date.now();
      console.log("  ", new Date(startTime).toTimeString().split(' ')[0], "Speech Start Detected from user <", user_name, ">\n startTime: ", startTime);

      speechStartHandler(startTime, false);
    };

    // The event canceled signals that an error occurred during recognition.
    // TODO: Leave canceled log at server
    recognizer.canceled = (s, e) => {
      console.log(`CANCELED: Reason=${e.reason}`);

      if (e.reason == CancellationReason.Error) {
        console.log(`"CANCELED: ErrorCode=${e.errorCode}`);
        console.log(`"CANCELED: ErrorDetails=${e.errorDetails}`);
        console.log("CANCELED: Did you update the subscription info?");
      }
    };

    // Event handler for session stopped events.
    // TODO: Leave session stopped log at server
    recognizer.sessionStopped = (s, e) => {
      console.log("  ", new Date().toTimeString().split(' ')[0], "  Session stopped event.");
    };

    // Starts speech recognition, until stopContinuousRecognitionAsync() is called.
    // TODO: Leave start recognition log at server
    recognizer.startContinuousRecognitionAsync(
      () => {
        timestamps[curTimestamp]["init"] = Date.now();
        console.log(timestamps[curTimestamp]["init"])
        console.log("Recognition started");
      },
      (err) => {
        console.trace("err - " + err);
        recognizer.close();
      }
    );
  }

  // Closes recognition stream.
  function stopStream() {
    if (recognizer) {
      // Stops continuous speech recognition.
      // TODO: Leave end recognition log at server
      recognizer.stopContinuousRecognitionAsync();
    }

    // Initialize values
    pushStream = null;
    audioConfig = null;
    recognizer = null;

    console.log(`Recognition from ${user_name} ended.`);
  }

  /**
   * Request silence detection to silence detection server.
   * @param {Number} timestamp: timestamp for distinguishing a current recording audio file
   * @param {Number} requestTimestamp: timestamp for leave log for current requset timestamp
   */
  function requestSilence(timestamp, requestTimestamp) {
    let requestStartTime = Date.now();
    let host = silencePort;

    console.log("-----requestSilence(" + user_name + ")-----")
    console.log("HOST: ", host)
    console.log("requestStart: ", requestStartTime)
    console.log("timestamp: ", new Date(timestamp).toTimeString().split(' ')[0])
    console.log("requestTimestamp: ", new Date(requestStartTime).toTimeString().split(' ')[0])
    console.log("---requestKeyword(" + user_name + ") start...");

    axios.post(
      host,
      {
        type: "requestAudio",
        dir: room_name + "_" + room_id,
        requestTimestamp: requestTimestamp,
        timestamp: timestamp,
        speaker: user_name,
      },
      {
        header: { "Content-Type": "multipart/form-data" },
      }
    ).then((response) => {
      let requestSuccess = Date.now();
      console.log("-----requestSilence(" + user_name + ") at " + requestStartTime + " success-----");
      console.log("Time spent: ", (requestSuccess - requestStartTime) / 1000);
      console.log("result: ", response.data);

      // Add delay log
      clerks.get(room_id).addDelLog(timestamp, (requestSuccess - requestStartTime) / 1000, "Silence");

      let isSilence = response.data.split("@@")[1];
      if (isSilence == "true") {
        console.log("timestamp: ", new Date(timestamp).toTimeString().split(' ')[0]);
        console.log("requestSuccess: ", new Date(requestSuccess).toTimeString().split(' ')[0]);

        const endTime = Date.now();
        console.log("  ", new Date(endTime).toTimeString().split(' ')[0], "Speech End Detected Manually for user <", user_name, ">");

        if (speechEnd) {
          console.log("    Already processed speech!")
          return;
        }

        speechEndHandler(endTime, true);
      }
    }).catch((e) => {
      console.log("-----requestSilence(" + user_name + ") ERROR-----");
      console.log("Pass this interval", requestTimestamp, "for timestamp", timestamp)
    })
  }

  /**
   * Set up speech-related variables when speech start detected.
   * @param {Number} startTime: timestamp when speech start detected
   * @param {Boolean} isManual: is this function call due to manually detected start signal?
   */
  function speechStartHandler(startTime, isManual) {
    timestamps[curTimestamp]["startLogs"].push([startTime]);
    speechEnd = false;

    let manual = isManual ? "-M" : "";
    fs.appendFile(logDir + '/' + user_name + '.txt', "(" + (startTime).toString() + ") SPEECH-START" + manual + "\n", function (err) {
      if (err) console.log(err);
      console.log('[START] log saved at ', startTime);
    });
  }

  /**
   * Cleanup speech-related variables when speech end detected.
   * @param {Number} endTime: timestamp when speech end detected
   * @param {Boolean} isManual: is this function call due to manually detected end signal?
   */
  async function speechEndHandler(endTime, isManual) {
    speechEnd = true;
    chunks = [];
    if (interval) {
      clearInterval(interval);
      interval = null;
      currentInterval = 0;
    }

    let { ts, isLast, _newLast } = await clerks.get(room_id).getMsgTimestamp(socket.id, user_name, getLastTimestamp("startLogs"), true);

    console.log("SPEECH END: islast - ", isLast);

    restartRecord(endTime, ts, isLast);

    let manual = isManual ? "-M" : "";
    fs.appendFile(logDir + '/' + user_name + '.txt', "(" + (endTime).toString() + ") SPEECH-END" + manual + "\n", function (err) {
      if (err) console.log(err);
      console.log('[END] log saved at ', endTime);
    });
  }

  /** 
   * Interface between input audio stream and recognition stream.
   * Acts as a buffer to smoothe out restarts of recognize stream.
   */
  const audioInputStreamTransform = new Writable({
    write(chunk, encoding, next) {
      if (pushStream) {
        pushStream.write(chunk);
      }

      next();
    },

    final() {
      if (pushStream) {
        pushStream.close();
      }
    },
  });

  //* Socket event listeners
  /**
   * Event listener for `updateParagraph` event.
   * Send `updateParagraph` request to clerks.
   */
  socket.on("updateParagraph", (paragraph, timestamp, editor, editTimestamp) => {
    clerks.get(room_id).updateParagraph(paragraph, timestamp, editor, editTimestamp, 1);
  })

  /**
   * Event listener for `updateSummary` event.
   * Send `updateSummary` request to clerks.
   */
  socket.on("updateSummary", (type, content, timestamp, editTimestamp) => {
    clerks.get(room_id).updateSummary(type, content, timestamp, editTimestamp);
  })

  /**
   * Event listener for `updateNotePadToSocket` event.
   * Send `updateNotePad` request to clerks.
   */
  socket.on("updateNotePadToSocket", (content, userkey, updateTimestamp) => {
    // console.log("audioFileHandler.js", updateTimestamp);
    clerks.get(room_id).updateNotePad(content, userkey, updateTimestamp);
  })

  /**
   * Event listener for `startTimer` event.
   * Send `startTimer` request to clerks.
   */
  socket.on("startTimer", (date, condition) => {
    clerks.get(room_id).startTimer(date, condition);
  })

  /**
   * Event listener for `startRecognition` event.
   * Initialize recognition variables and start STT recognition stream.
   */
  socket.on("startRecognition", (timestamp) => {
    endRecognition = false;
    console.log(
      `Recognition starting by ${user_name} in ${room_id}`
    );

    // Leave timestamp log for further use
    // PIN: timestamp def
    timestamps[timestamp] = { "init": 0, "startLogs": [], "endLogs": [] }
    curTimestamp = timestamp;
    audiofiles = [];

    curRecordTimestamp = 0;
    speechEnd = true;

    // Start ms STT service
    startStream();
  });

  /**
   * Event listener for `binaryAudioData` event.
   * Send audio stream data to microsoft STT server
   * 
   * @param data: audio stream data from `media-server/speech.js` file
   */
  socket.on("binaryAudioData", (data) => {
    audioInputStreamTransform.write(data);
  });

  /**
   * Event listener for `streamAudioData` event.
   * Record audio data from `media-server/speech.js`.
   * 
   * @param {mediaRecoder data} data: Audio data from mediarecorder in user's browser
   * @param {Number} timestamp: Timestamp where audio recording starts
   * 
   */
  socket.on("streamAudioData", (data, timestamp) => {
    // Check if room dir exist and make if not exist.
    const dir = './webm/' + room_name + "_" + room_id;
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, {
        recursive: true
      });
    }

    // Record audio files in webm format
    let filename = dir + "/" + user_name + "_" + timestamp + ".webm";
    let filestream = fs.createWriteStream(filename, { flags: 'a' });
    filestream.write(Buffer.from(new Uint8Array(data)), (err) => {
      if (err) throw err;
    })
    filestream.close();

    // Update `audiofiles`
    if (!audiofiles.includes(timestamp)) {
      audiofiles.push(timestamp);

      if (curRecordTimestamp == 0) {
        curRecordTimestamp = timestamp
      }

      // TODO: Leave new file log at server
    }

    if (!speechEnd) {
      if (!interval) {
        console.log("[SILENCE] Set Silence Detect Request Interval for user <", user_name, ">");
        interval = setInterval(() => {
          requestSilence(timestamp, currentInterval);
          currentInterval = Date.now();
        }, 2500);
      }

      if (currentInterval == 0) currentInterval = Date.now();
      console.log("[SILENCE] Update silence audio for user <", user_name, "> and interval", currentInterval);
    }
  })

  /**
   * Stop speech recognition stream when user closes the audio.
   */
  socket.on("endRecognition", () => {
    console.log("endRecognition from: ", user_name);
    endRecognition = true;
    stopStream();
  });

  /**
   * Stop speech recognition stream and stop restarting it on disconnection.
   */
  socket.on("disconnect", () => {
    stopStream();
    console.log(`${user_name} leaved room ${room_name} (${room_id})`);
  });
};
