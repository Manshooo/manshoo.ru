<script lang="ts">
	import ListInput from '$lib/admin/ListInput.svelte';
	import { api, ApiError } from '$lib/admin/client';
	import { renderMarkdown } from '$lib/markdown';
	import type { ProjectDetail } from '$lib/types';
	import { goto } from '$app/navigation';

	let { project = null }: { project?: ProjectDetail | null } = $props();

	// Форма — снимок проекта: поля дальше живут своей жизнью, пока их правят.
	// Родитель пересоздаёт компонент через {#key project.id}, поэтому следить
	// за изменениями пропса не нужно.
	// svelte-ignore state_referenced_locally
	const initial = project;

	// Порядок полей = порядок мыслей: что это → как было → чем горжусь → оформление
	let title = $state(initial?.title ?? '');
	let tagline = $state(initial?.tagline ?? '');
	let slug = $state(initial?.slug ?? '');
	let projectType = $state(initial?.project_type ?? 'pet');
	let status = $state(initial?.status ?? 'active');
	let role = $state(initial?.role ?? '');
	let org = $state(initial?.org ?? '');
	let periodStart = $state(initial?.period_start ?? new Date().toISOString().slice(0, 10));
	let periodEnd = $state(initial?.period_end ?? '');
	let ongoing = $state(!initial?.period_end);
	let descriptionMd = $state(initial?.description_md ?? '');
	let stack = $state<string[]>(initial?.stack ?? []);
	let highlights = $state<string[]>(initial?.highlights ?? []);
	let linkLive = $state(initial?.links?.live ?? '');
	let linkRepo = $state(initial?.links?.repo ?? '');
	let linkCase = $state(initial?.links?.case ?? '');
	let uptimeSlug = $state(initial?.uptime_monitor_slug ?? '');
	let isPublished = $state(initial?.is_published ?? false);
	let isFeatured = $state(initial?.is_featured ?? false);
	let sortOrder = $state(initial?.sort_order ?? 0);
	let coverUrl = $state(initial?.cover_url ?? null);

	let showPreview = $state(false);
	let error = $state('');
	let saving = $state(false);
	let uploading = $state(false);

	function payload() {
		const links: Record<string, string> = {};
		if (linkLive) links.live = linkLive;
		if (linkRepo) links.repo = linkRepo;
		if (linkCase) links.case = linkCase;
		return {
			title,
			tagline,
			slug,
			description_md: descriptionMd,
			role,
			org,
			project_type: projectType,
			status,
			period_start: periodStart,
			period_end: ongoing || !periodEnd ? null : periodEnd,
			stack,
			highlights,
			links,
			is_published: isPublished,
			is_featured: isFeatured,
			sort_order: sortOrder,
			uptime_monitor_slug: uptimeSlug
		};
	}

	async function save(event: SubmitEvent) {
		event.preventDefault();
		saving = true;
		error = '';
		try {
			const saved = project
				? await api.updateProject(project.id, payload())
				: await api.createProject(payload());
			goto(`/admin/projects/${saved.id}`, { invalidateAll: true });
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'Не удалось сохранить';
		} finally {
			saving = false;
		}
	}

	async function uploadCover(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file || !project) return;
		uploading = true;
		error = '';
		try {
			const updated = await api.uploadCover(project.id, file);
			coverUrl = updated.cover_url;
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'Не удалось загрузить обложку';
		} finally {
			uploading = false;
			input.value = '';
		}
	}

	async function removeCover() {
		if (!project) return;
		coverUrl = (await api.deleteCover(project.id)).cover_url;
	}

	async function remove() {
		if (!project || !confirm(`Удалить проект «${project.title}»? Отменить будет нельзя.`)) return;
		await api.deleteProject(project.id);
		goto('/admin', { invalidateAll: true });
	}
</script>

