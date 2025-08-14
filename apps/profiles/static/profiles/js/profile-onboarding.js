// ========================================
// 프로필 온보딩 통합 JavaScript
// ========================================

// 공통 유틸리티 함수들
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

// ========================================
// Profile Step 1: 학교/학과/학년/나이 선택
// ========================================
const ProfileStep1 = {
  init() {
    const universitySelect = document.getElementById('university');
    const majorSelect = document.getElementById('major');
    const gradeSelect = document.getElementById('grade');
    const ageSelect = document.getElementById('age');
    const nextButton = document.getElementById('next-button');
    const profileForm = document.getElementById('profile-form');

    // 페이지에 요소가 없으면 조용히 종료 (공통 스크립트 안전 가드)
    if (!universitySelect || !majorSelect || !gradeSelect || !ageSelect || !nextButton || !profileForm) {
      console.warn('[profile_1] 필요한 엘리먼트 일부가 없습니다. 스크립트를 종료합니다.');
      return;
    }

    // 학교 선택 시 학과 목록 업데이트 (인증 필요하므로 authFetch 사용)
    universitySelect.addEventListener('change', function () {
      const schoolName = this.value;
      if (schoolName) {
        ProfileOnboarding.authFetch(`/profiles/api/majors/?school_name=${encodeURIComponent(schoolName)}`)
          .then(response => response.json())
          .then(data => {
            majorSelect.innerHTML = '<option selected disabled value="">전공하시는 학과를 선택해주세요</option>';
            (data.majors || []).forEach(major => {
              const option = document.createElement('option');
              option.value = major;
              option.textContent = major;
              majorSelect.appendChild(option);
            });
            ProfileStep1.checkAllSelected();
          })
          .catch(error => {
            console.error('학과 목록 불러오기 실패:', error);
            alert('학과 목록을 불러오지 못했습니다. 인증 상태를 확인해주세요.');
          });
      }
    });

    function checkAllSelected() {
      const allSelected = universitySelect.value &&
                          majorSelect.value &&
                          gradeSelect.value &&
                          ageSelect.value;
      nextButton.disabled = !allSelected;
    }

    // 각 셀렉트에 change 핸들러 (존재하는 요소만 바인딩)
    [universitySelect, majorSelect, gradeSelect, ageSelect]
      .filter(Boolean)
      .forEach(select => select.addEventListener('change', checkAllSelected));

    // 폼 제출 처리 (인증 필요하므로 authFetch 사용)
    profileForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      const formData = {
        school_name: universitySelect.value,
        department: majorSelect.value,
        grade: gradeSelect.value,
        age: parseInt(ageSelect.value, 10)
      };

      try {
        const response = await ProfileOnboarding.authFetch('/profiles/api/school/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData),
        });

        if (response.ok) {
          // 다음 단계는 페이지 전용 URL로 이동
          window.location.href = '/profiles/step2/page/';
        } else {
          const error = await response.json().catch(() => ({}));
          alert('저장 중 오류가 발생했습니다: ' + JSON.stringify(error));
        }
      } catch (error) {
        console.error('저장 실패:', error);
        alert('저장 중 오류가 발생했습니다. 네트워크 상태를 확인해주세요.');
      }
    });

    // 초기 상태 확인 (필요 요소가 있을 때만)
    if (universitySelect && majorSelect && gradeSelect && ageSelect && typeof checkAllSelected === 'function') {
      checkAllSelected();
    }
  }
};

