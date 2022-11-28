// transcript.js
// Defines event handlers for transcripts from moderator server.
// Includes UI control on transcription and summary data arrival.

const messages = document.getElementById("messages");

const BoxColor = {
  MySure: "rgba(255, 229, 143, 0.5)",
  OtherSureSummary: "rgba(40, 167, 70, 0.3)",
  OtherSureTranscript: "rgba(40, 70, 167, 0.3)",
  Unsure: "rgba(117, 117, 117, 0.3)",
  GenMySure: "rgba(255, 229, 143, 0.3)",
  GenOtherSureSummary: "rgba(40, 167, 70, 0.1)",
  GenOtherSureTranscript: "rgba(40, 70, 167, 0.1)"
}

const TextColor = {
  Normal: "rgba(0, 0, 0, 1)",
  Unsure: "rgba(210, 70, 70, 1)",
  Generating: "rgba(0, 0, 0, 0.6)"
}

const PanelMode = {
  Summary: {
    Summary: 1,
    Transcript: 3
  },
  Transcript: {
    Summary: 3,
    Transcript: 1
  }
}

const CONFIDENCE_LIMIT = 0.5;

moderatorSocket.on("startTimer", onStartTimer);
moderatorSocket.on("startVoiceProcessing", onStartVoiceProcessing);
moderatorSocket.on("startPlay", onStartPlay);

moderatorSocket.on("restore", onRestore);
moderatorSocket.on("transcript", onTranscript);
moderatorSocket.on("summary", onSummary);
moderatorSocket.on("keyword", onKeyword);

moderatorSocket.on("updateParagraph", onUpdateParagraph);
moderatorSocket.on("updateSummary", onUpdateSummary);

moderatorSocket.on("removeMsgBox", removeMsg);

var notiAudio = new Audio("../img/notification.mp3");
var keywordMap = {};
var keywordParagraph = "";
let scrollPos = 0;
var isScrolling;
var subtaskPopup;
var mapPopup;
var subtaskTryCnt = 1;
let tempAnswers = [];

// Audio Start Timestamp
var audioStart = null;
//speakerTriggers: [[speakerName, timing, on/off (True,False), isDone], ... ] start from the back
let speakerTriggers = [
  ["Marina", -0.25, false, false],
  ["Marina", 1.05, true, false],
  ["Bibek", 1.05, false, false],    
  ["Hanhee", 2.45, false, false],
  ["Bibek", 2.46, true, false],
  ["Hanhee", 3.6, true, false],     
  ["Braahmi", 3.61, false, false],
  ["Hanhee", 5.07, false, false],
  ["Braahmi", 5.08, true, false],
  ["Braahmi", 6.26, false, false],
  ["Hanhee", 6.33, true, false],
  ["Braahmi", 7.7, true, false],
  ["Cesar", 7.72, false, false], 
  ["Cesar", 9.95, true, false],
  ["Marco", 9.95, false, false],  
  ["Marco", 10.43, true, false],
  ["Marina", 10.43, false, false],
  ["Marco", 10.70, false, false],
  ["Marina", 10.72, true, false],
  ["Marco", 12.68, true, false],
  ["Marina", 12.68, false, false],
  ["Marina", 14.28, true, false],
  ["Anar", 14.3, false, false],
  ["Bibek", 15.86, false, false],
  ["Anar", 15.88, true, false],
  ["Bibek", 16.93, true, false],
  ["Marco", 16.93, false, false],
  ["Marco", 17.78, true, false],
  ["Bibek", 17.81, false, false],
  ["Bibek", 17.92, true, false],
  ["Marco", 17.95, false, false],
  ["Marco", 18.8, true, false],
  ["Bibek", 18.83, false, false],
  ["Bibek", 20, true, false]
];

// SUBTASK MODAL
var modal = document.getElementById("subtaskModal");
var close_modal = document.getElementsByClassName("closeModal")[0];
var isTriggered = false;

// multitasking text index
var mtidx = 0;

let mul_sentences = null;

// close_modal.onclick = function () {
//   modal.style.display = "none";
// };
// window.onclick = function (event) {
//   if (event.target == modal) {
//     modal.style.display = "none";
//   }
// };

// VIDEO POP UP
// var for timing
var v1s = 0;
var v1e = 0;
var v2s = 0;
var v2e = 0;
var v3s = 0;
var v3e = 0;
var v4s = 0;
var v4e = 0;
var tp = 0;   //1 for game  / 2 for college
var isOverlayPossible = true

/************************************************************************************************
 * Timer & Subtask Related Functions
************************************************************************************************/
function onVideoPop() {
  //overlay_off();
  modal.style.display = "block";
  isOverlayPossible = false;
  notiAudio.play()
  document.getElementById("left-navbar").style.transform = "translateY(100%)";
  return 0
}

function offVideoPop() {
  modal.style.display = "none";
  isOverlayPossible = true;
  document.getElementById("left-navbar").style.transform = "translateY(0)";
  return 0
}

function speakerStart(speakerName) {
  document.getElementById('speaker_' + speakerName).setAttribute("class", "speakerSpeaking")
  console.log(speakerName, "start speaking")
}

function speakerEnd(speakerName) {
  document.getElementById('speaker_' + speakerName).setAttribute("class", "speakerNotSpeaking")
  console.log(speakerName, "stop speaking")
}


const countDownTimer = function (id, date, word) {
  var _vDate = new Date(date); // 전달 받은 일자
  var _second = 1000;
  var _minute = _second * 60;
  var _hour = _minute * 60;
  var _day = _hour * 24;
  var timer;

  function showRemaining() {
    var now = new Date();
    var distDt = _vDate - now;
    if (distDt < 0) {
      clearInterval(timer);
      document.getElementById(id).textContent = word;
      document.getElementById("subtask").setAttribute("disabled", "disabled");
      return;
    }

    var minutes = Math.floor((distDt % _hour) / _minute);
    var seconds = Math.floor((distDt % _minute) / _second);

    // Time remaining for the meeting
    if (id == "meeting-timer") {
      document.getElementById(id).innerHTML =
        "<i class='fas fa-hourglass-start'></i> " + word + " (" + minutes + "m " + seconds + "s)";

      if (distDt < 5 * 60 * 1000) {
        document.getElementById(id).style.color = "red";
      } else if (distDt < 10 * 60 * 1000) {
        document.getElementById(id).style.color = "blue";
      }

      if (audioStart) {
        distDt = audioStart + 20 * 60 * 1000 - now
        for (var tmpTrigger of speakerTriggers) {         //tmpTrigger [speakerName, timing, on/off (True,False), isDone]
          if (distDt < tmpTrigger[1] * 60 * 1000) {
            if (tmpTrigger[3]) {
              break
            }
            if (tmpTrigger[2]) {
              speakerStart(tmpTrigger[0])
            } else {
              speakerEnd(tmpTrigger[0])
            }
            tmpTrigger[3] = true
          }
        }
      }
    }
    // Time remaining for starting subtask
    else {
      // if (distDt < 25 * 60 * 1000) {
      //   document.getElementById(id).textContent =
      //     word + " (" + minutes + "m " + seconds + "s)";
      //   document.getElementById(id).removeAttribute("disabled");
      //   if (!isTriggered) {
      //     modal.style.display = "block";
      //     isTriggered = true;
      //   }
      // }
    }
    if (audioStart) {
      distDt = audioStart + 20 * 60 * 1000 - now
      if (distDt < v4e * 60 * 1000) {
        if (v4e != 0) {
          console.log('voo', audioStart)
          console.log('voff v4e', distDt, '-', v4e)
          v4e = offVideoPop();
        }
      } else if (distDt < v4s * 60 * 1000) {
        if (v4s != 0) {
          console.log('von v4s', distDt, '-', v4s)
          v4s = onVideoPop();
        }
      } else if (distDt < v3e * 60 * 1000) {
        if (v3e != 0) {
          console.log('voff v3e', distDt, '-', v3e)
          v3e = offVideoPop();
        }
      } else if (distDt < v3s * 60 * 1000) {
        if (v3s != 0) {
          console.log('von v3s', distDt, '-', v3s)
          v3s = onVideoPop();
        }
      } else if (distDt < v2e * 60 * 1000) {
        if (v2e != 0) {
          console.log('voff v2e', distDt, '-', v2e)
          v2e = offVideoPop();
        }
      } else if (distDt < v2s * 60 * 1000) {
        if (v2s != 0) {
          console.log('von v2s', distDt, '-', v2s)
          v2s = onVideoPop();
        }
      } else if (distDt < v1e * 60 * 1000) {
        if (v1e != 0) {
          console.log('voff v1e', distDt, '-', v1e)
          v1e = offVideoPop();
        }
      } else if (distDt < v1s * 60 * 1000) {
        if (v1s != 0) {
          console.log('von v1s', distDt, '-', v1s)
          v1s = onVideoPop();
        }
      }
    }
  }
  timer = setInterval(showRemaining, 1000);
};

function onStartTimer(startTime, condition) {
  startTime = new Date(startTime);
  let usernumber = parseInt(
    user_name.slice(user_name.length - 1, user_name.length)
  );
  console.log("onStartTimer()", startTime, "USER-NUMBER", usernumber);

  if (!isNaN(usernumber) && condition != "N") {
    // PARTICIPANTS, NOT ADMIN
    // Users can start subtask anytime
    let startsubtask = 30;

    console.log("PARTICIPANTS", user_name, "SUB-TASK START AT", startsubtask);
    countDownTimer(
      "subtask",
      startTime.getTime() + startsubtask * 60 * 1000,
      "Start Subtask"
    );
  }

  countDownTimer(
    "meeting-timer",
    startTime.getTime() + 30 * 60 * 1000,
    "Remaining Time"
  );

}

function onStartVoiceProcessing() {
  console.log("onStartVoiceProcessing()", user_name);

  // Start actor's voice stream input by start audio
  if (user_name.includes("Agree") || user_name.includes("Disagree") || user_name.includes("tutorial")) {
    rc.produce(RoomClient.mediaType.audio, document.getElementById('audio-select').value);
    rc.addUserLog(Date.now(), 'AUDIO-ON\n');
  }
  
  if (user_name.includes("cpsAdmin") || user_name.includes("tutorial")) {
    rc.waitVoiceProcessing();
  }
}

function onStartPlay() {
  console.log("onStartPlay()", user_name);
  if (!user_name.includes("Agree") && !user_name.includes("Disagree")) {
    // Play whole meeting conversation
    if (room_name.includes("College")) {
      playFile('../College/0511_N_S_College.mp3');
    }
    else { // Game
      playFile('../Game_tutorial/Game_tutorial.mp3');
    }

    audioStart = Date.now();
    console.log(audioStart)
  }
}

