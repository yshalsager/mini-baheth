<script lang="ts">
  import { infinite_scroll } from "$lib/attachments";
  import { Button } from "$lib/components/ui/button";
  import {
    ContextMenu,
    ContextMenuContent,
    ContextMenuItem,
    ContextMenuSeparator,
    ContextMenuTrigger,
  } from "$lib/components/ui/context-menu";
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu";
  import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "$lib/components/ui/table";
  import { RESULTS_PER_PAGE } from "$lib/constants";
  import type { SearchMatchPayload, Submatch } from "$lib/types";
  import LocateFixed from "@lucide/svelte/icons/locate-fixed";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import { openPath, revealItemInDir } from "@tauri-apps/plugin-opener";
  import { toast } from "svelte-sonner";

  type TextSegment = {
    text: string;
    highlighted: boolean;
  };

  let {
    results = [],
    open_result,
    selected_key = "",
    select_result,
    shown_count = $bindable(0),
    total_count = $bindable(0),
    data_root = "",
  }: {
    results?: SearchMatchPayload[];
    open_result: (path: string, line_number?: number) => void;
    selected_key?: string;
    select_result: (r: SearchMatchPayload) => void;
    shown_count?: number;
    total_count?: number;
    data_root?: string;
  } = $props();

  let render_count = $state(RESULTS_PER_PAGE);
  const visible_results = $derived(results.slice(0, render_count));
  const has_more = $derived(results.length > render_count);

  $effect(() => {
    shown_count = visible_results.length;
    total_count = results.length;
  });

  function load_more() {
    render_count = Math.min(render_count + RESULTS_PER_PAGE, results.length);
  }

  function key_of(r: SearchMatchPayload) {
    return r.path + ":" + (r.line_number ?? "na");
  }

  function handle_keydown(e: KeyboardEvent) {
    if (!results.length) return;
    const idx = results.findIndex(r => key_of(r) === selected_key);
    if (e.key === "ArrowDown") {
      const next = Math.min(idx === -1 ? 0 : idx + 1, results.length - 1);
      const r = results[next];
      if (!r) return;
      select_result(r);
      e.preventDefault();
      return;
    }
    if (e.key === "ArrowUp") {
      const prev = Math.max(idx === -1 ? 0 : idx - 1, 0);
      const r = results[prev];
      if (!r) return;
      select_result(r);
      e.preventDefault();
      return;
    }
    if (e.key === "Enter") {
      const current = idx === -1 ? results[0] : results[idx];
      if (!current) return;
      open_result(current.path, current.line_number);
      e.preventDefault();
    }
  }

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

  // os actions for dropdown menu
  function is_abs(p: string) {
    return p.startsWith("/") || /^[A-Za-z]:[\\\/]/.test(p);
  }
  function resolve_fs_path(p: string) {
    if (is_abs(p)) return p;
    const root = data_root || "";
    if (!root) return p;
    const sep = root.includes("\\") ? "\\" : "/";
    const base = root.endsWith(sep) ? root.slice(0, -1) : root;
    const rel = p.replace(/^([\\/])+/, "");
    return `${base}${sep}${rel}`;
  }

  async function open_in_os_path(path: string) {
    try {
      await openPath(resolve_fs_path(path));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error("فشل فتح الملف: " + msg);
      if (msg.toLowerCase().includes("not allowed")) {
        // degrade gracefully: show in folder if policy blocks opening
        try {
          await reveal_in_os_path(path);
        } catch {}
      }
    }
  }
  async function reveal_in_os_path(path: string) {
    try {
      await revealItemInDir(resolve_fs_path(path));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error("فشل إظهار الملف في المجلد: " + msg);
    }
  }

  function open_at_line(e: Event, r: SearchMatchPayload) {
    e.stopPropagation();
    open_result(r.path, r.line_number);
  }

  function copy_path(r: SearchMatchPayload) {
    navigator.clipboard?.writeText(r.path);
  }

  function format_mtime(m?: number) {
    if (!m || Number.isNaN(m)) return "";
    try {
      const d = new Date(m * 1000);
      return d.toLocaleString();
    } catch {
      return "";
    }
  }
</script>

