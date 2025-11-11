<script lang="ts">
  import { ScrollArea } from "$lib/components/ui/scroll-area"
  import { Button } from "$lib/components/ui/button"
  import { infinite_scroll } from "$lib/attachments"
  import { tick } from "svelte"
  import Copy from "@lucide/svelte/icons/copy"

  let {
    lines = [],
    line_number = null,
    loading = false,
    error = "",
    wrap = $bindable(true),
    font_px = $bindable(13),
    show_copy_line = true,
  }: {
    lines?: string[]
    line_number?: number | null
    loading?: boolean
    error?: string
    wrap?: boolean
    font_px?: number
    show_copy_line?: boolean
  } = $props()

  function center_on_mount(node: HTMLElement) {
    requestAnimationFrame(() => node.scrollIntoView({ block: "center", inline: "nearest", behavior: "smooth" }))
  }

  async function copy_line(text: string) {
    try {
      await navigator.clipboard?.writeText(text)
    } catch {}
  }

  const pre_class = $derived(wrap ? "whitespace-pre-wrap" : "whitespace-pre")

  let viewport_ref: HTMLElement | null = $state(null)
  const total = $derived(lines.length)

  const CHUNK = 500
  const WINDOW = 500
  const MAX_WINDOW = 2000
  let suppress_load = $state(false)
  let start_index = $state(0)
  let end_index = $state(0)

  $effect(() => {
    if (loading || error) {
      start_index = 0
      end_index = 0
      return
    }
    if (!total) {
      start_index = 0
      end_index = 0
      return
    }

    if (line_number && line_number > 0 && line_number <= total) {
      const target = line_number - 1
      const context = Math.floor(WINDOW / 2)
      start_index = Math.max(0, target - context)
      end_index = Math.min(total, start_index + WINDOW)
      suppress_load = true
      setTimeout(() => (suppress_load = false), 250)
    } else {
      start_index = 0
      end_index = Math.min(total, WINDOW)
    }
  })

  const visible = $derived(lines.slice(start_index, end_index))
  const has_more_top = $derived(start_index > 0)
  const has_more_bottom = $derived(end_index < total)

  async function load_more() {
    if (suppress_load) return
    if (!has_more_bottom) return
    const view = viewport_ref
    end_index = Math.min(total, end_index + CHUNK)
    await tick()
    const overflow = end_index - start_index - MAX_WINDOW
    if (overflow > 0) {
      const before = view?.scrollHeight ?? 0
      start_index = start_index + overflow
      await tick()
      const after = view?.scrollHeight ?? 0
      if (view) view.scrollTop = (view.scrollTop ?? 0) - (before - after)
    }
  }

  async function load_prev() {
    if (suppress_load) return
    if (!has_more_top) return
    const view = viewport_ref
    const prev_height = view?.scrollHeight ?? 0
    const prev_top = view?.scrollTop ?? 0
    start_index = Math.max(0, start_index - CHUNK)
    await tick()
    const next_height = view?.scrollHeight ?? 0
    if (view) view.scrollTop = prev_top + (next_height - prev_height)
    const overflow = end_index - start_index - MAX_WINDOW
    if (overflow > 0) {
      end_index = end_index - overflow
      await tick()
    }
  }
</script>

<ScrollArea orientation="both" class="h-full" bind:viewportRef={viewport_ref}>
    <div class="space-y-1 p-3" dir="auto" style={`font-size:${font_px}px`}>
      {#if loading}
        <p class="text-sm text-muted-foreground">جارٍ تحميل الملف...</p>
      {:else if error}
        <p class="text-sm text-destructive">{error}</p>
      {:else if !total}
        <p class="text-sm text-muted-foreground">لا يوجد محتوى للعرض.</p>
      {:else}
        {#if has_more_top}
          <div class="h-4" {@attach infinite_scroll(load_prev)}></div>
        {/if}

        {#each visible as line, i (start_index + i)}
          {@const display_no = start_index + i + 1}
          <div class="flex items-start gap-3">
            <span class="w-10 select-none text-end font-mono text-xs text-muted-foreground">{display_no}</span>
            {#if line_number === display_no}
              <span
                {@attach center_on_mount}
                aria-current="true"
                class={"flex-1 rounded bg-yellow-100 dark:bg-yellow-700 dark:text-yellow-50 px-2 py-1 " + pre_class}
              >
                {line}
              </span>
            {:else}
              <span class={"flex-1 rounded px-2 py-1 " + pre_class}>{line}</span>
            {/if}
            {#if show_copy_line}
              <Button
                size="icon"
                variant="ghost"
                title="نسخ السطر"
                aria-label="نسخ السطر"
                onclick={() => copy_line(line)}
              >
                <Copy class="size-4" />
              </Button>
            {/if}
          </div>
        {/each}

        {#if has_more_bottom}
          <div class="h-4" {@attach infinite_scroll(load_more)}></div>
        {/if}
      {/if}
    </div>
  </ScrollArea>
