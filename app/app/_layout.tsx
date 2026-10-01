// 앱 전체 내비게이션 레이아웃. expo-router가 app/ 폴더의 파일을 화면으로 등록한다.
// 폰의 라이트/다크 설정에 맞춰 헤더·배경 색을 바꾼다.
import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme } from 'react-native';

import { useTheme } from '@/constants/theme';

export default function RootLayout() {
  const isDark = useColorScheme() === 'dark';
  const c = useTheme();
  const base = isDark ? DarkTheme : DefaultTheme;
  const navTheme = {
    ...base,
    colors: { ...base.colors, background: c.background, card: c.background, text: c.text, border: c.border, primary: c.text },
  };

  return (
    <ThemeProvider value={navTheme}>
      <StatusBar style="auto" />
      <Stack>
        <Stack.Screen name="index" options={{ title: '핑계 생성기' }} />
        <Stack.Screen name="result" options={{ title: '결과' }} />
        <Stack.Screen name="history" options={{ title: '기록' }} />
      </Stack>
    </ThemeProvider>
  );
}
