// 전역변수 설정
let currentMatchId = null;
const MATCH_API_BASE = '/matches/api/matches';
const STATUS = { PENDING: '대기중', ACCEPTED: '수락됨', REJECTED: '거절됨' };

window.setCurrentPage = setCurrentPage;

// === Auth & HTTP helpers ===
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function getAccessToken() {
  return (
    localStorage.getItem('access') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('token') ||
    ''
  );
}

async function apiFetch(url, options = {}) {
  const token = getAccessToken();
  const headers = Object.assign(
    {
      'Accept': 'application/json',
    },
    options.headers || {}
  );
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const method = (options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) headers['X-CSRFToken'] = csrftoken;
  }
  const resp = await fetch(url, Object.assign({}, options, { headers, method }));
  if (resp.status === 401) {
    // 토큰 만료 등: 로그인 페이지로 유도
    window.location.replace('/users/login/');
    return Promise.reject(new Error('Unauthorized'));
  }
  return resp;
}

// === Page navigation(base.html에 있는) ===
function setCurrentPage(name) {
  const routes = {
    home: '/profiles/profile/',
    browse: '/matches/browse/',
    'chat-list': '/chats/rooms/page/',
    matching: '/matches/',
    mypage: '/users/mypage/',
  };
  const url = routes[name] || '/profiles/profile/'; // 기본값은 프로필 페이지로 이동
  window.location.href = url;
}

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

// === Match actions (Accept/Reject) ===
async function updateMatchStatus(matchId, nextStatus, payload = {}) {
  if (!matchId) {
    console.log('매칭 ID를 찾을 수 없습니다.');
    return;
  }

  // 백엔드 한글 TextChoices로 매핑
  const statusToSend = STATUS[nextStatus] || nextStatus; // 이미 한글이면 그대로

  // 거절 사유 키 정규화 (reason -> refusal_message)
  const normalizedPayload = { ...payload };
  if (Object.prototype.hasOwnProperty.call(normalizedPayload, 'reason') && normalizedPayload.reason) {
    normalizedPayload.refusal_message = normalizedPayload.reason;
    delete normalizedPayload.reason;
  }

  const body = JSON.stringify({ status: statusToSend, ...normalizedPayload });

  try {
    const url = `${MATCH_API_BASE}/${matchId}/status/`;

    const resp = await apiFetch(url, {
      method: 'PATCH',
      body,
    });

    if (!resp.ok) {
      const raw = await resp.text().catch(() => '');
      console.warn('← PATCH error', resp.status, raw);
      let err;
      try { err = JSON.parse(raw); } catch { err = {}; }
      alert(err.detail || `상태 변경에 실패했습니다. (HTTP ${resp.status})`);
      return;
    }

    const data = await resp.json().catch(() => ({}));

    // 서버가 채팅방 URL을 주면 바로 이동
    if (data && data.room_id) {
      window.location.href = `/chats/rooms/page/${data.room_id}/`;
      return;
    }
    // 아니면 매칭 페이지 리로드
    window.location.reload();
  } catch (e) {
    console.error(e);
    alert('요청 중 오류가 발생했습니다.');
    }
}

function extractMatchIdFrom(el) {
  if (!el) return null;
  // 우선순위: data-id, data-match-id, value, id 속성 내 숫자
  return (
    el.dataset?.id ||
    el.dataset?.matchId ||
    el.getAttribute('data-id') ||
    el.getAttribute('data-match-id') ||
    el.value ||
    (el.id && el.id.match(/\d+/)?.[0]) ||
    null
  );
}

