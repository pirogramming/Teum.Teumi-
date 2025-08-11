document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("accessToken");

    fetch("https://teumteumi.site/chats/rooms/list/", {
        headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        },
    })

    .then((res) => {
        if (!res.ok) throw new Error(`서버 응답 실패: ${res.status}`);
        return res.json();
    })

    .then((rooms) => {
        const list = document.getElementById("room-list");

        rooms.forEach((room) => {
            const names = room.participants.join(", ");
            const firstLetter = names[0] || "?";
            const message = room.last_message || "(메시지 없음)";
            const time = room.last_time
            ? new Date(room.last_time).toLocaleTimeString("ko-KR", {
                hour: "2-digit",
                minute: "2-digit",
                })
            : "";

            const li = document.createElement("li");
            li.className = "chat-room-item";
            li.innerHTML = `
                <a href="/chats/rooms/page/${room.room_id}/">
                    <div class="avatar">${firstLetter}</div>
                    <div class="chat-info">
                        <div class="nickname">${names}</div>
                        <div class="last-message">${message}</div>
                    </div>
                    <div class="chat-time">${time}</div>
                </a>
            `;
            list.appendChild(li);
        });
    })
    .catch((err) => {
        console.error("❌ 에러 발생:", err);
        alert("채팅방 목록을 불러올 수 없습니다.");
    });
});
