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

### 1. 서버 주소 설정 (EXPO_PUBLIC_API_URL)

폰은 노트북의 `localhost`에 접속할 수 없으므로, 노트북의 **Wi-Fi IP 주소**를 앱에 알려줘야 한다.

1. 노트북 IP 확인
   - Windows: PowerShell에서 `ipconfig` → **"무선 LAN 어댑터 Wi-Fi"** 항목의 `IPv4 주소` (예: `192.168.0.10`)
     - `vEthernet (WSL)`, `169.254.x.x` 주소는 쓰면 안 된다
   - macOS: `ipconfig getifaddr en0`
2. `app/.env` 파일 만들기 (`app/.env.example`을 복사)
   ```
   EXPO_PUBLIC_API_URL=http://192.168.0.10:8000
   ```
   `http://`와 포트 `:8000`까지 적고, 끝에 `/`는 붙이지 않는다.
3. 폰 브라우저에서 `http://<노트북 IP>:8000/health`를 열어 `{"status":"ok"}`가 보이는지 확인한다.
   안 보이면 앱도 서버에 접속할 수 없다 → 아래 "연결이 안 될 때" 참고.

`.env`를 바꾼 뒤에는 `npx expo start -c`로 캐시를 지우고 다시 시작해야 반영된다.
Wi-Fi가 바뀌면 IP도 바뀌니 다시 확인한다.

### 2. 실행

```bash
cd app
npm install
npx expo start
```

터미널에 뜬 QR 코드를 폰으로 스캔한다 (iOS는 카메라 앱, Android는 Expo Go 앱의 스캔 기능).

### 연결이 안 될 때

- 서버를 `--host 0.0.0.0`으로 실행했는지 확인한다 (빠뜨리면 노트북 안에서만 접속된다).
- Windows 방화벽 허용 창이 뜨면 허용한다.
- 회사·학교 Wi-Fi는 기기끼리의 통신을 막는 경우가 있다. 이때는 폰 핫스팟에 노트북을 연결하고, 노트북 IP를 다시 확인해서 `.env`에 넣는다.
- QR 스캔 후 앱 자체가 안 뜨면 `npx expo start --tunnel`을 쓴다. 단, 이 방법은 앱 번들만 터널로 받으므로 서버 주소(`EXPO_PUBLIC_API_URL`)는 여전히 같은 네트워크의 IP여야 한다.
