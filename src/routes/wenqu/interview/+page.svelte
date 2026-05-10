<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { user } from '$lib/stores';

  import {
    getSession,
    startInterview,
    submitAnswer,
    getRounds,
    generateFeedback,
    type InterviewRound
  } from '$lib/apis/wenqu';

  // Parse session ID from URL
  $: sessionId = $page.url.searchParams.get('session') || '';
  // Allow direct start without session (skip resume upload)
  $: directMode = !sessionId;

  let projectTitle = '';
  let projectDesc = '';
  let isLoading = true;
  let isSubmitting = false;
  let error = '';
  let currentRound: InterviewRound | null = null;
  let previousRounds: InterviewRound[] = [];
  let answerText = '';
  let interviewComplete = false;
  let feedbackReport: any = null;
  let isGeneratingFeedback = false;
  let scrollContainer: HTMLDivElement;

  function scrollToBottom() {
    if (scrollContainer) {
      setTimeout(() => {
        scrollContainer.scrollTo({ top: scrollContainer.scrollHeight, behavior: 'smooth' });
      }, 50);
    }
  }

  // Auto-scroll after each render that adds content
  $: if (previousRounds.length || currentRound || interviewComplete || feedbackReport) {
    scrollToBottom();
  }

  onMount(async () => {
    if (!sessionId || !$user) {
      if (!$user) {
        goto('/auth?redirect=/wenqu');
        return;
      }
      // Direct mode — show instruction
      isLoading = false;
      return;
    }

    try {
      // Load session info
      const session = await getSession($user.token, sessionId);
      projectTitle = session.project_title || '';
      projectDesc = session.project_description || '';

      // Check if interview already in progress
      const rounds = await getRounds($user.token, sessionId);
      if (rounds.length > 0) {
        previousRounds = rounds.slice(0, -1);
        const last = rounds[rounds.length - 1];
        if (last.answer === null) {
          currentRound = last;
        } else {
          currentRound = last;
          interviewComplete = true;
        }
      } else {
        // Start fresh interview
        const result = await startInterview($user.token, sessionId);
        currentRound = result.round;
      }
    } catch (e: any) {
      error = e.message || '加载面试失败';
    } finally {
      isLoading = false;
    }
  });

  async function handleSubmit() {
    if (!answerText.trim() || !currentRound || !$user) return;

    isSubmitting = true;
    error = '';

    try {
      const result = await submitAnswer($user.token, sessionId, answerText);

      if (result.interview_complete) {
        interviewComplete = true;
        currentRound = null;
      } else {
        // Add previous round to history
        const oldRound = await getRounds($user.token, sessionId);
        previousRounds = oldRound.slice(0, -1);
        currentRound = result.round;
      }

      answerText = '';
    } catch (e: any) {
      error = e.message || '提交失败';
    } finally {
      isSubmitting = false;
    }
  }

  async function handleGenerateReport() {
    if (!$user) return;
    isGeneratingFeedback = true;
    try {
      const result = await generateFeedback($user.token, sessionId);
      feedbackReport = result.report;
    } catch (e: any) {
      error = e.message || '生成报告失败';
    } finally {
      isGeneratingFeedback = false;
    }
  }

  function handleSubmitOnEnter(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }
</script>

