# DECISIONS

PRD에서 애매했던 부분과 고른 방법을 한 줄씩 기록한다.

- [M1] 템플릿 기본값은 `src/app/`이지만 PRD 구조대로 라우트를 `app/app/`에 둔다. `@/*` 경로 별칭은 `app/` 루트를 가리킨다.
- [M1] create-expo-app 기본 템플릿의 예제 화면·컴포넌트와 PRD 목록에 없는 의존성(@expo/ui, expo-image, reanimated, gesture-handler 등)은 삭제했다. web 실행용 react-dom/react-native-web은 템플릿 그대로 둔다.
- [M1] Expo SDK 57(생성 시점 최신 안정 버전)을 쓴다. Expo Go 앱도 SDK 57을 지원하는 최신 버전이어야 한다.
- [M1] 서버 의존성은 M1에 필요한 것만(fastapi, uvicorn, pytest, httpx) 버전 고정해 넣었다. pydantic은 fastapi가 함께 설치하며, python-dotenv·google-genai는 M3에서 추가한다.
- [M1] Starlette가 httpx 대신 httpx2를 권장하는 경고를 내지만, PRD 기술 스택대로 httpx를 유지한다 (테스트는 통과).
- [M1] /health가 동작하는지 확인하는 pytest 1개를 추가했다 (`server/tests/test_health.py`).
- [M2] 말투 칩(F6)·신뢰도 게이지(F7)·즐겨찾기 버튼(F9)·기록 아이콘(F8)은 M5 범위라 M2 화면에는 넣지 않았다.
- [M2] 로딩 표시·랜덤 로딩 문구는 실제 API 호출이 생기는 M4에서 넣는다. mock은 즉시 결과를 보여준다.
- [M2] mock 핑계는 상황·레벨과 관계없이 10개 중 랜덤이다 (PRD M2 정의대로). 다시 뽑기는 직전 핑계를 제외하고 고른다.
- [M2] "레벨별 이모지"는 레벨 1~10마다 이모지 하나씩(10개)으로 해석했다.
- [M2] 복사 토스트는 라이브러리 없이 화면 하단 텍스트를 1.5초 보여주는 방식으로 만들었다 (ToastAndroid는 iOS에 없음).
- [M2] 앱 제목은 홈 화면 상단 헤더("핑계 생성기")로 표시한다. 결과 화면 헤더는 "결과"이며 뒤로 가기로 홈에 돌아간다.
- [M3] 열린 질문 결정(사용자): LLM은 Gemini 유지, 서버는 당분간 로컬 실행만 한다 (PRD 섹션 9 반영).
- [M3] 모델은 `gemini-3.5-flash-lite`. 측정 시 응답 약 1초였고, 3.5-flash는 약 10초(p95 5초 초과), 3.8-flash는 503 과부하였다. 과부하 대비로 `.env`의 `GEMINI_MODEL`로 바꿀 수 있게 했다.
- [M3] 15초 타임아웃은 재시도를 포함한 전체 시간에 건다 (앱 타임아웃 20초 안에 끝나도록). 타임아웃이 나면 재시도하지 않는다.
- [M3] "재시도"는 JSON 파싱 실패뿐 아니라 Gemini API 오류(503 등)에도 1회 적용한다. 둘 다 실패하면 502 LLM_ERROR.
- [M3] LLM 응답이 길이 규칙(excuse 200자, comment 60자)을 넘기면 자르지 않고 파싱 실패로 보고 재시도한다.
- [M3] 코드펜스 제거와 별개로 Gemini의 JSON 출력 모드(response_mime_type)를 켜서 파싱 실패를 줄인다.
- [M3] 상황 앞뒤 공백은 제거하고 검증한다 (공백만 있으면 422).
- [M3] 429 RATE_LIMITED는 레이트리밋(M6)과 함께 구현한다. CORS 설정도 PRD 단계 목록에 없어 앱 연결(M4) 이후로 미룬다 (Expo Go 네이티브 앱은 CORS가 필요 없음).
- [M3] 샘플 스크립트는 Gemini 무료 티어 분당 한도(429) 때문에 호출 사이에 4초를 쉰다.