document.addEventListener("DOMContentLoaded", function () {

    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');

    if (tab) {
        showTab(tab);
    } else {
        showTab('request');
    }

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
            const matchId = extractMatchIdFrom(this);
            if (rejectModal) rejectModal.dataset.currentMatchId = matchId || '';
            showModal(rejectModal);
        });
    });

    // 수락하기 버튼
    document.querySelectorAll('.accept').forEach(btn => {
        btn.addEventListener('click', function () {
            const matchId = extractMatchIdFrom(this);
            updateMatchStatus(matchId, STATUS.ACCEPTED);
        });
    });

    // 매너온도 남기기 버튼
    document.querySelectorAll(".tab-right").forEach(btn => {
        if (btn.dataset.reviewed === 'false') {
            btn.addEventListener("click", function (event) {
                currentMatchId = this.dataset.id;
                showModal(reviewModal);
            });
        }
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

    const rejectSubmitBtn = document.getElementById('reject-submit') || document.querySelector('[data-role="reject-submit"]');
    const rejectReasonInput = document.getElementById('reject-text') || document.getElementById('reject-textarea') || document.querySelector('[name="reject_reason"]');
    if (rejectSubmitBtn) {
        rejectSubmitBtn.addEventListener('click', function () {
            const matchId = rejectModal?.dataset?.currentMatchId;
            const reason = (rejectReasonInput && rejectReasonInput.value) ? rejectReasonInput.value.trim() : '';
            updateMatchStatus(matchId, STATUS.REJECTED, reason ? { refusal_message: reason } : {});
        });
    }

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

// 매너온도 남기기 버튼(비동기식으로 처리)
document.addEventListener('click', async function (event) {

  // 클릭된 요소가 'review-button' 클래스를 가진 버튼인지 확인
  if (event.target.matches('.review-button')) {
      event.preventDefault();

     
      const matchId = currentMatchId;

      if (!matchId) {
          alert('매칭 ID를 찾을 수 없습니다.');
          return;
      }


      // 선택된 태도와 정도 값 가져오기
      const attitudeElements = document.querySelectorAll('input[name="attitude"]:checked');
      const attitudeValues = [];
      for (const el of attitudeElements) {
          if (el && el.value) {
              attitudeValues.push(el.value);
          }
      }
      const degreeElements = document.querySelectorAll('input[name="value"]:checked');
      const degreeValues = [];
      for (const el of degreeElements) {
          if (el && el.value) {
              degreeValues.push(el.value);
          }
      }

      const reviewData = {
          rating: document.getElementById('myRange').value,
          attitude_ids: attitudeValues,
          degree_ids: degreeValues,
          comment: document.querySelector('#oneline-review')?.value || '',
          meeting: document.querySelector('input[name="meet"]:checked').value,
          match_id: Number(currentMatchId), 
      };

      try {
          const response = await apiFetch('/reviews/', {
              method: 'POST',
              body: JSON.stringify(reviewData)
          });

          if (response.ok) {
              const result = await response.json();
              alert('리뷰가 성공적으로 저장되었습니다!');
              window.location.href = '/matches/?tab=completed';
          } else {
              let errorMessage = '알 수 없는 오류';
              try {
                  const result = await response.json();
                  errorMessage = result.detail || errorMessage;
              } catch (_) {
                  errorMessage = '서버 응답을 해석할 수 없습니다.';
              }
              alert(`리뷰 저장에 실패했습니다: ${errorMessage}`);
          }
      } catch (error) {
          alert('요청 처리 중 오류가 발생했습니다.');
      }
  }
});

document.querySelectorAll('.reject').forEach(btn => {
    btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        const nickname = btn.dataset.nickname;

        // 모달에 값 주입
        document.getElementById('reject-name').innerText = nickname;
        document.getElementById('reject-submit').dataset.id = id;
        document.getElementById('reject-submit').dataset.nickname = nickname;

        // 모달 열기
        document.getElementById('reject-reason').style.display = 'block';
        document.getElementById('modal-overlay').style.display = 'block';
    });
});

const reviewButtons = document.querySelectorAll(".review");
const reviewName = document.getElementById("review-name");

reviewButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        currentMatchId = btn.dataset.id; 
        reviewName.textContent = btn.dataset.nickname;
        document.getElementById("review").style.display = "block";
    });
});
