<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { user } from '$lib/stores';
  import { getSession, generateFeedback, getRounds, type FeedbackReport, type InterviewRound } from '$lib/apis/wenqu';

  $: sessionId = $page.url.searchParams.get('session') || '';

  let report: FeedbackReport | null = null;
  let rounds: InterviewRound[] = [];
  let projectTitle = '';
  let isLoading = true;
  let error = '';

  onMount(async () => {
    if (!sessionId || !$user) {
      error = '缺少面试会话 ID';
      isLoading = false;
      return;
    }

    try {
      const session = await getSession($user.token, sessionId);
      projectTitle = session.project_title || '';

      const [reportResult, roundsResult] = await Promise.all([
        generateFeedback($user.token, sessionId),
        getRounds($user.token, sessionId)
      ]);

      report = reportResult.report;
      rounds = roundsResult;
    } catch (e: any) {
      error = e.message || '加载报告失败';
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="max-w-3xl mx-auto">
  <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">面试反馈报告</h1>
  <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
    {projectTitle || '项目'} · 共 {rounds.length} 轮追问
  </p>

  {#if isLoading}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-500 dark:text-gray-400">生成报告...</p>
    </div>

  {:else if error}
    <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-200">
      {error}
    </div>

  {:else if report}
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <!-- Scores -->
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">综合评分</h2>
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <p class="text-3xl font-bold text-blue-600 dark:text-blue-400">{report.academic_score}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">学术深度</p>
        </div>
        <div class="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <p class="text-3xl font-bold text-green-600 dark:text-green-400">{report.expression_score}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">表达清晰度</p>
        </div>
        <div class="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <p class="text-3xl font-bold text-red-600 dark:text-red-400">{report.authenticity_score}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">真实性风险</p>
        </div>
      </div>

      <!-- Risk analysis -->
      {#if report.risk_flags?.length}
        <div class="mb-6">
          <h3 class="font-semibold text-gray-800 dark:text-gray-200 mb-3">漏洞分析</h3>
          <ul class="space-y-2">
            {#each report.risk_flags as flag}
              <li class="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                <span class="text-red-500 mt-0.5">•</span>
                {flag}
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      <!-- Improvement suggestions -->
      {#if report.improvement_suggestions?.length}
        <div class="mb-6">
          <h3 class="font-semibold text-gray-800 dark:text-gray-200 mb-3">改进建议</h3>
          <ul class="space-y-2">
            {#each report.improvement_suggestions as suggestion}
              <li class="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                <span class="text-green-500 mt-0.5">→</span>
                {suggestion}
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      <!-- Full report -->
      {#if report.full_report}
        <div>
          <h3 class="font-semibold text-gray-800 dark:text-gray-200 mb-3">详细报告</h3>
          <div class="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {report.full_report}
          </div>
        </div>
      {/if}
    </div>

    <!-- Interview history -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">面试记录</h2>
      {#each rounds as round, i}
        <div class="mb-4 pb-4 border-b border-gray-100 dark:border-gray-700 last:border-0 last:mb-0 last:pb-0">
          <p class="text-xs font-mono text-gray-400 dark:text-gray-500 mb-1">第 {i + 1} 轮</p>
          <p class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Q: {round.question}</p>
          {#if round.answer}
            <p class="text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded p-2 mt-1">A: {round.answer}</p>
          {/if}
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-gray-500 dark:text-gray-400">未找到报告。</p>
  {/if}
</div>
