<script lang="ts">
  import FileViewerDialog from "$lib/components/FileViewerDialog.svelte";
  import InlineFilePreview from "$lib/components/InlineFilePreview.svelte";
  import {
    Menubar,
    MenubarMenu,
    MenubarTrigger,
    MenubarContent,
    MenubarItem,
    MenubarSeparator,
  } from "$lib/components/ui/menubar";
  import {
    CommandDialog,
    CommandInput,
    CommandList,
    CommandGroup,
    CommandItem,
    CommandEmpty,
  } from "$lib/components/ui/command";
  import { toast } from "svelte-sonner";
  import ResultsList from "$lib/components/ResultsList.svelte";
  import SearchPanel from "$lib/components/SearchPanel.svelte";

  import { ResizablePaneGroup, ResizablePane, ResizableHandle } from "$lib/components/ui/resizable";
  import { userPrefersMode, setMode, resetMode } from 'mode-watcher'
  import { FILE_FILTERS, MAX_RESULTS } from "$lib/constants";
  import { fetch_file, get_data_root, list_directories, search as search_api, set_data_root } from "$lib/search";
  import { with_current } from "$lib/search-events";
  import { debounce } from "$lib/utils";
  import type { UnlistenFn } from "@tauri-apps/api/event";
  import { listen } from "@tauri-apps/api/event";
  import { open } from "@tauri-apps/plugin-dialog";
  import { onMount } from "svelte";

  import type { SearchCompletePayload, SearchErrorPayload, SearchMatchPayload, SearchStartedPayload } from "$lib/types";

  let data_root = $state("");
  let directories = $state<string[]>([]);
  let directory_search = $state("");
  let directories_loading = $state(false);
  let directories_error = $state("");
  let selected_directory = $state("");

  let file_filter = $state(FILE_FILTERS[0]);

  let query = $state("");
  let search_error = $state("");
  let searching = $state(false);
  let search_complete = $state(false);
  let current_request_id = $state("");
  let shown_count = $state(0);
  let total_count = $state(0);
  let elapsed_ms = $state(0);
  let _timer: number | null = null;

  let results = $state<SearchMatchPayload[]>([]);

  let modal_open = $state(false);
  let modal_loading = $state(false);
  let modal_file = $state("");
  let modal_lines = $state<string[]>([]);
  let modal_line_number = $state<number | null>(null);
  let modal_error = $state("");

  // inline preview state
  let selected_key = $state("");
  let preview_file = $state("");
  let preview_lines = $state<string[]>([]);
  let preview_line_number = $state<number | null>(null);
  let preview_loading = $state(false);
  let preview_error = $state("");
  let preview_wrap = $state(true);
  let preview_font_px = $state(13);
  let cmd_open = $state(false);
  let cmd_query = $state("");
  const help_url = "https://github.com/";

  let initialized = $state(false);

  const trimmed_query = $derived(query.trim());
  const can_search = $derived(!!trimmed_query && !!selected_directory);
  const search_hint = $derived(
    search_error
      ? ""
      : searching
        ? "جارٍ البحث..."
        : search_complete && !results.length
          ? "لم يتم العثور على نتائج"
          : ""
  );

  const directory_fetch = debounce((term: string) => {
    void refresh_directories(term);
  }, 250);

  const schedule_search = debounce(() => {
    void start_search();
  }, 400);

  onMount(() => {
    const disposers: UnlistenFn[] = [];

    const setup = async () => {
      const only_current = with_current(() => current_request_id);

      disposers.push(
        await listen<SearchStartedPayload>(
          "search_started",
          only_current(payload => {
            searching = true;
            search_complete = false;
            search_error = "";
            if (_timer) { clearInterval(_timer); _timer = null }
            const start = Date.now();
            elapsed_ms = 0;
            _timer = setInterval(() => { elapsed_ms = Date.now() - start }, 100) as unknown as number;
          })
        )
      );

      disposers.push(
        await listen<SearchMatchPayload>(
          "search_match",
          only_current(payload => {
            enqueue_result(payload);
          })
        )
      );

      disposers.push(
        await listen<SearchErrorPayload>(
          "search_error",
          only_current(payload => {
            search_error = payload.error;
            searching = false;
            if (_timer) { clearInterval(_timer); _timer = null }
          })
        )
      );

      disposers.push(
        await listen<SearchCompletePayload>(
          "search_complete",
          only_current(_ => {
            searching = false;
            search_complete = true;
            if (_timer) { clearInterval(_timer); _timer = null }
          })
        )
      );
    };

    void setup();
    void load_root_and_directories();

    return () => {
      disposers.forEach(fn => fn());
    };
  });

  function enqueue_result(match: SearchMatchPayload) {
    if (results.length >= MAX_RESULTS) return;
    results = [...results, match];
  }

  function normalize_path(value: string | null | undefined) {
    if (!value || value === "None" || value === "null") return "";
    return value;
  }

  function create_request_id() {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
    return Math.random().toString(36).slice(2);
  }

  function reset_results() {
    results = [];
    search_error = "";
    search_complete = false;
    searching = false;
    current_request_id = "";
  }

  async function load_root_and_directories() {
    try {
      const root = await get_data_root();
      data_root = normalize_path(root);
    } catch (error) {
      data_root = "";
    }

    await refresh_directories("");
    initialized = true;
  }

  async function refresh_directories(term: string) {
    directories_loading = true;
    directories_error = "";
    try {
      const response = await list_directories(term, 200);
      const options = response.directories ?? [];
      const previous = selected_directory;
      directories = options;
      if (!options.length) selected_directory = "";
      else if (!options.includes(previous)) selected_directory = options[0];
      if (initialized && query.trim() && selected_directory && selected_directory !== previous) void start_search();
    } catch (error) {
      directories_error = error instanceof Error ? error.message : String(error);
      directories = [];
      selected_directory = "";
    } finally {
      directories_loading = false;
    }
  }

  async function choose_root() {
    const selected = await open({ directory: true });
    if (!selected) return;
    const path = Array.isArray(selected) ? selected[0] : selected;
    try {
      const root = await set_data_root(path);
      data_root = normalize_path(root);
      selected_directory = data_root;
      await refresh_directories("");
      if (query.trim()) void start_search();
    } catch (error) {
      search_error = error instanceof Error ? error.message : String(error);
    }
  }

  async function start_search() {
    if (!can_search) return reset_results();

    const request_id = create_request_id();
    current_request_id = request_id;
    results = [];
    search_error = "";
    search_complete = false;
    searching = true;

    try {
      await search_api({ query: trimmed_query, directory: selected_directory, file_filter, request_id });
    } catch (error) {
      if (current_request_id !== request_id) return;
      search_error = error instanceof Error ? error.message : String(error);
      searching = false;
    }
  }

  async function open_result(path: string, line_number?: number) {
    modal_open = true;
    modal_loading = true;
    modal_error = "";
    try {
      const response = await fetch_file({ path, line_number: line_number ?? undefined });
      modal_file = response.file;
      modal_lines = response.lines;
      modal_line_number = response.line_number ?? line_number ?? null;
    } catch (error) {
      modal_error = error instanceof Error ? error.message : String(error);
      modal_lines = [];
      modal_line_number = null;
    } finally {
      modal_loading = false;
    }
  }

  function handle_select_result(r: SearchMatchPayload) {
    const key = r.path + ":" + (r.line_number ?? "na");
    if (selected_key === key) return;
    selected_key = key;
    preview_loading = true;
    preview_error = "";
    preview_file = "";
    preview_lines = [];
    preview_line_number = null;
    void fetch_file({ path: r.path, line_number: r.line_number ?? undefined })
      .then(resp => {
        preview_file = resp.file;
        preview_lines = resp.lines;
        preview_line_number = resp.line_number ?? r.line_number ?? null;
      })
      .catch(err => {
        preview_error = err instanceof Error ? err.message : String(err);
      })
      .finally(() => {
        preview_loading = false;
      });
  }
  function focus_query() {
    const el = document?.getElementById("query") as HTMLInputElement | null;
    el?.focus();
  }
  function focus_results() {
    const el = document?.getElementById("results-grid") as HTMLElement | null;
    el?.focus();
  }
  const commands = $derived([
    { id: "change-root", label: "تغيير مجلد البيانات", run: choose_root },
    { id: "focus-query", label: "التركيز على البحث", run: focus_query },
    { id: "focus-results", label: "التركيز على النتائج", run: focus_results },
    {
      id: "clear-query",
      label: "مسح البحث",
      run: () => {
        query = "";
        handle_query_input();
      },
    },
  ]);
  onMount(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        cmd_open = true;
      }
      if (e.altKey && (e.key === "+" || e.key === "=")) preview_font_px = Math.min(20, preview_font_px + 1);
      if (e.altKey && e.key === "-") preview_font_px = Math.max(11, preview_font_px - 1);
      if (e.altKey && e.key.toLowerCase() === "w") preview_wrap = !preview_wrap;
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  function handle_query_input() {
    if (!trimmed_query) return reset_results();
    schedule_search();
  }

  function handle_directory_search() {
    directory_fetch(directory_search);
  }

  function handle_directory_focus() {
    if (!directories.length) void refresh_directories(directory_search);
  }

  function handle_directory_value_change(value: string) {
    selected_directory = value;
  }

  function handle_file_filter_change(value: string) {
    file_filter = value;
  }

  function format_elapsed(ms: number) {
    if (!ms || ms < 0) return '0ms'
    const s = Math.floor(ms / 1000)
    const rem = ms % 1000
    if (s >= 60) {
      const m = Math.floor(s / 60)
      const ss = s % 60
      return `${m}m ${ss}s`
    }
    if (s > 0) return `${s}.${String(Math.floor(rem/100)).padStart(1,'0')}s`
    return `${ms}ms`
  }

  let prev_filter_key = $state("");
  $effect(() => {
    if (!initialized) return;
    const key = `${selected_directory}|${file_filter}`;
    if (key === prev_filter_key) return;
    prev_filter_key = key;
    if (!trimmed_query) return reset_results();
    if (can_search) void start_search();
  });

  // keep selection on search completion when possible; auto-select first if none
  $effect(() => {
    if (!search_complete) return;
    if (!results.length) return;
    const exists = results.some(r => r.path + ":" + (r.line_number ?? "na") === selected_key);
    if (exists) return;
    const first = results[0];
    if (!first) return;
    handle_select_result(first);
  });

  // toast errors
  $effect(() => {
    if (!search_error) return;
    toast.error(search_error);
  });
