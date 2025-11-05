<script lang="ts">
  import { Label } from "$lib/components/ui/label";
  import { Select, SelectContent, SelectItem, SelectTrigger } from "$lib/components/ui/select";

  let {
    file_filter = $bindable(""),
    options = [],
    handle_file_filter_change,
  }: {
    file_filter?: string;
    options?: string[];
    handle_file_filter_change: (value: string) => void;
  } = $props();

  const label = $derived(file_filter.replace("*.", ""));
</script>

<div class="space-y-2">
  <Label for="file-filter">نوع الملف</Label>
  <Select type="single" value={file_filter} onValueChange={handle_file_filter_change}>
    <SelectTrigger id="file-filter" class="w-full justify-between">
      <span data-slot="select-value" class="flex-1 truncate text-right">{label}</span>
    </SelectTrigger>
    <SelectContent class="max-h-72">
      {#each options as option (option)}
        <SelectItem value={option}>{option.replace("*.", "")}</SelectItem>
      {/each}
    </SelectContent>
  </Select>
</div>
