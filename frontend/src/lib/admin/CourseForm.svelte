<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, ApiError } from '$lib/admin/client';
	import type { Course } from '$lib/types';

	let { course = null }: { course?: Course | null } = $props();

	// Снимок курса, как в ProjectForm: родитель пересоздаёт форму через {#key}.
	// svelte-ignore state_referenced_locally
	const initial = course;

	let title = $state(initial?.title ?? '');
	let slug = $state(initial?.slug ?? '');
	let description = $state(initial?.description ?? '');
	let lecturer = $state(initial?.lecturer ?? '');
	let institution = $state(initial?.institution ?? '');
	let year = $state(initial?.year ?? '');
	let language = $state(initial?.language ?? 'ru');
	let license = $state(initial?.license.id ?? 'CC-BY-4.0');
	let bodyMd = $state(initial?.body_md ?? '');
	let isPublished = $state(initial?.is_published ?? false);
	let sortOrder = $state(initial?.sort_order ?? 0);

	let error = $state('');
	let saving = $state(false);

	const licenses = [
		['CC-BY-4.0', 'CC BY 4.0 — свободно с указанием автора'],
		['CC-BY-SA-4.0', 'CC BY-SA 4.0 — то же, производные под той же лицензией'],
		['CC0-1.0', 'CC0 — общественное достояние'],
		['CC-BY-NC-4.0', 'CC BY-NC 4.0 — без коммерции (часть датасетов такое не берёт)']
	];

	async function save(event: SubmitEvent) {
		event.preventDefault();
		saving = true;
		error = '';
		const payload = {
			title,
			slug,
			description,
			lecturer,
			institution,
			year,
			language,
			license,
			body_md: bodyMd,
			is_published: isPublished,
			sort_order: sortOrder
		};
		try {
			const saved = course
				? await api.updateCourse(course.id, payload)
				: await api.createCourse(payload);
			goto(`/admin/lectures#course-${saved.id}`, { invalidateAll: true });
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'Не удалось сохранить';
		} finally {
			saving = false;
		}
	}

	async function remove() {
		if (!course) return;
		const n = course.lectures.length;
		const what = n ? ` и все его лекции (${n})` : '';
		if (!confirm(`Удалить курс «${course.title}»${what}? Отменить будет нельзя.`)) return;
		await api.deleteCourse(course.id);
		goto('/admin/lectures', { invalidateAll: true });
	}
</script>

<form onsubmit={save}>
	<label>
		Название
		<input bind:value={title} required placeholder="Алгебра, 1 курс" />
	</label>
	<label>
		Одной строкой
		<input bind:value={description} required maxlength="300" />
	</label>
	<div class="row">
		<label>
			Лектор
			<input bind:value={lecturer} required />
		</label>
		<label>
			Вуз / площадка
			<input bind:value={institution} />
		</label>
		<label class="narrow">
			Год
			<input bind:value={year} />
		</label>
	</div>
	<div class="row">
		<label>
			Лицензия по умолчанию для лекций
			<select bind:value={license}>
				{#each licenses as [id, label] (id)}
					<option value={id}>{label}</option>
				{/each}
			</select>
		</label>
		<label class="narrow">
			Язык
			<input bind:value={language} />
		</label>
	</div>
	<label>
		О курсе (Markdown): для кого, где оригинальные видео, на каких условиях разрешена публикация
		<textarea bind:value={bodyMd} rows="6"></textarea>
	</label>
	<div class="row">
		<label>
			Адрес (slug, пусто — из названия)
			<input bind:value={slug} placeholder="algebra-1" />
		</label>
		<label class="narrow">
			Порядок
			<input type="number" bind:value={sortOrder} />
		</label>
	</div>
	<label class="check">
		<input type="checkbox" bind:checked={isPublished} />
		Опубликован (без этого не видна ни одна лекция курса)
	</label>

	{#if error}<p class="error">{error}</p>{/if}

	<div class="actions">
		<button type="submit" class="primary" disabled={saving}>
			{saving ? 'Сохраняем…' : 'Сохранить'}
		</button>
		<a href="/admin/lectures">Отмена</a>
		{#if course}
			<button type="button" class="danger" onclick={remove}>Удалить курс</button>
		{/if}
	</div>
</form>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
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
	.row {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	.row label {
		flex: 1;
		min-width: 12rem;
	}
	.row label.narrow {
		flex: 0 0 7rem;
		min-width: 0;
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
	.actions {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-top: 0.5rem;
	}
	button {
		font: inherit;
		border: 1px solid var(--border);
		background: var(--card);
		color: inherit;
		border-radius: 6px;
		padding: 0.35rem 0.9rem;
		cursor: pointer;
	}
	.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}
	.danger {
		margin-left: auto;
		color: #dc2626;
	}
	.error {
		color: #dc2626;
		white-space: pre-line;
	}
</style>
