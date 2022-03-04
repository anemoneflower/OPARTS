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

// SUBTASK MODAL
var modal = document.getElementById("subtaskModal");
var close_modal = document.getElementsByClassName("closeModal")[0];
var isTriggered = false;

close_modal.onclick = function () {
  modal.style.display = "none";
};
window.onclick = function (event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
};

/************************************************************************************************
 * Timer & Subtask Related Functions
************************************************************************************************/
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
    }
    // Time remaining for starting subtask
    else {
      if (distDt < 25 * 60 * 1000) {
        document.getElementById(id).textContent =
          word + " (" + minutes + "m " + seconds + "s)";
        document.getElementById(id).removeAttribute("disabled");
        if (!isTriggered) {
          modal.style.display = "block";
          isTriggered = true;
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

// Open popup for subtask
function openSubtask() {
  rc.addUserLog(Date.now(), "OPEN-SUBTASK\n");
  subtaskPopup = window.open(
    "../subtask.html",
    "_blank",
    "toolbar=yes,scrollbars=yes,resizable=yes,top=100,left=100,width=1200,height=1000"
  );
  subtaskPopup.onbeforeunload = function () {
    overlay_off();
    rc.addUserLog(Date.now(), "CLOSE-SUBTASK\n");
  };
}

function overlay_on() {
  document.getElementById("overlay").style.display = "block";
  document.getElementById("left-navbar").style.transform = "translateY(100%)";
}

function overlay_off() {
  document.getElementById("overlay").style.display = "none";
  document.getElementById("left-navbar").style.transform = "translateY(0)";
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
  overlay_on();
});

window.addEventListener('focus', function () {
  // console.log("WINDOW FOCUS ON - timestamp=" + Date.now());
  rc.addUserLog(Date.now(), "WINDOW-FOCUS-ON\n");
  overlay_off();
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
    rc.addUserLog(
      Date.now(),
      "TOGGLE-MODE/SUMMARY"
    );
  } else {
    rc.addUserLog(
      Date.now(),
      "TOGGLE-MODE/TRANSCRIPT"
    );
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
    if (userRoomCondition["topic"] == "Game") {       // multitasking game
      taskImg.src = "../img/MG.PNG";
      console.log("MG")
    } else {                                          // multitasking college
      taskImg.src = "../img/MC.PNG";
      console.log("MC")
    }
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