function playFile(file) {
  var audio = document.createElement('audio');
  audio.src = file;
  document.body.appendChild(audio);
  audio.play();

  audio.onended = function () {
    this.parentNode.removeChild(this);
  }
}

// Open popup for subtask
function openSubtask() {
  rc.addUserLog(Date.now(), "OPEN-SUBTASK\n");
  subtaskPopup = window.open(
    "../subtask.html",
    "_blank",
    "toolbar=yes,scrollbars=yes,resizable=yes,top=100,left=100,width=1200,height=1000"
  );
  subtaskPopup.onbeforeunload = function () {
    //overlay_off();
    rc.addUserLog(Date.now(), "CLOSE-SUBTASK\n");
  };
}

function overlay_on() {
  if (isOverlayPossible) {
    document.getElementById("overlay").style.display = "block";
    document.getElementById("left-navbar").style.transform = "translateY(100%)";
  }
}

function overlay_off() {
  if (isOverlayPossible) {
    document.getElementById("overlay").style.display = "none";
    document.getElementById("left-navbar").style.transform = "translateY(0)";
  }
}

// Submit answers for subtask
function onSubmitAnswer(answers) {
  rc.addUserLog(
    Date.now(),
    "SUBTASK-ANSWER/TRY-CNT=" + subtaskTryCnt + "/MSG=" + answers + "\n"
  );
  console.log("SUBTASK ANSWER_TRY" + subtaskTryCnt + "=" + answers);
  subtaskTryCnt++;
  tempAnswers = [];
}

// Save answers temporarily
function onSaveAnswer(answers) {
  rc.addUserLog(Date.now(), "SAVE-TEMP-ANSWERS\n");
  // console.log("SAVE TEMP ANSWERS");
  tempAnswers = answers;
}

function onRestore(past_paragraphs) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  console.log("onRestore: Restore past paragraphs");
  for (var timestamp in past_paragraphs) {
    let messageBox = getMessageBox(timestamp);
    if (messageBox) continue;

    let datas = past_paragraphs[timestamp];

    // Restore past paragraphs
    messageBox = createMessageBox(datas["speakerName"], timestamp);

    let transcript, summaryArr, confArr, speaker, hasSummary;
    let newsum = "";

    if (Object.keys(datas["editTrans"]).length === 0) {
      transcript = datas["ms"].join(" ");

      if (Object.keys(datas["sum"]).length === 0) hasSummary = false;
      else {
        hasSummary = true;
        summaryArr = datas["sum"]["summaryArr"];
        confArr = datas["sum"]["confArr"];
        speaker = datas["speakerName"];
      }
    } else {
      var lastKey = Object.keys(datas["editTrans"])[
        Object.keys(datas["editTrans"]).length - 1
      ];
      transcript = datas["editTrans"][lastKey]["content"];

      hasSummary = true;
      summaryArr = datas["editTrans"][lastKey]["sum"][0];
      confArr = datas["editTrans"][lastKey]["sum"][1];
      speaker = datas["speakerName"];
    }

    if (Object.keys(datas["editSum"]).length !== 0) {
      var lastKey = Object.keys(datas["editSum"])[
        Object.keys(datas["editSum"]).length - 1
      ];
      newsum = datas["editSum"][lastKey]["content"];
      // remove deleted paragraphs
      if (newsum === "") {
        messageBox.remove();
        continue;
      }
    }

    // Append the new transcript to the old paragraph.
    let summaryBox = messageBox.childNodes[mode.Summary];
    summaryBox.childNodes[1].textContent = ">> Generating transcript... <<";
    summaryBox.childNodes[2].textContent = transcript;

    let paragraphBox = messageBox.childNodes[mode.Transcript];
    paragraphBox.childNodes[1].textContent = ">> Generating transcript... <<";
    paragraphBox.childNodes[2].textContent = transcript;

    // remove deleted paragraphs
    if (!transcript) {
      messageBox.remove();
      continue;
    }

    if (hasSummary) {
      onSummary(summaryArr, confArr, speaker, timestamp);
    }

    if (newsum !== "") {
      onUpdateSummary("summary", newsum, timestamp, lastKey);
    }

    // Restore pinned message box
    if (datas["pinned"]) {
      pinBox(timestamp);
    }

    // Filtering with new message box
    displayUnitOfBox();
  }
}

/************************************************************************************************
 * Logging Functions
 ************************************************************************************************/
// Logging Window Focus ON/OFF
window.addEventListener('blur', function () {
  // console.log("WINDOW FOCUS OFF - timestamp=" + Date.now());
  rc.addUserLog(Date.now(), "WINDOW-FOCUS-OFF\n");
  //overlay_on();
});

window.addEventListener('focus', function () {
  // console.log("WINDOW FOCUS ON - timestamp=" + Date.now());
  rc.addUserLog(Date.now(), "WINDOW-FOCUS-ON\n");
  //overlay_off();
});

// Logging Scroll Event
messages.addEventListener("wheel", function (event) {
  window.clearTimeout(isScrolling); // Clear our timeout throughout the scroll
  isScrolling = setTimeout(function () {
    // Set a timeout to run after scrolling ends
    if (messages.scrollTop > scrollPos) {
      // console.log("SCROLL-DOWN");
      rc.addUserLog(Date.now(), "SCROLL-DOWN/POS=" + messages.scrollTop + "\n");
      checkCurBoxes();
    }
    else if (messages.scrollTop < scrollPos) {
      // console.log("SCROLL-UP");
      rc.addUserLog(Date.now(), "SCROLL-UP/POS=" + messages.scrollTop + "\n");
      checkCurBoxes();
    }
    scrollPos = messages.scrollTop;
  }, 66);
});

/************************************************************************************************
 * Main Functions
 ************************************************************************************************/
// Event listener on individual transcript arrival.
function onTranscript(transcript, speaker, timestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  console.log("ON TRANSCRIPT - timestamp=" + timestamp);
  if (!timestamp) {
    console.log("invalid timestamp!!", transcript, speaker, timestamp);
    return;
  }
  if (!transcript || transcript.trim().length == 0) {
    console.log("EMPTY TRANSCRIPT!!! REMOVE MSG BOX FROM ", speaker, " at ", timestamp);
    removeMsg(timestamp);
    return;
  }

  let messageBox = getMessageBox(timestamp);
  if (!messageBox) {
    messageBox = createMessageBox(speaker, timestamp);
  }

  console.log("v1")
  console.log(messageBox)

  let summaryBox = messageBox.childNodes[mode.Summary];
  summaryBox.childNodes[1].textContent = ">> Generating transcript... <<";
  summaryBox.childNodes[2].textContent = transcript;

  let paragraphBox = messageBox.childNodes[mode.Transcript];
  paragraphBox.childNodes[1].textContent = ">> Generating transcript... <<";
  paragraphBox.childNodes[2].textContent = transcript;

  console.log("v2")
  console.log(messageBox)

  // Filtering with new message box
  displayUnitOfBox();

  addScrollDownBtn(messageBox);
}

// Event listener on summary arrival.
function onSummary(summaryArr, confArr, speaker, timestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  console.log("ON SUMMARY - timestamp=" + timestamp);
  let messageBox = getMessageBox(timestamp);
  if (!messageBox) {
    // messageBox = createMessageBox(speaker, timestamp);
    console.log("[onSummary] No messageBox ERROR:", summaryArr, confArr, speaker, timestamp);
  }
  // Filtering with new message box
  displayUnitOfBox();

  if ((summaryArr[0].trim().length == 0) && (summaryArr[1].trim().length == 0)) {
    console.log("No summary:: Delete msg box: ", timestamp);
    removeMsg(timestamp);
  }

  let maxConf = Math.max(...confArr);
  let displaySum = (maxConf === confArr[0]) ? summaryArr[0] : summaryArr[1];

  if (mode == PanelMode.Summary) {
    if (maxConf < CONFIDENCE_LIMIT) {
      messageBox.style.background = BoxColor.Unsure;
    } else if (user_name === speaker) {
      messageBox.style.background = BoxColor.MySure;
    } else {
      messageBox.style.background = BoxColor.OtherSureSummary;
    }
  } else {
    if (user_name === speaker) {
      messageBox.style.background = BoxColor.MySure;
    } else {
      messageBox.style.background = BoxColor.OtherSureTranscript;
    }
  }

  let seeFullText = messageBox.childNodes[3].childNodes[0];
  seeFullText.style.display = "block";
  seeFullText.onclick = function () {
    showFullText(timestamp);
  };

  let paragraphBox = messageBox.childNodes[mode.Transcript];
  let paragraph = paragraphBox.childNodes[2];

  let summaryBox = messageBox.childNodes[mode.Summary];

  // Move existing transcript to fullText block.
  let transcript = summaryBox.childNodes[2].textContent;
  paragraph.textContent = transcript;

  var keywordList = summaryArr[2].split("@@@@@CD@@@@@AX@@@@@");
  keywordList = keywordList.filter((item) => item);
  keywordMap[timestamp.toString()] = keywordList;

  addKeywordsListBlockHelper(timestamp, keywordList);

  // Add buttons for trending keywords
  if (summaryArr[3]) {
    updateTrendingKeywords(summaryArr[3].split("@@@@@CD@@@@@AX@@@@@"));
  }

  // If confidence === -1, the summary result is only the paragraph itself.
  // Do not put confidence element as a sign of "this is not a summary"
  if (maxConf != -1) {
    if (maxConf < CONFIDENCE_LIMIT) {
      summaryBox.childNodes[1].textContent = ">> Is this summary accurate? <<";
      summaryBox.childNodes[1].style.color = TextColor.Unsure;
    } else {
      summaryBox.childNodes[1].textContent = ">> Summary <<";
    }
  }
  paragraphBox.childNodes[1].textContent = ">> Transcript <<";
  paragraphBox.childNodes[1].style.fontWeight = "bold";

  summaryBox.style.color = TextColor.Normal;
  summaryBox.style.fontSize = "medium";
  summaryBox.childNodes[1].style.fontWeight = "bold";
  summaryBox.childNodes[2].textContent = displaySum;

  if (mode == PanelMode.Transcript) {
    let paragraphTitle = paragraphBox.childNodes[1];
    paragraphTitle.textContent = ">> Transcript <<";
    paragraphTitle.style.display = "";
    paragraphTitle.style.fontWeight = "bold";

    paragraphBox.style.color = TextColor.Normal;
    paragraphBox.style.fontSize = "medium";
  }

  // Add edit button in order to allow user change contents (paragraph, absummary, exsummary)
  addEditBtn(paragraph, "paragraph", timestamp);
  addEditBtn(summaryBox.childNodes[2], "summary", timestamp);

  addScrollDownBtn(messageBox);
  checkCurBoxes();
}

