// 홈 화면. 상황(F1)·황당함 레벨(F2)·말투(F6)를 고르고 "핑계 만들기"로 결과 화면에 간다. 우상단 아이콘은 기록 화면.
import Slider from '@react-native-community/slider';
import { router, Stack } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import Chip from '@/components/Chip';
import { useTheme } from '@/constants/theme';
import { TONES, type Tone } from '@/lib/api';

const SITUATIONS = ['지각', '약속 취소', '과제 미제출', '연락 늦게 봄', '모임 불참', '운동 빠짐'];
const CUSTOM = '직접 입력';
const LEVEL_EMOJIS = ['🙂', '😐', '😅', '🤔', '😏', '🫣', '😵', '🤯', '🙀', '🪐'];

function levelLabel(level: number): string {
  if (level <= 3) return '현실적';
  if (level <= 6) return '수상함';
  if (level <= 9) return '황당';
  return '우주적';
}

export default function HomeScreen() {
  const c = useTheme();
  const [selected, setSelected] = useState<string | null>(null);
  const [customText, setCustomText] = useState('');
  const [absurdity, setAbsurdity] = useState(5);
  const [tone, setTone] = useState<Tone>(TONES[0]);

  // 직접 입력이면 입력값(1~50자), 아니면 고른 칩이 상황이 된다
  const situation = selected === CUSTOM ? customText.trim() : selected;
  const canSubmit = !!situation && situation.length <= 50;

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Stack.Screen
        options={{
          headerRight: () => (
            <Pressable onPress={() => router.push('/history')} style={styles.headerIcon} accessibilityRole="button" accessibilityLabel="기록 보기">
              <Text style={styles.headerIconText}>🕘</Text>
            </Pressable>
          ),
        }}
      />
      <Text style={[styles.section, { color: c.text }]}>어떤 상황인가요?</Text>
      <View style={styles.chips}>
        {[...SITUATIONS, CUSTOM].map((s) => (
          <Chip key={s} label={s} selected={selected === s} onPress={() => setSelected(s)} accessibilityLabel={`상황: ${s}`} />
        ))}
      </View>
      {selected === CUSTOM && (
        <TextInput
          style={[styles.input, { borderColor: c.border, backgroundColor: c.card, color: c.text }]}
          value={customText}
          onChangeText={setCustomText}
          maxLength={50}
          placeholder="상황을 입력하세요 (최대 50자)"
          placeholderTextColor={c.subtext}
          accessibilityLabel="상황 직접 입력"
        />
      )}

      <Text style={[styles.section, { color: c.text }]}>황당함 레벨</Text>
      <Text style={[styles.level, { color: c.text }]}>
        {LEVEL_EMOJIS[absurdity - 1]} {absurdity} · {levelLabel(absurdity)}
      </Text>
      <Slider
        minimumValue={1}
        maximumValue={10}
        step={1}
        value={absurdity}
        onValueChange={(v) => setAbsurdity(Math.round(v))}
        minimumTrackTintColor={c.primary}
        maximumTrackTintColor={c.track}
        thumbTintColor={c.primary}
        accessibilityLabel="황당함 레벨"
      />

      <Text style={[styles.section, { color: c.text }]}>말투</Text>
      <View style={styles.chips}>
        {TONES.map((t) => (
          <Chip key={t} label={t} selected={tone === t} onPress={() => setTone(t)} accessibilityLabel={`말투: ${t}`} />
        ))}
      </View>

      <Pressable
        disabled={!canSubmit}
        onPress={() => router.push({ pathname: '/result', params: { situation: situation ?? '', absurdity, tone } })}
        style={[styles.button, { backgroundColor: canSubmit ? c.primary : c.disabled }]}
        accessibilityRole="button"
        accessibilityLabel="핑계 만들기"
        accessibilityState={{ disabled: !canSubmit }}
      >
        <Text style={[styles.buttonText, { color: canSubmit ? c.onPrimary : c.onDisabled }]}>핑계 만들기</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 12 },
  section: { fontSize: 15, fontWeight: '600', marginTop: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  headerIcon: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  headerIconText: { fontSize: 22 },
  input: { minHeight: 44, borderWidth: 1, borderRadius: 12, paddingHorizontal: 12 },
  level: { fontSize: 18, textAlign: 'center' },
  button: { minHeight: 52, marginTop: 16, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  buttonText: { fontSize: 17, fontWeight: '700' },
});
