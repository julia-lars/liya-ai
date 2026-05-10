<script lang="ts">
  import { goto } from '$app/navigation';
</script>

<div class="flex flex-col items-center justify-center min-h-[70vh] text-center px-4">
  <!-- Hero -->
  <div class="mb-8">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-3">
      问渠
    </h1>
    <p class="text-lg text-gray-500 dark:text-gray-400 mb-1">
      AI 保研复试学术面试官
    </p>
    <p class="text-sm text-gray-400 dark:text-gray-500">
      问渠那得清如许，为有源头活水来。
    </p>
  </div>

  <!-- Value proposition -->
  <div class="max-w-xl mb-10 text-left">
    <div class="grid gap-4">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <h3 class="font-medium text-gray-900 dark:text-white mb-1">🎓 科研真实性审查</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">模拟严苛导师，验证你的项目经历真实性</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <h3 class="font-medium text-gray-900 dark:text-white mb-1">🔍 连续追问式压力测试</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">3-5 轮"剥洋葱式"深挖，暴露逻辑漏洞</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <h3 class="font-medium text-gray-900 dark:text-white mb-1">📊 多维度反馈报告</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">学术深度、表达清晰度、真实性风险三维评分</p>
      </div>
    </div>
  </div>

  <!-- CTA -->
  <button
    on:click={() => goto('/wenqu/upload')}
    class="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm"
  >
    开始模拟面试
  </button>

  <!-- Footer note -->
  <p class="mt-8 text-xs text-gray-400 dark:text-gray-600">
    专注于计算机系保研复试场景 · 建议使用脱敏简历
  </p>
</div>
