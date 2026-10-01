// 결과 화면. 서버에서 핑계를 받아 신뢰도 게이지(F7)와 함께 보여주고, 다시 뽑기(F4)·복사·공유(F5)·즐겨찾기(F9)를 한다.
// 생성된 핑계는 기록(F8)에 자동 저장된다.
import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, Share, StyleSheet, Text, View } from 'react-native';

import CredibilityGauge from '@/components/CredibilityGauge';
import { useTheme } from '@/constants/theme';
import { ApiError, fetchExcuse, isAwake, wakeServer, type Tone } from '@/lib/api';
import { addHistory, toggleFavorite, type SavedExcuse } from '@/lib/storage';

const LOADING_TEXTS = ['변명을 숙성하는 중…', '알리바이를 짜맞추는 중…', '그럴듯함을 계산하는 중…', '핑계 장인을 깨우는 중…'];
const WAKING_TEXT = '서버를 깨우는 중이에요… (최대 1분)';

export default function ResultScreen() {
  const c = useTheme();
  const { situation, absurdity, tone } = useLocalSearchParams<{ situation: string; absurdity: string; tone: Tone }>();
  const [excuse, setExcuse] = useState<SavedExcuse | null>(null);
  const [favorite, setFavorite] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingText, setLoadingText] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = async (previous: string | null) => {
    setError(null);
    try {
      // 무료 서버가 잠들어 있으면 먼저 깨운다 (약 1분). 깨어 있으면 바로 넘어간다
      if (!isAwake()) {
        setLoadingText(WAKING_TEXT);
        await wakeServer();
      }
      setLoadingText(LOADING_TEXTS[Math.floor(Math.random() * LOADING_TEXTS.length)]);
      const res = await fetchExcuse({ situation, absurdity: Number(absurdity), tone, previous_excuse: previous });
      const saved: SavedExcuse = {
        ...res,
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        situation,
        absurdity: Number(absurdity),
        tone,
        createdAt: Date.now(),
      };
      setExcuse(saved);
      setFavorite(false);
      await addHistory(saved);
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

  const copy = async (doneMessage = '복사했어요!') => {
    if (!excuse) return;
    try {
      await Clipboard.setStringAsync(excuse.excuse);
      setToast(doneMessage);
    } catch {
      setToast('복사하지 못했어요'); // 웹에서 클립보드 권한이 없을 때 등
    }
  };

  // 웹 브라우저 중 공유 시트(navigator.share)가 없는 곳(대부분의 PC 브라우저)은 복사로 대신한다
  const share = async () => {
    if (!excuse) return;
    if (Platform.OS === 'web' && typeof navigator !== 'undefined' && !('share' in navigator)) {
      await copy('공유 대신 복사했어요. 원하는 곳에 붙여넣어 주세요');
      return;
    }
    try {
      await Share.share({ message: excuse.excuse });
    } catch {
      // 사용자가 공유 창을 닫은 경우 등은 무시한다
    }
  };

  const loading = loadingText !== null;
  const canUse = !loading && !error && excuse !== null;

  return (
    <View style={styles.container}>
      <Text style={[styles.meta, { color: c.subtext }]}>
        {situation} · 황당함 {absurdity} · {tone}
      </Text>
      <View style={[styles.card, { backgroundColor: c.card, borderColor: c.border }]}>
        {loading ? (
          <View style={styles.loading}>
            <ActivityIndicator color={c.subtext} />
            <Text style={[styles.loadingText, { color: c.subtext }]}>{loadingText}</Text>
          </View>
        ) : error ? (
          <Text style={[styles.error, { color: c.bad }]}>{error}</Text>
        ) : (
          <>
            <Text style={[styles.excuse, { color: c.text }]}>{excuse?.excuse}</Text>
            {canUse && (
              <View style={[styles.divider, { borderColor: c.border }]}>
                <CredibilityGauge credibility={excuse.credibility} comment={excuse.comment} />
              </View>
            )}
          </>
        )}
      </View>

      {/* 에러 후 다시 뽑기는 마지막으로 성공한 핑계를 previous_excuse로 보낸다 */}
      <ActionButton primary label="다시 뽑기" disabled={loading} onPress={() => load(excuse?.excuse ?? null)} />
      <View style={styles.row}>
        <ActionButton label="복사" disabled={!canUse} onPress={() => copy()} />
        <ActionButton label="공유" disabled={!canUse} onPress={share} />
        <ActionButton
          label={favorite ? '★ 저장됨' : '☆ 즐겨찾기'}
          accessibilityLabel={favorite ? '즐겨찾기 해제' : '즐겨찾기'}
          disabled={!canUse}
          onPress={async () => excuse && setFavorite(await toggleFavorite(excuse))}
        />
      </View>

      {toast && <Text style={[styles.toast, { backgroundColor: c.toast, color: c.onToast }]}>{toast}</Text>}
    </View>
  );
}

type ActionButtonProps = { label: string; accessibilityLabel?: string; primary?: boolean; disabled: boolean; onPress: () => void };

// primary는 꽉 찬 주 버튼, 나머지는 테두리만 있는 보조 버튼
function ActionButton({ label, accessibilityLabel, primary, disabled, onPress }: ActionButtonProps) {
  const c = useTheme();
  const bg = primary ? (disabled ? c.disabled : c.primary) : c.card;
  const fg = disabled ? c.onDisabled : primary ? c.onPrimary : c.text;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={[styles.button, !primary && styles.secondary, { backgroundColor: bg, borderColor: c.border }]}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled }}
    >
      <Text style={[styles.buttonText, { color: fg }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 12 },
  meta: { fontSize: 13, textAlign: 'center' },
  card: { padding: 20, borderRadius: 20, borderWidth: 1, minHeight: 140, justifyContent: 'center', gap: 16 },
  excuse: { fontSize: 17, lineHeight: 26 },
  divider: { borderTopWidth: 1, paddingTop: 16 },
  loading: { alignItems: 'center', gap: 12 },
  loadingText: { fontSize: 15 },
  error: { fontSize: 16, lineHeight: 24, textAlign: 'center' },
  row: { flexDirection: 'row', gap: 8 },
  button: { minHeight: 48, borderRadius: 14, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  secondary: { flex: 1, borderWidth: 1 },
  buttonText: { fontSize: 15, fontWeight: '600' },
  toast: { alignSelf: 'center', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, overflow: 'hidden' },
});
