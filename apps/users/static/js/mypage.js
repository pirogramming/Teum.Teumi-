// 마이페이지 JavaScript

// 전역 변수
let scheduleData = Array(7).fill(null).map(() => Array(25).fill(false));

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('마이페이지 로드됨');
    
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
    
    // 기존 스케줄 데이터 로드
    loadExistingSchedule();
    
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
        // CSS 클래스를 사용하여 토글
        viewElement.classList.remove('hidden');
        editElement.classList.add('hidden');
    }
}

// 섹션 저장
function saveSection(section) {
    console.log('섹션 저장:', section);
    
    const formData = new FormData();
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken.value);
    }
    
    // 섹션별 데이터 수집
    if (section === 'basic') {
        const nickname = document.getElementById('basic-nickname');
        const mbti = document.getElementById('basic-mbti');
        const gender = document.getElementById('basic-gender');
        const introduction = document.getElementById('basic-introduction');
        
        if (nickname) formData.append('nickname', nickname.value);
        if (mbti) formData.append('mbti', mbti.value);
        if (gender) formData.append('gender', gender.value);
        if (introduction) formData.append('introduction', introduction.value);
    } else if (section === 'interests') {
        const selectedInterests = Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(input => input.value);
        if (selectedInterests.length !== 4) {
            alert('정확한 매칭을 위해 관심사 4개를 모두 선택해주세요.');
            return;
        }
        formData.append('interests', JSON.stringify(selectedInterests));
    } else if (section === 'schedule') {
        if (!scheduleData.some(day => day && day.some(time => time))) {
            alert('만날 수 있는 시간을 최소 1개 이상 선택해주세요.');
            return;
        }
        formData.append('schedule', JSON.stringify(scheduleData));
        console.log('스케줄 데이터 저장:', scheduleData);
    } else if (section === 'advanced') {
        const experience = document.getElementById('advanced-experience');
        const conversationStyle = document.getElementById('advanced-conversation-style');
        const location = document.getElementById('advanced-location');
        const goal = document.getElementById('advanced-goal');
        
        if (experience) formData.append('experience', experience.value);
        if (conversationStyle) formData.append('conversation_style', conversationStyle.value);
        if (location) formData.append('activity_location', location.value);
        if (goal) formData.append('goal_or_concern', goal.value);
        
        const selectedPersonalities = Array.from(document.querySelectorAll('input[name="personalities"]:checked')).map(input => input.value);
        formData.append('personalities', JSON.stringify(selectedPersonalities));
    }
    
    // API 호출
    fetch(`/users/update-${section}/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('저장되었습니다!');
            location.reload();
        } else {
            alert('저장에 실패했습니다: ' + (data.message || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('저장 오류:', error);
        alert('저장 중 오류가 발생했습니다.');
    });
}

// 관심사 카운터 업데이트
function updateInterestCount() {
    const checkedInterests = document.querySelectorAll('input[name="interests"]:checked');
    const countElement = document.getElementById('interest-count');
    const requiredText = document.querySelector('#interests-edit .required-text');
    const saveButton = document.querySelector('#interests-edit .save-button');
    
    console.log('관심사 카운터 업데이트:', checkedInterests.length);
    
    if (countElement) {
        countElement.textContent = checkedInterests.length;
    }
    
    if (requiredText) {
        if (checkedInterests.length === 4) {
            requiredText.innerHTML = '✅ 완성! 정확한 매칭을 위해 4개를 모두 선택해주셨어요.';
            requiredText.style.color = '#10b981';
        } else {
            requiredText.innerHTML = '정확한 매칭을 위해 관심사 4개를 모두 선택해주세요.';
            requiredText.style.color = '#6b7280';
        }
    }
    
    if (saveButton) {
        const isValid = checkedInterests.length === 4;
        saveButton.disabled = !isValid;
        saveButton.style.opacity = isValid ? '1' : '0.5';
        saveButton.style.pointerEvents = isValid ? 'auto' : 'none';
    }
    
    // 초과 선택 방지
    const allInterests = document.querySelectorAll('input[name="interests"]');
    allInterests.forEach(checkbox => {
        const isDisabled = !checkbox.checked && checkedInterests.length >= 4;
        checkbox.disabled = isDisabled;
        checkbox.parentElement.classList.toggle('disabled', isDisabled);
    });
}

// 성격 키워드 카운터 업데이트
function updatePersonalityCount() {
    const checkedPersonalities = document.querySelectorAll('input[name="personalities"]:checked');
    const countElement = document.getElementById('personality-count');
    
    console.log('성격 키워드 카운터 업데이트:', checkedPersonalities.length);
    
    if (countElement) {
        countElement.textContent = checkedPersonalities.length;
    }
    
    // 초과 선택 방지
    const allPersonalities = document.querySelectorAll('input[name="personalities"]');
    allPersonalities.forEach(checkbox => {
        const isDisabled = !checkbox.checked && checkedPersonalities.length >= 3;
        checkbox.disabled = isDisabled;
        checkbox.parentElement.classList.toggle('disabled', isDisabled);
    });
}

// 스케줄 초기화
function initializeSchedule() {
    console.log('initializeSchedule 함수 호출됨');
    const scheduleGrid = document.getElementById('schedule-grid');
    if (!scheduleGrid) {
        console.error('schedule-grid 요소를 찾을 수 없습니다');
        return;
    }
    console.log('schedule-grid 요소 찾음:', scheduleGrid);
    
    // 기존 내용 제거
    scheduleGrid.innerHTML = '';
    console.log('schedule-grid 내용 초기화됨');
    
    // 시간대별로 행 생성
    const timeSlots = [];
    for (let hour = 9; hour <= 22; hour++) {
        timeSlots.push(`${hour}:00`);
        timeSlots.push(`${hour}:30`);
    }
    timeSlots.push('23:00');
    
    console.log('생성할 시간 슬롯:', timeSlots);
    console.log('총 시간 슬롯 수:', timeSlots.length);
    
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
            
            // 기존 선택 상태 반영 (텍스트 없이 클래스만)
            if (scheduleData[dayIndex] && scheduleData[dayIndex][timeIndex]) {
                cell.classList.add('selected');
                console.log(`셀 선택됨: ${dayIndex}일 ${timeIndex}시간대 (${time})`);
            }
            
            row.appendChild(cell);
        }
        
        scheduleGrid.appendChild(row);
    });
    
    console.log('스케줄 그리드 초기화 완료, 총 행 수:', scheduleGrid.children.length);
    console.log('scheduleData 상태:', scheduleData);
}

// 기존 스케줄 데이터 로드
function loadExistingSchedule() {
    // Django 템플릿에서 전달받은 기존 스케줄 데이터를 scheduleData에 설정
    if (typeof existingScheduleData !== 'undefined' && existingScheduleData.length > 0) {
        // 기존 스케줄 데이터를 2차원 배열로 변환
        existingScheduleData.forEach(schedule => {
            const dayOfWeek = schedule.day_of_week;
            const startTime = schedule.start_time;
            const endTime = schedule.end_time;
            
            // 요일 인덱스 매핑 (Monday=0, Tuesday=1, ...)
            const dayMapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            };
            
            const dayIndex = dayMapping[dayOfWeek];
            if (dayIndex !== undefined) {
                // 시간을 30분 단위로 변환
                const startHour = parseInt(startTime.split(':')[0]);
                const startMinute = parseInt(startTime.split(':')[1]);
                const endHour = parseInt(endTime.split(':')[0]);
                const endMinute = parseInt(endTime.split(':')[1]);
                
                // 30분 단위 인덱스 계산 (9:00부터 시작)
                const startIndex = (startHour - 9) * 2 + (startMinute >= 30 ? 1 : 0);
                const endIndex = (endHour - 9) * 2 + (endMinute >= 30 ? 1 : 0);
                
                // 해당 시간 슬롯들을 true로 설정
                for (let i = Math.max(0, startIndex); i < Math.min(25, endIndex); i++) {
                    if (!scheduleData[dayIndex]) {
                        scheduleData[dayIndex] = Array(25).fill(false);
                    }
                    scheduleData[dayIndex][i] = true;
                }
            }
        });
    }
    
    console.log('기존 스케줄 데이터 로드 완료:', scheduleData);
}

// 스케줄 셀 토글
function toggleScheduleCell(dayIndex, timeIndex, cell) {
    // 디버그 정보 제거 - 셀 내용을 비우고 클래스만 토글
    cell.textContent = '';
    
    if (!scheduleData[dayIndex]) {
        scheduleData[dayIndex] = Array(25).fill(false);
    }
    
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