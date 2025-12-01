<script>
  import "../app.css";
  import { ModeWatcher } from "mode-watcher";
  import { Toaster } from "$lib/components/ui/sonner";
  import { loadLocale } from "wuchale/load-utils";
  import "../locales/main.loader.svelte.js";

  let { children } = $props();
  let locale = $state("ar");
</script>

<ModeWatcher />
{#await loadLocale(locale)}
  <!-- Loading translations -->
{:then}
  <div dir="rtl">
    {@render children()}
  </div>
  <Toaster richColors expand />
{/await}
