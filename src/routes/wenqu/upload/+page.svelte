<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores';
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  import { parseResume, selectProject, createSession } from '$lib/apis/wenqu';

  let resumeFile: File | null = null;
  let isUploading = false;
  let isParsing = false;
  let isCreatingSession = false;
  let error = '';
  let step: 'upload' | 'parsing' | 'selecting' | 'choose' = 'upload';
  let parsed: any = null;
  let scoredProjects: any[] = [];
  let selectedProject: any = null;

  async function handleFileSelected(e: Event) {
    const input = e.target as HTMLInputElement;
    if (!input.files?.length) return;
    resumeFile = input.files[0];
    error = '';
    await uploadAndParse();
  }

  async function uploadAndParse() {
    if (!resumeFile || !$user) return;

    isUploading = true;
    error = '';

    try {
      // Step 1: Upload file to liya-ai file system
      step = 'parsing';
      const formData = new FormData();
      formData.append('file', resumeFile);

      const uploadRes = await fetch(`${WEBUI_API_BASE_URL}/files/`, {
        method: 'POST',
        headers: { authorization: `Bearer ${$user.token}` },
        body: formData
      });
      if (!uploadRes.ok) throw new Error('文件上传失败');
      const fileData = await uploadRes.json();

      // Step 2: Parse resume
      isParsing = true;
      const parseResult = await parseResume($user.token, { file_id: fileData.id });

      if (!parseResult.projects || parseResult.projects.length === 0) {
        throw new Error('未能从简历中提取到科研项目，请确认简历内容');
      }

      parsed = parseResult;

      // Step 3: Score all projects
      step = 'selecting';
      const selectResult = await selectProject($user.token, parsed.projects);
      scoredProjects = selectResult.all_scored;

      // Step 4: Show top 3 for user to choose
      step = 'choose';
    } catch (e: any) {
      error = e.message || '处理失败，请重试';
      step = 'upload';
    } finally {
      isUploading = false;
      isParsing = false;
    }
  }

  async function handleProjectPick(project: any) {
    if (!$user || isCreatingSession) return;
    isCreatingSession = true;
    error = '';

    try {
      const sessionResult = await createSession($user.token, {
        resume_text: '',
        project_title: project.title,
        project_description: project.description || ''
      });
      goto(`/wenqu/interview?session=${sessionResult.session.id}`);
    } catch (e: any) {
      error = e.message || '创建面试失败';
      isCreatingSession = false;
    }
  }
</script>

<div class="max-w-2xl mx-auto">
  <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">上传简历</h1>

  <!-- Upload area -->
  {#if step === 'upload'}
    <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-10 text-center hover:border-blue-400 transition-colors">
      <label class="cursor-pointer block">
        <div class="mb-4 text-gray-400 dark:text-gray-500">
          <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p class="text-gray-600 dark:text-gray-300 mb-2">点击上传 PDF 简历</p>
        <p class="text-xs text-gray-400 dark:text-gray-500">支持 PDF 格式</p>
        <input type="file" accept=".pdf" class="hidden" on:change={handleFileSelected} />
      </label>
    </div>

  {/if}

  <!-- Parsing progress -->
  {#if step === 'parsing'}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600 dark:text-gray-300">正在解析简历...</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">提取科研项目信息</p>
    </div>
  {/if}

  <!-- Scoring progress -->
  {#if step === 'selecting'}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600 dark:text-gray-300">正在分析项目风险...</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">识别最容易被导师深挖的项目</p>
    </div>
  {/if}

  <!-- Choose project — top 3 highlighted -->
  {#if step === 'choose'}
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="font-semibold text-gray-900 dark:text-white mb-1">选择模拟面试项目</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        共提取 {parsed?.projects?.length ?? 0} 个科研项目，以下为风险评分最高的 3 个项目（越容易被导师深挖）
      </p>

      <!-- Top 3 pickers -->
      <div class="space-y-3 mb-6">
        {#each scoredProjects.slice(0, 3) as sp, i}
          <button
            on:click={() => handleProjectPick(sp)}
            disabled={isCreatingSession}
            class="w-full text-left bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 rounded-lg p-4 transition-colors disabled:opacity-50"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-mono font-bold text-white bg-blue-600 rounded-full w-5 h-5 flex items-center justify-center shrink-0">
                    {i + 1}
                  </span>
                  <span class="font-medium text-gray-900 dark:text-white truncate">{sp.title}</span>
                </div>
                {#if sp.reason}
                  <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1">{sp.reason}</p>
                {/if}
              </div>
              <span class="font-mono text-lg font-bold shrink-0 ml-3 {sp.risk_score >= 7 ? 'text-red-500' : sp.risk_score >= 4 ? 'text-yellow-500' : 'text-green-500'}">
                {sp.risk_score}/10
              </span>
            </div>
          </button>
        {/each}
      </div>

      <!-- Other projects (collapsed) -->
      {#if scoredProjects.length > 3}
        <details class="mb-4">
          <summary class="text-sm text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200">
            其他 {scoredProjects.length - 3} 个项目
          </summary>
          <div class="mt-2 space-y-1">
            {#each scoredProjects.slice(3) as sp}
              <button
                on:click={() => handleProjectPick(sp)}
                disabled={isCreatingSession}
                class="w-full text-left flex items-center justify-between px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700/50 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <span class="text-gray-700 dark:text-gray-300 truncate">{sp.title}</span>
                <span class="font-mono shrink-0 ml-2 {sp.risk_score >= 7 ? 'text-red-500' : sp.risk_score >= 4 ? 'text-yellow-500' : 'text-green-500'}">
                  {sp.risk_score}/10
                </span>
              </button>
            {/each}
          </div>
        </details>
      {/if}

      {#if isCreatingSession}
        <div class="text-center text-sm text-gray-400 dark:text-gray-500">创建面试中...</div>
      {/if}
    </div>
  {/if}

  <!-- Error -->
  {#if error}
    <div class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-200">
      {error}
      <button on:click={() => { step = 'upload'; error = ''; }} class="ml-2 underline">重试</button>
    </div>
  {/if}
</div>
