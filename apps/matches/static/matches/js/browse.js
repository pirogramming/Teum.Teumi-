// 메인 페이지(홈)로 이동
function goToHome() {
    console.log('홈으로 이동');
    window.location.href = '/profiles/profile/';
}

// ==== 관심사&학교 검색 기능 ====
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.querySelector(".search-input");
    const recommends = document.querySelectorAll(".recommend");

    // universities JSON 로드
    const universities = JSON.parse(document.getElementById('universities-data').textContent);

    searchInput.addEventListener("input", function () {
        const keyword = searchInput.value.trim().toLowerCase();

        recommends.forEach(recommend => {
            // 관심사 텍스트
            const tags = recommend.querySelectorAll(".small-tag");
            const tagTexts = Array.from(tags).map(tag => tag.innerText.toLowerCase());

            // school_id → school_name 변환
            const schoolId = recommend.dataset.schoolId;
            const schoolName = universities.find(u => u.school_id == schoolId)?.school_name.toLowerCase() || "";

            // 검색 조건: 관심사 OR 학교명
            const matchFound =
                tagTexts.some(tagText => tagText.includes(keyword)) ||
                schoolName.includes(keyword);

            if (keyword === "" || matchFound) {
                recommend.style.display = "";
            } else {
                recommend.style.display = "none";
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const popularTags = document.querySelectorAll(".tag");
    const recommends = document.querySelectorAll(".recommend");
    let activeTags = [];

    popularTags.forEach(tag => {
        tag.addEventListener("click", function () {
            const selectedTag = tag.textContent.trim().toLowerCase();

            // 배열에 있으면 제거, 없으면 추가
            if (activeTags.includes(selectedTag)) {
                activeTags = activeTags.filter(t => t !== selectedTag);
                tag.classList.remove("active");
            } else {
                activeTags.push(selectedTag);
                tag.classList.add("active");
            }

            // 필터링
            recommends.forEach(recommend => {
                const userTags = Array.from(recommend.querySelectorAll(".small-tag"))
                    .map(t => t.textContent.trim().toLowerCase());

                // activeTags가 비어 있으면 전체 표시
                if (activeTags.length === 0 || activeTags.some(tag => userTags.includes(tag))) {
                    recommend.style.display = "";
                } else {
                    recommend.style.display = "none";
                }
            });
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const universitySelect = document.getElementById("university");
    const departmentSelect = document.getElementById("department");

    // 처음에는 학과 선택 숨김
    departmentSelect.style.display = "none";

    universitySelect.addEventListener("change", function () {
        if (universitySelect.value) {
            departmentSelect.style.display = "";
        } else {
            departmentSelect.style.display = "none";
        }
    });
});

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
    if (filterBtn) {
        filterBtn.addEventListener("click", function () {
            smallView.style.display = "block";
            overlay.style.display = "block";
        });
    }

    // 닫기 버튼 클릭 시 닫기
    if (closeBtn) {
        closeBtn.addEventListener("click", closeSmallView);
    }
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
            const input = this.querySelector('input');
            input.checked = !input.checked;
            this.classList.toggle('selected', input.checked);
        });
    });

    // ===== 학교/학과 동적 선택 =====
    const universitySelect = document.getElementById("university");
    const departmentSelect = document.getElementById("department");
    const universitiesDataElement = document.getElementById("universities-data");

    if (universitySelect && departmentSelect && universitiesDataElement) {
        // 템플릿에서 전달받은 JSON 데이터
        const data = JSON.parse(universitiesDataElement.textContent);

        universitySelect.addEventListener("change", () => {
            const selectedId = universitySelect.value;
            const school = data.find(s => s.school_id == selectedId);

            // 학과 옵션 초기화
            departmentSelect.innerHTML = '<option selected disabled hidden value="">학과 선택</option>';

            if (school && school.departments) {
                school.departments.forEach(dept => {
                    const option = document.createElement("option");
                    option.value = dept.department_id;
                    option.textContent = dept.department_name;
                    departmentSelect.appendChild(option);
                });
            }
        });
    }
});