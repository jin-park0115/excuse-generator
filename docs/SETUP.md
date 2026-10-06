# 실행·배포 가이드

로컬에서 실행하는 방법, Render·Vercel 배포 절차, 문제 해결을 모았습니다. 프로젝트 소개는 [README](../README.md)를 보세요.

## 목차

1. [준비물](#준비물)
2. [로컬 실행](#로컬-실행)
3. [연결이 안 될 때](#연결이-안-될-때)
4. [서버 배포 (Render)](#서버-배포-render)
5. [웹 배포 (Vercel)](#웹-배포-vercel)
6. [CORS 설정](#cors-설정)
7. [급식체 유행어 고치기](#급식체-유행어-고치기)
8. [폴더 구조](#폴더-구조)

## 준비물

- Node.js 20+ / Python 3.10+
- **Gemini API 키** (https://aistudio.google.com/apikey 에서 무료 발급)
- 폰으로 볼 때: **Expo Go** 앱(최신 버전)과 **Expo 계정**(https://expo.dev 무료 가입). 컴퓨터에서 `npx expo login`, 폰 Expo Go에서도 같은 계정으로 로그인
- 폰과 컴퓨터가 **같은 Wi-Fi**에 연결 (로컬 서버를 쓸 때)

## 로컬 실행

### 1. 서버

```bash
cd server
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env → GEMINI_API_KEY 값을 채운다
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- 확인: http://localhost:8000/health → `{"status":"ok"}`
- 테스트: `pytest` (실제 LLM은 호출하지 않음)
- 프롬프트 품질 확인: `python -m scripts.sample_excuses` → 실제 Gemini로 18개(상황 3 × 레벨 1·5·10 × 말투 2)를 출력한다. 약 1.5분. Windows에서 한글이 깨지면 먼저 `set PYTHONIOENCODING=utf-8`

`server/.env`에 넣는 값:

| 키 | 필수 | 설명 |
| --- | --- | --- |
| `GEMINI_API_KEY` | ✅ | Gemini API 키 |
| `GEMINI_MODEL` | | 비우면 `gemini-3.5-flash-lite`. 과부하(503)가 계속될 때만 바꾼다 |
| `ALLOWED_ORIGINS` | | 비우면 전체 허용(개발용). 배포 시 웹 주소만 넣는다 |

### 2. 앱 서버 주소 (`EXPO_PUBLIC_API_URL`)

`app/.env.example`을 `app/.env`로 복사하고 서버 주소를 넣는다. `http(s)://`와 포트까지 쓰고 끝에 `/`는 붙이지 않는다.

| 서버 | 값 |
| --- | --- |
| 노트북 서버 | `http://<노트북 Wi-Fi IP>:8000` — 폰은 노트북의 `localhost`에 접속할 수 없다 |
| 배포 서버 | `https://excuse-generator-api-4m2b.onrender.com` |

노트북 IP 확인: Windows는 `ipconfig` → "무선 LAN 어댑터 Wi-Fi"의 IPv4 주소(`vEthernet (WSL)`·`169.254.x.x`는 제외), macOS는 `ipconfig getifaddr en0`.

`.env`를 바꾸면 `npx expo start -c`로 캐시를 지우고 다시 시작해야 반영된다.

### 3. 앱

```bash
cd app
npm install
npx expo start          # 폰: QR 코드 스캔(iOS는 카메라 앱, Android는 Expo Go)
npx expo start --web    # 브라우저에서 보기
```

## 연결이 안 될 때

| 증상 | 확인할 것 |
| --- | --- |
| Expo Go에 영어로 "The Internet connection appears to be offline" | 앱 코드(번들)를 노트북에서 못 받는 상태. 폰을 노트북과 같은 Wi-Fi로 연결하고, iPhone 설정 → Expo Go → **로컬 네트워크**를 켠다. 다른 네트워크(LTE 등)에서는 `npx expo start --tunnel` |
| 폰 브라우저에서 `http://<노트북 IP>:8000/health`가 안 열림 | 서버를 `--host 0.0.0.0`으로 실행했는지, Windows 방화벽 허용 창을 허용했는지. 회사·학교 Wi-Fi는 기기끼리 통신을 막기도 한다 → 폰 핫스팟에 노트북을 연결하고 IP를 다시 확인 |
| 앱에 "서버에 연결할 수 없어요" | 위 `/health` 확인, `app/.env`의 주소 확인 후 `npx expo start -c` |
| 앱에 "핑계 공장이 잠깐 멈췄어요" | 서버 로그 확인. Gemini 과부하(503)나 무료 한도일 수 있다. 과부하가 계속되면 `GEMINI_MODEL`로 다른 모델 지정 |
| 앱에 "핑계도 쉬어가며…" | 레이트리밋(IP당 분당 10회·일 200회). 1분 기다리거나 서버 재시작(메모리 기반이라 초기화) |
| 앱에 "서버를 깨우는 중이에요…"가 오래 뜸 | 배포 서버가 잠들었다 깨는 중(최대 약 1분). 정상 동작 |

## 서버 배포 (Render)

설정은 저장소 루트의 [`render.yaml`](../render.yaml)에 있다: Python 3.14.3, `server` 폴더, Singapore 리전, Free 플랜, 헬스 체크 `/health`.

### 처음 만들기

1. 저장소를 GitHub에 push한다 (`server/.env`는 `.gitignore`로 제외됨)
2. https://dashboard.render.com → **New → Blueprint** → 이 저장소 선택
3. `excuse-generator-api`(Python · Singapore · Free)가 보이면 환경변수를 입력한다
   - `GEMINI_API_KEY`: Gemini API 키
   - `GEMINI_MODEL`: `gemini-3.5-flash-lite`
4. **Apply**를 누르고 로그에 `Uvicorn running on http://0.0.0.0:10000`이 보일 때까지 기다린다
5. `https://<서비스 주소>.onrender.com/health` → `{"status":"ok"}`

### 환경변수 바꾸기

서비스 → **Environment** → **Edit** → 값 수정 또는 **+ Add Environment Variable** → **Save, rebuild, and deploy**.

> 이 프로젝트의 Render 서비스는 `render.yaml` 변경을 자동으로 반영하지 않는다(처음 만들 때만 읽음). `render.yaml`의 값을 바꾸면 대시보드 Environment에도 같은 값을 직접 넣는다.

### 서버가 잠들지 않게 하기 (GitHub Actions)

Render 무료 서버는 15분 동안 요청이 없으면 잠들고 깨는 데 약 1분 걸린다. [`.github/workflows/keep-alive.yml`](../.github/workflows/keep-alive.yml)이 10분마다 `/health`를 호출한다.

1. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret** (Variables가 아니라 Secrets, Environment secret이 아니라 repository secret)
   - Name: `SERVER_URL` / Secret: `https://<서비스 주소>.onrender.com` (끝에 `/` 없이)
2. **Actions → keep-alive → Run workflow**로 수동 실행해 초록 체크 확인

주의할 점:

- 비공개 저장소는 Actions 무료 시간(월 2,000분)을 넘는다 (실행마다 1분 올림, 10분 간격이면 월 약 4,300분). 공개 저장소는 제한 없음
- 예약 실행은 몇 분씩 늦어질 수 있고, 공개 저장소에서 60일간 커밋이 없으면 GitHub가 예약 실행을 끈다
- Render 무료 인스턴스 시간은 월 750시간이라 서버 1개를 내내 켜 둬도(최대 744시간) 넘지 않는다
- 그래도 서버가 잠들어 있으면 앱이 첫 요청 전에 `/health`로 깨운다

## 웹 배포 (Vercel)

설정은 [`app/vercel.json`](../app/vercel.json)에 있다: `npx expo export --platform web` → `dist`, 모든 주소를 `index.html`로(SPA).

1. https://vercel.com 에 GitHub로 로그인 → **Add New → Project** → 이 저장소 **Import**
2. 설정
   - **Root Directory**: `app`
   - **Framework Preset**: `Other` (Build Command·Output Directory는 비워 둔다)
   - **Environment Variables**: `EXPO_PUBLIC_API_URL` = `https://<Render 서비스 주소>.onrender.com`
3. **Deploy** → 이후 `main`에 push할 때마다 자동 배포

`EXPO_PUBLIC_API_URL`은 빌드할 때 코드에 들어가므로, 서버 주소를 바꾸면 Vercel에서 **Redeploy**해야 한다.

### 홈 화면에 앱처럼 추가하기

- **iPhone (Safari)**: 공유 버튼 → **홈 화면에 추가**
- **Android (Chrome)**: ⋮ → **홈 화면에 추가**(또는 **앱 설치**)

홈 화면에서 열면 주소창 없이 전체 화면으로 뜨고, 이름·아이콘은 "핑계생성기"로 나온다. 설정은 `app/public/`의 `index.html`(아이콘·전체 화면·상단 표시줄 색), `manifest.json`, 아이콘 PNG(180·192·512px). 아이콘을 바꿨다면 홈 화면 아이콘을 지우고 다시 추가해야 반영된다. 브라우저 탭 아이콘이 그대로면 Ctrl+F5나 시크릿 창으로 확인한다.

### 웹에서 달라지는 점

| 기능 | 앱 (Expo Go) | 웹 |
| --- | --- | --- |
| 공유 | OS 공유 시트 | 공유 시트가 있는 브라우저(모바일 Safari·Chrome)는 공유 시트, 없는 브라우저(대부분 PC)는 클립보드 복사로 대신 |
| 기록 삭제 | 왼쪽으로 밀기 | 항목 오른쪽 위 ✕ 버튼 |
| 기록·즐겨찾기 | 기기 저장소 | 브라우저 저장소(브라우저·기기마다 따로, 사이트 데이터를 지우면 사라짐) |
| 화면 폭 | 폰 전체 | PC에서는 가운데 640px |

## CORS 설정

Render 서버는 `ALLOWED_ORIGINS`에 적힌 웹 주소의 브라우저 요청만 받는다.

- 현재 값: `https://excuse-generator-app.vercel.app` (Render Environment와 `render.yaml` 둘 다)
- `https://`까지 쓰고 끝에 `/` 없이, 여러 개면 쉼표로 구분
- 비우면 전체 허용(`*`)
- Expo 앱(네이티브)은 Origin 헤더를 보내지 않아 영향 없음
- Vercel 미리보기 주소(`…-git-브랜치-….vercel.app`)는 막힌다. 필요하면 쉼표로 추가

확인 방법:

```bash
curl -s -o /dev/null -D - -X OPTIONS https://<서비스 주소>.onrender.com/api/excuse \
  -H "Origin: https://excuse-generator-app.vercel.app" -H "Access-Control-Request-Method: POST"
# → 200, access-control-allow-origin: https://excuse-generator-app.vercel.app
# Origin을 다른 주소로 바꾸면 → 400
```

## 급식체 유행어 고치기

[`server/slang.py`](../server/slang.py)의 `SLANG` 목록만 고치면 된다. 프롬프트나 다른 코드는 건드릴 필요 없다.

```python
Slang(expression="엄..", meaning="말문이 막히거나 어이없을 때 문장 앞에 붙이는 추임새",
      usage="어이없거나 말문이 막히는 순간, 본문 문장 맨 앞에 추임새로 붙임"),
Slang(expression="줴줴이야~", meaning='GG를 찰지게 외치는 말. "끝났다, 망했다"는 뜻',
      usage="신뢰도가 낮을 때 코멘트 끝에 붙임", min_level=9, max_level=10),
```

- 급식체일 때만 50% 확률(`SLANG_RATE`)로, 요청 레벨이 `min_level`~`max_level`(기본 1~10) 안에 드는 항목 중 하나를 넘긴다
- `usage`에는 예시 문장이 아니라 **설명**을 쓴다. 예시 문장을 쓰면 LLM이 그대로 베낀다 (테스트로 검사)
- 실존 인물·팀·집단을 가리키거나 놀리는 표현은 넣지 않는다

## 폴더 구조

```text
excuse-generator/
├── app/                       # Expo 앱 (iOS·Android·웹 공통)
│   ├── app/                   # 화면: index(홈), result(결과), history(기록)
│   ├── components/            # Chip, CredibilityGauge
│   ├── constants/theme.ts     # 라이트/다크 색상
│   ├── lib/                   # api.ts(서버 호출·깨우기), storage.ts(기록·즐겨찾기)
│   ├── public/                # 웹 HTML 템플릿, manifest.json, 홈 화면 아이콘
│   └── vercel.json            # 웹 배포 설정
├── server/                    # FastAPI
│   ├── main.py                # 엔드포인트, 에러 응답, CORS, 클라이언트 IP
│   ├── schemas.py             # Pydantic 모델
│   ├── llm.py                 # Gemini 호출·파싱·검사·재시도, 신뢰도·소재·과장 방법·유행어 선택
│   ├── prompts.py             # 시스템 프롬프트, 레벨 구간별 소재·과장 방법 후보
│   ├── slang.py               # 급식체 유행어 목록
│   ├── rate_limit.py          # IP별 분당 10회·일 200회
│   ├── scripts/sample_excuses.py
│   └── tests/
├── docs/                      # 실행·배포 가이드, 개발 기록, 스크린샷
├── .github/workflows/keep-alive.yml
├── render.yaml                # Render 배포 설정
├── PRD.md
└── DECISIONS.md
```