<div bind:this={scrollContainer} class="max-w-3xl mx-auto">
  {#if isLoading}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-500 dark:text-gray-400">加载面试...</p>
    </div>

  {:else if directMode}
    <!-- Direct entry mode without resume -->
    <div class="text-center py-12">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">准备开始面试</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        请先上传简历，以便 AI 导师针对你的科研项目进行深度追问。
      </p>
      <button
        on:click={() => goto('/wenqu/upload')}
        class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        上传简历
      </button>
    </div>

  {:else if feedbackReport}
    <!-- Show report inline -->
    <div class="prose dark:prose-invert max-w-none">
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">面试反馈报告</h2>

        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p class="text-2xl font-bold text-blue-600 dark:text-blue-400">{feedbackReport.academic_score}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">学术深度</p>
          </div>
          <div class="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p class="text-2xl font-bold text-green-600 dark:text-green-400">{feedbackReport.expression_score}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">表达清晰度</p>
          </div>
          <div class="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p class="text-2xl font-bold text-red-600 dark:text-red-400">{feedbackReport.authenticity_score}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">真实性风险</p>
          </div>
        </div>

        {#if feedbackReport.risk_flags?.length}
          <div class="mb-4">
            <h3 class="font-semibold text-gray-800 dark:text-gray-200 mb-2">漏洞分析</h3>
            <ul class="list-disc list-inside space-y-1">
              {#each feedbackReport.risk_flags as flag}
                <li class="text-sm text-gray-600 dark:text-gray-300">{flag}</li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if feedbackReport.improvement_suggestions?.length}
          <div class="mb-4">
            <h3 class="font-semibold text-gray-800 dark:text-gray-200 mb-2">改进建议</h3>
            <ul class="list-disc list-inside space-y-1">
              {#each feedbackReport.improvement_suggestions as suggestion}
                <li class="text-sm text-gray-600 dark:text-gray-300">{suggestion}</li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if feedbackReport.full_report}
          <div class="mt-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {feedbackReport.full_report}
          </div>
        {/if}
      </div>

      <button
        on:click={() => goto('/wenqu')}
        class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
      >
        返回首页
      </button>
    </div>

  {:else if interviewComplete}
    <!-- Interview complete -->
    <div class="text-center py-8">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">面试完成</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-6">共进行了 {previousRounds.length + 1} 轮追问</p>

      {#each previousRounds as round, i}
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-3 text-left">
          <div class="flex items-start gap-3">
            <span class="text-xs font-mono text-gray-400 dark:text-gray-500 mt-1">Q{i + 1}</span>
            <div class="flex-1">
              <p class="text-sm text-gray-800 dark:text-gray-200 mb-2">{round.question}</p>
              {#if round.answer}
                <p class="text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded p-2">
                  {round.answer}
                </p>
              {/if}
            </div>
          </div>
        </div>
      {/each}

      <button
        on:click={handleGenerateReport}
        disabled={isGeneratingFeedback}
        class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isGeneratingFeedback ? '生成报告中...' : '查看反馈报告'}
      </button>
    </div>

  {:else}
    <!-- Active interview -->
    <div>
      <div class="mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{projectTitle}</h2>
        <p class="text-xs text-gray-400 dark:text-gray-500">
          第 {previousRounds.length + 1} 轮 / 共 5 轮
        </p>
      </div>

      <!-- Previous rounds -->
      {#each previousRounds as round, i}
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-3">
          <p class="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">导师提问 #{i + 1}</p>
          <p class="text-sm text-gray-800 dark:text-gray-200 mb-2">{round.question}</p>
          <p class="text-xs font-medium text-green-600 dark:text-green-400 mb-1">你的回答</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">{round.answer}</p>
        </div>
      {/each}

      <!-- Current question -->
      {#if currentRound}
        <div class="bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
          <p class="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">导师提问 #{previousRounds.length + 1}</p>
          <p class="text-sm text-gray-800 dark:text-gray-200 mb-4">{currentRound.question}</p>

          <textarea
            bind:value={answerText}
            on:keydown={handleSubmitOnEnter}
            placeholder="输入你的回答..."
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          ></textarea>

          <div class="flex items-center justify-between mt-3">
            <span class="text-xs text-gray-400 dark:text-gray-500">Enter 发送 · Shift+Enter 换行</span>
            <button
              on:click={handleSubmit}
              disabled={isSubmitting || !answerText.trim()}
              class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? '提交中...' : '提交回答'}
            </button>
          </div>
        </div>
      {/if}

      {#if error}
        <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-200 mb-4">
          {error}
        </div>
      {/if}
    </div>
  {/if}
</div>
