// 마이페이지 JavaScript

// 공통 인증 함수 (프로필 온보딩과 동일)
const ProfileOnboarding = {
  // 토큰 부트스트랩
  bootstrapToken() {
    const tmplAccess = window.tmplAccess || '';
    const tmplRefresh = window.tmplRefresh || '';
    if (tmplAccess) localStorage.setItem('access', tmplAccess);
    if (tmplRefresh) localStorage.setItem('refresh', tmplRefresh);
  },

  // 인증된 fetch 헬퍼
  async authFetch(url, options = {}, tryRefresh = true) {
    const token = localStorage.getItem('access') || '';
    const headers = {
      ...(options.headers || {}),
      'Authorization': token ? `Bearer ${token}` : '',
    };
    const req = { ...options, headers };

    let res = await fetch(url, req);
    if (res.status === 401 && tryRefresh) {
      const newAccess = await this.refreshAccessToken();
      if (newAccess) {
        const retryHeaders = {
          ...(options.headers || {}),
          'Authorization': `Bearer ${newAccess}`,
        };
        res = await fetch(url, { ...options, headers: retryHeaders });
      }
    }
    return res;
  },

  // 토큰 갱신
  async refreshAccessToken() {
    const refresh = localStorage.getItem('refresh');
    if (!refresh) return null;
    try {
      const res = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh })
      });
      if (!res.ok) return null;
      const data = await res.json();
      if (data.access) {
        localStorage.setItem('access', data.access);
        return data.access;
      }
      return null;
    } catch (e) {
      return null;
    }
  }
};

// 전역 변수
let scheduleData = Array(7).fill(null).map(() => Array(25).fill(false));

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 토큰 부트스트랩
    ProfileOnboarding.bootstrapToken();
    
    // 자기소개 50자 카운터 즉시 반영
    const introArea = document.getElementById('basic-introduction');
    const countEl = document.getElementById('basic-intro-count');
    const msgEl = document.getElementById('basic-intro-message');
    if (introArea && countEl && msgEl) {
        // 프로필 4단계와 동일한 50자 이상 로직 적용
        const MIN_TEXT = 50;
        
        function updateTextCount() {
            const length = introArea.value.length;
            countEl.textContent = `${length}/${MIN_TEXT}자`;
            msgEl.innerHTML = length >= MIN_TEXT ? '✅ 완성!' : '📝 조금 더 써주세요';
        }
        
        function updateButtonState() {
            const saveButton = document.querySelector('#basic-edit .save-button');
            if (saveButton) {
                const isTextareaLongEnough = introArea.value.length >= MIN_TEXT;
                saveButton.disabled = !isTextareaLongEnough;
            }
        }
        
        // 이벤트 리스너 추가
        introArea.addEventListener('input', () => { 
            updateTextCount(); 
            updateButtonState(); 
        });
        
        // 초기 상태 설정
        updateTextCount();
        updateButtonState();
    }
    
    // AI 자기소개 버튼 핸들러 추가
    const aiButton = document.getElementById('ai-button');
    if (aiButton) {
        aiButton.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                aiButton.disabled = true;
                const originalText = aiButton.innerHTML;
                aiButton.innerHTML = `
                    <svg class="ai-svg" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-stars" viewBox="0 0 16 16">
                        <path d="M7.657 6.247c.11-.33.576-.33.686 0l.645 1.937a2.89 2.89 0 0 0 1.829 1.828l1.936.645c.33.11.33.576 0 .686l-1.937.645a2.89 2.89 0 0 0-1.828 1.829l-.645 1.936a.361.361 0 0 1-.686 0l-.645-1.937a2.89 2.89 0 0 0-1.828-1.828l-1.937-.645a.361.361 0 0 1 0-.686l1.937-.645a2.89 2.89 0 0 0 1.828-1.828zM3.794 1.148a.217.217 0 0 1 .412 0l.387 1.162c.173.518.579.924 1.097 1.097l1.162.387a.217.217 0 0 1 0 .412l-1.162.387A1.73 1.73 0 0 0 4.593 5.69l-.387 1.162a.217.217 0 0 1-.412 0L3.407 5.69A1.73 1.73 0 0 0 2.31 4.593l-1.162-.387a.217.217 0 0 1 0-.412l1.162-.387A1.73 1.73 0 0 0 3.407 2.31zM10.863.099a.145.145 0 0 1 .274 0l.258.774c.115.346.386.617.732.732l.774.258a.145.145 0 0 1 0 .274l-.774.258a1.16 1.16 0 0 0-.732.732l-.258.774a.145.145 0 0 1-.274 0l-.258-.774a1.16 1.16 0 0 0-.732-.732L9.1 2.137a.145.145 0 0 1 0-.274l.774-.258c.346-.115.617-.386.732-.732z"/>
                    </svg>AI로 추천받기
                    <span>✨</span>
                    <div style="margin-top: 4px; font-size: 12px; color: #666;">생성중...</div>
                `;
                
                // 기존 자기소개 (있는 경우)
                const existingIntroduction = introArea ? introArea.value : '';
                
                const res = await ProfileOnboarding.authFetch('/profiles/api/introduction/enhanced/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        existing_introduction: existingIntroduction 
                    })
                });
                
                const data = await res.json().catch(() => ({}));
                if (res.ok && data && data.ai_introduction) {
                    if (introArea) {
                        introArea.value = data.ai_introduction;
                        // 카운터와 버튼 상태 업데이트
                        const event = new Event('input', { bubbles: true });
                        introArea.dispatchEvent(event);
                    }
                } else {
                    alert((data && data.message) ? data.message : 'AI 자기소개 생성에 실패했습니다.');
                }
            } catch (err) {
                console.error('[mypage] AI 자기소개 생성 오류:', err);
                alert('AI 자기소개 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
            } finally {
                aiButton.disabled = false;
                aiButton.innerHTML = originalText;
            }
        });
    }
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
            
            // 자기소개 50자 검증 로직 재초기화
            const introArea = document.getElementById('basic-introduction');
            const countEl = document.getElementById('basic-intro-count');
            const msgEl = document.getElementById('basic-intro-message');
            if (introArea && countEl && msgEl) {
                const MIN_TEXT = 50;
                
                function updateTextCount() {
                    const length = introArea.value.length;
                    countEl.textContent = `${length}/${MIN_TEXT}자`;
                    msgEl.innerHTML = length >= MIN_TEXT ? '✅ 완성!' : '📝 조금 더 써주세요';
                }
                
                function updateButtonState() {
                    const saveButton = document.querySelector('#basic-edit .save-button');
                    if (saveButton) {
                        const isTextareaLongEnough = introArea.value.length >= MIN_TEXT;
                        saveButton.disabled = !isTextareaLongEnough;
                    }
                }
                
                // 기존 이벤트 리스너 제거 후 다시 추가
                introArea.removeEventListener('input', updateTextCount);
                introArea.removeEventListener('input', updateButtonState);
                
                introArea.addEventListener('input', () => { 
                    updateTextCount(); 
                    updateButtonState(); 
                });
                
                // 초기 상태 설정
                updateTextCount();
                updateButtonState();
            }
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
        
        // 50자 검증 및 UI 피드백 (프로필 4단계와 동일한 로직)
        const intro = (data.introduction || '').trim();
        const countEl = document.getElementById('basic-intro-count');
        const msgEl = document.getElementById('basic-intro-message');
        const MIN_TEXT = 50;
        
        if (countEl) countEl.textContent = `${intro.length}/${MIN_TEXT}자`;
        if (msgEl) msgEl.innerHTML = intro.length >= MIN_TEXT ? '✅ 완성!' : '📝 조금 더 써주세요';
        
        if (intro.length < MIN_TEXT) {
            alert('자기소개는 최소 50자 이상 작성해주세요.');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<span>💾</span> 저장';
            }
            return;
        }
        
        url = '/profiles/update-basic/';
    } else if (section === 'interests') {
        const selectedInterests = getSelectedValues('#interests-edit', 'interests');
        if (selectedInterests.length !== 4) {
            alert('관심사는 정확히 4개를 선택해야 저장할 수 있어요.');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<span>💾</span> 저장';
            }
            return;
        }
        data = { interests: JSON.stringify(selectedInterests) };
        url = '/profiles/update-interests/';
    } else if (section === 'schedule') {
        data = { schedule: JSON.stringify(scheduleData) };
        url = '/profiles/update-schedule/';
    } else if (section === 'advanced') {
        const selectedPersonalities = getSelectedValues('#advanced-edit', 'personalities');
        if (selectedPersonalities.length !== 3) {
            alert('성격 키워드는 정확히 3개를 선택해야 저장할 수 있어요.');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<span>💾</span> 저장';
            }
            return;
        }
        data = {
            experience: document.getElementById('advanced-experience').value,
            conversation_style: document.getElementById('advanced-conversation-style').value,
            activity_location: document.getElementById('advanced-location').value,
            goal_or_concern: document.getElementById('advanced-goal').value,
            personalities: JSON.stringify(selectedPersonalities)
        };
        url = '/profiles/update-advanced/';
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
        const count = selectedInterests.length;
        counter.textContent = String(count);
        counter.style.color = count === 4 ? '#3b82f6' : '#e74c3c';
    }
}

