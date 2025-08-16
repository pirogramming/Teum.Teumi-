// ========================================
// 프로필 홈/상세 공통 스크립트
// - 토큰 부트스트랩, 인증 fetch
// - 상세 페이지(신청/모달/스케줄 렌더) 초기화
// ========================================

const ProfilesApp = {
  bootstrapToken() {
    const access = window.tmplAccess || '';
    const refresh = window.tmplRefresh || '';
    if (access) localStorage.setItem('access', access);
    if (refresh) localStorage.setItem('refresh', refresh);
  },

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
    } catch (_) {
      return null;
    }
  },

  async authFetch(url, options = {}, tryRefresh = true) {
    const token = localStorage.getItem('access') || '';
    const headers = { ...(options.headers || {}), 'Authorization': token ? `Bearer ${token}` : '' };
    let res = await fetch(url, { ...options, headers });
    if (res.status === 401 && tryRefresh) {
      const newAccess = await this.refreshAccessToken();
      if (newAccess) {
        const retryHeaders = { ...(options.headers || {}), 'Authorization': `Bearer ${newAccess}` };
        res = await fetch(url, { ...options, headers: retryHeaders });
      }
    }
    return res;
  }
};

// =============================
// 상세 페이지 초기화 및 전역 함수
// =============================
const ProfileDetailPage = {
  init() {
    // 신청 버튼 활성화 제어
    const textarea = document.getElementById('applicationReason');
    const submitButton = document.querySelector('.submit-button');
    if (textarea && submitButton) {
      submitButton.disabled = true;
      textarea.addEventListener('input', () => {
        submitButton.disabled = textarea.value.trim().length === 0;
      });
    }

    // 전역 함수 바인딩 (템플릿의 onclick 핸들러에서 사용)
    window.goBack = () => window.history.back();
    window.showApplicationModal = () => {
      const m = document.getElementById('applicationModal');
      if (m) m.style.display = 'flex';
    };
    window.hideApplicationModal = () => {
      const m = document.getElementById('applicationModal');
      if (m) m.style.display = 'none';
    };
    window.showDetailModal = () => {
      const m = document.getElementById('detailModal');
      if (m) m.style.display = 'flex';
      ProfileDetailPage.renderSchedule();
    };
    window.hideDetailModal = () => {
      const m = document.getElementById('detailModal');
      if (m) m.style.display = 'none';
    };
    window.switchTab = (tabName) => {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
      const panel = document.getElementById(`${tabName}Tab`);
      if (panel) panel.classList.add('active');
      if (typeof event !== 'undefined' && event.target) {
        event.target.classList.add('active');
      }
      if (tabName === 'schedule') ProfileDetailPage.renderSchedule();
    };
    window.toggleLike = () => {
      const heart = document.querySelector('.heart-icon');
      if (heart) heart.classList.toggle('liked');
    };
    window.submitApplication = ProfileDetailPage.submitApplication;

    // 초기 로그
    document.addEventListener('DOMContentLoaded', () => {
      // noop - 자리표시자
    });
  },

  renderSchedule() {
    const grid = document.querySelector('.schedule-grid');
    if (!grid) return;
    const data = window.PROFILE_DATA || {};
    const schedule = data.schedule || [];
    const days = ['월', '화', '수', '목', '금', '토', '일'];
    const timeSlots = [];
    for (let h = 9; h <= 20; h++) { timeSlots.push(`${h}:00`); timeSlots.push(`${h}:30`); }
    timeSlots.push('21:00');

    let html = `<div class="schedule-header"><div class="time-label"></div>${days.map(d=>`<div class="day-label">${d}</div>`).join('')}</div>`;
    timeSlots.forEach((time, hourIndex) => {
      html += `<div class="schedule-row"><div class="time-label">${time}</div>`;
      html += days.map((_, dayIndex) => {
        const isAvailable = schedule && schedule[dayIndex] && schedule[dayIndex][hourIndex];
        return `<div class="schedule-cell ${isAvailable ? 'available' : ''}"></div>`;
      }).join('');
      html += `</div>`;
    });
    grid.innerHTML = html;
  },

  submitApplication() {
    const textarea = document.getElementById('applicationReason');
    const reason = (textarea && textarea.value ? textarea.value : '').trim();
    if (!reason) { alert('대화 신청 이유를 입력해주세요.'); return; }

    const toProfileId = window.TARGET_PROFILE_ID;
    const payload = { receiver: toProfileId, reason, message: reason, to_profile_id: toProfileId };
    const button = document.querySelector('#applicationModal .submit-button');
    const originalHTML = button ? button.innerHTML : null;
    if (button) { button.disabled = true; button.innerHTML = '전송 중...'; }

    (async () => {
      const endpoints = ['/matches/api/matches/'];
      let lastError = null;
      for (const url of endpoints) {
        try {
          const res = await ProfilesApp.authFetch(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
          });
          if (res.ok) {
            alert('대화 신청이 전송되었습니다!');
            const modal = document.getElementById('applicationModal');
            if (modal) modal.style.display = 'none';
            if (textarea) textarea.value = '';
            window.location.href = '/matches/';
            return;
          } else {
            let errText = '';
            try {
              const ct = res.headers.get('Content-Type') || '';
              if (ct.includes('application/json')) {
                const errJson = await res.json();
                errText = errJson.error || errJson.detail || JSON.stringify(errJson);
              } else {
                errText = await res.text();
              }
            } catch (_) { errText = ''; }
            lastError = `[${res.status}] ${errText || '응답 본문 없음'}`;
            if (res.status === 404) continue;
          }
        } catch (e) {
          lastError = e && e.message ? e.message : '네트워크 오류';
        }
      }
      alert('신청 실패: ' + (lastError || '알 수 없는 오류가 발생했습니다.'));
    })().finally(() => {
      if (button) { button.disabled = false; button.innerHTML = originalHTML || '<span>💌</span> 신청하기'; }
    });
  }
};

// =============================
// 부트스트랩
// =============================
document.addEventListener('DOMContentLoaded', () => {
  ProfilesApp.bootstrapToken();

  // 상세 페이지인지 간단히 감지
  if (document.getElementById('applicationReason') || document.getElementById('applicationModal')) {
    ProfileDetailPage.init();
  }
});


