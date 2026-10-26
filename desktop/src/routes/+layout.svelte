<script lang="ts">
  import "../app.css";
  import { ModeWatcher } from "mode-watcher";
  import { Toaster } from "#lib/components/ui/sonner/index.js";
  import { onMount } from "svelte";
  import { init_locale } from "#lib/stores/locale.js";

  let { children } = $props();

  onMount(() => {
    void init_locale();
  });
</script>

<ModeWatcher />
<div>
  {@render children()}
</div>
<Toaster richColors expand />
