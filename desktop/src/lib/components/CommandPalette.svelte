<script lang='ts'>
  import { Dialog, DialogContent, DialogHeader, DialogTitle } from '$lib/components/ui/dialog'
  import { Input } from '$lib/components/ui/input'

  type Command = { id: string; label: string; run: () => void }

  let { open = $bindable(false), commands = [] as Command[] }: { open?: boolean; commands?: Command[] } = $props()

  let q = $state('')
  const filtered = $derived(
    !q.trim() ? commands : commands.filter(c => c.label.toLowerCase().includes(q.trim().toLowerCase()))
  )

  function run(cmd: Command) {
    cmd.run()
    open = false
    q = ''
  }
</script>

<Dialog bind:open>
  <DialogContent class='max-w-md' dir='rtl'>
    <DialogHeader class='text-right'>
      <DialogTitle>الأوامر</DialogTitle>
    </DialogHeader>
    <div class='space-y-2'>
      <Input placeholder='ابحث عن أمر...' bind:value={q} autofocus />
      <div class='max-h-64 overflow-auto rounded border'>
        {#if !filtered.length}
          <p class='p-3 text-sm text-muted-foreground'>لا توجد أوامر مطابقة.</p>
        {:else}
          {#each filtered as cmd (cmd.id)}
            <button class='block w-full px-3 py-2 text-right text-sm hover:bg-muted' onclick={() => run(cmd)}>{cmd.label}</button>
          {/each}
        {/if}
      </div>
    </div>
  </DialogContent>
</Dialog>