// ========================================
// Profile Step 2: 관심사 선택
// ========================================
const ProfileStep2 = {
  init() {
    const form = document.getElementById('interest-form');
    const nextButton = document.getElementById('next-button');
    const tagCountEl = document.getElementById('tag-count');
    const tagCommentEl = document.getElementById('tag-comment');
    const tagNodes = Array.from(document.querySelectorAll('.tag[data-id]'));

    // 필수 요소 점검
    if (!form || !nextButton || tagNodes.length === 0) {
      console.warn('[profile_2] 필수 엘리먼트가 없어 스크립트를 종료합니다.');
      return;
    }

    const MAX_SELECT = 4;
    const selected = new Set(); // 선택된 관심사 id 보관

    // --- UI 업데이트 도우미 ---
    function updateCounterUI() {
      const count = selected.size;
      if (tagCountEl) tagCountEl.textContent = `선택된 관심사 : ${count}/${MAX_SELECT}`;
      if (tagCommentEl) {
        tagCommentEl.textContent = (count === MAX_SELECT)
          ? '좋아요! 이제 다음 단계로 넘어갈 수 있어요.'
          : '정확한 매칭을 위해 관심사 4개를 모두 선택해주세요.';
      }
      // 5단계 스타일과 동일: 최대치 도달 시 나머지 비활성화/투명도 처리
      tagNodes.forEach(node => {
        const id = node.getAttribute('data-id');
        const isSelected = selected.has(id);
        if (count >= MAX_SELECT && !isSelected) {
          node.classList.add('disabled');
          node.style.pointerEvents = 'none';
          node.style.opacity = '0.5';
          node.style.color = '#64748b';
        } else {
          node.classList.remove('disabled');
          node.style.pointerEvents = 'auto';
          node.style.opacity = '1';
          node.style.color = '';
        }
      });
      nextButton.disabled = (count !== MAX_SELECT);
    }

    function applySelectionStyles() {
      tagNodes.forEach(node => {
        const id = node.getAttribute('data-id');
        const keyword = node.getAttribute('data-keyword');
        if (selected.has(id)) {
          node.classList.add('selected');
          node.innerHTML = `✨ #${keyword}`;
        } else {
          node.classList.remove('selected');
          node.innerHTML = `#${keyword}`;
        }
      });
    }

    // --- 서버의 기존 선택값 불러와서 미리 체크 ---
    (async function preloadSelections(){
      try {
        const res = await ProfileOnboarding.authFetch('/profiles/api/interests/', { method: 'GET' });
        if (res.ok) {
          const data = await res.json();
          const ids = Array.isArray(data.interest_ids) ? data.interest_ids.map(String) : [];
          ids.slice(0, MAX_SELECT).forEach(id => selected.add(String(id)));
          applySelectionStyles();
          updateCounterUI();
        }
      } catch (e) {
        console.warn('[profile_2] 기존 선택 로드 실패:', e);
      }
    })();

    // --- 태그 클릭 토글 ---
    tagNodes.forEach(node => {
      node.addEventListener('click', () => {
        const id = node.getAttribute('data-id');
        if (!id) return;
        if (selected.has(id)) {
          selected.delete(id);
          node.classList.remove('selected');
          const keyword = node.getAttribute('data-keyword');
          node.innerHTML = `#${keyword}`;
        } else {
          if (selected.size >= MAX_SELECT) {
            // 최대 4개 제한 안내
            node.classList.add('shake');
            setTimeout(() => node.classList.remove('shake'), 400);
          } else {
            selected.add(id);
            node.classList.add('selected');
            const keyword = node.getAttribute('data-keyword');
            node.innerHTML = `✨ #${keyword}`;
          }
        }
        updateCounterUI();
      });
    });

    // --- 제출: PATCH /profiles/api/interests/ ---
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (selected.size !== MAX_SELECT) {
        alert('관심사는 정확히 4개를 선택해주세요.');
        return;
      }

      const payload = { interest_ids: Array.from(selected).map(id => Number(id)) };

      try {
        const res = await ProfileOnboarding.authFetch('/profiles/api/interests/', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          // 3단계 페이지로 이동
          window.location.href = '/profiles/step3/page/';
        } else {
          const err = await res.json().catch(() => ({}));
          alert('저장에 실패했습니다: ' + JSON.stringify(err));
        }
      } catch (e) {
        console.error('관심사 저장 실패:', e);
        alert('네트워크 오류로 저장에 실패했습니다. 잠시 후 다시 시도해주세요.');
      }
    });

    // 초기 상태
    updateCounterUI();
  }
};

