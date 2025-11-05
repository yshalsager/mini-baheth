<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Select, SelectContent, SelectItem, SelectTrigger } from "$lib/components/ui/select";

  let {
    directory_search = $bindable(""),
    directories = [],
    directories_loading = false,
    directories_error = "",
    selected_directory = $bindable(""),
    handle_directory_search,
    handle_directory_focus,
    handle_directory_value_change,
  }: {
    directory_search?: string;
    directories?: string[];
    directories_loading?: boolean;
    directories_error?: string;
    selected_directory?: string;
    handle_directory_search: () => void;
    handle_directory_focus: () => void;
    handle_directory_value_change: (value: string) => void;
  } = $props();

  const status_hint = $derived(directories_error || (directories_loading ? "جاري تحميل المجلدات..." : ""));
</script>

<div class="space-y-2">
  <Label for="directories">المجلدات</Label>
  <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
    <Input
      id="directories"
      placeholder="ابحث عن مجلد..."
      bind:value={directory_search}
      oninput={handle_directory_search}
      onfocus={handle_directory_focus}
      dir="auto"
    />
    <Select type="single" value={selected_directory} onValueChange={handle_directory_value_change}>
      <SelectTrigger class="w-full justify-between">
        <span data-slot="select-value" class="flex-1 truncate text-start">{selected_directory}</span>
      </SelectTrigger>
      <SelectContent class="max-h-72">
        {#each directories as option (option)}
          <SelectItem value={option}>{option}</SelectItem>
        {/each}
      </SelectContent>
    </Select>
  </div>
  {#if status_hint}
    <p class={"text-sm " + (directories_error ? "text-destructive" : "text-muted-foreground")}>{status_hint}</p>
  {/if}
</div>