function onKeyword(keywordList, speaker, timestamp) {
  console.log("ON KEYWORD - timestamp = " + timestamp);
  let messageBox = getMessageBox(timestamp);
  if (!messageBox) {
    messageBox = createMessageBox(speaker, timestamp);
  }
  // Filtering with new message box
  displayUnitOfBox();

  addKeywordsListBlockHelper(timestamp, keywordList);
}


function onUpdateParagraph(newParagraph, summaryArr, confArr, timestamp, editTimestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  // For summary request on overall summary of favorite keywords
  let check = timestamp.toString().split("@@@");
  if (check[0] === "summary-for-keyword") {
    if (check[1] === user_name) {
      // rc.addUserLog(Date.now(), 'SUMMARY-FOR-KEYWORD\n');
      let summaryBox = document.getElementById("summary-for-keyword");
      summaryBox.childNodes[1].childNodes[0].style.display = "none";
      let extSumm = summaryArr[1]
        .replace("?", ".")
        .replace("!", ".")
        .split(". ")
        .slice(0, 5);

      for (var sentence of extSumm) {
        if (!sentence.trim()) continue;
        let newPara = document.createElement("p");
        newPara.style.border = "1px solid grey";
        newPara.style.padding = "5px 5px 5px 5px";
        newPara.style.margin = "5px 5px 5px 3px";
        newPara.style.borderRadius = "5px";
        newPara.textContent = '"' + sentence + '"';
        summaryBox.append(newPara);
      }
    }
    return;
  }

  let messageBox = document.getElementById(timestamp.toString());
  let paragraph = messageBox.childNodes[mode.Transcript].childNodes[2];
  let summaryEl = messageBox.childNodes[mode.Summary];
  let speaker =
    messageBox.childNodes[0].childNodes[0].childNodes[0].textContent; //messageBox.title.nametag.strong.textContent

  // remove messageBox if newParagraph is empty
  if (!newParagraph) {
    console.log("[DEBUG] DELETING MESSAGEBOX - empty newParagraph (" + timestamp.toString() + ")");
    removeMsg(timestamp.toString());
    return;
  }

  rc.addUserLog(
    Date.now(),
    "UPDATE-PARAGRAPH-MESSAGEBOX/TIMESTAMP=" +
    timestamp +
    "/NEW-PARAGRAPH=" +
    newParagraph +
    "/OLD-PARAGRAPH=" +
    paragraph.textContent +
    "/NEW-SUMMARY=" +
    summaryArr[0] +
    "/OLD-SUMMARY=" +
    summaryEl.childNodes[2].textContent +
    "\n"
  );

  paragraph.textContent = newParagraph;

  // Add edited tag on new paragraph
  let editTag = document.getElementById("editTag-paragraph-" + timestamp.toString());
  if (!editTag) {
    editTag = document.createElement("span");
    editTag.setAttribute("id", "editTag-paragraph-" + timestamp.toString());
    editTag.style = "font-size:0.8em; color:gray";
    paragraph.append(editTag);
  }
  editTag.hidden = false;
  editTag.textContent = " (edited " + formatTime(editTimestamp) + ")";

  // If confidence === -1, the summary result is only the paragraph itself.
  // Do not put confidence element as a sign of "this is not a summary"
  if (confArr[0] !== -1) {
    if (confArr[0] < CONFIDENCE_LIMIT) {
      // LOW CONFIDENCE SCORE
      summaryEl.childNodes[1].textContent = ">> Is this summary accurate? <<";
      summaryEl.childNodes[1].style.color = TextColor.Unsure;

      messageBox.style.background = BoxColor.Unsure;
    } else {
      // HIGH CONFIDENCE SCORE
      summaryEl.childNodes[1].textContent = ">> Summary <<";
      if (user_name === speaker) {
        messageBox.style.background = BoxColor.MySure;
      } else {
        if (mode == PanelMode.Summary) {
          messageBox.style.background = BoxColor.OtherSureSummary;
        } else {
          messageBox.style.background = BoxColor.OtherSureTranscript;
        }
      }
    }
  }
  summaryEl.childNodes[2].textContent = summaryArr[0];

  // Add edited tag on new summary
  let sumeditTag = document.getElementById("editTag-summary-" + timestamp.toString());
  if (!sumeditTag) {
    sumeditTag = document.createElement("span");
    sumeditTag.setAttribute("id", "editTag-summary-" + timestamp.toString());
    sumeditTag.style = "font-size:0.8em; color:gray";
    summaryEl.childNodes[2].append(sumeditTag);
  }
  sumeditTag.hidden = false;
  sumeditTag.textContent = " (paragraph edited " + formatTime(editTimestamp) + ")";

  if (messageBox.getAttribute("pinned") === "true") {
    let pinbox = document.getElementById("pin" + timestamp.toString());
    pinbox.childNodes[1].textContent = summaryArr[0];
  }

  // Update keyword
  let keywordBox = messageBox.childNodes[2];
  let keyList = keywordBox.childNodes;
  for (var key of keyList) {
    if (key.textContent.charAt(0) === "#") {
      key.style.display = "none";
    }
  }
  let keywordList = summaryArr[2].split("@@@@@CD@@@@@AX@@@@@");
  keywordList = keywordList.filter((item) => item);
  keywordMap[timestamp.toString()] = keywordList;

  addKeywordsListBlockHelper(timestamp, keywordList);

  addEditBtn(paragraph, "paragraph", timestamp);
  addEditBtn(summaryEl.childNodes[2], "summary", timestamp);

  //Update trending keywords
  if (summaryArr[3]) {
    updateTrendingKeywords(summaryArr[3].split("@@@@@CD@@@@@AX@@@@@"));
  }

  // add current msg boxes
  checkCurBoxes();
}

function onUpdateSummary(type, content, timestamp, editTimestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  // If keywords change
  let trendingList = "";
  if (content.split("@@@@@CDC@@@@@AXA@@@@@").length > 1) {
    trendingList = content.split("@@@@@CDC@@@@@AXA@@@@@")[1];
    content = content.split("@@@@@CDC@@@@@AXA@@@@@")[0];
  }

  // Use updateSummary function for pin, addkey, delkey
  if (type === "pin") {
    pinBox(timestamp);
    return;
  }

  let messageBox = document.getElementById(timestamp.toString());
  let summaryEl = null;
  let msg = "New summary contents: " + timestamp + "\n";
  if (type == "summary") {
    summaryEl = messageBox.childNodes[mode.Summary];
    msg = msg + "                [AbSummary] " + content + "\n";
  }

  // remove messageBox if content is empty
  console.log("Content: ", content, !content, !content.trim());
  if (!content) {
    console.log("[DEBUG] DELETING MESSAGEBOX - empty content (" + timestamp.toString() + ")");
    removeMsg(timestamp.toString());
    return;
  }

  // if user change summary, confidence score == 1
  let speaker =
    messageBox.childNodes[0].childNodes[0].childNodes[0].textContent;
  if (user_name === speaker) {
    messageBox.style.background = BoxColor.MySure;
  } else {
    if (mode == PanelMode.Summary) {
      messageBox.style.background = BoxColor.OtherSureSummary;
    } else {
      messageBox.style.background = BoxColor.OtherSureTranscript;
    }
  }

  rc.addUserLog(
    Date.now(),
    "UPDATE-SUMMARY-MESSAGEBOX/TIMESTAMP=" +
    timestamp +
    "/NEW-SUMMARY=" +
    content +
    "/OLD-SUMMARY=" +
    summaryEl.childNodes[2].textContent +
    "\n"
  );

  summaryEl = messageBox.childNodes[mode.Summary];
  summaryEl.childNodes[1].textContent = ">> Summary <<"; // if user change summary, confidence score would be 100 %
  summaryEl.childNodes[1].style.color = TextColor.Normal;
  summaryEl.childNodes[2].textContent = content;

  // Add edited tag on new summary
  let editTag = document.getElementById("editTag-summary-" + timestamp.toString());
  if (!editTag) {
    editTag = document.createElement("span");
    editTag.setAttribute("id", "editTag-summary-" + timestamp.toString());
    editTag.style = "font-size:0.8em; color:gray";
    summaryEl.childNodes[2].append(editTag);
  }
  editTag.hidden = false;
  editTag.textContent = " (edited " + formatTime(editTimestamp) + ")";

  if (messageBox.getAttribute("pinned") === "true") {
    let pinbox = document.getElementById("pin" + timestamp.toString());
    pinbox.childNodes[1].textContent = content;
  }

  let keywordBox = messageBox.childNodes[2];
  let keyList = keywordBox.childNodes;
  for (var key of keyList) {
    if (key.textContent.charAt(0) === "#") {
      if (!content.includes(key.textContent.slice(1))) {
        key.style.display = "none";
      }
    }
  }
  addEditBtn(summaryEl.childNodes[2], type, timestamp);

  // Add buttons for trending keywords
  if (trendingList != "") {
    updateTrendingKeywords(trendingList.split("@@@@@CD@@@@@AX@@@@@"));
  }

  // add current msg boxes
  checkCurBoxes();
}

function updateTrendingKeywords(trendingList) {
  let trendingBtns = document.getElementsByClassName("trending-btn");
  let trendingBox = document.getElementById("keywords-list");
  while (trendingBtns.length > 0) {
    trendingBtns[0].parentNode.removeChild(trendingBtns[0]);
  }
  let i = 0;
  trendingList = trendingList.filter((item) => item);
  for (var newKey of trendingList) {
    let newBtn = document.createElement("button");
    newBtn.onclick = function () {
      trendingSearch(this.textContent.slice(1));
    };
    newBtn.className = "trending-btn";
    newBtn.textContent = "#" + newKey;
    newBtn.style.fontSize = "larger";
    newBtn.style.marginRight = "5px";
    newBtn.style.backgroundColor = "#FFDA3E";
    setTimeout(function () {
      newBtn.style.backgroundColor = "white";
    }, 7000);
    trendingBox.append(newBtn);
    i++;
    if (i > 4) {
      break;
    }
  }
}

function addKeywordsListBlockHelper(timestamp, keywords) {
  let messageBox = getMessageBox(timestamp);
  messageBox.childNodes[2].innerHTML = "";

  for (var keyword of keywords) {
    if (!keyword.trim()) continue;
    addKeywordBlockHelper(timestamp, keyword);
  }
}

