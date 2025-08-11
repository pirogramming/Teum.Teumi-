/* ========================================= */
/* 페이지 네비게이션 함수들 */
/* ========================================= */

/**
 * 마이페이지로 이동하는 함수
 * 사용처: 헤더의 사용자 아바타 클릭, 하단 네비게이션의 마이 버튼 클릭
 */
function goToMyPage() {
    console.log('마이페이지로 이동');
    // Django URL 패턴: /users/mypage/
    window.location.href = '/users/mypage/';
}

/**
 * 특정 사용자의 프로필 상세 페이지로 이동하는 함수
 * @param {number} userId - 이동할 프로필의 사용자 ID
 * 사용처: 사용자 카드 클릭, 프로필 아바타 클릭
 */
function goToProfileDetail(userId) {
    console.log('프로필 상세 페이지로 이동, User ID:', userId);
    // Django URL 패턴: /profiles/profile/{userId}/
    window.location.href = `/profiles/profile/${userId}/`;
}

/**
 * 특정 사용자와 대화를 시작하는 함수
 * 현재는 프로필 상세 페이지로 이동하며, 추후 직접 채팅 페이지로 이동하도록 개선 예정
 * @param {number} userId - 대화할 사용자의 ID
 * 사용처: "이 분과 대화해볼래요" 버튼 클릭
 */
function goToChat(userId) {
    console.log('대화 시작을 위해 프로필 상세 페이지로 이동, User ID:', userId);
    // TODO: 추후 직접 채팅 페이지로 이동하도록 수정 예정
    // 현재는 프로필 상세 페이지에서 대화 신청을 처리
    window.location.href = `/profiles/profile/${userId}/`;
}

/**
 * 친구 찾기/탐색 페이지로 이동하는 함수
 * 현재는 준비 중 상태로 알림만 표시
 * 사용처: 하단 네비게이션의 탐색 버튼, 빠른 액션의 친구 찾기 버튼
 */
function goToBrowse() {
    console.log('친구 찾기 페이지로 이동');
    window.location.href = '/matches/browse/';
}

/**
 * 매칭 현황 페이지로 이동하는 함수
 * 현재는 준비 중 상태로 알림만 표시
 * 사용처: 하단 네비게이션의 매칭 버튼, 빠른 액션의 매칭 현황 버튼
 */
function goToMatching() {
    console.log('매칭 현황 페이지로 이동 - 준비중');
    // TODO: 실제 매칭 페이지 구현 후 URL 연결 예정
    alert('매칭 기능은 준비 중입니다!');
}

/* ========================================= */
/* 하단 네비게이션 바 관리 함수 */
/* ========================================= */

/**
 * 하단 네비게이션 바의 페이지 전환을 처리하는 메인 함수
 * - 클릭된 네비게이션 아이템의 시각적 상태를 업데이트
 * - 해당 페이지로 실제 이동을 수행
 * 
 * @param {string} page - 이동할 페이지 식별자 ('home', 'browse', 'chat-list', 'matching', 'mypage')
 * 사용처: 하단 네비게이션의 모든 버튼들
 */
function setCurrentPage(page) {
    console.log(`페이지 전환 요청: ${page}`);
    
    // 1단계: 모든 네비게이션 아이템에서 active 클래스 제거
    // active 클래스는 현재 선택된 페이지를 시각적으로 강조하는 역할
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 2단계: 클릭된 아이템에 active 클래스 추가
    // event.target.closest()를 사용하여 버튼 내부의 어떤 요소를 클릭해도 정확한 버튼을 찾음
    const clickedItem = event.target.closest('.nav-item');
    if (clickedItem) {
        clickedItem.classList.add('active');
    }
    
    // 3단계: 페이지별 실제 이동 처리
    switch(page) {
        case 'home':
            console.log('홈 페이지로 이동');
            // 프로필 홈 페이지로 이동 (메인 피드)
            window.location.href = '/profiles/profile/';
            break;
            
        case 'browse':
            console.log('탐색 페이지로 이동');
            // 탐색 페이지로 이동
            window.location.href = '/matches/browse/';
            break;
            
        case 'chat-list':
            console.log('대화 목록 페이지로 이동');
            window.location.href = '/chats/rooms/page/';
            break;
            
        case 'matching':
            console.log('매칭 페이지로 이동 - 준비중');
            // TODO: 매칭 현황 및 관리 페이지 구현 예정
            alert('매칭 기능은 준비 중입니다!');
            break;
            
        case 'mypage':
            console.log('마이페이지로 이동');
            // 사용자 프로필 편집 페이지로 이동
            window.location.href = '/users/mypage/';
            break;
            
    }
}

