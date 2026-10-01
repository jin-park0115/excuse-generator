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
