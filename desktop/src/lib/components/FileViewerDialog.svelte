<script lang="ts">
  import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import FilePreviewContent from "$lib/components/FilePreviewContent.svelte";

  let {
    open = $bindable(false),
    file = "",
    lines = [],
    line_number = null,
    loading = false,
    error = "",
    wrap = $bindable(true),
  }: {
    open?: boolean;
    file?: string;
    lines?: string[];
    line_number?: number | null;
    loading?: boolean;
    error?: string;
    wrap?: boolean;
  } = $props();
</script>

<Dialog bind:open>
  <DialogContent class="w-[95vw] sm:w-[92vw] md:w-[90vw] lg:w-[88vw] xl:w-[85vw] max-w-[95vw] sm:max-w-[92vw] md:max-w-[90vw] lg:max-w-[88vw] xl:max-w-[85vw] 2xl:max-w-[80vw]" dir="rtl">
    <DialogHeader class="gap-2 text-start">
      <DialogTitle>{file}</DialogTitle>
      {#if line_number}
        <p class="text-sm text-muted-foreground">سطر {line_number}</p>
      {/if}
    </DialogHeader>
    <div class="max-h-[90vh] rounded border overflow-hidden">
      <FilePreviewContent
        lines={lines}
        {line_number}
        {loading}
        {error}
        bind:wrap
        font_px={13}
        show_copy_line={false}
      />
    </div>
    <DialogFooter class="justify-end">
      <Button variant="outline" onclick={() => (open = false)}>إغلاق</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
