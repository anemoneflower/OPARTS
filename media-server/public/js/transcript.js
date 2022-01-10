// transcript.js
// Defines event handlers for transcripts from moderator server.
// Includes UI control on transcription and summary data arrival.

const messages = document.getElementById("messages");
const trendingBox = document.getElementById("keywords-list");

const UnsureMessage_color = "rgba(117, 117, 117, 0.3)"; //"rgba(255, 208, 205, 1)"
const SureMessage_Mycolor = "rgba(40, 70, 167, 0.219)";
const SureMessage_Othercolor = "rgba(40, 167, 70, 0.219)";
const NotConfident_color = "rgba(44, 30, 187, 1)";
const confidence_limit = 0.5;

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

var startTime = new Date();
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
      if (distDt < 2 * 60 * 1000) {
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

function onStartTimer(startTime) {
  startTime = new Date(startTime);
  let usernumber = parseInt(
    user_name.slice(user_name.length - 1, user_name.length)
  );
  console.log("onStartTimer()", startTime, "USER-NUMBER", usernumber);

  if (!isNaN(usernumber)) {
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

// Logging Window Focus ON/OFF
window.addEventListener('blur', function () {
  // console.log("WINDOW FOCUS OFF - timestamp=" + Date.now());
  rc.addUserLog(Date.now(), "WINDOW-FOCUS-OFF\n");
});

window.addEventListener('focus', function () {
  // console.log("WINDOW FOCUS ON - timestamp=" + Date.now());
  rc.addUserLog(Date.now(), "WINDOW-FOCUS-ON\n");
});

// Logging Scroll Event
messages.addEventListener("wheel", function (event) {
  window.clearTimeout(isScrolling); // Clear our timeout throughout the scroll
  isScrolling = setTimeout(function () {
    // Set a timeout to run after scrolling ends
    if (messages.scrollTop > scrollPos) {
      // console.log("SCROLL-DOWN");
      rc.addUserLog(Date.now(), "SCROLL-DOWN/POS=" + messages.scrollTop + "\n");
    }
    else if (messages.scrollTop < scrollPos) {
      // console.log("SCROLL-UP");
      rc.addUserLog(Date.now(), "SCROLL-UP/POS=" + messages.scrollTop + "\n");
    }
    scrollPos = messages.scrollTop;
  }, 66);
});

function onUpdateParagraph(newParagraph, summaryArr, confArr, timestamp, editTimestamp) {
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
  let paragraph = messageBox.childNodes[3].childNodes[1];
  let summaryEl = messageBox.childNodes[1];
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
    summaryEl.childNodes[1].textContent +
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
    if (confArr[0] < confidence_limit) {
      // LOW CONFIDENCE SCORE
      summaryEl.childNodes[0].textContent = ">> Is this an accurate summary? <<";
      summaryEl.childNodes[0].style.color = NotConfident_color;

      messageBox.style.background = UnsureMessage_color;
    } else if (confArr[0] <= 1) {
      // HIGH CONFIDENCE SCORE
      summaryEl.childNodes[0].textContent = ">> Summary <<";
      if (user_name === speaker) {
        messageBox.style.background = SureMessage_Mycolor;
      } else {
        messageBox.style.background = SureMessage_Othercolor;
      }
    }
  }
  summaryEl.childNodes[0].style.fontWeight = "bold";
  summaryEl.childNodes[1].textContent = summaryArr[0];

  // Add edited tag on new summary
  let sumeditTag = document.getElementById("editTag-summary-" + timestamp.toString());
  if (!sumeditTag) {
    sumeditTag = document.createElement("span");
    sumeditTag.setAttribute("id", "editTag-summary-" + timestamp.toString());
    sumeditTag.style = "font-size:0.8em; color:gray";
    summaryEl.childNodes[1].append(sumeditTag);
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
  addEditBtn(summaryEl.childNodes[1], "summary", timestamp);
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

function onRestore(past_paragraphs) {
  console.log("onRestore: Restore past paragraphs");
  for (var timestamp in past_paragraphs) {
    let messageBox = getMessageBox(timestamp);
    if (messageBox) continue;

    let datas = past_paragraphs[timestamp];

    // Restore past paragraphs
    messageBox = createMessageBox(datas["speakerName"], timestamp);

    let transcript, summaryArr, confArr, name, hasSummary;
    let newsum = "";

    if (Object.keys(datas["editTrans"]).length === 0) {
      transcript = datas["ms"].join(" ");

      if (Object.keys(datas["sum"]).length === 0) hasSummary = false;
      else {
        hasSummary = true;
        summaryArr = datas["sum"]["summaryArr"];
        confArr = datas["sum"]["confArr"];
        name = datas["speakerName"];
      }
    } else {
      var lastKey = Object.keys(datas["editTrans"])[
        Object.keys(datas["editTrans"]).length - 1
      ];
      transcript = datas["editTrans"][lastKey]["content"];

      hasSummary = true;
      summaryArr = datas["editTrans"][lastKey]["sum"][0];
      confArr = datas["editTrans"][lastKey]["sum"][1];
      name = datas["speakerName"];
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
    let paragraph = messageBox.childNodes[3].childNodes[1];
    paragraph.textContent = transcript;

    // remove deleted paragraphs
    if (!transcript) {
      messageBox.remove();
      continue;
    }

    if (hasSummary) {
      onSummary(summaryArr, confArr, name, timestamp);
    }

    let seeFullText = messageBox.childNodes[3].childNodes[0];
    seeFullText.style.display = "block";

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

function onUpdateSummary(type, content, timestamp, editTimestamp) {
  // Use updateSummary function for pin, addkey, delkey
  if (type === "pin") {
    pinBox(timestamp);
    return;
  }

  let messageBox = document.getElementById(timestamp.toString());
  let summaryEl = null;
  let msg = "New summary contents: " + timestamp + "\n";
  if (type == "summary") {
    summaryEl = messageBox.childNodes[1];
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
    messageBox.style.background = SureMessage_Mycolor;
  } else {
    messageBox.style.background = SureMessage_Othercolor;
  }

  rc.addUserLog(
    Date.now(),
    "UPDATE-SUMMARY-MESSAGEBOX/TIMESTAMP=" +
    timestamp +
    "/NEW-SUMMARY=" +
    content +
    "/OLD-SUMMARY=" +
    summaryEl.childNodes[1].textContent +
    "\n"
  );

  summaryEl = messageBox.childNodes[1];
  summaryEl.childNodes[0].textContent = ">> Summary <<"; // if user change summary, confidence score would be 100 %
  summaryEl.childNodes[1].textContent = content;

  // Add edited tag on new summary
  let editTag = document.getElementById("editTag-summary-" + timestamp.toString());
  if (!editTag) {
    editTag = document.createElement("span");
    editTag.setAttribute("id", "editTag-summary-" + timestamp.toString());
    editTag.style = "font-size:0.8em; color:gray";
    summaryEl.childNodes[1].append(editTag);
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
  addEditBtn(summaryEl.childNodes[1], type, timestamp);
}

function removeMsg(timestamp) {
  console.log("ON RemoveMsg - timestamp = ", timestamp);
  let messageBox = getMessageBox(timestamp);
  if (messageBox) {
    messageBox.remove();
  }
}

// Event listener on individual transcript arrival.
function onTranscript(transcript, name, timestamp) {
  console.log("ON TRANSCRIPT - timestamp=" + timestamp);
  if (!timestamp) {
    console.log("invalid timestamp!!", transcript, name, timestamp);
    return;
  }
  if (!transcript || transcript.trim().length == 0) {
    console.log("EMPTY TRANSCRIPT!!! REMOVE MSG BOX FROM ", name, " at ", timestamp);
    removeMsg(timestamp);
    return;
  }

  let messageBox = getMessageBox(timestamp);
  if (!messageBox) {
    messageBox = createMessageBox(name, timestamp);
  }

  let seeFullText = messageBox.childNodes[3].childNodes[0];
  seeFullText.style.display = "block";

  // Append the new transcript to the old paragraph.
  let paragraph = messageBox.childNodes[3].childNodes[1];
  paragraph.textContent = transcript;

  // Filtering with new message box
  displayUnitOfBox();
}

function onKeyword(keywordList, name, timestamp) {
  console.log("ON KEYWORD - timestamp = " + timestamp);
  let messageBox = getMessageBox(timestamp);
  if (!messageBox) {
    messageBox = createMessageBox(name, timestamp);
  }
  // Filtering with new message box
  displayUnitOfBox();

  addKeywordsListBlockHelper(timestamp, keywordList);
}

// Event listener on summary arrival.
function onSummary(summaryArr, confArr, name, timestamp) {
  console.log("ON SUMMARY - timestamp=" + timestamp);
  let messageBox = getMessageBox(timestamp);
  if (!messageBox) {
    // messageBox = createMessageBox(name, timestamp);
    console.log("[onSummary] No messageBox ERROR:", summaryArr, confArr, name, timestamp);
  }
  // Filtering with new message box
  displayUnitOfBox();

  if ((summaryArr[0].trim().length == 0) && (summaryArr[1].trim().length == 0)) {
    console.log("No summary:: Delete msg box: ", timestamp);
    removeMsg(timestamp);
  }

  let maxConf = Math.max(...confArr);
  let displaySum = (maxConf === confArr[0]) ? summaryArr[0] : summaryArr[1];

  if (maxConf < confidence_limit) {
    messageBox.style.background = UnsureMessage_color;
  }

  let seeFullText = messageBox.childNodes[3].childNodes[0];
  seeFullText.style.display = "block";
  let paragraph = messageBox.childNodes[3].childNodes[1];
  paragraph.style.display = "none";

  let summaryBox = messageBox.childNodes[1];
  var keywordList = summaryArr[2].split("@@@@@CD@@@@@AX@@@@@");
  keywordList = keywordList.filter((item) => item);
  keywordMap[timestamp.toString()] = keywordList;

  addKeywordsListBlockHelper(timestamp, keywordList);

  // Add buttons for trending keywords
  var trendingList = summaryArr[3].split("@@@@@CD@@@@@AX@@@@@");
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

  // If confidence === -1, the summary result is only the paragraph itself.
  // Do not put confidence element as a sign of "this is not a summary"
  if (maxConf != -1) {
    if (maxConf < confidence_limit) {
      summaryBox.childNodes[0].textContent = ">> Is this an accurate summary? <<";
      summaryBox.childNodes[0].style.color = NotConfident_color;
    } else if (maxConf <= 1) {
      summaryBox.childNodes[0].textContent = ">> Summary <<";
    }
  }

  summaryBox.childNodes[0].style.fontWeight = "bold";
  summaryBox.childNodes[1].textContent = displaySum;

  // Add edit button in order to allow user change contents (paragraph, absummary, exsummary)
  // let paragraph = messageBox.childNodes[3].childNodes[0];
  addEditBtn(paragraph, "paragraph", timestamp);
  addEditBtn(summaryBox.childNodes[1], "summary", timestamp);

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

function addKeywordsListBlockHelper(timestamp, keywords) {
  let msgBox = getMessageBox(timestamp);
  msgBox.childNodes[2].innerHTML = "";

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

function editContent(type, timestamp) {
  let messageBox = document.getElementById(timestamp.toString());
  let oldtxt = null;
  let editTag = null;
  switch (type) {
    case "paragraph":
      let paragraph = messageBox.childNodes[3].childNodes[1];
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

      // paragraph.textContent = oldtxt.valueOf().split(" (edited)")[0];
      paragraph.lastChild.onclick = function () {
        finishEditContent("paragraph", oldtxt, timestamp, original);
      };
      paragraph.addEventListener("keypress", function (event) {
        // event.preventDefault();
        if (event.keyCode === 13) {
          finishEditContent("paragraph", oldtxt, timestamp, original);
        }
      });

      break;
    case "summary":
      let summary = messageBox.childNodes[1].childNodes[1];
      summary.contentEditable = "true";

      // change icon
      console.log("editContent-summary: ", summary);
      // console.log(summary.lastChild);

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

      // summary.textContent = oldtxt.valueOf().split(" (edited)")[0];
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
  let messageBox = document.getElementById(timestamp.toString());

  let editTimestamp = Date.now();
  let editTag;

  // Remove edited tag in oldtxt if exist
  let oldtxt_value = oldtxt.valueOf().trim();

  switch (type) {
    case "paragraph":
      let paragraph = messageBox.childNodes[3].childNodes[1];
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
        paragraph.style.backgroundColor = "#f2f2f2";
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
        // console.log(paragraph);
        // console.log(paragraph.childNodes[1]);
        toEditableIcon(paragraph.childNodes[1])

        editTag = document.getElementById("editTag-paragraph-" + timestamp.toString());
        if (editTag) {
          editTag.hidden = false;
        }

        paragraph.childNodes[1].onclick = function () {
          editContent(type, timestamp);
        };
        paragraph.style.backgroundColor = "#f2f2f2";
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
        summary = messageBox.childNodes[1].childNodes[1];
      }
      toEditableBg(summary);
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

// Display boxes with trending keywords
function displayTrendingHelper(keywordBtn) {
  let searchword = document.getElementById("search-word");
  searchword.value = keywordBtn.textContent.slice(1);
  removeSummaryBox();
  displayUnitOfBox();
  rc.addUserLog(
    Date.now(),
    "SEARCH-TRENDINGWORDS/MSG=" + searchword.value + "\n"
  );
}

var highlighter = new Hilitor();

function addSearchLog() {
  // console.log("addSearchLog")
  let searchword = document.getElementById("search-word").value.trim();
  rc.addUserLog(Date.now(), "SEARCH-WORD/MSG=" + searchword + "\n");
}

function displayUnitOfBox() {
  let searchword = document.getElementById("search-word").value.trim();
  let messageBoxes = document.getElementsByClassName("message-box");
  let paragraphs = document.getElementsByClassName("paragraph");

  for (var i = 0; i < messageBoxes.length; i++) {
    let isfiltered = paragraphs[i].textContent.includes(searchword.trim());
    let messageBox = messageBoxes[i];

    // check if paragraph is empty
    if (!messageBox.childNodes[3].childNodes[1].textContent.trim()) {
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
  searchword.value = keyword;
  displayUnitOfBox();
  createSummaryBox(keyword);
  let editTimestamp = Date.now();
  // rc.addUserLog(Date.now(), "SEARCH-FAVORITE/MSG=" + keyword + "\n");

  let messageBoxes = document.getElementsByClassName("message-box");
  let paragraphs = document.getElementsByClassName("paragraph");

  keywordParagraph = "";
  for (var i = 0; i < messageBoxes.length; i++) {
    let isfiltered = paragraphs[i].textContent.includes(keyword);
    let messageBox = messageBoxes[i];
    if (isfiltered) {
      keywordParagraph +=
        " " + messageBox.childNodes[3].childNodes[1].textContent;
    }
  }

  rc.addUserLog(
    Date.now(),
    "SEARCH-TRENDINGWORDS/MSG=" + searchword.value + "\n"
  );
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

// Helper function for searching when ENTER keydown
function checkEnter(e) {
  if (e.code === "Enter") {
    console.log("Enter press on search!");
    removeSummaryBox();
    addSearchLog();
    displayUnitOfBox();
  }
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

// Change given box's css style to bigger text
function displayBig(box) {
  box.style.marginLeft = "";
  box.style.fontSize = "medium";
  box.style.display = "";
}

// Reduce size of box and add left margin
function displaySm(box) {
  box.style.marginLeft = "1em";
  box.style.fontSize = "smaller";
  box.style.display = "";
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

// Display boxes if 'cond' is true, use given function 'fn' to show the box
function displayBoxes(cond, boxes, fn) {
  for (let box of boxes) {
    displayBox(cond, box, fn);
  }
}

// Creates a container element (message box)
// that holds a paragraph and its summary.
// The timestamp acts as an identifier for the element.
function createMessageBox(name, timestamp) {
  let messageBox = document.createElement("div");
  messageBox.setAttribute("id", timestamp.toString());
  messageBox.className = "message-box";

  if (user_name == name) {
    messageBox.style.borderBottom = "0.001em solid rgba(40, 70, 167, 0.5)";
    messageBox.style.background = SureMessage_Mycolor;
  }

  // messageBox.childNodes[0]: includes title - timestamp and name.
  let title = document.createElement("div");
  let nametag = document.createElement("span");
  let strong = document.createElement("strong");
  strong.textContent = name;
  nametag.className = "nametag";
  nametag.append(strong);

  let timetag = document.createElement("span");
  timetag.className = "timetag";
  timetag.append(document.createTextNode(formatTime(timestamp)));
  title.append(nametag, timetag);

  // Add pin button
  let pinBtn = document.createElement("button");
  let pin = document.createElement("i");
  pin.className = "fas fa-thumbtack";
  pin.style.color = "#F2F3F4";
  pinBtn.append(pin);
  pinBtn.style.backgroundColor = "transparent";
  pinBtn.style.border = "0";
  pinBtn.style.float = "right";
  pinBtn.style.display = "inline-block";
  messageBox.setAttribute("pinned", "false");
  pinBtn.onclick = function () {
    rc.updateSummary("pin", "pinBox", timestamp, Date.now());
    if (messageBox.getAttribute("pinned") === "false") {
      rc.addUserLog(
        Date.now(),
        "PIN-BOX/TIMESTAMP=" + timestamp.toString() + "\n"
      );
    } else {
      rc.addUserLog(
        Date.now(),
        "UNPIN-BOX/TIMESTAMP=" + timestamp.toString() + "\n"
      );
    }
  };

  title.append(pinBtn);
  messageBox.append(title);

  // messageBox.childNodes[1]: includes the abstractive summary and confidence level
  let summaryBox = document.createElement("div");
  summaryBox.className = "ab-summary-box";
  summaryBox.style.fontSize = "medium";
  summaryBox.style.marginLeft = "5px";
  summaryBox.style.marginTop = "1em";

  let summaryTitle = document.createElement("p");
  let summaryContent = document.createElement("p");

  summaryBox.append(summaryTitle);
  summaryBox.append(summaryContent);

  messageBox.append(summaryBox);

  // messageBox.childNodes[2]: includes the keywords
  let keywordBox = document.createElement("div");
  keywordBox.className = "keyword-box";
  keywordBox.style.fontSize = "smaller";
  keywordBox.style.marginLeft = "5px";
  keywordBox.style.marginBottom = "5px";
  messageBox.append(keywordBox);

  // messageBox.childNodes[3]: childNodes[0] = Button, childNodes[1] = Full paragraph
  let paragraphBox = document.createElement("div");

  let seeFullText = document.createElement("button");
  seeFullText.className = "seeFullText";
  seeFullText.style.fontSize = "x-small";
  seeFullText.style.display = "none";
  seeFullText.style.border = "0";
  seeFullText.style.backgroundColor = "transparent";
  seeFullText.style.marginTop = "5px";
  seeFullText.innerHTML = "<u>Full Script</u>";
  seeFullText.onclick = function () {
    showFullText(timestamp);
  };
  paragraphBox.append(seeFullText);

  let paragraph = document.createElement("p");
  paragraph.className = "paragraph";
  paragraph.style.fontSize = "smaller";
  paragraph.style.backgroundColor = "#f2f2f2";
  paragraph.style.borderRadius = "5px";
  paragraph.style.marginTop = "5px";
  paragraph.style.padding = "5px";
  paragraph.style.border = "1px solid #d4d4d4";
  paragraph.style.display = "none";
  paragraphBox.append(paragraph);

  messageBox.append(paragraphBox);

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
    let name = document.createElement("strong");
    name.textContent =
      "[" +
      messageBox.childNodes[0].childNodes[0].childNodes[0].textContent +
      "] ";
    name.style.marginLeft = "5px";
    let textCont = document.createElement("p");
    textCont.textContent =
      messageBox.childNodes[1].childNodes[1].textContent.substr(0, 50) + " ...";
    textCont.style.margin = "3px 5px 3px 5px";
    newPin.append(name);
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

function showPinBoxes() {
  let pinClick = document.getElementById("dropdownPin");
  if (pinClick.style.display === "none") {
    rc.addUserLog(Date.now(), "PIN-DROPDOWN-PIN-OPEN\n");
    pinClick.style.display = "block";
  } else {
    rc.addUserLog(Date.now(), "PIN-DROPDOWN-CLOSE\n");
    pinClick.style.display = "none";
  }
}

// Shows the full paragraph in each message box
function showFullText(timestamp) {
  let messageBox = document.getElementById(timestamp.toString());

  if (messageBox.childNodes[3].childNodes[1].style.display == "") {
    rc.addUserLog(
      Date.now(),
      "CLICK-HIDE-FULL-TEXT/TIMESTAMP=" + timestamp.toString() + "\n"
    );
    messageBox.childNodes[3].childNodes[1].style.display = "none";
    messageBox.childNodes[3].childNodes[0].innerHTML = "<u>Full Script</u>";
  } else {
    rc.addUserLog(
      Date.now(),
      "CLICK-SEE-FULL-TEXT/TIMESTAMP=" + timestamp.toString() + "\n"
    );
    messageBox.childNodes[3].childNodes[1].style.display = "";
    messageBox.childNodes[3].childNodes[0].innerHTML = "<u>Close</u>";
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

// Returns a span element that represents confidence level.
function confidenceElement(confidence) {
  let percentage = (confidence * 100).toFixed(1) + "%";
  let emoji = "";
  let color = "";

  if (confidence < 0.33) {
    emoji = " \u{1F641}";
    color = "red";
  } else if (confidence < confidence_limit) {
    emoji = " \u{1F610}";
    color = "blue";
  } else {
    emoji = " \u{1F600}";
    color = "green";
  }

  let elem = document.createElement("span");
  elem.style.color = color;
  elem.style.fontSize = "smaller";
  elem.textContent = emoji + " " + percentage;

  return elem;
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
