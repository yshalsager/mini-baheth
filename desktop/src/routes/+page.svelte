<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { pyInvoke } from "tauri-plugin-pytauri-api";

  let name = $state("");
  let greetMsg = $state("");

  async function greet(event: Event) {
    event.preventDefault();

    // Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
    const rsGreeting = await invoke<string>("greet", {
      name: name,
    });
    // Learn more about PyTauri commands at https://pytauri.github.io/pytauri/latest/usage/concepts/ipc/
    const pyGreeting = await pyInvoke<string>("greet", {
      name: name,
    });
    greetMsg = rsGreeting + "\n" + pyGreeting;

  }
</script>

<main class="container">
  <h1>Welcome to PyTauri</h1>

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
  <p>Click on any logo to learn more.</p>

  <form class="row" onsubmit={greet}>
    <input id="greet-input" placeholder="Enter a name..." bind:value={name} />
    <button type="submit">Greet</button>
  </form>
  <p id="greet-msg">{greetMsg}</p>
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

  input,
  button {
    border-radius: 8px;
    padding: 0.6em 1.2em;
    font-size: 1em;
    font-weight: 500;
    font-family: inherit;
    color: #0f0f0f;
    box-shadow: 0 2px 2px rgba(0, 0, 0, 0.2);
    outline: none;
  }

  input {
    background-color: #ffffff;
    border: 1px solid transparent;
  }

  button {
    border-width: 0;
    border-top: 2px solid color-mix(in oklab, white 50%, transparent);
    background: linear-gradient(-45deg, #205f8a, #24c8db);
    transition: opacity 0.5s ease;
    color: white;
  }

  button {
    cursor: pointer;

    &:hover {
      opacity: 70%;
    }

    &:active {
      opacity: 30%;

    }
  }

  #greet-input {
    margin-right: 5px;
  }

  #greet-msg {
    opacity: 50%;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      color: #f6f6f6;
      background-color: #1b1b1f;
    }

    input {
      color: #ffffff;
      background-color: #0f0f0f98;
    }
  }

</style>
