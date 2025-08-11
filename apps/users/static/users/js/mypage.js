// 마이페이지 JavaScript

// 전역 변수
let scheduleData = Array(7).fill(null).map(() => Array(25).fill(false));

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('마이페이지 로드됨');
    
    // 기존 스케줄 데이터 로드 (가장 먼저 실행)
    loadExistingSchedule();
    
    // 관심사 카운터 초기화 (편집 모드에서만)
    const interestsEdit = document.getElementById('interests-edit');
    if (interestsEdit && !interestsEdit.classList.contains('hidden')) {
        updateInterestCount();
    }
    
    // 성격 키워드 카운터 초기화 (편집 모드에서만)
    const advancedEdit = document.getElementById('advanced-edit');
    if (advancedEdit && !advancedEdit.classList.contains('hidden')) {
        updatePersonalityCount();
    }
    
    // 스케줄 초기화 (편집 모드에서만)
    const scheduleEdit = document.getElementById('schedule-edit');
    if (scheduleEdit && !scheduleEdit.classList.contains('hidden')) {
        initializeSchedule();
        updateScheduleValidation();
    }
    
    // 스케줄 편집 모드가 활성화되어 있다면 그리드 다시 렌더링
    const scheduleEditElement = document.getElementById('schedule-edit');
    if (scheduleEditElement && !scheduleEditElement.classList.contains('hidden')) {
        console.log('스케줄 편집 모드가 활성화되어 있어서 그리드 다시 렌더링');
        initializeSchedule();
        updateScheduleValidation();
    }
});

// 네비게이션 함수들
function goToHome() {
    console.log('홈으로 이동');
    window.location.href = '/profiles/profile/';
}

function showLogoutModal() {
    console.log('로그아웃 모달 표시');
    const modal = document.getElementById('logoutModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('show');
    }
}

function hideLogoutModal() {
    console.log('로그아웃 모달 숨김');
    const modal = document.getElementById('logoutModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

// 로그아웃 처리
function handleLogout() {
    console.log('로그아웃 처리 시작');
    
    const logoutButton = document.querySelector('.logout-button');
    if (logoutButton) {
        logoutButton.innerHTML = '<span class="loading-spinner">⏳</span> 로그아웃 중...';
        logoutButton.disabled = true;
    }
    
    // 로그아웃 페이지로 직접 이동
    window.location.href = '/users/logout/';
}

// 편집 모드 토글
function toggleEditSection(section) {
    console.log('편집 모드 토글:', section);
    
    const viewElement = document.getElementById(section + '-view');
    const editElement = document.getElementById(section + '-edit');
    
    if (viewElement && editElement) {
        // CSS 클래스를 사용하여 토글
        viewElement.classList.add('hidden');
        editElement.classList.remove('hidden');
        
        // 편집 모드에서 기존 데이터 보존
        if (section === 'basic') {
            // 기본 정보는 이미 HTML에서 value로 설정되어 있음
            console.log('기본 정보 편집 모드 활성화');
        } else if (section === 'interests') {
            updateInterestCount();
        } else if (section === 'schedule') {
            console.log('스케줄 편집 모드 활성화');
            // 기존 스케줄 데이터 다시 로드
            loadExistingSchedule();
            initializeSchedule();
            updateScheduleValidation();
        } else if (section === 'advanced') {
            updatePersonalityCount();
        }
    }
}

// 편집 취소
function cancelEdit(section) {
    console.log('편집 취소:', section);
    
    const viewElement = document.getElementById(section + '-view');
    const editElement = document.getElementById(section + '-edit');
    
    if (viewElement && editElement) {
        viewElement.classList.remove('hidden');
        editElement.classList.add('hidden');
    }
}

// 섹션 저장
function saveSection(section) {
    console.log('섹션 저장:', section);
    
    const saveButton = document.querySelector(`#${section}-edit .save-button`);
    if (saveButton) {
        saveButton.disabled = true;
        saveButton.innerHTML = '<span>⏳</span> 저장 중...';
    }
    
    let data = {};
    let url = '';
    
    if (section === 'basic') {
        data = {
            nickname: document.getElementById('basic-nickname').value,
            mbti: document.getElementById('basic-mbti').value,
            gender: document.getElementById('basic-gender').value,
            introduction: document.getElementById('basic-introduction').value
        };
        url = '/users/update-basic/';
    } else if (section === 'interests') {
        const selectedInterests = Array.from(document.querySelectorAll('#interests-edit input[name="interests"]:checked'))
            .map(checkbox => checkbox.value);
        data = { interests: JSON.stringify(selectedInterests) };
        url = '/users/update-interests/';
    } else if (section === 'schedule') {
        data = { schedule: JSON.stringify(scheduleData) };
        url = '/users/update-schedule/';
    } else if (section === 'advanced') {
        data = {
            experience: document.getElementById('advanced-experience').value,
            conversation_style: document.getElementById('advanced-conversation-style').value,
            activity_location: document.getElementById('advanced-location').value,
            goal_or_concern: document.getElementById('advanced-goal').value,
            personalities: JSON.stringify(Array.from(document.querySelectorAll('#advanced-edit input[name="personalities"]:checked'))
                .map(checkbox => checkbox.value))
        };
        url = '/users/update-advanced/';
    }
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert(result.message);
            // 페이지 새로고침으로 변경사항 반영
            window.location.reload();
        } else {
            alert('저장에 실패했습니다: ' + result.message);
        }
    })
    .catch(error => {
        console.error('저장 오류:', error);
        alert('저장에 실패했습니다: 업데이트 중 오류가 발생했습니다.');
    })
    .finally(() => {
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = '<span>💾</span> 저장';
        }
    });
}

