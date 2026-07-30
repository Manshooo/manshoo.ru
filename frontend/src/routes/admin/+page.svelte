<script lang="ts">
	import { api, ApiError } from '$lib/admin/client';
	import { formatPeriod } from '$lib/format';
	import type { ProjectDetail } from '$lib/types';

	let projects = $state<ProjectDetail[]>([]);
	let error = $state('');
	let loading = $state(true);

	$effect(() => {
		api
			.listProjects()
			.then((list) => (projects = list))
			.catch((e) => (error = e instanceof ApiError ? e.message : 'Не удалось загрузить'))
			.finally(() => (loading = false));
	});

	async function togglePublished(project: ProjectDetail) {
		const next = !project.is_published;
		try {
			const updated = await api.updateProject(project.id, { ...project, is_published: next });
			projects = projects.map((p) => (p.id === updated.id ? updated : p));
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'Не удалось сохранить';
		}
	}
</script>

<header class="head">
	<h1>Проекты</h1>
	<a class="button" href="/admin/projects/new">Добавить проект</a>
</header>

{#if error}
	<p class="error">{error}</p>
{/if}

{#if loading}
	<p class="muted">Загружаем…</p>
{:else if projects.length === 0}
	<p class="muted">Пока пусто. Самое время добавить первый проект.</p>
{:else}
	<ul class="list">
		{#each projects as project (project.id)}
			<li>
				<div class="main">
					<a href={`/admin/projects/${project.id}`} class="title">{project.title}</a>
					<span class="tagline">{project.tagline}</span>
					<span class="meta">
						{formatPeriod(project.period_start, project.period_end)}
						{#if project.is_featured}· закреплён{/if}
					</span>
				</div>
				<div class="actions">
					<span class="badge" class:published={project.is_published}>
						{project.is_published ? 'опубликован' : 'черновик'}
					</span>
					<button type="button" onclick={() => togglePublished(project)}>
						{project.is_published ? 'Снять' : 'Опубликовать'}
					</button>
					<a
						href={`/projects/${project.slug}${project.is_published ? '' : '?preview=1'}`}
						target="_blank"
						rel="noopener"
					>
						Смотреть ↗
					</a>
				</div>
			</li>
		{/each}
	</ul>
{/if}

<style>
	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	h1 {
		margin: 0;
		font-size: 1.5rem;
	}
	.button {
		border: 1px solid var(--accent);
		background: var(--accent);
		color: #fff;
		border-radius: 6px;
		padding: 0.35rem 0.9rem;
	}
	.button:hover {
		text-decoration: none;
		opacity: 0.9;
	}
	.list {
		list-style: none;
		padding: 0;
		margin: 1.5rem 0 0;
		display: grid;
		gap: 0.75rem;
	}
	.list li {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 1rem;
		align-items: center;
		justify-content: space-between;
		border: 1px solid var(--border);
		background: var(--card);
		border-radius: 10px;
		padding: 0.75rem 1rem;
	}
	.main {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		min-width: 14rem;
	}
	.title {
		font-weight: 600;
	}
	.tagline,
	.meta {
		color: var(--muted);
		font-size: 0.85rem;
	}
	.actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.9rem;
	}
	.badge {
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 0.05rem 0.6rem;
		font-size: 0.78rem;
		color: var(--muted);
	}
	.badge.published {
		color: #16a34a;
		border-color: color-mix(in srgb, #16a34a 40%, transparent);
	}
	button {
		font: inherit;
		font-size: 0.9rem;
		border: 1px solid var(--border);
		background: var(--bg);
		color: inherit;
		border-radius: 6px;
		padding: 0.2rem 0.7rem;
		cursor: pointer;
	}
	button:hover {
		border-color: var(--accent);
	}
	.muted {
		color: var(--muted);
	}
	.error {
		color: #dc2626;
	}
</style>
