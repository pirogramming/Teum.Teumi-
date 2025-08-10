# 틈틈이 API 명세서

## 마이페이지 편집 API

### 1. 기본 정보 업데이트 API

**엔드포인트:** `POST /users/update-basic/`

**설명:** 사용자의 기본 정보(닉네임, MBTI, 성별, 자기소개)를 업데이트합니다.

**요청 헤더:**
```
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: {csrf_token}
```

**요청 파라미터:**
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| nickname | string | Y | 사용자 닉네임 |
| mbti | string | Y | MBTI 유형 (예: ISTJ, ENFP 등) |
| gender | string | Y | 성별 (M: 남성, F: 여성) |
| introduction | string | Y | 자기소개 |

**요청 예시:**
```bash
curl -X POST /users/update-basic/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-CSRFToken: {csrf_token}" \
  -d "nickname=홍길동&mbti=ISTJ&gender=M&introduction=안녕하세요!"
```

**응답 성공 (200):**
```json
{
  "success": true,
  "message": "기본 정보가 성공적으로 업데이트되었습니다."
}
```

**응답 실패 (400):**
```json
{
  "success": false,
  "message": "모든 필수 필드를 입력해주세요."
}
```

**응답 실패 (404):**
```json
{
  "success": false,
  "message": "프로필을 찾을 수 없습니다."
}
```

---

### 2. 관심사 업데이트 API

**엔드포인트:** `POST /users/update-interests/`

**설명:** 사용자의 관심사를 업데이트합니다. 정확한 매칭을 위해 4개의 관심사를 선택해야 합니다.

**요청 헤더:**
```
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: {csrf_token}
```

**요청 파라미터:**
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| interests | string | Y | 선택된 관심사 ID 배열 (JSON 문자열) |

**요청 예시:**
```bash
curl -X POST /users/update-interests/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-CSRFToken: {csrf_token}" \
  -d "interests=[1,2,3,4]"
```

**응답 성공 (200):**
```json
{
  "success": true,
  "message": "관심사가 성공적으로 업데이트되었습니다."
}
```

**응답 실패 (400):**
```json
{
  "success": false,
  "message": "관심사 데이터가 없습니다."
}
```

---

### 3. 스케줄 업데이트 API

**엔드포인트:** `POST /users/update-schedule/`

**설명:** 사용자의 만날 수 있는 시간을 업데이트합니다. 최소 1개 이상의 시간을 선택해야 합니다.

**요청 헤더:**
```
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: {csrf_token}
```

**요청 파라미터:**
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule | string | Y | 스케줄 매트릭스 (JSON 문자열) - 7x25 배열 |

**스케줄 매트릭스 구조:**
- 7일 (월~일)
- 25개 시간 슬롯 (9:00~21:30, 30분 단위)
- `true`: 선택된 시간, `false`: 선택되지 않은 시간

**요청 예시:**
```bash
curl -X POST /users/update-schedule/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-CSRFToken: {csrf_token}" \
  -d "schedule=[[true,false,true,...],[false,true,false,...],...]"
```

**응답 성공 (200):**
```json
{
  "success": true,
  "message": "스케줄이 성공적으로 업데이트되었습니다."
}
```

**응답 실패 (400):**
```json
{
  "success": false,
  "message": "스케줄 데이터가 없습니다."
}
```

---

### 4. 상세 정보 업데이트 API

**엔드포인트:** `POST /users/update-advanced/`

**설명:** 사용자의 상세 정보(경험, 대화스타일, 활동위치, 성격키워드, 목표)를 업데이트합니다.

**요청 헤더:**
```
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: {csrf_token}
```

**요청 파라미터:**
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| experience | string | N | 경험과 활동 |
| conversation_style | string | N | 대화 스타일 (casual/deep/humor/debate) |
| activity_location | string | N | 주요 활동 위치 |
| goal_or_concern | string | N | 현재 목표나 고민 |
| personalities | string | N | 선택된 성격 키워드 ID 배열 (JSON 문자열) |

**대화 스타일 옵션:**
- `casual`: ☕ 수다형
- `deep`: 🎯 깊은대화형
- `humor`: 😄 유머형
- `debate`: 💼 토론형

**요청 예시:**
```bash
curl -X POST /users/update-advanced/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-CSRFToken: {csrf_token}" \
  -d "experience=UX 해커톤 2회 참가&conversation_style=casual&activity_location=혜화 캠퍼스&goal_or_concern=포트폴리오 준비&personalities=[1,2,3]"
```

**응답 성공 (200):**
```json
{
  "success": true,
  "message": "상세 정보가 성공적으로 업데이트되었습니다."
}
```

**응답 실패 (400):**
```json
{
  "success": false,
  "message": "잘못된 성격 키워드 데이터 형식입니다."
}
```

---

## 로그아웃 API

### 5. 로그아웃 API

**엔드포인트:** `GET /users/logout/`

**설명:** 사용자를 로그아웃 처리하고 로그인 페이지로 리다이렉트합니다.

**요청 헤더:**
```
X-CSRFToken: {csrf_token}
```

**요청 예시:**
```bash
curl -X GET /users/logout/ \
  -H "X-CSRFToken: {csrf_token}"
```

**응답:** 로그인 페이지로 리다이렉트 (`/users/login/`)

---

## 공통 응답 형식

### 성공 응답
```json
{
  "success": true,
  "message": "작업이 성공적으로 완료되었습니다."
}
```

### 실패 응답
```json
{
  "success": false,
  "message": "오류 메시지"
}
```

## 오류 코드

| HTTP 상태 코드 | 설명 |
|---------------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (필수 파라미터 누락, 잘못된 데이터 형식) |
| 401 | 인증 실패 |
| 404 | 리소스를 찾을 수 없음 |
| 500 | 서버 내부 오류 |

## 인증

모든 API는 사용자 인증이 필요합니다. `@permission_classes([IsAuthenticated])` 데코레이터를 사용하여 인증된 사용자만 접근할 수 있습니다.

## CSRF 보안

모든 POST 요청에는 CSRF 토큰이 필요합니다. 요청 헤더에 `X-CSRFToken`을 포함해야 합니다.

## 데이터 검증

### 기본 정보 검증
- 모든 필드 (nickname, mbti, gender, introduction) 필수 입력
- MBTI는 유효한 16가지 유형 중 하나여야 함
- 성별은 'M' 또는 'F'만 허용

### 관심사 검증
- 정확히 4개의 관심사를 선택해야 함
- 선택된 관심사 ID가 유효해야 함

### 스케줄 검증
- 최소 1개 이상의 시간을 선택해야 함
- 스케줄 매트릭스는 7x25 배열이어야 함

### 성격 키워드 검증
- 최대 3개의 성격 키워드 선택 가능
- 선택된 키워드 ID가 유효해야 함 