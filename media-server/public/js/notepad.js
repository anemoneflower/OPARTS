// notepad.js
// Defines event handlers for notepad.

moderatorSocket.on("updateNotePad", onUpdateNotePad);

/**
 * Save updated notepad contents
 * 
 * TODO: 수정이력 저장 + Restore
 * TODO: Logging
 */
function save_note() {
  let notepad = document.getElementById("notepad");
  let updateTimestamp = Date.now()
  console.log(notepad.value, updateTimestamp);
  rc.updateNotePad(notepad.value, updateTimestamp);
}

/**
 * Show updated notepad contents to users.
 * 
 * @param {string} content Notepad content
 * @param {int} userkey Userkey 1==Writer1, 2==Writer2
 * @param {timestamp} updateTimestamp
 */
function onUpdateNotePad(content, userkey, updateTimestamp) {
  console.log("onUpdateNotePad", content, userkey, updateTimestamp);
  let writerTag = document.getElementById("saveTag-writer");
  writerTag.style = "font-size:0.8em; color:gray";
  writerTag.textContent = " (saved " + formatTime(updateTimestamp) + ")";

  if (userkey == 1) {
    let note1Content = document.getElementById("notepad-1");
    note1Content.textContent = content;

    let saveTag = document.getElementById("saveTag-viewer-1");
    saveTag.style = "font-size:0.8em; color:gray";
    saveTag.textContent = " (saved " + formatTime(updateTimestamp) + ")";
  }
  else { //userkey == 2
    let note2Content = document.getElementById("notepad-2");
    note2Content.textContent = content;

    let saveTag = document.getElementById("saveTag-viewer-2");
    saveTag.style = "font-size:0.8em; color:gray";
    saveTag.textContent = " (saved " + formatTime(updateTimestamp) + ")";
  }
}

function showTap(key) {
  let writeBtn = document.getElementById("note-write");
  let note1Btn = document.getElementById("note-1");
  let note2Btn = document.getElementById("note-2");
  let taskBtn = document.getElementById("task");

  let writeContent = document.getElementById("notepad-group");
  let note1Content = document.getElementById("notearea-1");
  let note2Content = document.getElementById("notearea-2");
  let taskContent = document.getElementById("task-img");

  switch (key) {
    case 'Write':
      toDarkBtns([writeBtn]);
      toLightBtns([note1Btn, note2Btn, taskBtn]);

      writeContent.hidden = false;
      note1Content.hidden = true;
      note2Content.hidden = true;
      taskContent.hidden = true;
      break;
    case 'Note1':
      toDarkBtns([note1Btn]);
      toLightBtns([writeBtn, note2Btn, taskBtn]);

      writeContent.hidden = true;
      note1Content.hidden = false;
      note2Content.hidden = true;
      taskContent.hidden = true;
      break;
    case 'Note2':
      toDarkBtns([note2Btn]);
      toLightBtns([writeBtn, note1Btn, taskBtn]);

      writeContent.hidden = true;
      note1Content.hidden = true;
      note2Content.hidden = false;
      taskContent.hidden = true;
      break;
    case 'Task':
      toDarkBtns([taskBtn]);
      toLightBtns([writeBtn, note1Btn, note2Btn]);

      writeContent.hidden = true;
      note1Content.hidden = true;
      note2Content.hidden = true;
      taskContent.hidden = false;
      break;
  }
}

/***************************************************
 * Helper Functions
****************************************************/

function toDarkBtns(btnList) {
  btnList.forEach(btn => {
    btn.classList.remove('btn-outline-dark');
    btn.classList.add('btn-dark');
  })
}

function toLightBtns(btnList) {
  btnList.forEach(btn => {
    btn.classList.remove('btn-dark');
    btn.classList.add('btn-outline-dark');
  })
}