// ========================================
// Profile Step 3: 시간표 선택
// ========================================
const ProfileStep3 = {
  init() {
    const cells = document.querySelectorAll('.cell');
    const nextButton = document.getElementById('next-button');
    const scheduleForm = document.getElementById('schedule-form');

    if (!cells.length || !nextButton || !scheduleForm) {
      console.warn('[profile_3] 필요한 엘리먼트가 없습니다.');
      return;
    }

    // 셀 내용 완전히 비우기 (요일명 제거)
    cells.forEach(cell => {
      cell.textContent = '';
      cell.innerHTML = '';
    });

    // 기존 공강시간 불러오기
    this.loadExistingSchedule();

    // 셀 선택 토글 & 버튼 상태
    function updateButtonState() {
      const anySelected = document.querySelector('.cell.selected') !== null;
      if (nextButton) {
        nextButton.disabled = !anySelected;
      }
    }

    cells.forEach(cell => {
      cell.addEventListener('click', () => {
        cell.classList.toggle('selected');
        updateButtonState();
      });
    });

    // 폼 제출
    scheduleForm.addEventListener('submit', async function(e) {
      e.preventDefault();

      const selectedCells = document.querySelectorAll('.cell.selected');
      const freeTimes = Array.from(selectedCells).map(cell => ({
        day_of_week: cell.dataset.day,
        start_time: cell.dataset.time,
        end_time: ProfileStep3.getEndTime(cell.dataset.time)
      }));

      const payload = { free_times: freeTimes };

      try {
        const response = await ProfileOnboarding.authFetch('/profiles/api/free_time/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          alert('공강시간이 성공적으로 저장되었습니다!');
          window.location.href = '/profiles/step4/page/';
        } else {
          const error = await response.json().catch(() => ({}));
          alert('저장 중 오류가 발생했습니다: ' + JSON.stringify(error));
        }
      } catch (error) {
        console.error('저장 실패:', error);
        alert('저장 중 오류가 발생했습니다. 네트워크 상태를 확인해주세요.');
      }
    });

    // 초기 버튼 상태
    updateButtonState();
  },

  async loadExistingSchedule() {
    try {
      const response = await ProfileOnboarding.authFetch('/profiles/api/free_time/', { method: 'GET' });
      if (response.ok) {
        const data = await response.json();
        if (data.free_times) {
          data.free_times.forEach(freeTime => {
            const cell = document.querySelector(`[data-day="${freeTime.day_of_week}"][data-time="${freeTime.start_time}"]`);
            if (cell) cell.classList.add('selected');
          });
          this.updateButtonState();
        }
      } else if (response.status === 401) {
        console.warn('인증 필요: 토큰을 확인하세요.');
      }
    } catch (error) {
      console.error('공강시간 불러오기 실패:', error);
    }
  },

  getEndTime(startTime) {
    const [hours, minutes] = startTime.split(':').map(Number);
    const endMinutes = minutes + 30;
    const endHours = hours + Math.floor(endMinutes / 60);
    const finalMinutes = endMinutes % 60;
    return `${endHours.toString().padStart(2, '0')}:${finalMinutes.toString().padStart(2, '0')}`;
  },

  updateButtonState() {
    const anySelected = document.querySelector('.cell.selected') !== null;
    const nextButton = document.getElementById('next-button');
    if (nextButton) {
      nextButton.disabled = !anySelected;
    }
  }
};

// ========================================
// 초기화
// ========================================
document.addEventListener('DOMContentLoaded', function() {
  // 토큰 부트스트랩
  ProfileOnboarding.bootstrapToken();

  // 현재 페이지에 따라 적절한 스크립트 실행
  const path = window.location.pathname;
  
  if (path.includes('/step1/')) {
    ProfileStep1.init();
  } else if (path.includes('/step2/')) {
    ProfileStep2.init();
  } else if (path.includes('/step3/')) {
    ProfileStep3.init();
  }
});
