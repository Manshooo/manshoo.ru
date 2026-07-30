<script lang="ts">
	import { page } from '$app/state';
	import ProjectForm from '$lib/admin/ProjectForm.svelte';
	import { api, ApiError } from '$lib/admin/client';
	import type { ProjectDetail } from '$lib/types';

	let project = $state<ProjectDetail | null>(null);
	let error = $state('');

	$effect(() => {
		const id = Number(page.params.id);
		api
			.getProject(id)
			.then((p) => (project = p))
			.catch((e) => (error = e instanceof ApiError ? e.message : 'Проект не найден'));
	});
</script>

{#if error}
	<p class="error">{error}</p>
{:else if project}
	<h1>{project.title}</h1>
	<!-- key: при переходе между проектами форма пересобирается с новыми данными -->
	{#key project.id}
		<ProjectForm {project} />
	{/key}
{:else}
	<p class="muted">Загружаем…</p>
{/if}

<style>
	h1 {
		font-size: 1.5rem;
		margin: 0 0 1.5rem;
	}
	.muted {
		color: var(--muted);
	}
	.error {
		color: #dc2626;
	}
</style>
