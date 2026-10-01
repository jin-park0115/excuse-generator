// 기록(최근 20개)과 즐겨찾기(개수 제한 없음)를 기기의 AsyncStorage에 저장·불러온다 (F8, F9).
// 둘은 따로 저장한다: 기록에서 밀려나거나 지워져도 즐겨찾기는 남는다.
import AsyncStorage from '@react-native-async-storage/async-storage';

import type { Excuse, Tone } from '@/lib/api';

export type SavedExcuse = Excuse & {
  id: string;
  situation: string;
  absurdity: number;
  tone: Tone;
  createdAt: number;
};

const HISTORY_KEY = 'history';
const FAVORITES_KEY = 'favorites';
const HISTORY_LIMIT = 20;

async function read(key: string): Promise<SavedExcuse[]> {
  try {
    const raw = await AsyncStorage.getItem(key);
    return raw ? (JSON.parse(raw) as SavedExcuse[]) : [];
  } catch {
    return []; // 저장소가 깨졌거나 읽기 실패해도 앱은 빈 목록으로 계속 동작한다
  }
}

async function write(key: string, items: SavedExcuse[]): Promise<void> {
  try {
    await AsyncStorage.setItem(key, JSON.stringify(items));
  } catch (e) {
    console.warn('저장 실패', e);
  }
}

export const getHistory = () => read(HISTORY_KEY);
export const getFavorites = () => read(FAVORITES_KEY);

// 새 기록을 맨 앞에 넣고, 20개를 넘으면 오래된 것부터 지운다
export async function addHistory(item: SavedExcuse): Promise<void> {
  await write(HISTORY_KEY, [item, ...(await getHistory())].slice(0, HISTORY_LIMIT));
}

export async function removeHistory(id: string): Promise<void> {
  await write(HISTORY_KEY, (await getHistory()).filter((e) => e.id !== id));
}

export async function removeFavorite(id: string): Promise<void> {
  await write(FAVORITES_KEY, (await getFavorites()).filter((e) => e.id !== id));
}

// 즐겨찾기에 없으면 추가, 있으면 뺀다. 바뀐 뒤 즐겨찾기 여부를 돌려준다
export async function toggleFavorite(item: SavedExcuse): Promise<boolean> {
  const favorites = await getFavorites();
  if (favorites.some((e) => e.id === item.id)) {
    await removeFavorite(item.id);
    return false;
  }
  await write(FAVORITES_KEY, [item, ...favorites]);
  return true;
}
