// 서버 호출. /health로 잠든 서버를 깨우고(wakeServer), /api/excuse로 핑계를 받는다.
// 실패하면 화면에 보여줄 문구(PRD 섹션 5)를 담은 ApiError를 던진다.

// 서버가 허용하는 말투 5개 (server/schemas.py의 Tone과 같아야 한다). 첫 번째가 기본값
export const TONES = ['공손한 직장인체', '사극체', '급식체', '뉴스 앵커체', '발표자(학회)체'] as const;
export type Tone = (typeof TONES)[number];

export type Excuse = { excuse: string; credibility: number; comment: string };
export type ExcuseRequest = { situation: string; absurdity: number; tone: Tone; previous_excuse: string | null };

const API_URL = process.env.EXPO_PUBLIC_API_URL;
const TIMEOUT_MS = 20000;
const WAKE_TIMEOUT_MS = 75000; // Render 무료 서버는 잠들었다 깨는 데 약 1분 걸린다
const AWAKE_FOR_MS = 10 * 60 * 1000; // 마지막 응답 후 10분 안이면 깨어 있다고 본다 (Render는 15분 무요청 시 잠듦)

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_INPUT: '입력을 다시 확인해주세요',
  RATE_LIMITED: '핑계도 쉬어가며 만들어야 해요. 잠시 후 다시!',
  LLM_ERROR: '핑계 공장이 잠깐 멈췄어요',
  LLM_TIMEOUT: '너무 오래 고민하는 중이에요. 다시 시도해주세요',
};
const NETWORK_ERROR = '서버에 연결할 수 없어요. 인터넷 연결을 확인해주세요';

export class ApiError extends Error {}

// 제한 시간 안에 응답이 없으면 끊는 fetch. 연결 실패·시간 초과는 ApiError로 바꾼다
async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number, timeoutMessage: string): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch {
    // 서버가 꺼졌거나, 비행기 모드이거나, 제한 시간 안에 응답이 없을 때
    throw new ApiError(timedOut ? timeoutMessage : NETWORK_ERROR);
  } finally {
    clearTimeout(timer);
  }
}

let lastOkAt = 0;
let waking: Promise<void> | null = null;

export const isAwake = () => Date.now() - lastOkAt < AWAKE_FOR_MS;

// 서버가 깨어 있지 않으면 /health로 깨운다. 동시에 여러 번 불러도 요청은 한 번만 보낸다
export function wakeServer(): Promise<void> {
  if (isAwake()) return Promise.resolve();
  waking ??= fetchWithTimeout(`${API_URL}/health`, { method: 'GET' }, WAKE_TIMEOUT_MS, NETWORK_ERROR)
    .then((res) => {
      if (!res.ok) throw new ApiError(NETWORK_ERROR);
      lastOkAt = Date.now();
    })
    .finally(() => {
      waking = null;
    });
  return waking;
}

export async function fetchExcuse(req: ExcuseRequest): Promise<Excuse> {
  const res = await fetchWithTimeout(
    `${API_URL}/api/excuse`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(req) },
    TIMEOUT_MS,
    ERROR_MESSAGES.LLM_TIMEOUT,
  );
  lastOkAt = Date.now(); // 에러 응답이라도 서버가 답했으면 깨어 있는 것
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(ERROR_MESSAGES[body?.error?.code] ?? ERROR_MESSAGES.LLM_ERROR);
  }
  return res.json();
}
