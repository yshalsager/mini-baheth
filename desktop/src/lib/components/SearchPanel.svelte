<script lang='ts'>
  import DirectoryPicker from '$lib/components/DirectoryPicker.svelte'
  import FileFilterSelect from '$lib/components/FileFilterSelect.svelte'
  import SearchInput from '$lib/components/SearchInput.svelte'
  import { CardContent } from '$lib/components/ui/card'
  import { Separator } from '$lib/components/ui/separator'
  import { FILE_FILTERS } from '$lib/constants'

  let {
    directory_search = $bindable(''),
    directories = [],
    directories_loading = false,
    directories_error = '',
    selected_directory = $bindable(''),
    file_filter = $bindable(FILE_FILTERS[0]),
    query = $bindable(''),
    directory_hint = '',
    search_hint = '',
    search_error = '',
    handle_directory_search,
    handle_directory_focus,
    handle_directory_value_change,
    handle_file_filter_change,
    handle_query_input,
    on_enter
  }: {
    directory_search?: string
    directories?: string[]
    directories_loading?: boolean
    directories_error?: string
    selected_directory?: string
    file_filter?: string
    query?: string
    directory_hint?: string
    search_hint?: string
    search_error?: string
    handle_directory_search: () => void
    handle_directory_focus: () => void
    handle_directory_value_change: (value: string) => void
    handle_file_filter_change: (value: string) => void
    handle_query_input: () => void
    on_enter: () => void
  } = $props()
</script>

<CardContent class='space-y-6'>
  <div class='grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]'>
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
    <FileFilterSelect bind:file_filter options={FILE_FILTERS} {handle_file_filter_change} />
  </div>

  <Separator />

  <SearchInput bind:query {search_hint} {search_error} {handle_query_input} on_enter={on_enter} />
</CardContent>
