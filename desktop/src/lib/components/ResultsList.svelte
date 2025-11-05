<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Table, TableBody, TableHead, TableHeader, TableRow, TableCell } from "$lib/components/ui/table";
  import { FlexRender, createSvelteTable } from "$lib/components/ui/data-table";
  import type { ColumnDef } from "@tanstack/table-core";
  import { getCoreRowModel } from "@tanstack/table-core";
  import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "$lib/components/ui/dropdown-menu";
  import LocateFixed from "@lucide/svelte/icons/locate-fixed";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import type { SearchMatchPayload, Submatch } from "$lib/types";
  import { infinite_scroll } from "$lib/attachments";
  import { RESULTS_PER_PAGE } from "$lib/constants";
  import { openPath, revealItemInDir } from "@tauri-apps/plugin-opener";

  type TextSegment = {
    text: string;
    highlighted: boolean;
  };

  let {
    results = [],
    open_result,
    page_size = RESULTS_PER_PAGE,
    selected_key = '',
    select_result,
  }: {
    results?: SearchMatchPayload[];
    open_result: (path: string, line_number?: number) => void;
    page_size?: number;
    selected_key?: string;
    select_result: (r: SearchMatchPayload) => void;
  } = $props();

  let render_count = $state(page_size);
  const visible_results = $derived(results.slice(0, render_count));
  const has_more_results = $derived(results.length > render_count);

  const columns: ColumnDef<SearchMatchPayload, unknown>[] = [
    {
      id: 'file',
      header: 'الملف',
      cell: ({ row }) => row.original.path,
    },
    {
      id: 'line',
      header: 'السطر',
      cell: ({ row }) => `#${row.original.line_number}`,
    },
    {
      id: 'snippet',
      header: 'المقتطف',
      cell: ({ row }) => row.original,
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => row.original,
    },
  ];

  const table = createSvelteTable<SearchMatchPayload>({
    data: [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  $effect(() => {
    table.setOptions(prev => ({ ...prev, data: visible_results }))
  })

  function key_of(r: SearchMatchPayload) {
    return r.path + ":" + (r.line_number ?? "na");
  }

  function handle_keydown(e: KeyboardEvent) {
    if (!results.length) return;
    const idx = results.findIndex(r => key_of(r) === selected_key);
    if (e.key === 'ArrowDown') {
      const next = Math.min((idx === -1 ? 0 : idx + 1), results.length - 1);
      const r = results[next];
      if (!r) return;
      if (next >= render_count && has_more_results) {
        render_count = Math.min(render_count + page_size, results.length);
      }
      select_result(r);
      e.preventDefault();
      return;
    }
    if (e.key === 'ArrowUp') {
      const prev = Math.max((idx === -1 ? 0 : idx - 1), 0);
      const r = results[prev];
      if (!r) return;
      select_result(r);
      e.preventDefault();
      return;
    }
    if (e.key === 'Enter') {
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
  async function open_in_os_path(path: string) { try { await openPath(path) } catch {} }
  async function reveal_in_os_path(path: string) { try { await revealItemInDir(path) } catch {} }

  
</script>

<section class="space-y-2">
  <div class="overflow-hidden rounded border bg-background">
    <Table id="results-grid" class="w-full text-sm" role="grid" aria-label="النتائج" tabindex={0} onkeydown={handle_keydown}>
      <TableHeader class="bg-muted/50">
        {#each table.getHeaderGroups() as headerGroup}
          <TableRow class="text-right">
            {#each headerGroup.headers as header}
              <TableHead class="px-3 py-2">
                {#if header.isPlaceholder}
                  
                {:else}
                  <FlexRender content={header.column.columnDef.header} context={header.getContext()} />
                {/if}
              </TableHead>
            {/each}
          </TableRow>
        {/each}
      </TableHeader>
      <TableBody>
        {#if table.getRowModel().rows.length === 0 && visible_results.length}
          {#each visible_results as result, idx (result.path + ':' + (result.line_number ?? 'na') + ':' + idx)}
            <TableRow class="border-t text-right align-top hover:bg-muted/30">
              <TableCell class="px-3 py-2" dir="ltr">
                <div class="flex items-center justify-between gap-2" dir="ltr">
                  <Button variant="link" class="px-0 text-sm" onclick={() => open_result(result.path)}>{result.path}</Button>
                  <div class="flex items-center gap-1">
                    <Button variant="ghost" size="icon" aria-label="افتح عند السطر" title="افتح عند السطر" onclick={(e) => { e.stopPropagation(); open_result(result.path, result.line_number); }}>
                      <LocateFixed class="size-4" />
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger class="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted" aria-label="المزيد" title="المزيد" onclick={(e) => e.stopPropagation()}>
                        <MoreHorizontal class="size-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent class="min-w-40" onkeydown={(e) => e.stopPropagation()}>
                        <DropdownMenuItem onclick={() => { navigator.clipboard?.writeText(result.path) }}>نسخ المسار</DropdownMenuItem>
                        <DropdownMenuItem onclick={() => { open_in_os_path(result.path) }}>فتح الملف</DropdownMenuItem>
                        <DropdownMenuItem onclick={() => { reveal_in_os_path(result.path) }}>إظهار في المجلد</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onclick={() => open_result(result.path, result.line_number)}>افتح عند السطر</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </TableCell>
              <TableCell class="px-3 py-2 w-16" dir="ltr">#{result.line_number}</TableCell>
              <TableCell class="px-3 py-2">
                {#if result.context_before}
                  <p class="mb-1 text-xs text-muted-foreground" dir="auto">{result.context_before}</p>
                {/if}
                <div class="overflow-x-auto whitespace-pre rounded bg-accent/30 p-2" dir="auto">
                  {#each build_segments(result) as segment, i (i)}
                    <span class="rounded px-1 py-0.5" class:bg-yellow-200={segment.highlighted}>{segment.text}</span>
                  {/each}
                </div>
                {#if result.context_after}
                  <p class="mt-1 text-xs text-muted-foreground" dir="auto">{result.context_after}</p>
                {/if}
              </TableCell>
            </TableRow>
          {/each}
        {:else}
        {#each table.getRowModel().rows as row (row.id)}
          {@const result = row.original}
          <TableRow class="border-t text-right align-top hover:bg-muted/30 data-[selected=true]:bg-accent/20" data-selected={selected_key === (result.path + ':' + (result.line_number ?? 'na'))} onclick={() => select_result(result)} aria-selected={selected_key === (result.path + ':' + (result.line_number ?? 'na'))}>
            {#each row.getVisibleCells() as cell}
              <TableCell class="px-3 py-2" dir={(cell.column.id === 'file' || cell.column.id === 'line') ? 'ltr' : 'auto'}>
                {#if cell.column.id === 'file'}
                  <div class="flex items-center justify-between gap-2" dir="ltr">
                    <Button variant="link" class="px-0 text-sm" onclick={() => open_result(result.path)}>{result.path}</Button>
                    <div class="flex items-center gap-1">
                      <Button variant="ghost" size="icon" aria-label="افتح عند السطر" title="افتح عند السطر" onclick={(e) => { e.stopPropagation(); open_result(result.path, result.line_number); }}>
                        <LocateFixed class="size-4" />
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger class="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted" aria-label="المزيد" title="المزيد" onclick={(e) => e.stopPropagation()}>
                          <MoreHorizontal class="size-4" />
                        </DropdownMenuTrigger>
                        <DropdownMenuContent class="min-w-40" onkeydown={(e) => e.stopPropagation()}>
                          <DropdownMenuItem onclick={() => { navigator.clipboard?.writeText(result.path) }}>نسخ المسار</DropdownMenuItem>
                          <DropdownMenuItem onclick={() => { open_in_os_path(result.path) }}>فتح الملف</DropdownMenuItem>
                          <DropdownMenuItem onclick={() => { reveal_in_os_path(result.path) }}>إظهار في المجلد</DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onclick={() => open_result(result.path, result.line_number)}>افتح عند السطر</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                {:else if cell.column.id === 'line'}
                  #{result.line_number}
                {:else if cell.column.id === 'snippet'}
                  {#if result.context_before}
                    <p class="mb-1 text-xs text-muted-foreground" dir="auto">{result.context_before}</p>
                  {/if}
                  <div class="overflow-x-auto whitespace-pre rounded bg-accent/30 p-2" dir="auto">
                    {#each build_segments(result) as segment, i (i)}
                      <span class="rounded px-1 py-0.5" class:bg-yellow-200={segment.highlighted}>{segment.text}</span>
                    {/each}
                  </div>
                  {#if result.context_after}
                    <p class="mt-1 text-xs text-muted-foreground" dir="auto">{result.context_after}</p>
                  {/if}
                {:else if cell.column.id === 'actions'}
                  
                {:else}
                  <FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
                {/if}
              </TableCell>
            {/each}
          </TableRow>
        {/each}
        {/if}
      </TableBody>
    </Table>
  </div>

  {#if has_more_results}
    <div class="h-4" {@attach infinite_scroll(() => { render_count = Math.min(render_count + page_size, results.length) })}></div>
  {/if}
</section>
