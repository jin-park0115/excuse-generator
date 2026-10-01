// 기록 화면. 최근 생성 20개(F8)와 즐겨찾기(F9) 탭, 항목을 누르면 전체 보기, 왼쪽으로 밀면 삭제.
import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState, type ReactNode } from 'react';
import { Animated, FlatList, PanResponder, Pressable, StyleSheet, Text, View } from 'react-native';

import Chip from '@/components/Chip';
import CredibilityGauge from '@/components/CredibilityGauge';
import { getFavorites, getHistory, removeFavorite, removeHistory, type SavedExcuse } from '@/lib/storage';

type Tab = 'history' | 'favorites';

export default function HistoryScreen() {
  const [tab, setTab] = useState<Tab>('history');
  const [items, setItems] = useState<SavedExcuse[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setItems(await (tab === 'history' ? getHistory() : getFavorites()));
  }, [tab]);

  // 화면에 들어올 때마다(결과 화면에서 돌아올 때 포함) 다시 읽는다
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const remove = async (id: string) => {
    await (tab === 'history' ? removeHistory(id) : removeFavorite(id));
    await load();
  };

  return (
    <View style={styles.container}>
      <View style={styles.tabs}>
        <Chip label="최근 기록" selected={tab === 'history'} onPress={() => setTab('history')} />
        <Chip label="즐겨찾기" selected={tab === 'favorites'} onPress={() => setTab('favorites')} />
      </View>

      <FlatList
        key={tab} // 탭이 바뀌면 행을 새로 만든다 (같은 핑계가 두 탭에 다 있을 수 있음)
        data={items}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>{tab === 'history' ? '아직 만든 핑계가 없어요' : '별표한 핑계가 없어요'}</Text>
        }
        ListFooterComponent={items.length > 0 ? <Text style={styles.hint}>왼쪽으로 밀어서 삭제</Text> : null}
        renderItem={({ item }) => {
          const open = openId === item.id;
          return (
            <SwipeToDelete onDelete={() => remove(item.id)}>
              <Pressable
                onPress={() => setOpenId(open ? null : item.id)}
                style={styles.item}
                accessibilityRole="button"
                accessibilityHint={open ? '접기' : '전체 보기'}
              >
                <Text style={styles.meta}>
                  {item.situation} · 황당함 {item.absurdity} · {item.tone}
                </Text>
                <Text style={styles.excuse} numberOfLines={open ? undefined : 2}>
                  {item.excuse}
                </Text>
                {open && <CredibilityGauge credibility={item.credibility} comment={item.comment} />}
              </Pressable>
            </SwipeToDelete>
          );
        }}
      />
    </View>
  );
}

const DELETE_THRESHOLD = -120;

// 왼쪽으로 일정 거리 이상 밀면 onDelete를 부른다. 스크린리더 사용자는 "삭제" 동작으로 지울 수 있다.
function SwipeToDelete({ onDelete, children }: { onDelete: () => void; children: ReactNode }) {
  const x = useRef(new Animated.Value(0)).current;
  const pan = useRef(
    PanResponder.create({
      // 가로로 확실히 움직일 때만 잡는다 (세로 스크롤 방해 안 함)
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 10 && Math.abs(g.dx) > Math.abs(g.dy) * 2,
      onPanResponderMove: (_, g) => x.setValue(Math.min(0, g.dx)),
      onPanResponderRelease: (_, g) => {
        if (g.dx < DELETE_THRESHOLD) {
          Animated.timing(x, { toValue: -600, duration: 150, useNativeDriver: true }).start(onDelete);
        } else {
          Animated.spring(x, { toValue: 0, useNativeDriver: true }).start();
        }
      },
      onPanResponderTerminate: () => Animated.spring(x, { toValue: 0, useNativeDriver: true }).start(),
    }),
  ).current;

  return (
    <View
      style={styles.swipeContainer}
      accessibilityActions={[{ name: 'delete', label: '삭제' }]}
      onAccessibilityAction={(e) => e.nativeEvent.actionName === 'delete' && onDelete()}
    >
      <View style={styles.deleteBg}>
        <Text style={styles.deleteText}>삭제</Text>
      </View>
      <Animated.View style={{ transform: [{ translateX: x }] }} {...pan.panHandlers}>
        {children}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  tabs: { flexDirection: 'row', gap: 8, paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  list: { padding: 20, gap: 12 },
  empty: { textAlign: 'center', color: '#888', marginTop: 40 },
  hint: { textAlign: 'center', color: '#aaa', fontSize: 12, marginTop: 8 },
  swipeContainer: { borderRadius: 12, overflow: 'hidden' },
  deleteBg: { ...StyleSheet.absoluteFill, backgroundColor: '#E74C3C', alignItems: 'flex-end', justifyContent: 'center', paddingRight: 20 },
  deleteText: { color: '#fff', fontWeight: 'bold' },
  item: { padding: 16, gap: 8, backgroundColor: '#F2F7FE', minHeight: 44 },
  meta: { fontSize: 12, color: '#888' },
  excuse: { fontSize: 16, lineHeight: 24 },
});
