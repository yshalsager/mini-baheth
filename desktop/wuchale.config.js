// @ts-check
import { defineConfig } from 'wuchale'
import { adapter } from '@wuchale/svelte'

export default defineConfig({
  sourceLocale: 'ar',
  otherLocales: ['en'],
  adapters: {
    main: adapter({
      files: {
        include: ['src/routes/**/*.svelte', 'src/lib/components/**/*.svelte'],
        ignore: ['src/lib/components/ui/**/*', 'src/lib/hooks/**/*'],
      },
    }),
  },
})
