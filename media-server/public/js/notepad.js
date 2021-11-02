// notepad.js
// Defines event handlers for notepad.

moderatorSocket.on("updateNotePad", onUpdateNotePad);

/**
 * @anemoneflower add comment
 * 회의록 저장 함수
 * TODO: 사용자 구분
 * TODO: 수정이력 저장 + Restore
 * TODO: Logging
 */
function save_note() {
  let notepad = document.getElementById("notepad");
  console.log(notepad.value);
  rc.updateNotePad(notepad.value);
}

/**
 * @anemoneflower add comments
 * 회의록 작성자가 저장한 content를 각 user에게 보여주는 함수
 * @param {*} content 
 * @param {*} userkey 
 */
function onUpdateNotePad(content, userkey) {
  // console.log("onUpdateNotePad", content, userkey);
  if (userkey == 1) {
    let note1Content = document.getElementById("notepad-1");
    note1Content.textContent = content;
  }
  else { //userkey == 2
    let note2Content = document.getElementById("notepad-2");
    note2Content.textContent = content;
  }
}

function showTap(key) {
  let writeBtn = document.getElementById("note-write");
  let note1Btn = document.getElementById("note-1");
  let note2Btn = document.getElementById("note-2");
  let taskBtn = document.getElementById("task");

  let writeContent = document.getElementById("notepad-group");
  let note1Content = document.getElementById("notepad-1");
  let note2Content = document.getElementById("notepad-2");
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
