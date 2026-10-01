# 핑계 생성기

상황·황당함 레벨·말투를 고르면 LLM이 핑계를 만들어주는 Expo 앱 + FastAPI 서버. 자세한 내용은 [PRD.md](PRD.md).

## 준비물

- Node.js 20+ / Python 3.10+
- 폰에 **Expo Go** 앱 (App Store / Play Store, 최신 버전)
- 컴퓨터와 폰이 **같은 Wi-Fi**에 있어야 한다
- **Expo 계정** (https://expo.dev 에서 무료 가입). 컴퓨터에서 `npx expo login`, 폰의 Expo Go 앱에서도 같은 계정으로 로그인한다

## 서버 실행

```bash
cd server
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # GEMINI_API_KEY에 Gemini API 키를 넣는다
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Gemini API 키는 https://aistudio.google.com/apikey 에서 무료로 받을 수 있다. 서버는 로컬에서만 실행한다.

확인: 브라우저에서 http://localhost:8000/health → `{"status":"ok"}`

테스트: `server` 폴더에서 `pytest` (실제 LLM은 호출하지 않는다)

샘플 핑계 18개 보기 (실제 Gemini 호출, 약 1.5분): `server` 폴더에서 `python -m scripts.sample_excuses`

## 앱 실행

```bash
cd app
npm install
npx expo start
```

터미널에 뜬 QR 코드를 폰으로 스캔한다 (iOS는 카메라 앱, Android는 Expo Go 앱의 스캔 기능).
같은 Wi-Fi인데 연결이 안 되면 `npx expo start --tunnel`을 쓴다.
