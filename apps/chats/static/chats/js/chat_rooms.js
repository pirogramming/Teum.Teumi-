document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("accessToken");

    fetch("http://localhost:8000/chats/rooms/list/", {
        headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
        }
    })
        .then(res => {
        if (!res.ok) throw new Error(`서버 응답 실패: ${res.status}`);
        return res.json();
        })
        .then(rooms => {
        const list = document.getElementById("room-list");

        rooms.forEach(room => {
            const names = room.participants.join(", ");
            const message = room.last_message || "(메시지 없음)";
            const time = room.last_time ? new Date(room.last_time).toLocaleString() : "";

            const li = document.createElement("li");
            li.className = "chat-room-item";
            li.innerHTML = `
            <a href="/chats/rooms/page/${room.room_id}/">
                초대된 사람 :  ${names}<br>
                ${message}<br>
                ${time}
            </a>
            `;
            list.appendChild(li);
        });
        })
        .catch(err => {
        console.error("❌ 에러 발생:", err);
        alert("채팅방 목록을 불러올 수 없습니다.");
        });
});
