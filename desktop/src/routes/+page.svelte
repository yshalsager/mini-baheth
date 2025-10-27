<script lang="ts">
  import { onMount } from 'svelte';
  import { open } from '@tauri-apps/plugin-dialog';
  import { pyInvoke } from 'tauri-plugin-pytauri-api';

  let directories: string[] = [];
  let status = 'Loading recent directories...';
  let dataRoot = '';

  async function refreshDirectories(limit = 5) {
    try {
      const response = await pyInvoke<{ directories: string[] }>('list_directories', { limit: limit ?? undefined });
      directories = response.directories;
      status = directories.length ? 'Listing a few directories from the search root:' : 'No directories found.';
    } catch (error) {
      status = error instanceof Error ? error.message : String(error);
      directories = [];
    }
  }

  async function loadRootAndDirectories() {
    try {
      dataRoot = await pyInvoke<string>('get_data_root', {});
    } catch (error) {
      dataRoot = error instanceof Error ? error.message : String(error);
    }
    await refreshDirectories();
  }

  async function chooseRoot() {
    const selected = await open({ directory: true });
    if (!selected) {
      return;
    }
    const path = Array.isArray(selected) ? selected[0] : selected;
    try {
      dataRoot = await pyInvoke<string>('set_data_root', { path });
      await refreshDirectories();
    } catch (error) {
      status = error instanceof Error ? error.message : String(error);
    }
  }

  onMount(loadRootAndDirectories);
</script>

<main class="container">
  <h1>Mini Baheth Desktop</h1>

  <a href="https://pytauri.github.io/pytauri/latest/" target="_blank">
    <img src="/pytauri.svg" class="logo pytauri" alt="Pytauri logo" />
  </a>
  <div class="row">
    <a href="https://vitejs.dev" target="_blank">
      <img src="/vite.svg" class="logo vite" alt="Vite logo" />
    </a>
    <a href="https://tauri.app" target="_blank">
      <img src="/tauri.svg" class="logo tauri" alt="Tauri logo" />
    </a>
    <a href="https://svelte.dev/" target="_blank">
      <img src="/svelte.svg" class="logo svelte-kit" alt="Svelte logo" />
    </a>
    <a href="https://python.org" target="_blank">
      <img src="/python.svg" class="logo python" alt="Python logo" />
    </a>
  </div>
  <div class="controls">
    <p class="tagline">{status}</p>
    <p class="root">Current root: <span>{dataRoot}</span></p>
    <button class="chooser" on:click={chooseRoot}>Choose directory…</button>
  </div>
  {#if directories.length}
    <ul class="directory-list">
      {#each directories as dir}
        <li>{dir}</li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  .logo.vite:hover {
    filter: drop-shadow(0 0 2em #747bff);
  }

  .logo.python:hover {
    filter: drop-shadow(0 0 2em #7b661b);
  }

  .logo.tauri:hover {
    filter: drop-shadow(0 0 2em #24c8db);
  }

  .logo.pytauri:hover {
    filter: drop-shadow(0 0 2em #2294b2);
  }

  .logo.svelte-kit:hover {
    filter: drop-shadow(0 0 2em #ff3e00);
  }

  :root {
    font-family: Inter, Avenir, Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 24px;
    font-weight: 400;

    color: #0f0f0f;
    background-color: #f6f6f6;

    font-synthesis: none;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    -webkit-text-size-adjust: 100%;
  }

  .container {
    box-sizing: border-box;
    padding: 8px;
    height: 100vh;
    gap: 1em;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
  }

  .logo {
    will-change: filter;
    transition: 0.75s;

    &:not(.pytauri) {
      height: 3em;
    }

    &.pytauri {
      height: 6em;
    }
  }

  .row {
    display: flex;
    justify-content: center;

    &:has(a) {
      gap: 2em;
    }
  }

  a {
    font-weight: 500;
    color: #646cff;
    text-decoration: inherit;
  }

  a:hover {
    color: #535bf2;
  }

  h1 {
    text-align: center;
  }

  .controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
  }

  .tagline {
    margin-top: 0.5rem;
    font-size: 1.05rem;
    color: #3b3b3b;
  }

  .root {
    font-size: 0.9rem;
    color: #505050;
  }

  .root span {
    font-family: Menlo, Monaco, monospace;
  }

  .chooser {
    border-width: 0;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.95rem;
    font-weight: 500;
    background: linear-gradient(-45deg, #205f8a, #24c8db);
    color: white;
    cursor: pointer;
    transition: opacity 0.3s ease;
  }

  .chooser:hover {
    opacity: 0.85;
  }

  .directory-list {
    list-style: none;
    margin: 0.5rem auto 0;
    padding: 0;
    display: inline-flex;
    flex-direction: column;
    gap: 0.35rem;
    font-family: Menlo, Monaco, monospace;
    font-size: 0.95rem;
    background: rgba(255, 255, 255, 0.75);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  }
</style>
