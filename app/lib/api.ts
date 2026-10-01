// 서버 /api/excuse 호출. 실패하면 화면에 보여줄 문구(PRD 섹션 5)를 담은 ApiError를 던진다.

// 서버가 허용하는 말투 5개 (server/schemas.py의 Tone과 같아야 한다). 첫 번째가 기본값
export const TONES = ['공손한 직장인체', '사극체', '급식체', '뉴스 앵커체', '발표자(학회)체'] as const;
export type Tone = (typeof TONES)[number];

export type Excuse = { excuse: string; credibility: number; comment: string };
export type ExcuseRequest = { situation: string; absurdity: number; tone: Tone; previous_excuse: string | null };

const API_URL = process.env.EXPO_PUBLIC_API_URL;
const TIMEOUT_MS = 20000;

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_INPUT: '입력을 다시 확인해주세요',
  RATE_LIMITED: '핑계도 쉬어가며 만들어야 해요. 잠시 후 다시!',
  LLM_ERROR: '핑계 공장이 잠깐 멈췄어요',
  LLM_TIMEOUT: '너무 오래 고민하는 중이에요. 다시 시도해주세요',
};
const NETWORK_ERROR = '서버에 연결할 수 없어요. 인터넷 연결을 확인해주세요';

export class ApiError extends Error {}

export async function fetchExcuse(req: ExcuseRequest): Promise<Excuse> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/excuse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal: controller.signal,
    });
  } catch {
    // 서버가 꺼졌거나, 비행기 모드이거나, 20초 안에 응답이 없을 때
    throw new ApiError(timedOut ? ERROR_MESSAGES.LLM_TIMEOUT : NETWORK_ERROR);
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(ERROR_MESSAGES[body?.error?.code] ?? ERROR_MESSAGES.LLM_ERROR);
  }
  return res.json();
}