function addKeywordBlockHelper(timestamp, keyword) {
  let msgBox = getMessageBox(timestamp);
  let keywordBox = msgBox.childNodes[2];
  let keywordBtn = document.createElement("p");
  keywordBtn.className = "keyword-btn";
  keywordBtn.setAttribute("id", timestamp.toString() + "@@@" + keyword);
  keywordBtn.textContent = "#" + keyword;
  keywordBtn.style.display = "inline-block";
  keywordBtn.style.fontSize = "small";
  keywordBtn.style.padding = "0px 5px 0px 3px";
  keywordBtn.style.border = "1px solid #6b787e";
  keywordBtn.style.borderRadius = "5px";
  let delBtn = document.createElement("button");
  delBtn.className = "fas fa-times";
  delBtn.style.backgroundColor = "transparent";
  delBtn.style.border = 0;
  delBtn.onclick = function () {
    rc.addUserLog(
      Date.now(),
      "DELETE-KEYWORD/MSG=" + keyword + "/TIMESTAMP=" + timestamp + "\n"
    );
    removeKeyword(this.parentNode, timestamp);
  };
  delBtn.style.display = "none";
  keywordBtn.append(delBtn);
  keywordBtn.style.backgroundColor = "transparent";

  keywordBtn.style.margin = "0px 5px 2px 0px";
  keywordBox.append(keywordBtn);
}

function toEditableBg(p) {
  p.style.background = "none";
}

function toEditingBg(p) {
  p.style.background = "aliceblue";
}

function toEditableIcon(btn) {
  btn.style.opacity = "0.5";
  btn.childNodes[0].className = "fas fa-pen";
}

function toEditingIcon(btn) {
  btn.style.opacity = "0.8";
  btn.childNodes[0].className = "fas fa-check";
}

function addEditBtn(area, type, timestamp) {
  let editBtn1 = document.createElement("span");
  editBtn1.className = "edit-btn";
  editBtn1.id = "edit-" + type + "-" + timestamp;
  editBtn1.onclick = function () {
    editContent(type, timestamp);
    rc.addUserLog(
      Date.now(),
      "START-EDIT-MESSAGE/TYPE=" + type + "/TIMESTAMP=" + timestamp + "\n"
    );
  };
  let pen1 = document.createElement("i");
  pen1.className = "fas fa-pen";
  editBtn1.append(pen1);
  area.append(editBtn1);
}

function removeMsg(timestamp) {
  console.log("ON RemoveMsg - timestamp = ", timestamp);
  let messageBox = getMessageBox(timestamp);
  if (messageBox) {
    messageBox.remove();
  }
}

function editContent(type, timestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  let messageBox = document.getElementById(timestamp.toString());
  let oldtxt = null;
  let editTag = null;
  switch (type) {
    case "paragraph":
      let paragraph = messageBox.childNodes[mode.Transcript].childNodes[2];
      paragraph.contentEditable = "true";

      // change icon
      toEditingBg(paragraph);
      toEditingIcon(paragraph.lastChild);

      // Remove edited tag if exist
      editTag = document.getElementById("editTag-paragraph-" + timestamp.toString());
      oldtxt = paragraph.textContent;
      if (editTag) {
        editTag.hidden = true;
        oldtxt = oldtxt.split(editTag.textContent)[0];
      }

      original = paragraph.textContent;

      paragraph.lastChild.onclick = function () {
        finishEditContent("paragraph", oldtxt, timestamp, original);
      };
      paragraph.addEventListener("keypress", function (event) {
        if (event.keyCode === 13) {
          finishEditContent("paragraph", oldtxt, timestamp, original);
        }
      });

      break;
    case "summary":
      let summary = messageBox.childNodes[mode.Summary].childNodes[2];
      summary.contentEditable = "true";

      // change icon
      console.log("editContent-summary: ", summary);

      toEditingBg(summary);
      toEditingIcon(summary.lastChild);

      // Remove edited tag if exist
      oldtxt = summary.textContent;
      editTag = document.getElementById("editTag-summary-" + timestamp.toString());
      if (editTag) {
        editTag.hidden = true;
        oldtxt = oldtxt.split(editTag.textContent)[0];
      }

      original = summary.textContent;

      summary.lastChild.onclick = function () {
        finishEditContent("summary", oldtxt, timestamp, original);
      };
      summary.addEventListener("keydown", function (event) {
        if (event.keyCode === 13) {
          finishEditContent("summary", oldtxt, timestamp, original);
        }
      });
      break;
  }
}

function finishEditContent(type, oldtxt, timestamp, original) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  let messageBox = document.getElementById(timestamp.toString());

  let editTimestamp = Date.now();
  let editTag;

  // Remove edited tag in oldtxt if exist
  let oldtxt_value = oldtxt.valueOf().trim();

  switch (type) {
    case "paragraph":
      let paragraph = messageBox.childNodes[mode.Transcript].childNodes[2];
      // console.log("finishEditContent: ", paragraph.textContent);
      toEditableBg(paragraph);
      paragraph.contentEditable = "false";

      var paragraph_value = paragraph.textContent;

      editTag = document.getElementById("editTag-paragraph-" + timestamp.toString());
      if (editTag) {
        paragraph_value = paragraph_value.split(editTag.textContent)[0];
      }
      paragraph_value = paragraph_value.trim();
      if (user_name != 'cpsAdmin' && !paragraph_value) {
        console.log("[ERROR] ONLY cpsAdmin can delete messagebox!");
        paragraph_value = oldtxt_value;
        paragraph.textContent = original;
        addEditBtn(paragraph, "paragraph", timestamp);
      }

      if (oldtxt_value != paragraph_value) {
        console.log("finisheditContent::: not same");
        console.log(oldtxt_value, paragraph_value);
        // update paragraph and summary on all users
        paragraph.textContent = paragraph_value;

        rc.updateParagraph(
          paragraph.textContent,
          timestamp,
          messageBox.childNodes[0].childNodes[0].textContent,
          editTimestamp
        );
        if (mode == PanelMode.Summary) {
          paragraph.style.backgroundColor = "#f2f2f2";
        }
        rc.addUserLog(
          editTimestamp,
          "FINISH-EDIT-PARAGRAPH" +
          "/TYPE=" +
          type +
          "/PARAGRAPH=" +
          messageBox.childNodes[0].childNodes[0].textContent +
          "/OLDPARAGRAPH=" +
          oldtxt +
          "/TIMESTAMP=" +
          timestamp +
          "\n"
        );
      } else {
        // change icon
        toEditableIcon(paragraph.childNodes[1])

        editTag = document.getElementById("editTag-paragraph-" + timestamp.toString());
        if (editTag) {
          editTag.hidden = false;
        }

        paragraph.childNodes[1].onclick = function () {
          editContent(type, timestamp);
        };
        if (mode == PanelMode.Summary) {
          paragraph.style.backgroundColor = "#f2f2f2";
        }
        rc.addUserLog(
          editTimestamp,
          "CANCEL-EDIT-PARAGRAPH/TYPE=" +
          type +
          "/TIMESTAMP=" +
          timestamp +
          "\n"
        );
      }
      break;
    default:
      let summary = null;
      if (type == "summary") {
        summary = messageBox.childNodes[mode.Summary].childNodes[2];
      }

      if (mode == PanelMode.Summary) {
        toEditableBg(summary);
      } else {
        summary.style.backgroundColor = "#f2f2f2";
      }
      summary.contentEditable = "false";

      var summary_value = summary.textContent.trim();

      editTag = document.getElementById("editTag-summary-" + timestamp.toString());
      if (editTag) {
        summary_value = summary_value.split(editTag.textContent)[0];
      }
      summary_value = summary_value.trim();

      if (user_name != 'cpsAdmin' && !summary_value) {
        console.log("[ERROR] ONLY cpsAdmin can delete messagebox!");
        summary_value = oldtxt_value;
        summary.textContent = original;
        addEditBtn(summary, "summary", timestamp);
      }

      if (oldtxt_value != summary_value) {
        console.log(oldtxt_value, summary_value)
        summary.textContent = summary_value;

        rc.updateSummary(
          "summary",
          summary.textContent,
          timestamp,
          editTimestamp
        );
        rc.addUserLog(
          editTimestamp,
          "FINISH-EDIT-SUMMARY" +
          "/TYPE=" +
          type +
          "/SUMMARY=" +
          summary.textContent +
          "/OLDSUMMARY=" +
          oldtxt +
          "/TIMESTAMP=" +
          timestamp +
          "\n"
        );
      } else {
        toEditableIcon(summary.lastChild);
        summary.lastChild.onclick = function () {
          editContent(type, timestamp);
        };

        editTag = document.getElementById("editTag-summary-" + timestamp.toString());
        if (editTag) {
          editTag.hidden = false;
        }

        rc.addUserLog(
          editTimestamp,
          "CANCEL-EDIT-SUMMARY/TYPE=" + type + "/TIMESTAMP=" + timestamp + "\n"
        );
      }
      break;
  }
}

var highlighter = new Hilitor();

function displayUnitOfBox() {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  let searchword = document.getElementById("search-word").value.trim();
  let messageBoxes = document.getElementsByClassName("message-box");
  let paragraphs = document.getElementsByClassName("paragraph");

  for (var i = 0; i < messageBoxes.length; i++) {
    let isfiltered = paragraphs[i].textContent.toLowerCase().includes(searchword.trim().toLowerCase());
    let messageBox = messageBoxes[i];

    // check if paragraph is empty
    if (!messageBox.childNodes[mode.Transcript].childNodes[2].textContent.trim()) {
      console.log("[DEBUG] DELETING EMPTY MESSAGEBOX in displayUnitOfBox");
      messageBox.remove();
    }
    else {
      displayBox(true && isfiltered, messageBox, displayYes);
    }
  }

  // highlight with search-word
  if (searchword == "") {
    if (highlighter) {
      highlighter.remove();
    }
  } else {
    highlighter.apply(searchword);
  }
}

function addScrollDownBtn(messageBox) {
  // Scroll down the messages area.
  let scrolldownbutton = document.getElementById("scrollbtn");
  if (
    messages.scrollTop + messages.clientHeight + messageBox.clientHeight + 20 >
    messages.scrollHeight
  ) {
    messages.scrollTop = messages.scrollHeight;
    scrolldownbutton.style.display = "none";
  } else {
    scrolldownbutton.style.display = "";
  }
}

function scrollDown() {
  messages.scrollTop = messages.scrollHeight;

  let scrolldownbutton = document.getElementById("scrollbtn");
  scrolldownbutton.style.display = "none";
}
//////////////////////////////////////////////
/************* Helper functions *************/

// Helper function for logging click button "검색하기"
function get_position_of_mousePointer(event, tag) {
  event = event || window.event;

  var x = 0; // 마우스 포인터의 좌측 위치
  var y = 0; // 마우스 포인터의 위쪽 위치

  if (event.pageX) {
    // pageX & pageY를 사용할 수 있는 브라우저일 경우
    x = event.pageX;
    y = event.pageY;
  } else {
    // 그외 브라우저용
    x =
      event.clientX +
      document.body.scrollLeft +
      document.documentElement.scrollLeft;
    y =
      event.clientY +
      document.body.scrollTop +
      document.documentElement.scrollTop;
  }
  console.log(" -> x position : " + x + ", y position : " + y);
  //return { positionX : x, positionY : y };
  rc.addUserLog(
    Date.now(),
    "GET-POSITION-OF-MOUSE-" + tag + ": " + x + ", " + y + "\n"
  );
  // document.onkeydown = noEvent;
}

