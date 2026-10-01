// 앱 색상 토큰(라이트/다크). 화면에서는 useTheme()으로 현재 모드의 색을 받아 쓴다.
import { useColorScheme } from 'react-native';

const light = {
  background: '#FAFAFA',
  card: '#FFFFFF',
  border: '#E4E4E7',
  text: '#18181B',
  subtext: '#71717A',
  primary: '#18181B', // 주 버튼·선택된 칩
  onPrimary: '#FAFAFA',
  disabled: '#E4E4E7',
  onDisabled: '#A1A1AA',
  track: '#E4E4E7', // 게이지·슬라이더 바탕
  good: '#10B981',
  warn: '#F59E0B',
  bad: '#EF4444',
  toast: '#27272A',
  onToast: '#FAFAFA',
};

const dark: typeof light = {
  background: '#09090B',
  card: '#18181B',
  border: '#27272A',
  text: '#FAFAFA',
  subtext: '#A1A1AA',
  primary: '#FAFAFA',
  onPrimary: '#18181B',
  disabled: '#27272A',
  onDisabled: '#71717A',
  track: '#27272A',
  good: '#34D399',
  warn: '#FBBF24',
  bad: '#F87171',
  toast: '#E4E4E7',
  onToast: '#18181B',
};

export type Theme = typeof light;

export function useTheme(): Theme {
  return useColorScheme() === 'dark' ? dark : light;
}
