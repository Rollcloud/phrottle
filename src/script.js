"use strict";

const clientID = undefined;
const serverSocket = new WebSocket("ws://" + location.host + "/move");
serverSocket.onerror = (event) => {
  console.log("WebSocket error: ", event);
};

const send_message = (type, text) => {
  const message = {
    type: type,
    text: text,
    id: clientID,
    date: Date.now(),
  };
  serverSocket.send(JSON.stringify(message));
};
const display_message = (text) => {
  const li = document.createElement("li");
  li.classList.add("list-group-item", "bg-dark", "text-light", "text-opacity-75");
  li.textContent = text;
  statusList.prepend(li);

  while (statusList.childNodes.length > 5) {
    statusList.removeChild(statusList.childNodes[statusList.childNodes.length - 1]);
  }
};

const statusList = document.querySelector("#status-list");

serverSocket.onopen = () => {
  send_message("ping", "");
};
serverSocket.onmessage = (event) => {
  console.log(event.data);
  const message = JSON.parse(event.data);
  if (message["type"] == "pong") display_message("ready");
  else if (message["type"] == "ack") display_message(message["text"]);
};

let moveLeftBtn = document.querySelector("#move-left");
let moveRightBtn = document.querySelector("#move-right");

const move_left = () => {
  send_message("move", "left");
};
const move_right = () => {
  send_message("move", "right");
};
const stop = () => {
  send_message("stop", "");
};

moveLeftBtn.addEventListener("touchstart", move_left);
moveLeftBtn.addEventListener("mousedown", move_left);
moveLeftBtn.addEventListener("touchend", stop);
moveLeftBtn.addEventListener("mouseup", stop);

moveRightBtn.addEventListener("touchstart", move_right);
moveRightBtn.addEventListener("mousedown", move_right);
moveRightBtn.addEventListener("touchend", stop);
moveRightBtn.addEventListener("mouseup", stop);

window.addEventListener(
  "keydown",
  (event) => {
    if (event.defaultPrevented) {
      return; // Do nothing if event already handled
    }

    switch (event.code) {
      case "KeyA":
      case "ArrowLeft":
        move_left();
        break;
      case "KeyD":
      case "ArrowRight":
        move_right();
        break;
    }
  },
  true
);
// window.addEventListener(
//   "keyup",
//   (event) => {
//     if (event.defaultPrevented) {
//       return; // Do nothing if event already handled
//     }

//     switch (event.code) {
//       case "KeyA":
//       case "ArrowLeft":
//         stop();
//         break;
//       case "KeyD":
//       case "ArrowRight":
//         stop();
//         break;
//     }
//   },
//   true
// );
window.addEventListener(
  "keydown",
  (event) => {
    if (event.defaultPrevented) {
      return; // Do nothing if event already handled
    }

    switch (event.code) {
      case "KeyS":
      case "ArrowDown":
      case "Space":
        stop();
        break;
    }
  },
  true
);