// 관심사 카운터 업데이트
function updateInterestCount() {
    const selectedInterests = document.querySelectorAll('#interests-edit input[name="interests"]:checked');
    const counter = document.getElementById('interest-count');
    if (counter) {
        counter.textContent = `${selectedInterests.length}/4`;
        counter.style.color = selectedInterests.length >= 4 ? '#e74c3c' : '#2c3e50';
    }
}

// 성격 키워드 카운터 업데이트
function updatePersonalityCount() {
    const selectedPersonalities = document.querySelectorAll('#advanced-edit input[name="personalities"]:checked');
    const counter = document.getElementById('personality-count');
    if (counter) {
        counter.textContent = `${selectedPersonalities.length}/3`;
        counter.style.color = selectedPersonalities.length >= 3 ? '#e74c3c' : '#2c3e50';
    }
}

// 스케줄 초기화
function initializeSchedule() {
    console.log('initializeSchedule 함수 호출됨');
    const scheduleGrid = document.getElementById('schedule-grid');
    if (!scheduleGrid) {
        console.error('schedule-grid 요소를 찾을 수 없습니다');
        return;
    }
    
    // 기존 내용 제거
    scheduleGrid.innerHTML = '';
    
    // 시간대별로 행 생성 (9:00-21:00, 30분 단위, 총 25개 슬롯)
    const timeSlots = [];
    for (let hour = 9; hour <= 21; hour++) {
        timeSlots.push(`${hour}:00`);
        timeSlots.push(`${hour}:30`);
    }
    
    timeSlots.forEach((time, timeIndex) => {
        const row = document.createElement('div');
        row.className = 'schedule-row';
        
        // 시간 셀
        const timeCell = document.createElement('div');
        timeCell.className = 'time-cell';
        timeCell.textContent = time;
        row.appendChild(timeCell);
        
        // 요일별 셀
        for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
            const cell = document.createElement('div');
            cell.className = 'schedule-cell';
            cell.onclick = () => toggleScheduleCell(dayIndex, timeIndex, cell);
            
            // 기존 선택 상태 반영
            if (scheduleData[dayIndex] && scheduleData[dayIndex][timeIndex]) {
                cell.classList.add('selected');
            }
            
            row.appendChild(cell);
        }
        
        scheduleGrid.appendChild(row);
    });
    
    console.log('스케줄 그리드 초기화 완료');
}

