// 기록 화면. 최근 생성 20개(F8)와 즐겨찾기(F9) 탭, 항목을 누르면 전체 보기, 왼쪽으로 밀면 삭제(웹은 ✕ 버튼).
import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState, type ReactNode } from 'react';
import { Animated, FlatList, PanResponder, Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import Chip from '@/components/Chip';
import CredibilityGauge from '@/components/CredibilityGauge';
import { useTheme } from '@/constants/theme';
import { getFavorites, getHistory, removeFavorite, removeHistory, type SavedExcuse } from '@/lib/storage';

type Tab = 'history' | 'favorites';

export default function HistoryScreen() {
  const c = useTheme();
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
          <Text style={[styles.empty, { color: c.subtext }]}>{tab === 'history' ? '아직 만든 핑계가 없어요' : '별표한 핑계가 없어요'}</Text>
        }
        ListFooterComponent={items.length > 0 ? <Text style={[styles.hint, { color: c.subtext }]}>{Platform.OS === 'web' ? '오른쪽 위 ✕로 삭제' : '왼쪽으로 밀어서 삭제'}</Text> : null}
        renderItem={({ item }) => {
          const open = openId === item.id;
          return (
            <SwipeToDelete onDelete={() => remove(item.id)}>
              <Pressable
                onPress={() => setOpenId(open ? null : item.id)}
                style={[styles.item, { backgroundColor: c.card, borderColor: c.border }]}
                accessibilityRole="button"
                accessibilityHint={open ? '접기' : '전체 보기'}
              >
                <Text style={[styles.meta, { color: c.subtext }]}>
                  {item.situation} · 황당함 {item.absurdity} · {item.tone}
                </Text>
                <Text style={[styles.excuse, { color: c.text }]} numberOfLines={open ? undefined : 2}>
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
  const c = useTheme();
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

  // 웹(특히 PC 마우스)은 밀어서 지우기가 어색해서 삭제 버튼을 따로 보여준다
  if (Platform.OS === 'web') {
    return (
      <View style={styles.swipeContainer}>
        {children}
        <Pressable onPress={onDelete} style={styles.webDelete} accessibilityRole="button" accessibilityLabel="삭제">
          <Text style={{ color: c.subtext, fontSize: 16 }}>✕</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View
      style={styles.swipeContainer}
      accessibilityActions={[{ name: 'delete', label: '삭제' }]}
      onAccessibilityAction={(e) => e.nativeEvent.actionName === 'delete' && onDelete()}
    >
      <View style={[styles.deleteBg, { backgroundColor: c.bad }]}>
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
  empty: { textAlign: 'center', marginTop: 40 },
  hint: { textAlign: 'center', fontSize: 12, marginTop: 8 },
  swipeContainer: { borderRadius: 16, overflow: 'hidden' },
  deleteBg: { ...StyleSheet.absoluteFill, alignItems: 'flex-end', justifyContent: 'center', paddingRight: 20 },
  deleteText: { color: '#fff', fontWeight: 'bold' },
  webDelete: { position: 'absolute', top: 0, right: 0, width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  item: { padding: 16, gap: 8, minHeight: 44, borderWidth: 1, borderRadius: 16 },
  meta: { fontSize: 12 },
  excuse: { fontSize: 15, lineHeight: 22 },
});
