// @ts-check
import { defineConfig } from 'wuchale'
import { adapter } from '@wuchale/svelte'

export default defineConfig({
  locales: ['ar', 'en'],
  adapters: {
    main: adapter({
      sourceLocale: 'ar',
      files: {
        include: ['src/routes/**/*.svelte', 'src/lib/components/**/*.svelte'],
        ignore: ['src/lib/components/ui/**/*', 'src/lib/hooks/**/*'],
      },
    }),
  },
})
