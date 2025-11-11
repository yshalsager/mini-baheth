<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import FilePreviewContent from "$lib/components/FilePreviewContent.svelte";

  let {
    file = "",
    lines = [],
    line_number = null,
    loading = false,
    error = "",
    wrap = $bindable(true),
    font_px = $bindable(13),
  }: {
    file?: string;
    lines?: string[];
    line_number?: number | null;
    loading?: boolean;
    error?: string;
    wrap?: boolean;
    font_px?: number;
  } = $props();

  function inc_font(delta: number) {
    font_px = Math.max(11, Math.min(20, font_px + delta));
  }
  async function copy_all() {
    try {
      await navigator.clipboard?.writeText(lines.join("\n"));
    } catch {}
  }
</script>

<div class="flex h-full flex-col gap-2">
  <div class="flex items-center justify-between">
    <div class="min-w-0">
      <h3 class="truncate text-sm font-medium" dir="ltr">{file}</h3>
      {#if line_number}
        <p class="text-xs text-muted-foreground">سطر {line_number}</p>
      {/if}
    </div>
    <div class="flex items-center gap-1">
      <Button size="icon" variant="outline" onclick={() => inc_font(-1)} title="تصغير">−</Button>
      <Button size="icon" variant="outline" onclick={() => inc_font(+1)} title="تكبير">+</Button>
      <Button size="sm" variant="outline" onclick={() => (wrap = !wrap)} title="التفاف"
        >{wrap ? "التفاف" : "سطر واحد"}</Button
      >
      <Button size="sm" variant="outline" onclick={copy_all} title="نسخ الكل">نسخ</Button>
    </div>
  </div>

  <div class="min-h-0 flex-1 rounded border">
    {#key file}
      <FilePreviewContent
        {lines}
        {line_number}
        {loading}
        {error}
        bind:wrap
        bind:font_px
        show_copy_line={true}
      />
    {/key}
  </div>
</div>
