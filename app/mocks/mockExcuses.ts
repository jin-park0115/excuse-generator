// M2용 가짜 핑계 데이터. 서버 연결(M4) 전까지 이 중 하나를 랜덤으로 보여준다.
// 모양은 서버 응답(PRD 섹션 5)과 같게 맞춰 둔다.

export type Excuse = { excuse: string; credibility: number; comment: string };

export const mockExcuses: Excuse[] = [
  { excuse: '버스가 배차 간격보다 15분 늦게 왔습니다. 정말 죄송합니다.', credibility: 90, comment: '누구나 한 번쯤 겪는 일이죠.' },
  { excuse: '휴대폰 알람이 업데이트되면서 꺼져 있었습니다.', credibility: 80, comment: '업데이트 탓은 꽤 먹힙니다.' },
  { excuse: '엘리베이터에서 이웃 할머니의 손자 자랑을 끝까지 들었습니다.', credibility: 55, comment: '디테일이 오히려 수상합니다.' },
  { excuse: '현관문 비밀번호를 바꾼 다음 날이라 기억이 안 났습니다.', credibility: 45, comment: '그럴 수도… 있을까요?' },
  { excuse: '편의점 사장님이 로또 번호 고르는 걸 도와달라고 하셨습니다.', credibility: 35, comment: '당첨됐으면 안 왔겠죠.' },
  { excuse: '비둘기가 가방에 들어와서 지하철에서 못 내렸습니다.', credibility: 15, comment: '비둘기도 출근 중이었나 봅니다.' },
  { excuse: '마라톤 대회 행렬에 휩쓸려 10km를 완주하고 왔습니다.', credibility: 12, comment: '기록은 나쁘지 않았다고 합니다.' },
  { excuse: '길고양이가 제 신발 위에서 잠들어서 깨울 수가 없었습니다.', credibility: 20, comment: '고양이라면 이해합니다.' },
  { excuse: '평행우주의 제가 대신 출근한 줄 알았습니다.', credibility: 2, comment: '그 우주에서도 지각했을 겁니다.' },
  { excuse: '시간여행자가 제 시계를 빌려 가서 아직 안 돌려줬습니다.', credibility: 1, comment: '돌려받으면 알려주세요.' },
];

// 직전 핑계와 겹치지 않는 핑계를 하나 고른다 (F4).
export function getMockExcuse(previous?: string): Excuse {
  const pool = mockExcuses.filter((e) => e.excuse !== previous);
  return pool[Math.floor(Math.random() * pool.length)];
}
