<script lang="ts">
  import DirectoryPicker from "$lib/components/DirectoryPicker.svelte";
  import FileFilterSelect from "$lib/components/FileFilterSelect.svelte";
  import SearchInput from "$lib/components/SearchInput.svelte";
  import { CardContent } from "$lib/components/ui/card";
  import { Separator } from "$lib/components/ui/separator";
  import { FILE_FILTERS } from "$lib/constants";

  let {
    directory_search = $bindable(""),
    directories = [],
    directories_loading = false,
    directories_error = "",
    selected_directory = $bindable(""),
    file_filters = $bindable<string[]>([FILE_FILTERS[0]]),
    search_mode = $bindable<'smart' | 'regex' | 'ignore' | 'require'>('smart'),
    query = $bindable(""),
    data_root = "",
    search_hint = "",
    search_error = "",
    handle_directory_search,
    handle_directory_focus,
    handle_directory_value_change,
    handle_file_filter_change,
    handle_query_input,
    on_enter,
  }: {
    directory_search?: string;
    directories?: string[];
    directories_loading?: boolean;
    directories_error?: string;
    selected_directory?: string;
    file_filters?: string[];
    query?: string;
    search_mode?: 'smart' | 'regex' | 'ignore' | 'require';
    data_root?: string;
    search_hint?: string;
    search_error?: string;
    handle_directory_search: () => void;
    handle_directory_focus: () => void;
    handle_directory_value_change: (value: string) => void;
    handle_file_filter_change: (values: string[]) => void;
    handle_query_input: () => void;
    on_enter: () => void;
  } = $props();

  const root_hint = $derived(data_root ? `المجلد الحالي: \n‎${data_root}` : "لم يتم اختيار مجلد البيانات بعد");
</script>

<CardContent class="space-y-6 py-4">
  <p class="text-sm text-muted-foreground select-none whitespace-pre-wrap">{root_hint}</p>
  <div class="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
    <DirectoryPicker
      bind:directory_search
      {directories}
      {directories_loading}
      {directories_error}
      bind:selected_directory
      {handle_directory_search}
      {handle_directory_focus}
      {handle_directory_value_change}
    />
    <FileFilterSelect bind:file_filters options={FILE_FILTERS} {handle_file_filter_change} />
  </div>

  <Separator />

  <SearchInput bind:query bind:search_mode {search_hint} {search_error} {handle_query_input} {on_enter} />
</CardContent>
