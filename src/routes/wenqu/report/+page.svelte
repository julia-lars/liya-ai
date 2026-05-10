<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { user } from '$lib/stores';
  import { getSession, generateFeedback, getRounds, type FeedbackReport, type InterviewRound } from '$lib/apis/wenqu';
  import DOMPurify from 'dompurify';
  import { marked } from 'marked';

  $: sessionId = $page.url.searchParams.get('session') || '';

  let report: FeedbackReport | null = null;
  let rounds: InterviewRound[] = [];
  let projectTitle = '';
  let isLoading = true;
  let isRegenerating = false;
  let error = '';
  let isDownloading = false;

  $: renderedReport = report?.full_report
    ? DOMPurify.sanitize(marked.parse(report.full_report) as string)
    : '';

  function downloadPDF() {
    if (!report) return;
    isDownloading = true;

    const scoreRow = (label: string, score: number, color: string) =>
      `<div style="text-align:center;padding:12px;background:${color};border-radius:8px;">
        <div style="font-size:28px;font-weight:bold;color:#1f2937;">${score}</div>
        <div style="font-size:12px;color:#6b7280;margin-top:4px;">${label}</div>
      </div>`;

    const riskHtml = report.risk_flags?.length
      ? `<h3 style="margin:20px 0 10px;font-size:16px;">漏洞分析</h3>
         <ul>${report.risk_flags.map(f => `<li style="margin:4px 0;color:#4b5563;">${f}</li>`).join('')}</ul>`
      : '';

    const suggestHtml = report.improvement_suggestions?.length
      ? `<h3 style="margin:20px 0 10px;font-size:16px;">改进建议</h3>
         <ul>${report.improvement_suggestions.map(s => `<li style="margin:4px 0;color:#4b5563;">${s}</li>`).join('')}</ul>`
      : '';

    const fullHtml = marked.parse(report.full_report || '');
    const w = window.open('', '_blank');
    if (!w) { isDownloading = false; return; }
    w.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>面试反馈报告 - ${projectTitle}</title>
        <style>
          @page { margin: 20mm; }
          body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 14px; line-height: 1.8; color: #1f2937; padding: 20px; max-width: 800px; margin: 0 auto; }
          h1 { font-size: 22px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
          h2 { font-size: 18px; margin-top: 24px; }
          h3 { font-size: 16px; margin-top: 20px; }
          .scores { display: flex; gap: 12px; margin: 20px 0; justify-content: center; }
          .scores > div { flex: 1; max-width: 140px; }
          ul { padding-left: 20px; }
          li { margin: 4px 0; }
          pre { background: #f3f4f6; padding: 12px; border-radius: 6px; overflow-x: auto; }
          code { background: #f3f4f6; padding: 2px 4px; border-radius: 3px; font-size: 13px; }
          blockquote { border-left: 4px solid #3b82f6; margin: 12px 0; padding: 8px 16px; background: #f9fafb; color: #4b5563; }
          @media print { body { padding: 0; } .no-print { display: none; } }
        </style>
      </head>
      <body>
        <h1>面试反馈报告</h1>
        <p style="color:#6b7280;font-size:13px;">${projectTitle} · ${new Date().toLocaleDateString('zh-CN')}</p>
        <div class="scores">
          ${scoreRow('学术深度', report.academic_score, '#eff6ff')}
          ${scoreRow('表达清晰度', report.expression_score, '#f0fdf4')}
          ${scoreRow('真实性风险', report.authenticity_score, '#fef2f2')}
        </div>
        ${riskHtml}
        ${suggestHtml}
        <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;">
        ${fullHtml}
        <p class="no-print" style="text-align:center;margin-top:40px;color:#9ca3af;font-size:12px;">
          按 Ctrl+P 或 Cmd+P 保存为 PDF
        </p>
        <script>
          setTimeout(() => { window.print(); }, 300);
        <\/script>
      </body>
      </html>
    `);
    w.document.close();
    setTimeout(() => { isDownloading = false; }, 1000);
  }

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

      <!-- Full report (rendered Markdown) -->
      {#if report.full_report}
        <div>
          <h3 class="font-semibold text-gray-800 dark:text-gray-200 mb-3">详细报告</h3>
          <div class="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg text-sm text-gray-700 dark:text-gray-300 leading-relaxed prose dark:prose-invert max-w-none">
            {@html renderedReport}
          </div>
        </div>
      {/if}

      <!-- Action buttons -->
      <div class="mt-4 flex items-center justify-center gap-3">
        {#if report.academic_score === 0 && report.expression_score === 0}
          <button
            on:click={async () => {
              isRegenerating = true;
              try {
                const result = await generateFeedback($user.token, sessionId, true);
                report = result.report;
              } catch (e: any) {
                error = e.message || '重新生成失败';
              } finally {
                isRegenerating = false;
              }
            }}
            disabled={isRegenerating}
            class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRegenerating ? '生成中...' : '重新生成报告'}
          </button>
        {/if}
        <button
          on:click={downloadPDF}
          disabled={isDownloading || !report.full_report}
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm rounded-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isDownloading ? '生成中...' : '下载 PDF'}
        </button>
      </div>
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
