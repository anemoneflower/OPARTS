/**
 * audioFileHandler.js
 * Defines event listeners for transcripting and summarizing user audio streams.
 * References:
 * https://docs.microsoft.com/ko-kr/azure/cognitive-services/speech-service/get-started-speech-to-text?tabs=windowsinstall&pivots=programming-language-nodejs
*/

const { Writable } = require("stream");
const { clerks } = require("./global");

const fs = require("fs");

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
  let lastStopTimestamp = 0;

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

  /**
   * @param {String} type "startLogs" or "endLogs"
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
   * @param {RecognitionResult} data Recognition result from recognizer.recognized function
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

  function restartRecord(startTimestamp, timestamp, isLast) {
    if (endRecognition) {
      isLast = true;
      speechEnd = true;
    }

    // start new recording signal
    socket.emit("startNewRecord", startTimestamp);

    // stop recording signal
    let stopTimestamp = Date.now();
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
    lastStopTimestamp = stopTimestamp;
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
        if (e.result.reason === sdk.ResultReason.RecognizedSpeech) {
          let recogTime = Date.now();
          speechCallback(e.result);
          fs.appendFile(logDir + '/' + user_name + '.txt', "(" + (recogTime).toString() + ") SPEECH-RECOGNIZED\n", function (err) {
            if (err) console.log(err);
            console.log('[RECOG] log saved at ', recogTime);
          });
        } else {
          console.log(
            "ERROR: Speech was cancelled or could not be recognized. Ensure your microphone is working properly."
          );
        }
      }
    };

    // Event handler for speech stopped events.
    recognizer.speechEndDetected = async (s, e) => {
      const endTime = new Date();
      console.log("  ", endTime.toTimeString().split(' ')[0], "Speech End Detected from user <", user_name, ">");
      // console.log(e)

      if (speechEnd) {
        console.log("    Already processed speech!")
        return;
      }
      speechEnd = true;

      let { ts, isLast, _newLast } = await clerks.get(room_id).getMsgTimestamp(socket.id, user_name, getLastTimestamp("startLogs"), true);

      console.log("SPEECH END: islast - ", isLast);

      restartRecord(endTime.valueOf(), ts, isLast);
      fs.appendFile(logDir + '/' + user_name + '.txt', "(" + (endTime.valueOf()).toString() + ") SPEECH-END\n", function (err) {
        if (err) console.log(err);
        console.log('[END] log saved at ', endTime.valueOf());
      });
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

      timestamps[curTimestamp]["startLogs"].push([startTime]);
      speechEnd = false;

      console.log("  ", new Date(startTime).toTimeString().split(' ')[0], "Speech Start Detected from user <", user_name, ">\n startTime: ", startTime);

      fs.appendFile(logDir + '/' + user_name + '.txt', "(" + (startTime).toString() + ") SPEECH-START\n", function (err) {
        if (err) console.log(err);
        console.log('[START] log saved at ', startTime);
      });
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
  socket.on("startTimer", (date) => {
    clerks.get(room_id).startTimer(date);
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
    lastStopTimestamp = 0;
    speechEnd = true;

    // Start ms STT service
    startStream();
  });

  /**
   * Event listener for `binaryAudioData` event.
   * Send audio stream data to microsoft STT server
   * 
   * @param data audio stream data from `media-server/speech.js` file
   * @param timestamp timestamp for specify record time and file name
   */
  socket.on("binaryAudioData", (data) => {
    audioInputStreamTransform.write(data);
  });

  /**
   * Event listener for `streamAudioData` event.
   * Record audio data from `media-server/speech.js`.
   * 
   * @param {mediaRecoder data} data Audio data from mediarecorder in user's browser
   * @param {Number} timestamp Timestamp where audio recording starts
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
