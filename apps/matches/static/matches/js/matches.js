// 탭 전환 함수
    function showTab(tabName) {
        const tabs = document.querySelectorAll('.tab-content');
        const buttons = document.querySelectorAll('.tab-button');

        tabs.forEach(tab => {
            tab.style.display = 'none';
        });

        buttons.forEach(btn => {
            btn.removeAttribute('id'); // 'active' id 제거
        });

        document.getElementById(`tab-${tabName}`).style.display = 'block';
        const activeButton = Array.from(buttons).find(btn =>
            btn.getAttribute('onclick') === `showTab('${tabName}')`
        );
        if (activeButton) {
            activeButton.id = 'active';
        }
    }
 
document.addEventListener("DOMContentLoaded", function () {

    showTab('request');

    // 모달 공통 요소
    const overlay = document.getElementById("modal-overlay");
    const reviewOverlay = document.getElementById("review-modal-overlay");
    const rejectModal = document.getElementById("reject-reason");
    const reviewModal = document.getElementById("review");

    // 모달 열기
    function showModal(modal) {
        modal.style.display = "block";
        if(modal === rejectModal) {
            overlay.style.display = "block";
        } else if(modal === reviewModal) {
            reviewOverlay.style.display = "block";
        }
    }

    // 모달 닫기
    function hideModal(modal) {
        modal.style.display = "none";
        if(modal === rejectModal) {
            overlay.style.display = "none";
        } else if(modal === reviewModal) {
            reviewOverlay.style.display = "none";
        }
    }

    // 정중히 거절하기 버튼
    document.querySelectorAll(".reject").forEach(btn => {
        btn.addEventListener("click", function () {
            showModal(rejectModal);
        });
    });

    // 매너온도 남기기 버튼
    document.querySelectorAll(".tab-right").forEach(btn => {
        btn.addEventListener("click", function () {
            showModal(reviewModal);
        });
    });

    // 닫기 버튼
    rejectModal.querySelector(".close span").addEventListener("click", function () {
        hideModal(rejectModal);
    });

    reviewModal.querySelector(".close span").addEventListener("click", function () {
        hideModal(reviewModal);
    });

    document.getElementById("reject-cancle").addEventListener("click", function () {
        hideModal(rejectModal);
    })

    document.getElementById("review-cancle").addEventListener("click", function () {
        hideModal(reviewModal);
    })

    // 오버레이 클릭 → 모달 닫기
    overlay.addEventListener("click", function () {
        hideModal(rejectModal);
        hideModal(reviewModal);
    });

    // 슬라이더 관련
    const slider = document.getElementById("myRange");
    const output = document.getElementById("value");

    function updateValue(input) {
        output.textContent = parseFloat(input.value).toFixed(1) + "점";
    }

    function updateRangeBackground(input) {
        const val = (input.value - input.min) / (input.max - input.min) * 100;
        input.style.background = `linear-gradient(to right, #6366f1 ${val}%, #ddd ${val}%)`;
    }

    if (slider && output) {
        slider.addEventListener('input', function () {
            updateValue(this);
            updateRangeBackground(this);
        });

        // 초기값 세팅
        updateValue(slider);
        updateRangeBackground(slider);
    }
});