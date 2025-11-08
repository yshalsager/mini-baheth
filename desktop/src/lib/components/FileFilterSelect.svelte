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
    const set = new Set(file_filters);
    if (value === 'all') {
      file_filters = ['all'];
    } else {
      if (set.has('all')) set.delete('all');
      if (set.has(value)) set.delete(value)
      else set.add(value)
      file_filters = Array.from(set);
    }
    handle_file_filter_change(file_filters);
  }

  const summary = $derived(() => {
    if (!file_filters?.length) return '—'
    if (file_filters.includes('all')) return 'الكل'
    return file_filters.map(v => v.replace('*.','')).join(', ')
  })
</script>

<div class="space-y-2">
  <Label for="file-filter-trigger">نوع الملف</Label>
  <DropdownMenu>
    <DropdownMenuTrigger id="file-filter-trigger" class="w-full rounded border px-2 py-1 text-sm text-end">
      {summary()}
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
