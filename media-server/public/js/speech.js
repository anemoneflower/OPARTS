// recognition.js
// Streams audio into a moderator server (socket.io server).
// Defines methods and events to stream audio to be transcribed by
// Google Cloud Speech-to-text API.
// Reference: https://stackoverflow.com/questions/50976084/how-do-i-stream-live-audio-from-the-browser-to-google-cloud-speech-via-socket-io

// TODO: figure out a way to get the right host name.
const moderatorSocket = io(`https://${moderator_hostname}:${moderator_port}/`, {
  query: {
    room_id: room_id,
    room_name: room_name,
    user_name: user_name,
  },
});

const actorDir = '../College_fragment/';
const actorList = ['1_Bibek-Agree-1', '2_Marco-Disagree-4', '3_Bibek-Agree-1',
  '4_Marco-Disagree-4', '5_Bibek-Agree-1', '6_Anar-Disagree-8',
  '7_Marina-Agree-5', '8_Marco-Disagree-4', '9_Marina-Agree-5',
  '10_Marco-Disagree-4', '11_Cesar-Agree-2', '12_Braahmi-Disagree-3',
  '13_Hanhee-Agree-6', '14_Braahmi-Disagree-3', '15_Haneee-Agree-6',
  '16_Bibek-Agree-1', '17_Marina-Agree-5'];

// Stream Audio
let bufferSize = 2048,
  AudioContext,
  context,
  processor,
  input,
  globalStream,
  producer_id,
  track,
  stream,
  actors,
  actorTrack = null,
  actorName,
  audioDuration;

let mediaRecorder = null, currTimestamp = 0;

let AudioStreamer = {
  /**
   * @param {function} onData Callback to run on data each time it's received
   * @param {function} onError Callback to run on an error if one is emitted.
   */
  initRecording: function (stream, onError) {
    // Use `AudioContext` to send audio data for MS STT
    AudioContext = window.AudioContext || window.webkitAudioContext;
    context = new AudioContext();
    processor = context.createScriptProcessor(bufferSize, 1, 1);
    processor.connect(context.destination);
    context.resume();

    // Play audio file for simulation if the user_name matches
    if (user_name.includes("Agree") || user_name.includes("Disagree")) {
      startActing(0);
    }
    else {
      input = context.createMediaStreamSource(stream);
      input.connect(processor);
    }

    moderatorSocket.on("recognitionError", (error) => {
      if (onError) {
        onError("error");
      }
      // We don't want to emit another end stream event
      closeAll();
    });
  },

  stopRecording: function () {
    moderatorSocket.emit("endSimulation", user_name);
  },
};


function startActing(actoridx) {
  console.log(`startActing actor ${actoridx}: ${actorList[actoridx]}`);
  console.log(actorTrack);
  if (actorTrack !== null) {
    actorTrack.disconnect(context.destination);
    actorTrack.disconnect(processor);
    actorTrack = null;
    moderatorSocket.emit("endSimulation", actorName);
  }

  if (actoridx === actorList.length) {
    console.log("End Of Simulation!!");
    return
  }

  actorName = actorList[actoridx].split('_')[1]
  let filedir = actorDir + actorList[actoridx] + '.wav';

  var audioFile1 = fetch(filedir).then(response => response.arrayBuffer()).then(buffer => context.decodeAudioData(buffer)).then(buffer => {
    actorTrack = context.createBufferSource();
    audioDuration = buffer.duration;
    console.log(`Actor ${actorName}: ${audioDuration}s`);
    setTimeout(startActing, audioDuration * 1000, actoridx + 1);
    actorTrack.buffer = buffer;
    actorTrack.connect(context.destination);
    actorTrack.connect(processor);
    actorTrack.start(0);
  });

  moderatorSocket.emit("startSimulation", Date.now(), actorName);
  // TODO: use MediaRecorder API instead.
  processor.onaudioprocess = function (e) {
    microphoneProcess(e);
  };
}

/**
 * Start recording new audio on "startNewRecord".
 */
rc.on(RoomClient.EVENTS.startAudio, () => {
  console.log("RoomClient.EVENTS.startAudio");

  producer_id = rc.producerLabel.get(mediaType.audio);
  track = rc.producers.get(producer_id).track;
  stream = new MediaStream([track]);

  AudioStreamer.initRecording(stream,
    (data) => {
      console.log(data);
    },
    (err) => {
      console.log(err);
    });
});

rc.on(RoomClient.EVENTS.stopAudio, () => {
  AudioStreamer.stopRecording();
  closeAll();
});

//* Helper functions
/**
 * Processes microphone data into a data stream
 *
 * @param {object} e Input from the microphone
 */
function microphoneProcess(e) {
  var left = e.inputBuffer.getChannelData(0);
  var left16 = convertFloat32ToInt16(left);
  moderatorSocket.emit("binaryAudioData", left16);
}

/**
 * Converts a buffer from float32 to int16. Necessary for streaming.
 * sampleRateHertz of 1600.
 *
 * @param {object} buffer Buffer being converted
 */
function convertFloat32ToInt16(buffer) {
  let l = buffer.length;
  let buf = new Int16Array(l / 3);

  while (l--) {
    if (l % 3 === 0) {
      buf[l / 3] = buffer[l] * 0xffff;
    }
  }
  return buf.buffer;
}

/**
 * Stops recording and closes everything down. Runs on error or on stop.
 */
function closeAll() {
  console.log("CLOSEALL");
  // Clear the listeners (prevents issue if opening and closing repeatedly)
  moderatorSocket.off("recognitionError");

  if (processor) {
    if (input) {
      try {
        input.disconnect(processor);
      } catch (error) {
        console.warn("Attempt to disconnect input failed.");
      }
    }
    processor.disconnect(context.destination);
  }
  if (context) {
    context.close().then(function () {
      input = null;
      processor = null;
      context = null;
      AudioContext = null;
    });
  }
  if (mediaRecorder) {
    mediaRecorder.stop();
    mediaRecorder = null;
  }

  producer_id = null;
  track = null;
  stream = null;
}
