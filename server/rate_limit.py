# IP별 호출 한도 (PRD 섹션 7: 분당 10회, 일 200회). 메모리에만 저장하므로 서버를 재시작하면 초기화된다.
import time
from collections import defaultdict, deque

MINUTE = 60
DAY = 24 * 60 * 60


# ponytail: 단일 프로세스 메모리 기반. 서버를 여러 대로 늘리면 Redis 같은 공용 저장소가 필요하다
class RateLimiter:
    def __init__(self, per_minute: int = 10, per_day: int = 200) -> None:
        self.per_minute = per_minute
        self.per_day = per_day
        self.hits: dict[str, deque[float]] = defaultdict(deque)  # IP → 최근 24시간 호출 시각(오래된 순)

    def allow(self, key: str, now: float | None = None) -> bool:
        """한도 안이면 호출을 기록하고 True, 넘었으면 기록하지 않고 False."""
        now = time.monotonic() if now is None else now
        q = self.hits[key]
        while q and now - q[0] >= DAY:
            q.popleft()
        if len(q) >= self.per_day:
            return False
        # 최근 1분 호출 수: 뒤(최신)부터 세다가 1분보다 오래된 게 나오면 멈춘다
        recent = 0
        for t in reversed(q):
            if now - t >= MINUTE:
                break
            recent += 1
        if recent >= self.per_minute:
            return False
        q.append(now)
        return True
