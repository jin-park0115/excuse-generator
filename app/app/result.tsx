// 결과 화면. 핑계를 보여주고 다시 뽑기(F4), 복사·공유(F5)를 한다. M2에서는 mock 데이터를 쓴다.
import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, Share, StyleSheet, Text, View } from 'react-native';

import { getMockExcuse } from '@/mocks/mockExcuses';

export default function ResultScreen() {
  const { situation, absurdity } = useLocalSearchParams<{ situation: string; absurdity: string }>();
  const [excuse, setExcuse] = useState(() => getMockExcuse());
  const [toast, setToast] = useState<string | null>(null);

  // 토스트는 1.5초 뒤 사라진다
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 1500);
    return () => clearTimeout(t);
  }, [toast]);

  const copy = async () => {
    await Clipboard.setStringAsync(excuse.excuse);
    setToast('복사했어요!');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.meta}>
        {situation} · 황당함 {absurdity}
      </Text>
      <View style={styles.card}>
        <Text style={styles.excuse}>{excuse.excuse}</Text>
      </View>

      <View style={styles.row}>
        <ActionButton label="다시 뽑기" onPress={() => setExcuse(getMockExcuse(excuse.excuse))} />
        <ActionButton label="복사" onPress={copy} />
        <ActionButton label="공유" onPress={() => Share.share({ message: excuse.excuse })} />
      </View>

      {toast && <Text style={styles.toast}>{toast}</Text>}
    </View>
  );
}

function ActionButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={styles.button} accessibilityRole="button" accessibilityLabel={label}>
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 16 },
  meta: { fontSize: 14, color: '#888', textAlign: 'center' },
  card: { padding: 24, borderRadius: 16, backgroundColor: '#F2F7FE' },
  excuse: { fontSize: 20, lineHeight: 30 },
  row: { flexDirection: 'row', gap: 8 },
  button: { flex: 1, minHeight: 48, borderRadius: 12, backgroundColor: '#208AEF', alignItems: 'center', justifyContent: 'center' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  toast: { alignSelf: 'center', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#333', color: '#fff', overflow: 'hidden' },
});
