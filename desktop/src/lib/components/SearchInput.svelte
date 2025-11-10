<script lang="ts">
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import { Button } from '$lib/components/ui/button'
  import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select'
  import XIcon from '@lucide/svelte/icons/x'

  let {
    query = $bindable(""),
    search_hint = "",
    search_error = "",
    handle_query_input,
    search_mode = $bindable<'smart' | 'regex' | 'ignore' | 'require'>('smart'),
  on_enter,
  }: {
    query?: string;
    search_hint?: string;
    search_error?: string;
    handle_query_input: () => void;
    search_mode?: 'smart' | 'regex' | 'ignore' | 'require';
    on_enter: () => void;
  } = $props();
</script>

<div class="space-y-2">
  <Label for="query">عبارة البحث</Label>
  <div class="flex items-center gap-2">
    <Input
      id="query"
      placeholder="ابحث عن شيء ما"
      bind:value={query}
      oninput={handle_query_input}
      onkeydown={e => e.key === "Enter" && on_enter()}
      dir="auto"
    />
    <div class="flex items-center gap-2">
      <label for="mode" class="text-sm whitespace-nowrap">نمط البحث</label>
      <Select type="single" value={search_mode} onValueChange={(v: string) => { search_mode = v as any; handle_query_input() }}>
        <SelectTrigger id="mode" class="h-9 w-48 justify-between">
          <span data-slot="select-value" class="truncate text-start">
            {search_mode === 'smart' ? 'ذكي' : search_mode === 'regex' ? 'تعبير اعتيادي' : search_mode === 'ignore' ? 'تجاهل التشكيل' : 'التزام التشكيل'}
          </span>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="smart">ذكي</SelectItem>
          <SelectItem value="regex">تعبير اعتيادي</SelectItem>
          <SelectItem value="ignore">تجاهل التشكيل</SelectItem>
          <SelectItem value="require">التزام التشكيل</SelectItem>
        </SelectContent>
      </Select>
    </div>
    {#if query}
      <Button
        aria-label="Clear"
        title="Clear"
        variant="outline"
        size="sm"
        onclick={() => {
          query = "";
          handle_query_input();
        }}
      >
        <XIcon />
      </Button>
    {/if}
  </div>
  {#if search_hint}
    <p class="text-sm text-muted-foreground" aria-live="polite">{search_hint}</p>
  {/if}
  {#if search_error}
    <p class="text-sm text-destructive">{search_error}</p>
  {/if}
</div>
