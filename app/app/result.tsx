// 결과 화면. 서버에서 핑계를 받아 보여주고 다시 뽑기(F4), 복사·공유(F5)를 한다.
import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, Share, StyleSheet, Text, View } from 'react-native';

import { ApiError, fetchExcuse, type Excuse } from '@/lib/api';

const LOADING_TEXTS = ['변명을 숙성하는 중…', '알리바이를 짜맞추는 중…', '그럴듯함을 계산하는 중…', '핑계 장인을 깨우는 중…'];

export default function ResultScreen() {
  const { situation, absurdity } = useLocalSearchParams<{ situation: string; absurdity: string }>();
  const [excuse, setExcuse] = useState<Excuse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingText, setLoadingText] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = async (previous: string | null) => {
    setLoadingText(LOADING_TEXTS[Math.floor(Math.random() * LOADING_TEXTS.length)]);
    setError(null);
    try {
      setExcuse(await fetchExcuse({ situation, absurdity: Number(absurdity), previous_excuse: previous }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : '핑계 공장이 잠깐 멈췄어요');
    } finally {
      setLoadingText(null);
    }
  };

  // 화면에 들어오면 바로 한 번 생성한다
  useEffect(() => {
    load(null);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 토스트는 1.5초 뒤 사라진다
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 1500);
    return () => clearTimeout(t);
  }, [toast]);

  const copy = async () => {
    if (!excuse) return;
    await Clipboard.setStringAsync(excuse.excuse);
    setToast('복사했어요!');
  };

  const loading = loadingText !== null;
  const canUse = !loading && !error && excuse !== null;

  return (
    <View style={styles.container}>
      <Text style={styles.meta}>
        {situation} · 황당함 {absurdity}
      </Text>
      <View style={styles.card}>
        {loading ? (
          <View style={styles.loading}>
            <ActivityIndicator />
            <Text style={styles.loadingText}>{loadingText}</Text>
          </View>
        ) : error ? (
          <Text style={styles.error}>{error}</Text>
        ) : (
          <Text style={styles.excuse}>{excuse?.excuse}</Text>
        )}
      </View>

      <View style={styles.row}>
        {/* 에러 후 다시 뽑기는 마지막으로 성공한 핑계를 previous_excuse로 보낸다 */}
        <ActionButton label="다시 뽑기" disabled={loading} onPress={() => load(excuse?.excuse ?? null)} />
        <ActionButton label="복사" disabled={!canUse} onPress={copy} />
        <ActionButton label="공유" disabled={!canUse} onPress={() => excuse && Share.share({ message: excuse.excuse })} />
      </View>

      {toast && <Text style={styles.toast}>{toast}</Text>}
    </View>
  );
}

function ActionButton({ label, disabled, onPress }: { label: string; disabled: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={[styles.button, disabled && styles.buttonOff]}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 16 },
  meta: { fontSize: 14, color: '#888', textAlign: 'center' },
  card: { padding: 24, borderRadius: 16, backgroundColor: '#F2F7FE', minHeight: 140, justifyContent: 'center' },
  excuse: { fontSize: 20, lineHeight: 30 },
  loading: { alignItems: 'center', gap: 12 },
  loadingText: { fontSize: 16, color: '#555' },
  error: { fontSize: 18, lineHeight: 28, color: '#C0392B', textAlign: 'center' },
  row: { flexDirection: 'row', gap: 8 },
  button: { flex: 1, minHeight: 48, borderRadius: 12, backgroundColor: '#208AEF', alignItems: 'center', justifyContent: 'center' },
  buttonOff: { backgroundColor: '#aaa' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  toast: { alignSelf: 'center', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#333', color: '#fff', overflow: 'hidden' },
});