<section class="space-y-2">
  <div class="overflow-hidden rounded border bg-background">
    <Table
      id="results-grid"
      class="w-full text-sm"
      role="grid"
      aria-label="النتائج"
      tabindex={0}
      onkeydown={handle_keydown}
    >
      <TableHeader class="bg-muted/50">
        <TableRow class="text-end">
          <TableHead class="px-3 py-2">الملف</TableHead>
          <TableHead class="px-3 py-2">السطر</TableHead>
          <TableHead class="px-3 py-2">التاريخ</TableHead>
          <TableHead class="px-3 py-2">المقتطف</TableHead>
          <TableHead class="px-3 py-2"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {#each visible_results as result, idx (key_of(result) + ":" + idx)}
          {@const key = key_of(result)}
          <ContextMenu>
            <ContextMenuTrigger class="contents">
              <TableRow
                class="border-t text-end align-top hover:bg-muted/30 data-[selected=true]:bg-accent/20"
                data-selected={selected_key === key}
                onclick={() => select_result(result)}
                aria-selected={selected_key === key}
              >
                <TableCell class="px-3 py-2" dir="ltr">
                  <div class="flex min-w-0 items-center justify-between gap-2" dir="ltr">
                    <Button variant="link" class="px-0 text-sm truncate" onclick={() => open_result(result.path)}
                      >{result.path}</Button
                    >
                    <div class="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="افتح عند السطر"
                        title="افتح عند السطر"
                        onclick={e => open_at_line(e, result)}
                      >
                        <LocateFixed class="size-4" />
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger
                          class="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted"
                          aria-label="المزيد"
                          title="المزيد"
                          onclick={e => e.stopPropagation()}
                        >
                          <MoreHorizontal class="size-4" />
                        </DropdownMenuTrigger>
                        <DropdownMenuContent class="min-w-40" onkeydown={e => e.stopPropagation()}>
                          <DropdownMenuItem onclick={() => copy_path(result)}>نسخ المسار</DropdownMenuItem>
                          <DropdownMenuItem
                            onclick={() => {
                              open_in_os_path(result.path);
                            }}>فتح الملف</DropdownMenuItem
                          >
                          <DropdownMenuItem
                            onclick={() => {
                              reveal_in_os_path(result.path);
                            }}>إظهار في المجلد</DropdownMenuItem
                          >
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onclick={() => open_result(result.path, result.line_number)}
                            >افتح عند السطر</DropdownMenuItem
                          >
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </TableCell>
                <TableCell class="px-3 py-2 w-16" dir="ltr">#{result.line_number}</TableCell>
                <TableCell class="px-3 py-2 w-44" dir="ltr">{format_mtime(result.mtime)}</TableCell>
                <TableCell class="px-3 py-2">
                  {#if result.context_before}
                    <p class="mb-1 text-xs text-muted-foreground" dir="auto">{result.context_before}</p>
                  {/if}
                  <div class="overflow-x-auto whitespace-pre rounded bg-accent/30 p-2" dir="auto">
                    {#each build_segments(result) as segment, i (i)}
                      <span
                        class={"rounded px-1 py-0.5 " +
                          (segment.highlighted ? "bg-yellow-200 dark:bg-yellow-700 dark:text-yellow-50" : "")}
                        >{segment.text}</span
                      >
                    {/each}
                  </div>
                  {#if result.context_after}
                    <p class="mt-1 text-xs text-muted-foreground" dir="auto">{result.context_after}</p>
                  {/if}
                </TableCell>
                <TableCell class="px-3 py-2"></TableCell>
              </TableRow>
            </ContextMenuTrigger>
            <ContextMenuContent class="min-w-40" onkeydown={e => e.stopPropagation()}>
              <ContextMenuItem onclick={() => copy_path(result)}>نسخ المسار</ContextMenuItem>
              <ContextMenuItem
                onclick={() => {
                  open_in_os_path(result.path);
                }}>فتح الملف</ContextMenuItem
              >
              <ContextMenuItem
                onclick={() => {
                  reveal_in_os_path(result.path);
                }}>إظهار في المجلد</ContextMenuItem
              >
              <ContextMenuSeparator />
              <ContextMenuItem onclick={() => open_result(result.path, result.line_number)}
                >افتح عند السطر</ContextMenuItem
              >
            </ContextMenuContent>
          </ContextMenu>
        {/each}
      </TableBody>
    </Table>
  </div>

  {#if has_more}
    <div class="h-4" {@attach infinite_scroll(load_more)}></div>
  {/if}
</section>