</script>

<main class="h-svh w-full bg-muted/10">
  <div class="flex min-w-0 w-full p-4 h-full">
    <div class="flex-1 min-h-0 min-w-0 overflow-x-hidden space-y-4 flex flex-col">
        <div class="flex items-end justify-between text-right">
          <div class="flex items-end gap-3">
            <div>
              <h1 class="text-2xl font-bold">باحث الصغير</h1>
            </div>
          </div>
        </div>

        <Menubar>
          <MenubarMenu>
            <MenubarTrigger>ملف</MenubarTrigger>
            <MenubarContent>
              <MenubarItem onclick={choose_root}>فتح مجلد</MenubarItem>
            </MenubarContent>
          </MenubarMenu>
          <MenubarMenu>
            <MenubarTrigger>تحرير</MenubarTrigger>
            <MenubarContent>
              <MenubarItem
                onclick={() => {
                  query = "";
                  handle_query_input();
                }}>مسح البحث</MenubarItem
              >
            </MenubarContent>
          </MenubarMenu>
          <MenubarMenu>
            <MenubarTrigger>عرض</MenubarTrigger>
            <MenubarContent>
              <MenubarItem onclick={() => (preview_wrap = !preview_wrap)}>تبديل التفاف السطور</MenubarItem>
              <MenubarSeparator />
              <MenubarItem onclick={() => (preview_font_px = Math.max(11, preview_font_px - 1))}>تصغير الخط</MenubarItem>
              <MenubarItem onclick={() => (preview_font_px = Math.min(20, preview_font_px + 1))}>تكبير الخط</MenubarItem>
              <MenubarSeparator />
              <MenubarItem onclick={() => setMode('light')}>{userPrefersMode.current === 'light' ? '✓ ' : ''}الوضع الفاتح</MenubarItem>
              <MenubarItem onclick={() => setMode('dark')}>{userPrefersMode.current === 'dark' ? '✓ ' : ''}الوضع الداكن</MenubarItem>
              <MenubarItem onclick={() => resetMode()}>{userPrefersMode.current === 'system' ? '✓ ' : ''}مطابق للنظام</MenubarItem>
            </MenubarContent>
          </MenubarMenu>
          <MenubarMenu>
            <MenubarTrigger>مساعدة</MenubarTrigger>
            <MenubarContent>
              <MenubarItem
                onclick={() => {
                  try {
                    import("@tauri-apps/plugin-opener").then(m => m.openUrl(help_url));
                  } catch {}
                }}>الدليل</MenubarItem
              >
            </MenubarContent>
          </MenubarMenu>
        </Menubar>

        <div class="rounded border bg-background">
          <SearchPanel
            bind:directory_search
            {directories}
            {directories_loading}
            {directories_error}
            bind:selected_directory
            bind:file_filter
            bind:query
            {data_root}
            {search_hint}
            {search_error}
            {handle_directory_search}
            {handle_directory_focus}
            {handle_directory_value_change}
            {handle_file_filter_change}
            {handle_query_input}
            on_enter={() => start_search()}
          />
        </div>

        <ResizablePaneGroup direction="horizontal" class="w-full flex-1 min-h-0 rounded border">
          <ResizablePane class="min-w-0" defaultSize={60} minSize={35}>
            <section class="h-full min-w-0 space-y-4 overflow-y-auto overflow-x-hidden p-3">
              {#if !trimmed_query}
                <p class="text-right text-sm text-muted-foreground">ابدأ بكتابة عبارة البحث لعرض النتائج.</p>
              {:else if !results.length && searching}
                <p class="text-right text-sm text-muted-foreground">جارٍ جمع النتائج...</p>
              {:else if !results.length && search_complete}
                <p class="text-right text-sm text-muted-foreground">لم يتم العثور على نتائج مطابقة.</p>
              {/if}

              {#key current_request_id}
                <ResultsList
                  {results}
                  {open_result}
                  {selected_key}
                  select_result={handle_select_result}
                  bind:shown_count
                  bind:total_count
                />
              {/key}
            </section>
          </ResizablePane>
          <ResizableHandle withHandle />
          <ResizablePane class="min-w-0" defaultSize={40} minSize={25}>
            <section class="h-full min-w-0 overflow-hidden rounded bg-background p-4 text-right">
              <InlineFilePreview
                file={preview_file}
                lines={preview_lines}
                line_number={preview_line_number}
                loading={preview_loading}
                error={preview_error}
                bind:wrap={preview_wrap}
                bind:font_px={preview_font_px}
              />
            </section>
          </ResizablePane>
        </ResizablePaneGroup>

        <footer class="flex items-center justify-between rounded border bg-background px-3 py-2 text-xs text-muted-foreground">
          <div class="flex items-center gap-2">
            <span
              >{searching
                ? "جارٍ البحث..."
                : search_error
                  ? "فشل البحث"
                  : search_complete
                    ? "انتهى البحث"
                    : "جاهز"}</span
            >
            {#if search_error}
              <span class="text-destructive">{search_error}</span>
            {/if}
          </div>
          <div class="flex items-center gap-3" dir="ltr">
            <span>showing {shown_count} of {total_count}</span>
            <span>|</span>
            <span>elapsed: {format_elapsed(elapsed_ms)}</span>
          </div>
        </footer>
    </div>
  </div>
</main>

<FileViewerDialog
  bind:open={modal_open}
  file={modal_file}
  lines={modal_lines}
  line_number={modal_line_number}
  loading={modal_loading}
  error={modal_error}
/>

<CommandDialog bind:open={cmd_open}>
  <div class="text-right">
    <CommandInput placeholder="ابحث عن أمر..." oninput={(e: any) => { cmd_query = e?.currentTarget?.value ?? '' }} />
  </div>
  <CommandList>
    <CommandEmpty>لا توجد أوامر مطابقة.</CommandEmpty>
    <CommandGroup heading="بحث">
      {#if (cmd_query || query).trim()}
        <CommandItem value={`ابحث: ${(cmd_query || query)}`}
          onclick={() => { query = (cmd_query || query); handle_query_input(); cmd_open = false; start_search() }}>
          ابحث: {(cmd_query || query)}
        </CommandItem>
      {/if}
    </CommandGroup>
    <CommandGroup heading="الأوامر">
      {#each commands as c (c.id)}
        <CommandItem
          value={c.label}
          onclick={() => {
            c.run();
            cmd_open = false;
          }}>{c.label}</CommandItem
        >
      {/each}
    </CommandGroup>
  </CommandList>
</CommandDialog>
