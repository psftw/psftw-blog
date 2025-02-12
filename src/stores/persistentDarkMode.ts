import { persistentAtom } from '@nanostores/persistent';

export const persistentTheme = persistentAtom<boolean | null>('theme', null, {
  encode: JSON.stringify,
  decode: JSON.parse
});

export function toggleDarkMode() {
  const newTheme = !persistentTheme.get();
  persistentTheme.set(newTheme);
}