// 기존 스케줄 데이터 로드
function loadExistingSchedule() {
    console.log('loadExistingSchedule 함수 호출됨');
    
    // scheduleData 초기화
    scheduleData = Array(7).fill(null).map(() => Array(25).fill(false));
    
    // Django 템플릿에서 전달받은 기존 스케줄 데이터를 scheduleData에 설정
    if (typeof existingScheduleData !== 'undefined' && existingScheduleData.length > 0) {
        console.log('기존 스케줄 데이터 발견:', existingScheduleData.length, '개');
        
        existingScheduleData.forEach(schedule => {
            const dayOfWeek = schedule.day_of_week;
            const startTime = schedule.start_time;
            const endTime = schedule.end_time;
            
            console.log('처리 중인 스케줄:', { dayOfWeek, startTime, endTime });
            
            // 요일 인덱스 매핑 (한글 요일명 - 한 글자)
            const dayMapping = {
                '월': 0, '화': 1, '수': 2, '목': 3,
                '금': 4, '토': 5, '일': 6
            };
            
            let dayIndex = dayMapping[dayOfWeek];
            // 숫자 문자열로 전달된 기존 데이터(0~6)도 대응
            if (dayIndex === undefined) {
                const numericDay = parseInt(dayOfWeek, 10);
                if (!Number.isNaN(numericDay) && numericDay >= 0 && numericDay <= 6) {
                    dayIndex = numericDay;
                }
            }
            if (dayIndex !== undefined) {
                // 시간을 30분 단위로 변환
                const startHour = parseInt(startTime.split(':')[0]);
                const startMinute = parseInt(startTime.split(':')[1]);
                const endHour = parseInt(endTime.split(':')[0]);
                const endMinute = parseInt(endTime.split(':')[1]);
                
                // 30분 단위 인덱스 계산 (9:00부터 시작, 25개 슬롯)
                const startIndex = (startHour - 9) * 2 + (startMinute >= 30 ? 1 : 0);
                const endIndex = (endHour - 9) * 2 + (endMinute >= 30 ? 1 : 0);
                
                console.log('시간 인덱스:', { startIndex, endIndex });
                
                // 해당 시간 슬롯들을 true로 설정
                for (let i = Math.max(0, startIndex); i < Math.min(25, endIndex); i++) {
                    scheduleData[dayIndex][i] = true;
                }
            } else {
                console.log('알 수 없는 요일:', dayOfWeek);
            }
        });
        
        console.log('기존 스케줄 데이터 로드 완료');
    } else {
        console.log('기존 스케줄 데이터가 없습니다');
    }
}

// 스케줄 셀 토글
function toggleScheduleCell(dayIndex, timeIndex, cell) {
    // 셀 내용을 비우고 클래스만 토글
    cell.textContent = '';
    
    scheduleData[dayIndex][timeIndex] = !scheduleData[dayIndex][timeIndex];
    cell.classList.toggle('selected', scheduleData[dayIndex][timeIndex]);
    
    updateScheduleValidation();
}

// 스케줄 유효성 검사
function updateScheduleValidation() {
    const hasSelection = scheduleData.some(day => day && day.some(time => time));
    const saveButton = document.querySelector('#schedule-edit .save-button');
    
    if (saveButton) {
        saveButton.disabled = !hasSelection;
        saveButton.style.opacity = hasSelection ? '1' : '0.5';
        saveButton.style.pointerEvents = hasSelection ? 'auto' : 'none';
        
        // 버튼 텍스트 업데이트
        const buttonText = saveButton.querySelector('span');
        if (buttonText) {
            buttonText.textContent = hasSelection ? '💾' : '⏳';
        }
    }
}

// 이벤트 리스너들
document.addEventListener('change', function(e) {
    if (e.target.name === 'interests') {
        updateInterestCount();
    } else if (e.target.name === 'personalities') {
        updatePersonalityCount();
    }
});

// 전역 함수로 노출
window.goToHome = goToHome;
window.showLogoutModal = showLogoutModal;
window.hideLogoutModal = hideLogoutModal;
window.handleLogout = handleLogout;
window.toggleEditSection = toggleEditSection;
window.cancelEdit = cancelEdit;
window.saveSection = saveSection;
window.updateInterestCount = updateInterestCount;
window.updatePersonalityCount = updatePersonalityCount;
window.toggleScheduleCell = toggleScheduleCell; 