<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores';
  import { getSessions, getRounds, type WenquSession } from '$lib/apis/wenqu';

  let sessions: WenquSession[] = [];
  let roundCounts: Record<string, number> = {};
  let isLoading = true;
  let error = '';

  onMount(async () => {
    if (!$user) {
      goto('/auth?redirect=/wenqu/history');
      return;
    }

    try {
      const all = await getSessions($user.token);
      sessions = all.filter(s => s.status === 'completed');

      // Fetch round counts for each session
      await Promise.all(
        sessions.map(async (s) => {
          try {
            const rounds = await getRounds($user.token, s.id);
            roundCounts[s.id] = rounds.length;
          } catch {
            roundCounts[s.id] = 0;
          }
        })
      );
    } catch (e: any) {
      error = e.message || '加载失败';
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="max-w-3xl mx-auto">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">历史面试</h1>
    <button
      on:click={() => goto('/wenqu/upload')}
      class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700 transition-colors"
    >
      新的面试
    </button>
  </div>

  {#if isLoading}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-500 dark:text-gray-400">加载中...</p>
    </div>

  {:else if error}
    <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-200">
      {error}
    </div>

  {:else if sessions.length === 0}
    <div class="text-center py-16 text-gray-400 dark:text-gray-500">
      <p class="text-lg mb-2">暂无完成的面试记录</p>
      <p class="text-sm mb-4">完成一次模拟面试后，记录会显示在这里</p>
      <button
        on:click={() => goto('/wenqu/upload')}
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        开始第一次面试
      </button>
    </div>

  {:else}
    <div class="space-y-3">
      {#each sessions as session}
        <div
          on:click={() => goto(`/wenqu/report?session=${session.id}`)}
          class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="font-medium text-gray-900 dark:text-white truncate">
                {session.project_title || '未命名项目'}
              </h3>
              {#if session.project_description}
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                  {session.project_description}
                </p>
              {/if}
            </div>
            <div class="flex items-center gap-3 ml-4 shrink-0">
              <span class="text-xs text-gray-400 dark:text-gray-500">
                {roundCounts[session.id] ?? '?'} 轮
              </span>
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
          <div class="flex items-center gap-2 mt-2">
            <span class="text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded">已完成</span>
            <span class="text-xs text-gray-400 dark:text-gray-500">
              {new Date(session.created_at * 1000).toLocaleString('zh-CN')}
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
