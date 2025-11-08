<script lang="ts">
  import { Label } from '$lib/components/ui/label'
  import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuTrigger } from '$lib/components/ui/dropdown-menu'

  let {
    file_filters = $bindable<string[]>([]),
    options = [],
    handle_file_filter_change,
  }: {
    file_filters?: string[];
    options?: string[];
    handle_file_filter_change: (values: string[]) => void;
  } = $props();

  function toggle(value: string) {
    if (value === 'all') {
      file_filters = ['all']
      handle_file_filter_change(file_filters)
      return
    }
    let arr = file_filters.filter(v => v !== 'all')
    const i = arr.indexOf(value)
    if (i >= 0) arr = [...arr.slice(0, i), ...arr.slice(i + 1)]
    else arr = [...arr, value]
    file_filters = arr
    handle_file_filter_change(file_filters)
  }

  const summary = $derived(
    !file_filters?.length
      ? '—'
      : file_filters.includes('all')
        ? 'الكل'
        : file_filters.map(v => v.replace('*.', '')).join(', ')
  )
</script>

<div class="space-y-2">
  <Label for="file-filter-trigger">نوع الملف</Label>
  <DropdownMenu>
    <DropdownMenuTrigger id="file-filter-trigger" class="w-full rounded border px-2 py-1 text-sm text-end">
      {summary}
    </DropdownMenuTrigger>
    <DropdownMenuContent class="w-56">
      {#each options as option (option)}
        <DropdownMenuCheckboxItem checked={file_filters.includes(option)} onclick={() => toggle(option)}>
          {option.replace('*.','')}
        </DropdownMenuCheckboxItem>
      {/each}
      <DropdownMenuCheckboxItem checked={file_filters.includes('all')} onclick={() => toggle('all')}>
        الكل
      </DropdownMenuCheckboxItem>
    </DropdownMenuContent>
  </DropdownMenu>
</div>
