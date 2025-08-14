let logoutTimer = null;
let extendPromptShown = false;

function getTokenRemainingTime(token){
    if(!token) return 0;
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp *1000 -Date.now();
}

async function refreshAccessToken() {
    const refresh = localStorage.getItem('refresh');
    if(!refresh){
        alert('로그인이 필요합니다!');
        logout();
        return;
    }

    const res = await fetch('/users/token/refresh/',{
            method : 'POST',
            headers : {'Content-Type': 'application/json'},
            body : JSON.stringify({refresh})
    });

    if(res.ok){
        const data = await res.json();
        localStorage.setItem('access',data.access);
        alert('로그인이 연장되었습니다.')
        extendPromptShown = false;
    }
    else{
        alert('세션이 만료되었습니다. 다시 로그인 해주세요.')
        logout();
    }
}

function logout() {
    window.location.href = '/users/logout/'; 
}

function checkTokenExpiry() {
    const access = localStorage.getItem('access');
    const remaining = getTokenRemainingTime(access);

    if (remaining > 0 && remaining <= 5 * 60 * 1000) {
        if (!extendPromptShown){
            extendPromptShown = true;
            if (confirm('엑세스 토큰이 곧 만료됩니다.\n로그인을 연장하시겠습니까?')) {
                refreshAccessToken();
                if (logoutTimer) {
                    clearTimeout(logoutTimer);
                    logoutTimer = null;
                }
            } else {
                if (!logoutTimer) {
                    logoutTimer = setTimeout(() => {
                        alert('세션이 만료되어 로그아웃됩니다.');
                        logout();
                    }, 5 * 60 * 1000);
                }
            }
        }
    }
}

setInterval(checkTokenExpiry, 60 * 1000);