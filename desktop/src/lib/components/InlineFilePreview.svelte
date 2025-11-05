<script lang='ts'>
  import { ScrollArea } from '$lib/components/ui/scroll-area'
  import { Button } from '$lib/components/ui/button'

  let { file = '', lines = [], line_number = null, loading = false, error = '', wrap = $bindable(true), font_px = $bindable(13) }: {
    file?: string
    lines?: string[]
    line_number?: number | null
    loading?: boolean
    error?: string
    wrap?: boolean
    font_px?: number
  } = $props()

  function center_on_mount(node: HTMLElement) {
    requestAnimationFrame(() => node.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' }))
  }

  function inc_font(delta: number) {
    font_px = Math.max(11, Math.min(20, font_px + delta))
  }
  async function copy_all() {
    try {
      await navigator.clipboard?.writeText(lines.join('\n'))
    } catch {}
  }

  const pre_class = $derived(wrap ? 'whitespace-pre-wrap' : 'whitespace-pre')
</script>

<div class='flex h-full flex-col gap-2'>
  <div class='flex items-center justify-between'>
    <div class='min-w-0'>
      <h3 class='truncate text-sm font-medium' dir='ltr'>{file}</h3>
      {#if line_number}
        <p class='text-xs text-muted-foreground'>سطر {line_number}</p>
      {/if}
    </div>
    <div class='flex items-center gap-1'>
      <Button size='icon' variant='outline' onclick={() => inc_font(-1)} title='تصغير'>−</Button>
      <Button size='icon' variant='outline' onclick={() => inc_font(+1)} title='تكبير'>+</Button>
      <Button size='sm' variant='outline' onclick={() => (wrap = !wrap)} title='التفاف'>{wrap ? 'التفاف' : 'سطر واحد'}</Button>
      <Button size='sm' variant='outline' onclick={copy_all} title='نسخ الكل'>نسخ</Button>
    </div>
  </div>

  <div class='min-h-0 flex-1 rounded border'>
    {#key file}
      <ScrollArea orientation='both' class='h-full'>
        <div class='space-y-1 p-3' dir='auto' style={`font-size:${font_px}px`}>
          {#if loading}
            <p class='text-sm text-muted-foreground'>جارٍ تحميل الملف...</p>
          {:else if error}
            <p class='text-sm text-destructive'>{error}</p>
          {:else if !lines.length}
            <p class='text-sm text-muted-foreground'>لا يوجد محتوى للعرض.</p>
          {:else}
            {#each lines as line, index (index)}
              <div class='flex items-start gap-3'>
                <span class='w-10 select-none text-right font-mono text-xs text-muted-foreground'>{index + 1}</span>
                {#if line_number === index + 1}
                  <span {@attach center_on_mount} aria-current='true' class={'flex-1 rounded bg-yellow-100 dark:bg-yellow-700 dark:text-yellow-50 px-2 py-1 ' + pre_class}>
                    {line}
                  </span>
                {:else}
                  <span class={'flex-1 rounded px-2 py-1 ' + pre_class}>{line}</span>
                {/if}
              </div>
            {/each}
          {/if}
        </div>
      </ScrollArea>
    {/key}
  </div>
</div>
