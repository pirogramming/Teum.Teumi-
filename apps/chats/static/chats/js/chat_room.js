const token = localStorage.getItem("accessToken");
const roomId = ROOM_ID;

if (!token || !roomId) {
    alert("잘못된 접근입니다.");
}

// 운영 하드코딩: teumteumi.site 고정 (로컬 테스트 시 아래를 주석 처리하고 동적 생성 사용)
const socket = new WebSocket(`wss://teumteumi.site/ws/chat/${roomId}/?token=${token}`);
const log = document.getElementById("chat-log");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

socket.onopen = () => {
    console.log("연결 성공");
};

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    const { message, sender, sender_id, created_at } = data;
    console.log("CURRENT_USER_ID:", CURRENT_USER_ID);
    console.log("sender_id:", sender_id);
    const isMine = sender_id == CURRENT_USER_ID; 
    addMessage(sender, message, created_at, isMine);
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

function addMessage(sender, content, timestamp, isMine){
    const row = document.createElement("div");
    row.className = `message-row ${isMine ? "mymessege" : "other-messege"}`;

    // if(!isMine){
    //     const profile = document.createElement("div");
    //     profile.className = "profile";
    //     profile.innerText = sender[0];
    //     row.appendChild(profile);
    // }

    const bubble = document.createElement("div");
    bubble.className = "message-bubble"
    bubble.innerHTML = `
        <div class="message-header">
            ${/* !isMine ? `<span class="sender">${sender}</span>` : "" */""}
            <span class="text">${content}</span>
        </div>
        <div class="timestamp">${formatTime(new Date(timestamp || Date.now()))}</div>
        `;
        
    row.appendChild(bubble);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
}

function formatTime(data){
    const h = data.getHours();
    const m = data.getMinutes().toString().padStart(2, "0");
    const ampm = h>=12 ? "오후" : "오전";
    const hour = h % 12 || 12;
    return `${ampm} ${hour}:${m}`;
}

fetch(`https://teumteumi.site/chats/rooms/${roomId}/messages/`, {
    headers: {
        Authorization: `Bearer ${token}`
    }
})
    .then(res => res.json())
    .then(messages => {
        messages.forEach(m => {
            addMessage(m.sender, m.content, m.created_at, m.isMine);
        });
    })
    .catch(err => {
        console.error("이전 메시지 불러오기 실패", err);
    });
