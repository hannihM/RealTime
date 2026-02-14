// const socket = io();

// let mediaRecorder;
// let username;
// let room;
// let targetLang;

// document.getElementById("joinBtn").onclick = () => {
//     username = document.getElementById("username").value;
//     console.log("Username:", username);
//     room = document.getElementById("room").value;
//     console.log("Room:", room);
//     targetLang = document.getElementById("lang").value;
//     console.log("Target Language:", targetLang);
//     if(!username || !room) return;
//     socket.emit("join", {username, room});
// };

// document.getElementById("startBtn").onclick = async () => {
//     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//     mediaRecorder = new MediaRecorder(stream);

//     mediaRecorder.ondataavailable = async (e) => {
//         if (e.data.size > 0) {
//             const arrayBuffer = await e.data.arrayBuffer();
//             const base64Chunk = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
//             socket.emit("audio_chunk", { chunk: base64Chunk, username, room, target_lang: targetLang });
//         }
//     };

//     mediaRecorder.start(1000); // send every 1 second
// };

// // Receive translated audio from others
// socket.on("translated_audio", (data) => {
//     const chatDiv = document.getElementById("chat");
//     chatDiv.innerHTML += `<p><b>${data.from}:</b> ${data.text}</p>`;
//     const audioEl = document.getElementById("ttsAudio");
//     audioEl.src = "data:audio/mp3;base64," + data.audio;
//     audioEl.play();
// });
