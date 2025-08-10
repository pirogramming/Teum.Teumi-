document.addEventListener("DOMContentLoaded", function () {
    const filterBtn = document.getElementById("filter");
    const smallView = document.querySelector(".small-view");
    const overlay = document.getElementById("modal-overlay");
    const closeBtn = document.querySelector(".close");
    const cancelBtn = document.getElementById("cancle");

    // 처음에는 small-view와 overlay를 숨김
    smallView.style.display = "none";
    overlay.style.display = "none";

    // 필터 아이콘 클릭 시 열기
    filterBtn.addEventListener("click", function () {
        smallView.style.display = "block";
        overlay.style.display = "block";
    });

    // 닫기 버튼 클릭 시 닫기
    closeBtn.addEventListener("click", closeSmallView);
    if (cancelBtn) {
        cancelBtn.addEventListener("click", closeSmallView);
    }

    // 오버레이 클릭 시 닫기
    overlay.addEventListener("click", closeSmallView);

    function closeSmallView() {
        smallView.style.display = "none";
        overlay.style.display = "none";
    }

    // view-tag 클릭 시 선택 토글
    const viewTags = document.querySelectorAll(".view-tag");
    viewTags.forEach(tag => {
        tag.addEventListener("click", function () {
            tag.classList.toggle("selected");
        });
    });
});