// Click favorite keyword button
function trendingSearch(keyword) {
  removeSummaryBox();
  let searchword = document.getElementById("search-word");

  // reclick keyword button to return
  if (keyword == searchword.value) {
    returnTrending();
    return
  }

  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  searchword.value = keyword;
  displayUnitOfBox();
  createSummaryBox(keyword);
  let editTimestamp = Date.now();
  // rc.addUserLog(Date.now(), "SEARCH-FAVORITE/MSG=" + keyword + "\n");

  let messageBoxes = document.getElementsByClassName("message-box");
  let paragraphs = document.getElementsByClassName("paragraph");

  keywordParagraph = "";
  for (var i = 0; i < messageBoxes.length; i++) {
    let isfiltered = paragraphs[i].textContent.toLowerCase().includes(keyword.toLowerCase());
    let messageBox = messageBoxes[i];
    if (isfiltered) {
      keywordParagraph +=
        " " + messageBox.childNodes[mode.Transcript].childNodes[2].textContent;
    }
  }

  rc.addUserLog(
    Date.now(),
    "SEARCH-TRENDINGWORDS/MSG=" + searchword.value + "\n"
  );
  checkCurBoxes();
  rc.updateParagraph(
    keywordParagraph,
    "summary-for-keyword@@@" + user_name,
    "OVERALL@@@" + keyword,
    editTimestamp
  );
}

// Show the overall summary for each thread (favorite keyword)
function createSummaryBox(keyword) {
  let summaryBox = document.createElement("div");
  summaryBox.setAttribute("id", "summary-for-keyword");
  summaryBox.className = "summary-box";

  // summaryBox.childNodes[0]: Includes the keyword
  let title = document.createElement("div");
  let nametag = document.createElement("span");
  let strong = document.createElement("strong");
  strong.textContent = "[Key sentences of #" + keyword + "]";
  nametag.className = "nametag";
  nametag.append(strong);
  title.append(nametag);
  summaryBox.append(title);

  // summaryBox.childNodes[1]: Includes abstract summary
  let overallSummaryBox = document.createElement("div");
  let overallSum = document.createElement("p");
  overallSum.textContent = "Processing overall summary...";
  overallSummaryBox.style.fontSize = "medium";
  overallSummaryBox.style.marginLeft = "5px";
  overallSummaryBox.style.marginTop = "1em";
  overallSummaryBox.append(overallSum);
  summaryBox.append(overallSummaryBox);

  messages.insertBefore(summaryBox, messages.firstChild);
  summaryBox.scrollIntoView(true);
  return summaryBox;
}

// Remove existing summaryBox
function removeSummaryBox() {
  let summaryBox = document.getElementById("summary-for-keyword");
  if (summaryBox) {
    summaryBox.remove();
  }
}

// Delete text in search box & Display all boxes
function showAllBoxes() {
  let searchWord = document.getElementById("search-word");
  searchWord.value = "";
  removeSummaryBox();
  displayUnitOfBox();
}

// Hide box
function displayNo(box) {
  box.style.display = "none";
}

// Show box
function displayYes(box) {
  box.style.display = "";
}

// Disply box if 'cond' is true, use given function 'fn' to show the box
function displayBox(cond, box, fn) {
  if (cond) {
    fn(box);
  } else {
    displayNo(box);
  }
}

// Creates a container element (message box)
// that holds a paragraph and its summary.
// The timestamp acts as an identifier for the element.
function createMessageBox(speaker, timestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value;

  let messageBox = document.createElement("div");
  messageBox.setAttribute("id", timestamp.toString());
  messageBox.className = "message-box";

  if (user_name === speaker) {
    messageBox.style.borderBottom = "0.001em solid rgba(225, 229, 143, 0.7)";
    messageBox.style.background = BoxColor.GenMySure;
  } else {
    if (mode == "summary") {
      messageBox.style.background = BoxColor.GenOtherSureSummary;
    } else {
      messageBox.style.borderBottom = "0.001em solid rgba(40, 70, 167, 0.7)";
      messageBox.style.background = BoxColor.GenOtherSureTranscript;
    }
  }

  // messageBox.childNodes[0]: includes title - timestamp and speaker.
  let title = document.createElement("div");
  let nametag = document.createElement("span");
  let strong = document.createElement("strong");
  strong.textContent = speaker;
  nametag.className = "nametag";
  nametag.append(strong);

  let timetag = document.createElement("span");
  timetag.className = "timetag";
  timetag.append(document.createTextNode(formatTime(timestamp)));
  title.append(nametag, timetag);

  // Add pin button
  // let pinBtn = document.createElement("button");
  // let pin = document.createElement("i");
  // pin.className = "fas fa-thumbtack";
  // pin.style.color = "#F2F3F4";
  // pinBtn.append(pin);
  // pinBtn.style.backgroundColor = "transparent";
  // pinBtn.style.border = "0";
  // pinBtn.style.float = "right";
  // pinBtn.style.display = "inline-block";
  // messageBox.setAttribute("pinned", "false");
  // pinBtn.onclick = function () {
  //   rc.updateSummary("pin", "pinBox", timestamp, Date.now());
  //   if (messageBox.getAttribute("pinned") === "false") {
  //     rc.addUserLog(
  //       Date.now(),
  //       "PIN-BOX/TIMESTAMP=" + timestamp.toString() + "\n"
  //     );
  //   } else {
  //     rc.addUserLog(
  //       Date.now(),
  //       "UNPIN-BOX/TIMESTAMP=" + timestamp.toString() + "\n"
  //     );
  //   }
  // };

  // title.append(pinBtn);
  messageBox.append(title);

  if (mode == "summary") {
    // messageBox.childNodes[1]: childNodes[0] = Button, childNodes[1] = Title, childNodes[3] = Summary (in Summary Mode: Button will never show)
    let summaryBox = document.createElement("div");
    summaryBox.className = "ab-summary-box";
    setStyleTop(summaryBox);

    let seeSummary = document.createElement("button");
    seeSummary.className = "seeSummary";
    setStyleSeeButton(seeSummary);
    seeSummary.innerHTML = "<u>Summary</u>";
    seeSummary.onclick = function () {
      showFullText(timestamp);
    };
    summaryBox.append(seeSummary);

    let summaryTitle = document.createElement("p");
    let summaryContent = document.createElement("p");
    summaryContent.className = "ab-summary";

    summaryBox.append(summaryTitle);
    summaryBox.append(summaryContent);

    messageBox.append(summaryBox);
  } else {
    // messageBox.childNodes[1]: childNodes[0] = Button, childNodes[1] = Title, childNodes[2] = Full paragraph (in Transcript Mode: Button will never show)
    let paragraphBox = document.createElement("div");
    paragraphBox.className = "paragraph-box";
    setStyleTop(paragraphBox);

    let seeFullText = document.createElement("button");
    seeFullText.className = "seeFullText";
    setStyleSeeButton(seeFullText);
    seeFullText.innerHTML = "<u>Full Script</u>";
    seeFullText.onclick = function () {
      showFullText(timestamp);
    };
    paragraphBox.append(seeFullText);

    let paragraphTitle = document.createElement("p");
    let paragraph = document.createElement("p");
    paragraph.className = "paragraph";

    paragraphBox.append(paragraphTitle);
    paragraphBox.append(paragraph);

    messageBox.append(paragraphBox);
  }



  // messageBox.childNodes[2]: includes the keywords
  let keywordBox = document.createElement("div");
  keywordBox.className = "keyword-box";
  keywordBox.style.fontSize = "smaller";
  keywordBox.style.marginLeft = "5px";
  messageBox.append(keywordBox);

  if (mode == "summary") {
    // messageBox.childNodes[3]: childNodes[0] = Button, childNodes[1] = Full paragraph (in Summary Mode)
    let paragraphBox = document.createElement("div");
    paragraphBox.className = "paragraph-box";

    let seeFullText = document.createElement("button");
    seeFullText.className = "seeFullText";
    setStyleSeeButton(seeFullText);
    seeFullText.innerHTML = "<u>Full Script</u>";
    seeFullText.onclick = function () {
      showFullText(timestamp);
    };
    paragraphBox.append(seeFullText);

    let paragraphTitle = document.createElement("p");
    let paragraph = document.createElement("p");
    paragraph.className = "paragraph";

    setStyleBottomContent(paragraph);
    paragraphTitle.style.display = "none";

    paragraphBox.append(paragraphTitle);
    paragraphBox.append(paragraph);

    messageBox.append(paragraphBox);
  } else {
    // messageBox.childNodes[3]: includes the abstractive summary and confidence level (in Transcript Mode: will never show)
    let summaryBox = document.createElement("div");
    summaryBox.className = "ab-summary-box";

    let seeSummary = document.createElement("button");
    seeSummary.className = "seeSummary";
    setStyleSeeButton(seeSummary);
    seeSummary.innerHTML = "<u>Summary</u>";
    seeSummary.onclick = function () {
      showFullText(timestamp);
    };
    summaryBox.append(seeSummary);

    let summaryTitle = document.createElement("p");
    let summaryContent = document.createElement("p");
    summaryContent.className = "ab-summary";

    setStyleBottomContent(summaryContent);
    summaryTitle.style.display = "none";

    summaryBox.append(summaryTitle);
    summaryBox.append(summaryContent);

    messageBox.append(summaryBox);
  }

  // Finally append the box to 'messages' area
  let lastchild = true;
  for (var box of messages.childNodes) {
    if (Number(box.id) > timestamp) {
      messages.insertBefore(messageBox, box);
      lastchild = false;
      break;
    }
  }
  if (lastchild) {
    messages.appendChild(messageBox);
    rc.addUserLog(
      Date.now(),
      "CREATE-MSGBOX/POS=" + messageBox.offsetTop + "/TIMESTAMP=" + timestamp + "\n"
    );
  }
  return messageBox;
}

