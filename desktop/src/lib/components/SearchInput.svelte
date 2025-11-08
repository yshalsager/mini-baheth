<script lang="ts">
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import { Button } from '$lib/components/ui/button'
  import { Toggle } from '$lib/components/ui/toggle'
  import RegexIcon from '@lucide/svelte/icons/regex'
  import XIcon from '@lucide/svelte/icons/x'

  let {
    query = $bindable(""),
    search_hint = "",
    search_error = "",
    handle_query_input,
    regex = $bindable(false),
  on_enter,
  }: {
    query?: string;
    search_hint?: string;
    search_error?: string;
    handle_query_input: () => void;
    regex?: boolean;
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
    <Toggle
      aria-label="Regex"
      title="Regex"
      bind:pressed={regex}
      onclick={handle_query_input}
      class="h-9 min-w-9"
    >
      <RegexIcon />
    </Toggle>
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
