<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores';
  import { WEBUI_API_BASE_URL } from '$lib/constants';
  import { parseResume, selectProject, createSession } from '$lib/apis/wenqu';

  let resumeFile: File | null = null;
  let isUploading = false;
  let isParsing = false;
  let error = '';
  let step: 'upload' | 'parsing' | 'selecting' | 'ready' = 'upload';
  let parsed: any = null;
  let selectedProject: any = null;
  let scoredProjects: any[] = [];
  let sessionId = '';

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

      // Step 2: Parse resume using Wenqu engine (backend extracts text from PDF)
      isParsing = true;
      const parseResult = await parseResume($user.token, { file_id: fileData.id });

      if (!parseResult.projects || parseResult.projects.length === 0) {
        throw new Error('未能从简历中提取到科研项目，请确认简历内容');
      }

      parsed = parseResult;

      // Step 3: Select target project
      step = 'selecting';
      const selectResult = await selectProject($user.token, parsed.projects);
      selectedProject = selectResult.selected_project;
      scoredProjects = selectResult.all_scored;

      // Step 4: Create session
      const sessionResult = await createSession($user.token, {
        resume_text: `file_id:${fileData.id}`,
        project_title: selectedProject.title,
        project_description: selectedProject.description || ''
      });

      sessionId = sessionResult.session.id;
      step = 'ready';
    } catch (e: any) {
      error = e.message || '处理失败，请重试';
      step = 'upload';
    } finally {
      isUploading = false;
      isParsing = false;
    }
  }

  function startInterview() {
    if (!sessionId) return;
    goto(`/wenqu/interview?session=${sessionId}`);
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

    <!-- Text fallback -->
    <div class="mt-4 text-center">
      <button
        on:click={() => goto('/wenqu/interview')}
        class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        跳过上传，直接开始面试
      </button>
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

  <!-- Selecting progress -->
  {#if step === 'selecting'}
    <div class="text-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-600 dark:text-gray-300">正在分析项目风险...</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">识别最容易被导师深挖的项目</p>
    </div>
  {/if}

  <!-- Ready — show parsed results -->
  {#if step === 'ready' && selectedProject}
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="font-semibold text-gray-900 dark:text-white mb-3">已锁定高风险项目</h2>

      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
        <p class="font-medium text-red-800 dark:text-red-200">{selectedProject.title}</p>
        <p class="text-sm text-red-600 dark:text-red-300 mt-1">{selectedProject.description}</p>
      </div>

      <div class="mb-4">
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">所有项目风险评分：</p>
        <div class="space-y-2">
          {#each scoredProjects as sp}
            <div class="flex items-center justify-between text-sm bg-gray-50 dark:bg-gray-700/50 rounded px-3 py-2">
              <span class="text-gray-700 dark:text-gray-300">{sp.title}</span>
              <span class="font-mono {sp.risk_score >= 7 ? 'text-red-600' : sp.risk_score >= 4 ? 'text-yellow-600' : 'text-green-600'}">
                {sp.risk_score}/10
              </span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Extract projects count -->
      <p class="text-xs text-gray-400 dark:text-gray-500 mb-4">
        共提取 {parsed?.projects?.length ?? 0} 个科研项目
      </p>

      <button
        on:click={startInterview}
        class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        开始面试 — {selectedProject.title}
      </button>
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
