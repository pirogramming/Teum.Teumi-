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
    console.log('매칭 현황 페이지로 이동');
    window.location.href = '/matches/';
}

/* ========================================= */
/* 하단 네비게이션 바 관리 함수 */
/* ========================================= */

/**
 * 하단 네비게이션 바의 페이지 전환을 처리하는 메인 함수
 * - 해당 페이지로 실제 이동을 수행
 * - 페이지 이동 후 setActiveNavigation()이 자동으로 활성 상태를 설정
 * 
 * @param {string} page - 이동할 페이지 식별자 ('home', 'browse', 'chat-list', 'matching', 'mypage')
 * 사용처: 하단 네비게이션의 모든 버튼들
 */
function setCurrentPage(page) {
    console.log(`페이지 전환 요청: ${page}`);
    
    // 페이지별 실제 이동 처리
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
            console.log('매칭 페이지로 이동');
            window.location.href = '/matches/';
            break;
            
        case 'mypage':
            console.log('마이페이지로 이동');
            // 사용자 프로필 편집 페이지로 이동
            window.location.href = '/users/mypage/';
            break;
            
    }
}

/**
 * 현재 페이지에 맞는 하단 네비게이션 활성 상태를 설정하는 함수
 * 페이지 로드 시 자동으로 호출되어 현재 페이지에 맞는 네비게이션 아이템을 활성화
 */
function setActiveNavigation() {
    const currentPath = window.location.pathname;
    console.log('현재 경로:', currentPath);
    
    // 모든 네비게이션 아이템에서 active 클래스 제거
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 현재 페이지에 맞는 네비게이션 아이템 활성화
    if (currentPath.includes('/profiles/profile/') && !currentPath.includes('/detail/')) {
        // 프로필 홈 페이지
        const homeNav = document.querySelector('.nav-item[data-page="home"]');
        if (homeNav) homeNav.classList.add('active');
    } else if (currentPath.includes('/matches/browse/')) {
        // 탐색 페이지
        const browseNav = document.querySelector('.nav-item[data-page="browse"]');
        if (browseNav) browseNav.classList.add('active');
    } else if (currentPath.includes('/chats/')) {
        // 대화 목록 페이지
        const chatNav = document.querySelector('.nav-item[data-page="chat-list"]');
        if (chatNav) chatNav.classList.add('active');
    } else if (currentPath.includes('/matches/') && !currentPath.includes('/browse/')) {
        // 매칭 페이지
        const matchingNav = document.querySelector('.nav-item[data-page="matching"]');
        if (matchingNav) matchingNav.classList.add('active');
    } else if (currentPath.includes('/users/mypage/')) {
        // 마이페이지
        const mypageNav = document.querySelector('.nav-item[data-page="mypage"]');
        if (mypageNav) mypageNav.classList.add('active');
    }
}

// 페이지 로드 시 현재 페이지에 맞는 네비게이션 활성 상태 설정
document.addEventListener('DOMContentLoaded', function() {
    setActiveNavigation();
});

