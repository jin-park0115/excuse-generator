# DECISIONS

PRD에서 애매했던 부분과 고른 방법을 한 줄씩 기록한다.

- [M1] 템플릿 기본값은 `src/app/`이지만 PRD 구조대로 라우트를 `app/app/`에 둔다. `@/*` 경로 별칭은 `app/` 루트를 가리킨다.
- [M1] create-expo-app 기본 템플릿의 예제 화면·컴포넌트와 PRD 목록에 없는 의존성(@expo/ui, expo-image, reanimated, gesture-handler 등)은 삭제했다. web 실행용 react-dom/react-native-web은 템플릿 그대로 둔다.
- [M1] Expo SDK 57(생성 시점 최신 안정 버전)을 쓴다. Expo Go 앱도 SDK 57을 지원하는 최신 버전이어야 한다.
- [M1] 서버 의존성은 M1에 필요한 것만(fastapi, uvicorn, pytest, httpx) 버전 고정해 넣었다. pydantic은 fastapi가 함께 설치하며, python-dotenv·google-genai는 M3에서 추가한다.
- [M1] Starlette가 httpx 대신 httpx2를 권장하는 경고를 내지만, PRD 기술 스택대로 httpx를 유지한다 (테스트는 통과).
- [M1] /health가 동작하는지 확인하는 pytest 1개를 추가했다 (`server/tests/test_health.py`).