// Pins message box
function pinBox(timestamp) {
  let stringTime = timestamp.toString();
  let messageBox = document.getElementById(stringTime);
  let pinBtn = messageBox.childNodes[0].childNodes[2];
  let dropdownPin = document.getElementById("dropdownPin");
  let newPin = document.createElement("a");

  if (messageBox.getAttribute("pinned") === "false") {
    messageBox.setAttribute("pinned", "true");
    newPin.setAttribute("id", "pin" + stringTime);
    newPin.href = "#";
    newPin.addEventListener("click", function () {
      rc.addUserLog(Date.now(), "CLICK-PIN/TIMESTAMP=" + stringTime + "\n");
      console.log(
        "CLICK-PIN -> TIMESTAMP=" + stringTime,
        messageBox,
        messageBox.offsetTop,
        messageBox.offsetHeight
      );
      messageBox.scrollIntoView(false);
    });
    newPin.style.padding = "2px 2px 2px 2px";
    newPin.style.backgroundColor = "#ffffff";
    newPin.style.border = "0.1px solid #d4d4d4";
    newPin.style.fontSize = "smaller";
    newPin.style.color = "#000000";
    newPin.style.float = "left";
    newPin.style.width = "250px";
    newPin.style.overflow = "auto";
    newPin.style.textAlign = "left";
    newPin.style.textDecoration = "none";
    newPin.style.overflowX = "hidden";
    let speaker = document.createElement("strong");
    speaker.textContent =
      "[" +
      messageBox.childNodes[0].childNodes[0].childNodes[0].textContent +
      "] ";
    speaker.style.marginLeft = "5px";
    let textCont = document.createElement("p");
    textCont.textContent =
      messageBox.childNodes[1].childNodes[1].textContent.substr(0, 50) + " ...";
    textCont.style.margin = "3px 5px 3px 5px";
    newPin.append(speaker);
    newPin.append(textCont);
    dropdownPin.append(newPin);
    pinBtn.childNodes[0].style.color = "#000000";
  } else {
    messageBox.setAttribute("pinned", "false");
    let delPin = document.getElementById("pin" + stringTime);
    delPin.remove();
    pinBtn.childNodes[0].style.color = "#F2F3F4";
  }
}

// Shows the full paragraph / summary in each message box (in Summary Mode / Transcript Mode)
function showFullText(timestamp) {
  let toggleMode = document.getElementById("toggle-mode");
  let mode = toggleMode.value == "summary" ? PanelMode.Summary : PanelMode.Transcript;

  let messageBox = document.getElementById(timestamp.toString());

  if (messageBox.childNodes[3].childNodes[2].style.display == "") {
    if (mode == PanelMode.Summary) {
      rc.addUserLog(
        Date.now(),
        "CLICK-HIDE-FULL-TEXT/TIMESTAMP=" + timestamp.toString() + "\n"
      );
      messageBox.childNodes[3].childNodes[0].innerHTML = "<u>Full Script</u>";
    } else {
      rc.addUserLog(
        Date.now(),
        "CLICK-HIDE-SUMMARY/TIMESTAMP=" + timestamp.toString() + "\n"
      );
      messageBox.childNodes[3].childNodes[0].innerHTML = "<u>Summary</u>";
    }
    messageBox.childNodes[3].childNodes[2].style.display = "none";
  } else {
    if (mode == PanelMode.Summary) {
      rc.addUserLog(
        Date.now(),
        "CLICK-SEE-FULL-TEXT/TIMESTAMP=" + timestamp.toString() + "\n"
      );
    } else {
      rc.addUserLog(
        Date.now(),
        "CLICK-SEE-SUMMARY/TIMESTAMP=" + timestamp.toString() + "\n"
      );
    }
    messageBox.childNodes[3].childNodes[0].innerHTML = "<u>Close</u>";
    messageBox.childNodes[3].childNodes[2].style.display = "";
  }
}

// Gets an existing message box that matches given timestamp.
function getMessageBox(timestamp) {
  return document.getElementById(timestamp.toString());
}

// Formats time from a timestamp in hh:mm:ss AM/PM format.
function formatTime(timestamp) {
  // console.log("formatTime");
  // console.log(Number(timestamp));
  let date = new Date(Number(timestamp));
  // console.log(date);

  // Appends leading zero for one-digit hours, minutes, and seconds
  function appendZero(time) {
    return time < 10 ? "0" + time : time.toString();
  }

  let hours = appendZero(date.getHours() % 12);
  let ampm = date.getHours() < 12 ? "AM" : "PM";
  let minutes = appendZero(date.getMinutes());
  let seconds = appendZero(date.getSeconds());

  return `${hours}:${minutes}:${seconds} ${ampm}`;
}

////////////////////////////////////////////////////////////////////////////////////
///////////////////////////       HIGHLIGHTER              /////////////////////////
////////////////////////////////////////////////////////////////////////////////////

// Original JavaScript code by Chirp Internet: chirpinternet.eu
// Please acknowledge use of this code by including this header.

function Hilitor(id, tag) {
  // private variables
  var targetNode = document.getElementById(id) || document.body;
  var hiliteTag = tag || "MARK";
  var skipTags = new RegExp("^(?:" + hiliteTag + "|SCRIPT|FORM|SPAN)$");
  var colors = ["#ff6"];
  var wordColor = [];
  var colorIdx = 0;
  var matchRegExp = "";
  var openLeft = false;
  var openRight = false;

  // characters to strip from start and end of the input string
  var endRegExp = new RegExp("^[^\\w]+|[^\\w]+$", "g");

  // characters used to break up the input string into words
  var breakRegExp = new RegExp("[^\\w'-]+", "g");

  this.setEndRegExp = function (regex) {
    endRegExp = regex;
    return endRegExp;
  };

  this.setBreakRegExp = function (regex) {
    breakRegExp = regex;
    return breakRegExp;
  };

  this.setMatchType = function (type) {
    switch (type) {
      case "left":
        this.openLeft = false;
        this.openRight = true;
        break;

      case "right":
        this.openLeft = true;
        this.openRight = false;
        break;

      case "open":
        this.openLeft = this.openRight = true;
        break;

      default:
        this.openLeft = this.openRight = false;
    }
  };

  this.setRegex = function (input) {
    // input = input.replace(endRegExp, "");
    // input = input.replace(breakRegExp, "|");
    // input = input.replace(/^\||\|$/g, "");
    if (input) {
      var re = "(" + input + ")";
      matchRegExp = new RegExp(re, "i");
      return matchRegExp;
    }
    return false;
  };

  this.getRegex = function () {
    var retval = matchRegExp.toString();
    retval = retval.replace(/(^\/(\\b)?|\(|\)|(\\b)?\/i$)/g, "");
    retval = retval.replace(/\|/g, " ");
    return retval;
  };

  // recursively apply word highlighting
  this.hiliteWords = function (node) {
    if (node === undefined || !node) return;
    if (!matchRegExp) return;
    if (skipTags.test(node.nodeName)) return;

    if (node.hasChildNodes()) {
      for (var i = 0; i < node.childNodes.length; i++)
        this.hiliteWords(node.childNodes[i]);
    }
    if (node.nodeType == 3) {
      // NODE_TEXT
      if ((nv = node.nodeValue) && (regs = matchRegExp.exec(nv))) {
        if (!wordColor[regs[0].toLowerCase()]) {
          wordColor[regs[0].toLowerCase()] = colors[colorIdx++ % colors.length];
        }
        var match = document.createElement(hiliteTag);
        match.appendChild(document.createTextNode(regs[0]));
        match.style.backgroundColor = wordColor[regs[0].toLowerCase()];
        match.style.color = "#000";

        var after = node.splitText(regs.index);
        after.nodeValue = after.nodeValue.substring(regs[0].length);
        node.parentNode.insertBefore(match, after);
      }
    }
  };

  // remove highlighting
  this.remove = function () {
    var arr = document.getElementsByTagName(hiliteTag);
    while (arr.length && (el = arr[0])) {
      var parent = el.parentNode;
      parent.replaceChild(el.firstChild, el);
      parent.normalize();
    }
  };

  // start highlighting at target node
  this.apply = function (input) {
    this.remove();
    if (input === undefined || !(input = input.replace(/(^\s+|\s+$)/g, ""))) {
      return;
    }
    if (this.setRegex(input)) {
      this.hiliteWords(targetNode);
    }
    return matchRegExp;
  };
}


/**
 * Return trending keywords
 */
function returnTrending() {
  showAllBoxes();
  scrollDown();
  rc.addUserLog(
    Date.now(),
    "SEARCH-TRENDINGWORDS/RETURN\n"
  );
  checkCurBoxes();
}


/**
 * Save log for current watching msg boxes
 */
function checkCurBoxes() {
  let messageBoxes = document.getElementsByClassName("message-box");

  let curBoxes = [];
  let boxMargin = 1;
  let curStart = messages.scrollTop;
  let curEnd = messages.scrollTop + messages.clientHeight;
  var msgStart = 0
  var msgEnd = 0;

  for (var i = 0; i < messageBoxes.length; i++) {
    let messageBox = messageBoxes[i]

    if (messageBox.style.display == "none") {
      continue;
    }

    msgEnd = msgStart + messageBox.clientHeight;
    if (msgStart > curEnd) {
      break;
    }
    if (msgEnd > curStart) {
      if (messageBox.id != "summary-fo-keyword") {
        curBoxes.push(messageBox.id);
      }
    }
    msgStart = msgEnd + boxMargin;
  }

  rc.addUserLog(
    Date.now(),
    "CURRENT-MSG-BOXES/TIMESTAMPS=" + curBoxes.toString() + "\n"
  )
}

/**
 * Toggle summary / transcript mode
 */
