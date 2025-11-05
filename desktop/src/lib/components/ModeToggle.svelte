<script lang='ts'>
  import { Button } from '$lib/components/ui/button'
  import Sun from '@lucide/svelte/icons/sun'
  import Moon from '@lucide/svelte/icons/moon'
  import Monitor from '@lucide/svelte/icons/monitor'
  import { mode } from 'mode-watcher'

  const order = ['light', 'dark', 'system'] as const
  function next(val: string) {
    const i = order.indexOf((val as any) ?? 'system')
    return order[(i + 1) % order.length]
  }

  function toggle() {
    // @ts-ignore - mode store accepts 'light' | 'dark' | 'system'
    mode.set(next(mode.current as any) as any)
  }

  const label = $derived(mode.current === 'dark' ? 'الوضع الداكن' : mode.current === 'light' ? 'الوضع الفاتح' : 'مطابق للنظام')
</script>

<Button variant='outline' size='sm' onclick={toggle} title={label} aria-label={label} class='inline-flex items-center gap-2'>
  {#if mode.current === 'dark'}
    <Moon class='size-4' />
  {:else if mode.current === 'light'}
    <Sun class='size-4' />
  {:else}
    <Monitor class='size-4' />
  {/if}
  <span class='hidden sm:inline'>{label}</span>
</Button>

