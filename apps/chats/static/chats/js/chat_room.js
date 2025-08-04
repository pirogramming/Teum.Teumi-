const token = localStorage.getItem("accessToken");
const roomId = ROOM_ID;

if (!token || !roomId) {
    alert("잘못된 접근입니다.");
}

const socket = new WebSocket(`ws://localhost:8000/ws/chat/${roomId}/?token=${token}`);
const log = document.getElementById("chat-log");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

socket.onopen = () => {
    console.log("연결 성공");
};

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    const msgElem = document.createElement("div");
    msgElem.className = "msg";
    msgElem.innerText = `${data.sender || "익명"}: ${data.message}`;
    log.appendChild(msgElem);
    log.scrollTop = log.scrollHeight;
};

socket.onclose = () => {
    console.warn("연결 종료");
};

sendBtn.onclick = sendMessage;
input.onkeyup = (e) => {
    if (e.key === "Enter") sendMessage();
};

function sendMessage() {
    const message = input.value.trim();
    if (!message) return;
    socket.send(JSON.stringify({ message }));
    input.value = "";
}

// 이전 채팅 내역 불러오기
fetch(`http://127.0.0.1:8000/chats/rooms/${roomId}/messages/`, {
    headers: {
        Authorization: `Bearer ${token}`
    }
})
.then(res => res.json())
.then(messages => {
    messages.forEach(m => {
        const msgElem = document.createElement("div");
        msgElem.className = "msg";
        msgElem.innerText = `${m.sender}: ${m.content}`;
        log.appendChild(msgElem);
    });
    log.scrollTop = log.scrollHeight;
});
