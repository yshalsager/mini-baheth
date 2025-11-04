<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Card, CardContent, CardHeader } from "$lib/components/ui/card";
  import LocateFixed from "@lucide/svelte/icons/locate-fixed";
  import type { SearchMatchPayload, Submatch } from "$lib/types";
  import { infinite_scroll } from "$lib/attachments";
  import { RESULTS_PER_PAGE } from "$lib/constants";

  type TextSegment = {
    text: string;
    highlighted: boolean;
  };

  let {
    results = [],
    open_result,
    page_size = RESULTS_PER_PAGE,
  }: {
    results?: SearchMatchPayload[];
    open_result: (path: string, line_number?: number) => void;
    page_size?: number;
  } = $props();

  let render_count = $state(page_size);
  const visible_results = $derived(results.slice(0, render_count));
  const has_more_results = $derived(results.length > render_count);

  function build_segments(result: SearchMatchPayload): TextSegment[] {
    const text = result.lines ?? "";
    const matches = (result.submatches ?? [])
      .map(entry => {
        const payload = entry as Submatch;
        const match_text = typeof payload.match?.text === "string" ? payload.match.text : "";
        const start = typeof payload.start === "number" ? payload.start : undefined;
        const end = typeof payload.end === "number" ? payload.end : undefined;
        return { start, end, text: match_text };
      })
      .filter(item => item.text.length > 0)
      .sort((a, b) => (a.start ?? 0) - (b.start ?? 0));

    if (!matches.length) return text ? [{ text, highlighted: false }] : [];

    const segments: TextSegment[] = [];
    let cursor = 0;
    for (const match of matches) {
      let start = resolve_index(text, match.start);
      let end = resolve_index(text, match.end);
      if (start === null || start < cursor || start > text.length) {
        const cursor_index = text.indexOf(match.text, cursor);
        const fallback_index = cursor_index !== -1 ? cursor_index : text.indexOf(match.text);
        if (fallback_index === -1) continue;
        start = fallback_index;
      }
      if (end === null || end <= start || end > text.length) end = start + match.text.length;
      start = Math.max(0, Math.min(start, text.length));
      end = Math.max(start, Math.min(end, text.length));
      if (start > cursor) segments.push({ text: text.slice(cursor, start), highlighted: false });
      const snippet = text.slice(start, end) || match.text;
      segments.push({ text: snippet, highlighted: true });
      cursor = end;
    }
    if (cursor < text.length) segments.push({ text: text.slice(cursor), highlighted: false });
    return segments;
  }

  function resolve_index(text: string, offset: number | undefined) {
    if (typeof offset !== "number" || Number.isNaN(offset) || offset < 0) return null;
    return byte_offset_to_index(text, offset);
  }

  function byte_offset_to_index(text: string, offset: number) {
    if (offset <= 0) return 0;
    let bytes = 0;
    for (let i = 0; i < text.length; ) {
      if (bytes >= offset) return i;
      const code_point = text.codePointAt(i);
      if (code_point === undefined) break;
      bytes += byte_length_for_code_point(code_point);
      const next = i + (code_point > 0xffff ? 2 : 1);
      if (bytes > offset) return next;
      i = next;
    }
    return text.length;
  }

  function byte_length_for_code_point(code_point: number) {
    if (code_point <= 0x7f) return 1;
    if (code_point <= 0x7ff) return 2;
    if (code_point <= 0xffff) return 3;
    return 4;
  }
</script>

<section class="space-y-4">
  <div class="space-y-4">
    {#each visible_results as result, idx (result.path + ":" + (result.line_number ?? "na") + ":" + idx)}
      <Card class="border shadow-sm">
        <CardHeader class="items-end gap-2 text-right">
          <div class="flex flex-wrap items-center justify-between gap-3" dir="ltr">
            <Button variant="link" class="px-0 text-sm" onclick={() => open_result(result.path)}>{result.path}</Button>
            <Button
              variant="link"
              class="px-0 text-sm"
              aria-label="افتح عند السطر"
              title="افتح عند السطر"
              onclick={() => open_result(result.path, result.line_number)}
            >
              <LocateFixed class="size-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="space-y-2">
          {#if result.context_before}
            <p class="text-xs text-muted-foreground" dir="auto">{result.context_before}</p>
          {/if}
          <div class="rounded-md bg-accent/30 p-3 whitespace-pre-wrap" dir="auto">
            {#each build_segments(result) as segment, i (i)}
              <span class="rounded px-1 py-0.5" class:bg-yellow-200={segment.highlighted}>{segment.text}</span>
            {/each}
          </div>
          {#if result.context_after}
            <p class="text-xs text-muted-foreground" dir="auto">{result.context_after}</p>
          {/if}
        </CardContent>
      </Card>
    {/each}
  </div>

  {#if has_more_results}
    <div
      class="h-4"
      {@attach infinite_scroll(() => {
        render_count = Math.min(render_count + page_size, results.length);
      })}
    ></div>
  {/if}
</section>