function toggleMode() {
  //removeSummaryBox();
  let toggleBtn = document.getElementById("toggle-mode");
  let curMode = toggleBtn.value;

  if (curMode == "summary") {
    toggleBtn.value = "transcript";
    toggleBtn.innerText = "Transcript Mode";
    rc.addUserLog(
      Date.now(),
      "TOGGLE-MODE/SUMMARY=TRANSCRIPT\n"
    );
  } else {
    toggleBtn.value = "summary";
    toggleBtn.innerText = "Summary Mode";
    rc.addUserLog(
      Date.now(),
      "TOGGLE-MODE/TRANSCRIPT=SUMMARY\n"
    );
  }

  let messageBoxes = document.getElementsByClassName("message-box");

  for (var i = 0; i < messageBoxes.length; i++) {
    let messageBox = messageBoxes[i];
    let timestamp = messageBox.id;

    let tmp = messageBox.childNodes[1].innerHTML;
    messageBox.childNodes[1].innerHTML = messageBox.childNodes[3].innerHTML;
    messageBox.childNodes[3].innerHTML = tmp;

    if (messageBox.childNodes[1].childNodes[1].textContent != ">> Generating transcript... <<") {
      setStyleCom(messageBox.childNodes[1]);
      // message box color
      if (user_name != messageBox.childNodes[0].childNodes[0].childNodes[0].textContent) {                                               // others' msg box
        if (curMode == "summary") {
          messageBox.style.borderBottom = "0.001em solid rgba(40, 70, 167, 0.7)";
          messageBox.style.background = BoxColor.OtherSureTranscript;
        } else {
          messageBox.style.borderBottom = "0.001em solid rgba(40, 167, 70, 0.7)";
          if (messageBox.childNodes[1].childNodes[1].textContent == ">> Is this summary accurate? <<") {
            messageBox.childNodes[1].childNodes[1].style.color = TextColor.Unsure;
            messageBox.style.background = BoxColor.Unsure;
          } else {
            messageBox.style.background = BoxColor.OtherSureSummary;
          }
        }
      } else {                                                                                             // my msg box
        if (curMode == "summary") {
          messageBox.style.background = BoxColor.MySure;
        } else {
          if (messageBox.childNodes[1].childNodes[1].textContent == ">> Is this summary accurate? <<") {
            messageBox.childNodes[1].childNodes[1].style.color = TextColor.Unsure;
            messageBox.style.background = BoxColor.Unsure;
          } else {
            messageBox.style.background = BoxColor.MySure;
          }
        }
      }
      // show other elements in message box
      // show text button
      messageBox.childNodes[1].childNodes[0].style.display = "none";
      messageBox.childNodes[3].childNodes[0].style.display = "block";
      messageBox.childNodes[3].childNodes[0].onclick = function () {
        showFullText(timestamp);
      };
    } else {
      if (messageBox.style.background != BoxColor.GenMySure) {
        if (curMode == "summary") {
          messageBox.style.borderBottom = "0.001em solid rgba(40, 70, 167, 0.7)";
          messageBox.style.background = BoxColor.GenOtherSureTranscript;
        } else {
          messageBox.style.borderBottom = "0.001em solid rgba(40, 167, 70, 0.7)";
          messageBox.style.background = BoxColor.GenOtherSureSummary;
        }
      }
    }


    // Title
    messageBox.childNodes[1].childNodes[1].style.display = "";
    messageBox.childNodes[3].childNodes[1].style.display = "none";
    // text
    setStyleBottomContent(messageBox.childNodes[3].childNodes[2]);
    if (messageBox.childNodes[1].childNodes[2].style.display == "") {
      messageBox.childNodes[3].childNodes[0].innerHTML = "<u>Close</u>";
      messageBox.childNodes[3].childNodes[2].style.display = "";
    }
    setStyleTopContent(messageBox.childNodes[1].childNodes[2]);
  }

  let editBtns = document.getElementsByClassName("edit-btn");

  for (var i = 0; i < editBtns.length; i++) {
    let editBtn = editBtns[i];
    let btnId = editBtn.id;
    let btnInfo = btnId.split("-");

    editBtn.onclick = function () {
      editContent(btnInfo[1], btnInfo[2]);
      rc.addUserLog(
        Date.now(),
        "START-EDIT-MESSAGE/TYPE=" + btnInfo[1] + "/TIMESTAMP=" + btnInfo[2] + "\n"
      );
    };
  }


}

/**
 * set style of box for each mode
 * @param {html object} box : summary box or transcript box
 */
function setStyleCom(box) {
  box.style.fontSize = "medium";
  box.childNodes[1].style.color = TextColor.Normal;
  box.style.marginLeft = "5px";
  box.style.marginTop = "1em";
  box.style.display = "";
}

/**
 * set style of box for each mode
 * @param {html object} box : summary box or transcript box
 */
function setStyleTop(box) {
  box.style.fontSize = "smaller";
  box.style.color = TextColor.Generating;
  box.style.marginLeft = "5px";
  box.style.marginTop = "1em";
}

/**
 * set style of content in box for each mode
 * @param {html object} box : summary box or transcript box
 */
function setStyleTopContent(box) {
  box.style.fontSize = "unset";
  box.style.backgroundColor = "transparent";
  box.style.border = "none";
  box.style.display = "";
  box.style.marginTop = "0px";
  box.style.padding = "0px";
}

/**
 * set style of content in box for each mode
 * @param {html object} box : summary box or transcript box
 */
function setStyleBottomContent(box) {
  box.style.fontSize = "smaller";
  box.style.backgroundColor = "#f2f2f2";
  box.style.borderRadius = "5px";
  box.style.marginTop = "5px";
  box.style.padding = "5px";
  box.style.border = "1px solid #d4d4d4";
  box.style.display = "none";
}

function setStyleSeeButton(button) {
  button.style.fontSize = "x-small";
  button.style.display = "none";
  button.style.border = "0";
  button.style.backgroundColor = "transparent";
  button.style.marginTop = "5px";
}

/**
 * get result of subtask from pop-up
 * @param {JSON} subtaskResult 
 */
function onSaveSubtask(subtaskResult) {

  rc.addSubtaskLog(
    Date.now(),
    JSON.stringify(subtaskResult) + "\n"
  )
}

/**
 * get saved subtask result that user wrote
 * @returns saved subtask result in JSON
 */
function onLoadSubtask() {
  let subtaskResult = rc.loadSubtaskLog();
  return subtaskResult;
}

/**
 * adjust room setting according to room name and user name
 * userRoomCondition = {"user_num" : number, "condition" : n/m, "system" : s/b, "topic" : game/college}
 */