// 성격 키워드 카운터 업데이트
function updatePersonalityCount() {
    const selectedPersonalities = document.querySelectorAll('#advanced-edit input[name="personalities"]:checked');
    const counter = document.getElementById('personality-count');
    if (counter) {
        const count = selectedPersonalities.length;
        counter.textContent = String(count);
        counter.style.color = count === 3 ? '#3b82f6' : '#e74c3c';
    }
}

// 공통 유틸: 선택된 값 배열 반환
function getSelectedValues(containerSelector, inputName) {
    return Array.from(document.querySelectorAll(`${containerSelector} input[name="${inputName}"]:checked`))
        .map(cb => cb.value);
}

// 공통 유틸: 프로필 2단계 방식 - 초과 선택 시 원복 + 흔들림
function enforceMaxSelectionSoft(containerSelector, inputName, max, itemClass, targetInput) {
    const container = document.querySelector(containerSelector);
    if (!container || !targetInput) return;
    const checkedNow = container.querySelectorAll(`input[name="${inputName}"]:checked`).length;
    if (checkedNow > max) {
        // 방금 체크된 항목을 원복
        targetInput.checked = false;
        const item = targetInput.closest(`.${itemClass}`);
        if (item) {
            item.classList.add('shake');
            setTimeout(() => item.classList.remove('shake'), 400);
        }
    }
}

// 개별 제한 함수는 공통 유틸 enforceMaxSelection으로 대체됨

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
        enforceMaxSelectionSoft('#interests-edit', 'interests', 4, 'interest-item', e.target);
        updateInterestCount();
    } else if (e.target.name === 'personalities') {
        enforceMaxSelectionSoft('#advanced-edit', 'personalities', 3, 'personality-item', e.target);
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