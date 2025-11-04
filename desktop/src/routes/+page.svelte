<script lang="ts">
  import FileViewerDialog from "$lib/components/FileViewerDialog.svelte";
  import ResultsList from "$lib/components/ResultsList.svelte";
  import SearchPanel from "$lib/components/SearchPanel.svelte";
  import { Button } from "$lib/components/ui/button";
  import { Card, CardHeader, CardTitle } from "$lib/components/ui/card";
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

  let results = $state<SearchMatchPayload[]>([]);

  let modal_open = $state(false);
  let modal_loading = $state(false);
  let modal_file = $state("");
  let modal_lines = $state<string[]>([]);
  let modal_line_number = $state<number | null>(null);
  let modal_error = $state("");

  let initialized = $state(false);

  const root_hint = $derived(data_root ? `المجلد الحالي: ${data_root}` : "لم يتم اختيار مجلد البيانات بعد");
  const trimmed_query = $derived(query.trim());
  const can_search = $derived(!!trimmed_query && !!selected_directory);
  const directory_hint = $derived(
    directories_loading
      ? "جاري تحميل المجلدات..."
      : directories.length
        ? "اختر مجلداً للبحث بداخله"
        : "لم يتم العثور على مجلدات مطابقة"
  );
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
          })
        )
      );

      disposers.push(
        await listen<SearchCompletePayload>(
          "search_complete",
          only_current(_ => {
            searching = false;
            search_complete = true;
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

  let prev_filter_key = $state("");
  $effect(() => {
    if (!initialized) return;
    const key = `${selected_directory}|${file_filter}`;
    if (key === prev_filter_key) return;
    prev_filter_key = key;
    if (!trimmed_query) return reset_results();
    if (can_search) void start_search();
  });
</script>

<main class="min-h-screen bg-muted/10 py-8" dir="rtl">
  <div class="mx-auto flex max-w-6xl flex-col gap-6 px-4">
    <header class="flex flex-col gap-2 text-right">
      <h1 class="text-3xl font-bold">باحث الصغير</h1>
      <p class="text-sm text-muted-foreground">{root_hint}</p>
      <div class="flex flex-wrap items-center justify-end gap-3">
        <Button variant="outline" size="sm" onclick={choose_root}>تغيير مجلد البيانات</Button>
      </div>
    </header>

    <Card class="shadow-sm">
      <CardHeader class="space-y-2 text-right">
        <CardTitle>خيارات البحث</CardTitle>
        <p class="text-sm text-muted-foreground">{directory_hint}</p>
      </CardHeader>
      <SearchPanel
        bind:directory_search
        {directories}
        {directories_loading}
        {directories_error}
        bind:selected_directory
        bind:file_filter
        bind:query
        {directory_hint}
        {search_hint}
        {search_error}
        {handle_directory_search}
        {handle_directory_focus}
        {handle_directory_value_change}
        {handle_file_filter_change}
        {handle_query_input}
        on_enter={() => start_search()}
      />
    </Card>

    <section class="space-y-4">
      {#if !trimmed_query}
        <p class="text-right text-sm text-muted-foreground">ابدأ بكتابة عبارة البحث لعرض النتائج.</p>
      {:else if !results.length && searching}
        <p class="text-right text-sm text-muted-foreground">جارٍ جمع النتائج...</p>
      {:else if !results.length && search_complete}
        <p class="text-right text-sm text-muted-foreground">لم يتم العثور على نتائج مطابقة.</p>
      {/if}

      <ResultsList {results} {open_result} />
    </section>
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
