<script lang='ts'>
  import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '$lib/components/ui/dialog'
  import { ScrollArea } from '$lib/components/ui/scroll-area'
  import { Button } from '$lib/components/ui/button'

  let { open = $bindable(false), file = '', lines = [], line_number = null, loading = false, error = '' }: {
    open?: boolean
    file?: string
    lines?: string[]
    line_number?: number | null
    loading?: boolean
    error?: string
  } = $props()

  function center_on_mount(node: HTMLElement) {
    requestAnimationFrame(() => node.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' }))
  }
  
</script>

<Dialog bind:open>
  <DialogContent class='max-w-3xl' dir='rtl'>
    <DialogHeader class='gap-2 text-right'>
      <DialogTitle>{file}</DialogTitle>
      {#if line_number}
        <p class='text-sm text-muted-foreground'>سطر {line_number}</p>
      {/if}
    </DialogHeader>
    <ScrollArea class='max-h-[400px] rounded border'>
      <div class='space-y-1 p-4' dir='auto'>
        {#if loading}
          <p class='text-sm text-muted-foreground'>جارٍ تحميل الملف...</p>
        {:else if error}
          <p class='text-sm text-destructive'>{error}</p>
        {:else}
          {#each lines as line, index (index)}
            <div class='flex items-start gap-3'>
              <span class='w-10 select-none text-right font-mono text-xs text-muted-foreground'>{index + 1}</span>
              {#if line_number === index + 1}
                <span {@attach center_on_mount} aria-current='true' class='flex-1 whitespace-pre-wrap rounded px-2 py-1 bg-yellow-100 dark:bg-yellow-700 dark:text-yellow-50'>{line}</span>
              {:else}
                <span class='flex-1 whitespace-pre-wrap rounded px-2 py-1'>{line}</span>
              {/if}
            </div>
          {/each}
        {/if}
      </div>
    </ScrollArea>
    <DialogFooter class='justify-end'>
      <Button variant='outline' onclick={() => (open = false)}>إغلاق</Button>
    </DialogFooter>
  </DialogContent>
  
</Dialog>
