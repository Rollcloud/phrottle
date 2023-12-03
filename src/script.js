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

serverSocket.onopen = () => {
  send_message("ping", "");
};
serverSocket.onmessage = (event) => {
  console.log(event.data);
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