<form onsubmit={save}>
	<section>
		<h2>Что это</h2>
		<label>
			Название
			<input bind:value={title} required />
		</label>
		<label>
			Одной строкой
			<input bind:value={tagline} required placeholder="Чем этот проект интересен" />
		</label>
		<label>
			Slug (пусто — соберётся из названия)
			<input bind:value={slug} placeholder="my-project" />
		</label>
		<div class="row">
			<label>
				Тип
				<select bind:value={projectType}>
					<option value="pet">пет-проект</option>
					<option value="work">работа</option>
					<option value="oss">open source</option>
					<option value="freelance">фриланс</option>
				</select>
			</label>
			<label>
				Статус
				<select bind:value={status}>
					<option value="active">живой</option>
					<option value="wip">в разработке</option>
					<option value="archived">архив</option>
				</select>
			</label>
		</div>
	</section>

	<section>
		<h2>Резюме-контекст</h2>
		<div class="row">
			<label>
				Роль
				<input bind:value={role} placeholder="Backend-разработчик" />
			</label>
			<label>
				Компания / контекст
				<input bind:value={org} placeholder="пет-проект" />
			</label>
		</div>
		<div class="row">
			<label>
				Начало
				<input type="date" bind:value={periodStart} required />
			</label>
			<label>
				Конец
				<input type="date" bind:value={periodEnd} disabled={ongoing} />
			</label>
		</div>
		<label class="check">
			<input type="checkbox" bind:checked={ongoing} />
			по настоящее время
		</label>
	</section>

	<section>
		<h2>Суть</h2>
		<label>
			<span class="label-row">
				Описание (Markdown)
				<button type="button" class="link" onclick={() => (showPreview = !showPreview)}>
					{showPreview ? 'скрыть превью' : 'показать превью'}
				</button>
			</span>
			<textarea bind:value={descriptionMd} rows="10"></textarea>
		</label>
		{#if showPreview}
			<!-- eslint-disable-next-line svelte/no-at-html-tags -- превью своего же текста -->
			<div class="preview">{@html renderMarkdown(descriptionMd)}</div>
		{/if}

		<ListInput bind:items={stack} label="Стек" placeholder="Go, PostgreSQL…" />
		<ListInput
			bind:items={highlights}
			label="Ключевые фишки"
			placeholder="Чем горжусь, цифры, сложности"
			multiline
		/>
	</section>

	<section>
		<h2>Ссылки и оформление</h2>
		<label>
			Живой проект
			<input bind:value={linkLive} placeholder="https://example.com" />
		</label>
		<label>
			Репозиторий
			<input bind:value={linkRepo} placeholder="https://github.com/…" />
		</label>
		<label>
			Кейс / статья
			<input bind:value={linkCase} />
		</label>
		<label>
			Монитор uptime (slug из uptime/config.yaml)
			<input bind:value={uptimeSlug} placeholder="azzb" />
		</label>

		<div class="cover">
			<span class="cover-label">Обложка</span>
			{#if !project}
				<p class="muted">Сохраните проект — потом можно будет загрузить обложку.</p>
			{:else}
				{#if coverUrl}
					<img src={coverUrl} alt="Обложка проекта" />
				{/if}
				<div class="cover-actions">
					<input type="file" accept="image/*" onchange={uploadCover} disabled={uploading} />
					{#if coverUrl}
						<button type="button" onclick={removeCover}>Удалить обложку</button>
					{/if}
				</div>
				{#if uploading}<p class="muted">Загружаем…</p>{/if}
			{/if}
		</div>
	</section>

	<section>
		<h2>Публикация</h2>
		<label class="check">
			<input type="checkbox" bind:checked={isPublished} />
			опубликован
		</label>
		<label class="check">
			<input type="checkbox" bind:checked={isFeatured} />
			закреплён вверху
		</label>
		<label class="narrow">
			Порядок
			<input type="number" bind:value={sortOrder} />
		</label>
	</section>

	{#if error}
		<p class="error">{error}</p>
	{/if}

	<div class="actions">
		<button type="submit" class="primary" disabled={saving}>
			{saving ? 'Сохраняем…' : 'Сохранить'}
		</button>
		{#if project}
			<a
				class="secondary"
				href={`/projects/${project.slug}${isPublished ? '' : '?preview=1'}`}
				target="_blank"
				rel="noopener"
			>
				Предпросмотр ↗
			</a>
			<button type="button" class="danger" onclick={remove}>Удалить</button>
		{/if}
		<a class="secondary" href="/admin">Назад к списку</a>
	</div>
</form>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	section {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}
	h2 {
		margin: 0;
		font-size: 1.05rem;
		color: var(--muted);
		font-weight: 600;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.9rem;
		color: var(--muted);
	}
	label.check {
		flex-direction: row;
		align-items: center;
		gap: 0.5rem;
	}
	label.narrow input {
		max-width: 8rem;
	}
	.label-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}
	.row {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	.row label {
		flex: 1;
		min-width: 12rem;
	}
	input,
	select,
	textarea {
		font: inherit;
		color: inherit;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 0.4rem 0.6rem;
		resize: vertical;
	}
	input[type='checkbox'] {
		width: auto;
	}
	.preview {
		border: 1px dashed var(--border);
		border-radius: 8px;
		padding: 0.5rem 1rem;
		background: var(--card);
	}
	.cover {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.cover-label {
		font-size: 0.9rem;
		color: var(--muted);
	}
	.cover img {
		max-width: 100%;
		border-radius: 8px;
		border: 1px solid var(--border);
	}
	.cover-actions {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		flex-wrap: wrap;
	}
	.actions {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		flex-wrap: wrap;
		border-top: 1px solid var(--border);
		padding-top: 1.25rem;
	}
	button,
	.secondary {
		font: inherit;
		border: 1px solid var(--border);
		background: var(--bg);
		color: inherit;
		border-radius: 6px;
		padding: 0.4rem 0.9rem;
		cursor: pointer;
	}
	button:hover,
	.secondary:hover {
		border-color: var(--accent);
		text-decoration: none;
	}
	.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}
	.danger {
		color: #dc2626;
		margin-left: auto;
	}
	.link {
		border: none;
		background: none;
		color: var(--accent);
		padding: 0;
		font-size: 0.85rem;
	}
	.muted {
		color: var(--muted);
		margin: 0;
		font-size: 0.9rem;
	}
	.error {
		color: #dc2626;
	}
</style>