function onUserCondition() {
  let userRoomCondition = rc.loadUserRoomCondition();
  if (userRoomCondition["user_num"] % 2 == 0) {
    let toggleMode = document.getElementById("toggle-mode");

    toggleMode.value = "summary";
    toggleMode.innerText = "Summary Mode";
  }

  let taskImg = document.getElementById("task-img");
  if (userRoomCondition["condition"] == "N") {
    if (userRoomCondition["topic"] == "Game") {       // normal game
      taskImg.src = "../img/NG.PNG";
      console.log("NG")
    } else {                                          // normal college
      taskImg.src = "../img/NC.PNG";
      console.log("NC")
    }
    let subtaskBtn = document.getElementById("subtask");
    subtaskBtn.style.display = "none";
  } else {
    if (userRoomCondition["topic"] == "College") {       // multitasking game
      taskImg.src = "../img/MC.PNG";
      console.log("MC")
      v1s = 18;
      v1e = 16.5;
      v2s = 13;
      v2e = 11.5;
      v3s = 8;
      v3e = 6.5;
      v4s = 3;
      v4e = 1.5;
      tp = 2
      mul_sentences = ['Mr and Mrs Dursley, of number four, Privet Drive, were proud to say that they were perfectly normal, thank you very much.', 'They were the last people you’d expect to be involved in anything strange or mysterious, because they just didn’t hold with such nonsense.', 
        'Mr Dursley was the director of a firm called Grunnings, which made drills.', 'He was a big, beefy man with hardly any neck, although he did have a very large moustache.', 'Mrs Dursley was thin and blonde and had nearly twice the usual amount of neck, which came in very useful as she spent so much of her time craning over garden fences, spying on the neighbours.', 
        'The Dursleys had a small son called Dudley and in their opinion there was no finer boy anywhere.', 'The Dursleys had everything they wanted, but they also had a secret, and their greatest fear was that somebody would discover it.', 'They didn’t think they could bear it if anyone found out about the Potters.', 'Mrs Potter was Mrs Dursley’s sister, but they hadn’t met for several years; in fact, Mrs Dursley pretended she didn’t have a sister, because her sister and her good-for-nothing husband were as unDursleyish as it was possible to be.', 'The Dursleys shuddered to think what the neighbours would say if the Potters arrived in the street.', 'The Dursleys knew that the Potters had a small son, too, but they had never even seen him.', 'This boy was another good reason for keeping the Potters away; they didn’t want Dudley mixing with a child like that.', 'When Mr and Mrs Dursley woke up on the dull, grey Tuesday our story starts, there was nothing about the cloudy sky outside to suggest that strange and mysterious things would soon be happening all over the country.', 'Mr Dursley hummed as he picked out his most boring tie for work and Mrs Dursley gossiped away happily as she wrestled a screaming Dudley into his high chair.', 'None of them noticed a large tawny owl flutter past the window.', 'At half past eight, Mr Dursley picked up his briefcase, pecked Mrs Dursley on the cheek and tried to kiss Dudley goodbye but missed, because Dudley was now having a tantrum and throwing his cereal at the walls.', '‘Little tyke,’ chortled Mr Dursley as he left the house.', 'He got into his car and backed out of number four’s drive.', 'It was on the corner of the street that he noticed the first sign of something peculiar - a cat reading a map.', 'For a second, Mr Dursley didn’t realise what he had seen - then he jerked his head around to look again.', 'There was a tabby cat standing on the corner of Privet Drive, but there wasn’t a map in sight.', 'What could he have been thinking of?', 
        'It must have been a trick of the light.', 'Mr Dursley blinked and stared at the cat. It stared back.', 'As Mr Dursley drove around the corner and up the road, he watched the cat in his mirror.', 'It was now reading the sign that said Privet Drive - no, looking at the sign; cats couldn’t read maps or signs.', 'Mr Dursley gave himself a little shake and put the cat out of his mind.', 'As he drove towards town he thought of nothing except a large order of drills he was hoping to get that day.', 'But on the edge of town, drills were driven out of his mind by something else.', 'As he sat in the usual morning traffic jam, he couldn’t help noticing that there seemed to be a lot of strangely dressed people about. People in cloaks.', 'Mr Dursley couldn’t bear people who dressed in funny clothes - the get-ups you saw on young people!', 'He supposed this was some stupid new fashion.', 'He drummed his fingers on the steering wheel and his eyes fell on a huddle of these weirdos standing quite close by.', 'They were whispering excitedly together.', 'Mr Dursley was enraged to see that a couple of them weren’t young at all; why, that man had to be older than he was, and wearing an emerald-green cloak!', 'The nerve of him!', 'But then it struck Mr Dursley that this was probably some silly stunt - these people were obviously collecting for something ... yes, that would be it.', 'The traffic moved on, and a few minutes later, Mr Dursley arrived in the Grunnings car park, his mind back on drills.', 'Mr Dursley always sat with his back to the window in his office on the ninth floor.', 'If he hadn’t, he might have found it harder to concentrate on drills that morning.', 'He didn’t see the owls swooping past in broad daylight, though people down in the street did; they pointed and gazed open-mouthed as owl after owl sped overhead.', 'Most of them had never seen an owl even at nighttime.', 'Mr Dursley, however, had a perfectly normal, owl-free morning.', 'He yelled at five different people.', 'He made several important telephone calls and shouted a bit more.', 
        'He was in a very good mood until lunch-time, when he thought he’d stretch his legs and walk across the road to buy himself a bun from the baker’s opposite.', 'He’d forgotten all about the people in cloaks until he passed a group of them next to the baker’s.', 'He eyed them angrily as he passed.', 'He didn’t know why, but they made him uneasy.', 'This lot were whispering excitedly, too, and he couldn’t see a single collecting tin.', 'It was on his way back past them, clutching a large doughnut in a bag, that he caught a few words of what they were saying.', '‘The Potters, that’s right, that’s what I heard - yes, their son, Harry -’', 'Mr Dursley stopped dead. Fear flooded him.', 'He looked back at the whisperers as if he wanted to say something to them, but thought better of it.', 'He dashed back across the road, hurried up to his office, snapped at his secretary not to disturb him, seized his telephone and had almost finished dialling his home number when he changed his mind.', 'He put the receiver back down and stroked his moustache, thinking ... no, he was being stupid.', 'Potter wasn’t such an unusual name.', 'He was sure there were lots of people called Potter who had a son called Harry.', 'Come to think of it, he wasn’t even sure his nephew was called Harry.', 'He’d never even seen the boy.', 'It might have been Harvey. Or Harold.', 'There was no point in worrying Mrs Dursley, she always got so upset at any mention of her sister.', 'He didn’t blame her - if he’d had a sister like that... but all the same, those people in cloaks ...', 'He found it a lot harder to concentrate on drills that afternoon, and when he left the building at five o’clock, he was still so worried that he walked straight into someone just outside the door.', '‘Sorry,’ he grunted, as the tiny old man stumbled and almost fell.', 'It was a few seconds before Mr Dursley realised that the man was wearing a violet cloak.', 'He didn’t seem at all upset at being almost knocked to the ground.', 'On the contrary, his face split into a wide smile and he said in a squeaky voice that made passers-by stare:', 
        '‘Don’t be sorry my dear sir, for nothing could upset me today! Rejoice, for You-Know-Who has gone at last! Even Muggles like yourself should be celebrating, this happy happy day!’', 'And the old man hugged Mr Dursley around the middle and walked off.', 'Mr Dursley stood rooted to the spot.', 'He had been hugged by a complete stranger.', 'He also thought he had been called a Muggle, whatever that was.', 'He was rattled.', 'He hurried to his car and set off home, hoping he was imagining things, which he had never hoped before, because he didn’t approve of imagination.', 'As he pulled into the driveway of number four, the first thing he saw - and it didn’t improve his mood - was the tabby cat he’d spotted that morning. It was now sitting on his garden wall.', 'He was sure it was the same one; it had the same markings around its eyes.', '‘Shoo!’ said Mr Dursley loudly.', 'The cat didn’t move.', 'It just gave him a stern look.', 'Was this normal cat behaviour, Mr Dursley wondered.', 'Trying to pull himself together, he let himself into the house.', 'He was still determined not to mention anything to his wife.', 'Mrs Dursley had had a nice, normal day. She told him over dinner all about Mrs Next Door’s problems with her daughter and how Dudley had learnt a new word (‘Shan’t!’).', 'Mr Dursley tried to act normally.', 'When Dudley had been put to bed, he went into the living-room in time to catch the last report on the evening news:', 'And finally, bird-watchers everywhere have reported that the nation’s owls have been behaving very unusually today.', 'Although owls normally hunt at night and are hardly ever seen in daylight, there have been hundreds of sightings of these birds flying in every direction since sunrise.', 'Experts are unable to explain why the owls have suddenly changed their sleeping pattern.', 'The news reader allowed himself a grin.', '‘Most mysterious. And now, over to Jim McGuffin with the weather. Going to be any more showers of owls tonight, Jim?’', '‘Well, Ted,’ said the weatherman, ‘I don’t know about that, but it’s not only the owls that have been acting oddly today.', 
        'Viewers as far apart as Kent, Yorkshire and Dundee have been phoning in to tell me that instead of the rain I promised yesterday, they’ve had a downpour of shooting stars!', 'Perhaps people have been celebrating Bonfire Night early - it’s not until next week, folks!', 'But 1 can promise a wet night tonight.’', 'Mr Dursley sat frozen in his armchair.', 'Shooting stars all over Britain?', 'Owls flying by daylight?', 'Mysterious people in cloaks all over the place?', 'And a whisper, a whisper about the Potters ...', 'Mrs Dursley came into the living-room carrying two cups of tea.', 'It was no good. He’d have to say something to her.', 'He cleared his throat nervously.', '‘Er - Petunia, dear - you haven’t heard from your sister lately, have you?’', 'As he had expected, Mrs Dursley looked shocked and angry.', 'After all, they normally pretended she didn’t have a sister.', '‘No,’ she said sharply. ‘Why?’', '‘Funny stuff on the news,’ Mr Dursley mumbled.', '‘Owls ... shooting stars ... and there were a lot of funny-looking people in town today ...’', '‘So?’ snapped Mrs Dursley.', '‘Well, I just thought ... maybe ... it was something to do with ... you know ... her lot.’', 'Mrs Dursley sipped her tea through pursed lips.', 'Mr Dursley wondered whether he dared tell her he’d heard the name ‘Potter’.', 'He decided he didn’t dare. Instead he said, as casually as he could,', '‘Their son - he’d be about Dudley’s age now, wouldn’t he?’', '‘I suppose so,’ said Mrs Dursley stiffly.', '‘What’s his name again? Howard, isn’t it?’', '‘Harry. Nasty, common name, if you ask me.’', '‘Oh, yes,’ said Mr Dursley, his heart sinking horribly. ‘Yes, I quite agree.’', 'He didn’t say another word on the subject as they went upstairs to bed.', 'While Mrs Dursley was in the bathroom, Mr Dursley crept to the bedroom window and peered down into the front garden.', 'The cat was still there. It was staring down Privet Drive as though it was waiting for something.', 'Was he imagining things? Could all this have anything to do with the Potters?', 'If it did ... if it got out that they were related to a pair of - well, he didn’t think he could bear it.', 
        'The Dursleys got into bed. Mrs Dursley fell asleep quickly but Mr Dursley lay awake, turning it all over in his mind.', 'His last, comforting thought before he fell asleep was that even if the Potters were involved, there was no reason for them to come near him and Mrs Dursley.', 'The Potters knew very well what he and Petunia thought about them and their kind ...', 'He couldn’t see how he and Petunia could get mixed up in anything that might be going on.', 'He yawned and turned over. It couldn’t affect them ...', 'How very wrong he was.', 'Mr Dursley might have been drifting into an uneasy sleep, but the cat on the wall outside was showing no sign of sleepiness.', 'It was sitting as still as a statue, its eyes fixed unthinkingly on the far corner of Privet Drive.', 'It didn’t so much as quiver when a car door slammed in the next street, nor when two owls swooped overhead.', 'In fact, it was nearly midnight before the cat moved at all.', 'A man appeared on the corner the cat had been watching, appeared so suddenly and silently you’d have thought he’d just popped out of the ground.', 'The cat’s tail twitched and its eyes narrowed.', 'Nothing like this man had ever been seen in Privet Drive.', 'He was tall, thin and very old, judging by the silver of his hair and beard, which were both long enough to tuck into his belt.', 'He was wearing long robes, a purple cloak which swept the ground and high-heeled, buckled boots.', 'His blue eyes were light, bright and sparkling behind half-moon spectacles and his nose was very long and crooked, as though it had been broken at least twice.', 'This man’s name was Albus Dumbledore.', 'Albus Dumbledore didn’t seem to realise that he had just arrived in a street where everything from his name to his boots was unwelcome.', 'He was busy rummaging in his cloak, looking for something.', 'But he did seem to realise he was being watched, because he looked up suddenly at the cat, which was still staring at him from the other end of the street.', 'For some reason, the sight of the cat seemed to amuse him.', 'He chuckled and muttered, ‘I should have known.’', 'He had found what he was looking for in his inside pocket.', 
        'It seemed to be a silver cigarette lighter.', 'He flicked it open, held it up in the air and clicked it.', 'The nearest street lamp went out with a little pop.', 'He clicked it again - the next lamp flickered into darkness.', 'Twelve times he clicked the Put-Outer, until the only lights left in the whole street were two tiny pinpricks in the distance, which were the eyes of the cat watching him.', 'If anyone looked out of their window now, even beady-eyed Mrs Dursley, they wouldn’t be able to see anything that was happening down on the pavement.'];
    } else {                                          // multitasking college
      taskImg.src = "../img/MG.PNG";
      console.log("MG")
      v1s = 19.5;
      v1e = 19;
      v2s = 18.8;
      v2e = 18.5;
      v3s = 0;
      v3e = 0;
      v4s = 0;
      v4e = 0;
      tp = 1
      mul_sentences = ['He was an old man who fished alone in a skiff in the Gulf Stream and he had gone eighty-four days now without taking a fish.', 'In the first forty days a boy had been with him.', "But after forty days without a fish the boy's parents had told him that the old man was now definitely and finally salao, which is the worst form of unlucky, and the boy", 'had gone at their orders in another boat which caught three good fish the first week.', 'It made the boy sad to see the old man come in each day with his skiff empty and he always went down to help him carry either the coiled lines or the gaff and harpoon and the sail that was furled around the mast.', 'The sail was patched with flour sacks and, furled, it looked like the flag of permanent defeat.', 'The old man was thin and gaunt with deep wrinkles in the back of his neck.', 'The brown blotches of the benevolent skin cancer the sun brings from its reflection on the tropic sea were on his cheeks.', 'The blotches ran well down the sides of his face and his hands had the deep-creased scars from handling heavy fish on the cords.', 'But none of these scars were fresh.', 'They were as old as erosions in a fishless desert.', 'Everything about him was old except his eyes and they were the same color as the sea and were cheerful and undefeated.', '"Santiago," the boy said to him as they climbed the bank from where the skiff was hauled up.', '"I could go with you again.  We\'ve made some money."', 'The old man had taught the boy to fish and the boy loved him.', '"No," the old man said.', '"You\'re with a lucky boat.  Stay with them."', '"But remember how you went eighty-seven days without fish and then we caught big ones every day for three weeks."', '"I remember," the old man said.', '"I know you did not leave me because you doubted."', '"It was papa made me leave.  I am a boy and I must obey him."', '"I know," the old man said.', '"It is quite normal."', '"He hasn\'t much faith."', '"No," the old man said.', '"But we have.  Haven\'t we?"', '"Yes," the boy said.', '"Can I offer you a beer on the Terrace and then we\'ll take the stuff home."', '"Why not?" the old man said.', '"Between fishermen."']
    }
    document.getElementById('mul_text').innerText = mul_sentences[0];
  }

  if (userRoomCondition["system"] == "B") {           // baseline
    let panel = document.getElementById("right");
    let base = document.getElementById("baseline");
    panel.hidden = true;
    base.hidden = false;
    console.log("B")
  } else {

    console.log("S")
  }
}

// typing multitasking
function submitMulText() {
  var multext = document.getElementById('mul_textarea').value;

  if (multext.length > 0) {
    //console.log(multext)
    document.getElementById('mul_textarea').value = "";
    
    mtidx = mtidx + 1;

    if (mtidx == mul_sentences.length) {
      mtidx = 0;
    }

    document.getElementById('mul_text').innerText = mul_sentences[mtidx];

    rc.addSubtaskLog(
      Date.now(),
      multext + "\n"
    )
  }
}
