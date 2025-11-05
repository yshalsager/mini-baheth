<script>
  import "../app.css";
  import { ModeWatcher } from "mode-watcher";
  import { Toaster } from "$lib/components/ui/sonner";
  let { children } = $props();
</script>

<ModeWatcher />
<div dir="rtl">
  {@render children()}
</div>
<Toaster richColors expand />
