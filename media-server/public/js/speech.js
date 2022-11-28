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
  '4_Marco-Disagree-4', '5_Bibek-Agree-1', '6_Anar-Disagree-8', '7_Anar-Disagree-8',
  '8_Marina-Agree-5', '9_Marina-Agree-5', '10_Marco-Disagree-4', '11_Marco-Disagree-4', '12_Marina-Agree-5',
  '13_Marco-Disagree-4', '14_Cesar-Agree-2', '15_Cesar-Agree-2', '16_Cesar-Agree-2', '17_Braahmi-Disagree-3', '18_Braahmi-Disagree-3',
  '19_Hanhee-Agree-6', '20_Hanhee-Agree-6', '21_Braahmi-Disagree-3', '22_Braahmi-Disagree-3', '23_Haneee-Agree-6',
  '24_Bibek-Agree-1', '25_Bibek-Agree-1', '26_Marina-Agree-5'];

const tutorialActorDir = '../Game_tutorial/'
const tutorialActorList = ['1_Cesar-Agree-2', '2_Marina-Agree-5', '3_Bibek-Agree-1', '4_Marco-Disagree-4']

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
    if (user_name.includes("Agree") || user_name.includes("Disagree") || user_name.includes("tutorial")) {
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
    moderatorSocket.emit("endSimulation", user_name, 0);
  },
};


function startActing(actoridx) {
  let curactorList, curactorDir;
  if (user_name.includes("tutorial")) {
    curactorList = tutorialActorList;
    curactorDir = tutorialActorDir;
  }
  else {
    curactorList = actorList;
    curactorDir = actorDir;
  }

  console.log(`startActing actor ${actoridx}: ${curactorList[actoridx]}`);
  console.log(actorTrack);
  if (actorTrack !== null) {
    if (!user_name.includes("tutorial")){
      actorTrack.disconnect(context.destination);
    }
    actorTrack.disconnect(processor);
    actorTrack = null;
    moderatorSocket.emit("endSimulation", actorName, actoridx);
  }

  if (actoridx === curactorList.length) {
    console.log("End Of Simulation!!");
    return
  }

  actorName = curactorList[actoridx].split('_')[1]
  let filedir = curactorDir + curactorList[actoridx] + '.wav';

  var audioFile1 = fetch(filedir).then(response => response.arrayBuffer()).then(buffer => context.decodeAudioData(buffer)).then(buffer => {
    actorTrack = context.createBufferSource();
    audioDuration = buffer.duration;
    console.log(`Reserve actor ${actorName} ${actoridx}: ${audioDuration}s`);
    setTimeout(startActing, audioDuration * 1000, actoridx + 1);
    actorTrack.buffer = buffer;
    if (!user_name.includes("tutorial")){
      actorTrack.connect(context.destination);
    }
    actorTrack.connect(processor);
    actorTrack.start(0);
  });

  moderatorSocket.emit("startSimulation", Date.now(), actorName, actoridx + 1);
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
