<script lang="ts">
  import { page } from '$app/stores';
  import { user, WEBUI_NAME, config } from '$lib/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  let mounted = false;
  onMount(() => { mounted = true; });
</script>

<div class="wenqu-layout h-screen max-h-[100dvh] flex flex-col bg-gray-50 dark:bg-gray-900">
  <!-- Top navigation -->
  <nav class="shrink-0 sticky top-0 z-40 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <a href="/wenqu" class="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
          问渠
        </a>
        <span class="text-sm text-gray-400 dark:text-gray-500">|</span>
        <span class="text-sm text-gray-500 dark:text-gray-400">AI 保研学术面试官</span>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <a href="/wenqu/history" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">历史记录</a>
        <a href="/wenqu/upload" class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">开始面试</a>
        {#if $user}
          <a href="/" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">返回聊天</a>
        {/if}
      </div>
    </div>
  </nav>

  <!-- Page content — scrollable area -->
  <main class="flex-1 overflow-y-auto">
    <div class="max-w-5xl mx-auto px-4 py-8">
      <slot />
    </div>
  </main>
</div>
