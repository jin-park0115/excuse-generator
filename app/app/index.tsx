// 홈 화면. 상황(F1)과 황당함 레벨(F2)을 고르고 "핑계 만들기"로 결과 화면에 간다.
import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

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
  const [selected, setSelected] = useState<string | null>(null);
  const [customText, setCustomText] = useState('');
  const [absurdity, setAbsurdity] = useState(5);

  // 직접 입력이면 입력값(1~50자), 아니면 고른 칩이 상황이 된다
  const situation = selected === CUSTOM ? customText.trim() : selected;
  const canSubmit = !!situation && situation.length <= 50;

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.section}>어떤 상황인가요?</Text>
      <View style={styles.chips}>
        {[...SITUATIONS, CUSTOM].map((s) => (
          <Pressable
            key={s}
            onPress={() => setSelected(s)}
            style={[styles.chip, selected === s && styles.chipOn]}
            accessibilityRole="button"
            accessibilityLabel={`상황: ${s}`}
            accessibilityState={{ selected: selected === s }}
          >
            <Text style={selected === s && styles.chipTextOn}>{s}</Text>
          </Pressable>
        ))}
      </View>
      {selected === CUSTOM && (
        <TextInput
          style={styles.input}
          value={customText}
          onChangeText={setCustomText}
          maxLength={50}
          placeholder="상황을 입력하세요 (최대 50자)"
          accessibilityLabel="상황 직접 입력"
        />
      )}

      <Text style={styles.section}>황당함 레벨</Text>
      <Text style={styles.level}>
        {LEVEL_EMOJIS[absurdity - 1]} {absurdity} · {levelLabel(absurdity)}
      </Text>
      <Slider
        minimumValue={1}
        maximumValue={10}
        step={1}
        value={absurdity}
        onValueChange={(v) => setAbsurdity(Math.round(v))}
        accessibilityLabel="황당함 레벨"
      />

      <Pressable
        disabled={!canSubmit}
        onPress={() => router.push({ pathname: '/result', params: { situation: situation ?? '', absurdity } })}
        style={[styles.button, !canSubmit && styles.buttonOff]}
        accessibilityRole="button"
        accessibilityLabel="핑계 만들기"
        accessibilityState={{ disabled: !canSubmit }}
      >
        <Text style={styles.buttonText}>핑계 만들기</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, gap: 12 },
  section: { fontSize: 16, fontWeight: '600', marginTop: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { minHeight: 44, paddingHorizontal: 16, justifyContent: 'center', borderRadius: 22, borderWidth: 1, borderColor: '#ccc' },
  chipOn: { backgroundColor: '#208AEF', borderColor: '#208AEF' },
  chipTextOn: { color: '#fff', fontWeight: '600' },
  input: { minHeight: 44, borderWidth: 1, borderColor: '#ccc', borderRadius: 8, paddingHorizontal: 12 },
  level: { fontSize: 20, textAlign: 'center' },
  button: { minHeight: 52, marginTop: 16, borderRadius: 12, backgroundColor: '#208AEF', alignItems: 'center', justifyContent: 'center' },
  buttonOff: { backgroundColor: '#aaa' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
