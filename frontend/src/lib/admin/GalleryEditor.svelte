<script lang="ts">
	// Галерея проекта. Как и обложка, правки уходят в api сразу —
	// кнопка «Сохранить» формы их не касается.
	import { api, ApiError } from '$lib/admin/client';
	import type { ProjectImage } from '$lib/types';

	let { projectId, images: initial }: { projectId: number; images: ProjectImage[] } = $props();

	// Снимок, как и в ProjectForm: дальше список живёт своей жизнью
	// svelte-ignore state_referenced_locally
	let images = $state(initial);
	let progress = $state('');
	let reordering = $state(false);
	let errors = $state<string[]>([]);

	// Пока идёт загрузка или перестановка, порядок на сервере и здесь может
	// разойтись — api такой запрос отклонит, поэтому стрелки выключаем
	const busy = $derived(Boolean(progress) || reordering);

	const message = (e: unknown, fallback: string) => (e instanceof ApiError ? e.message : fallback);

	async function upload(event: Event) {
		const input = event.target as HTMLInputElement;
		const files = [...(input.files ?? [])];
		input.value = '';
		errors = [];
		// По одному: каждый файл укладывается в лимит, а битый не губит остальные
		for (const [i, file] of files.entries()) {
			progress = `Загружаем ${i + 1} из ${files.length}…`;
			try {
				images = [...images, await api.uploadImage(projectId, file)];
			} catch (e) {
				errors = [...errors, `${file.name}: ${message(e, 'не удалось загрузить')}`];
			}
		}
		progress = '';
	}

	async function saveCaption(image: ProjectImage, caption: string) {
		if (caption.trim() === image.caption) return;
		try {
			const updated = await api.updateImage(projectId, image.id, caption);
			images = images.map((i) => (i.id === updated.id ? updated : i));
		} catch (e) {
			errors = [message(e, 'Не удалось сохранить подпись')];
		}
	}

	async function move(index: number, delta: number) {
		const target = index + delta;
		if (target < 0 || target >= images.length) return;
		const previous = images;
		const next = [...images];
		[next[index], next[target]] = [next[target], next[index]];
		images = next; // показываем сразу, при ошибке откатываем
		reordering = true;
		try {
			await api.reorderImages(
				projectId,
				next.map((i) => i.id)
			);
		} catch (e) {
			images = previous;
			errors = [message(e, 'Не удалось поменять порядок')];
		} finally {
			reordering = false;
		}
	}

	async function remove(image: ProjectImage) {
		if (!confirm('Удалить кадр из галереи?')) return;
		try {
			await api.deleteImage(projectId, image.id);
			images = images.filter((i) => i.id !== image.id);
		} catch (e) {
			errors = [message(e, 'Не удалось удалить')];
		}
	}
</script>

<div class="gallery">
	{#if images.length}
		<ul>
			{#each images as image, i (image.id)}
				<li>
					<a href={image.url} target="_blank" rel="noopener">
						<img src={image.thumb_url} alt={image.caption || `Кадр ${i + 1}`} loading="lazy" />
					</a>
					<input
						value={image.caption}
						placeholder="Подпись (необязательно)"
						maxlength="200"
						aria-label={`Подпись к кадру ${i + 1}`}
						onchange={(e) => saveCaption(image, e.currentTarget.value)}
					/>
					<span class="controls">
						<button
							type="button"
							onclick={() => move(i, -1)}
							disabled={busy || i === 0}
							aria-label="Левее">←</button
						>
						<button
							type="button"
							onclick={() => move(i, 1)}
							disabled={busy || i === images.length - 1}
							aria-label="Правее">→</button
						>
						<button type="button" class="danger" onclick={() => remove(image)}>Удалить</button>
					</span>
				</li>
			{/each}
		</ul>
	{/if}

	<label class="add">
		Добавить изображения
		<input type="file" accept="image/*" multiple onchange={upload} disabled={Boolean(progress)} />
	</label>
	<p class="muted">
		Можно выбрать сразу несколько файлов, до 5 МБ каждый. На сайте — сетка превью, по клику кадр
		открывается целиком.
	</p>
	{#if progress}<p class="muted">{progress}</p>{/if}
	{#each errors as error (error)}
		<p class="error">{error}</p>
	{/each}
</div>

<style>
	.gallery {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr));
		gap: 0.75rem;
	}
	li {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.5rem;
	}
	img {
		display: block;
		width: 100%;
		aspect-ratio: 4 / 3;
		object-fit: cover;
		border-radius: 6px;
	}
	input {
		font: inherit;
		font-size: 0.85rem;
		color: inherit;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 0.3rem 0.5rem;
	}
	.controls {
		display: flex;
		gap: 0.3rem;
	}
	button {
		font: inherit;
		font-size: 0.85rem;
		border: 1px solid var(--border);
		background: var(--bg);
		color: inherit;
		border-radius: 6px;
		padding: 0.15rem 0.55rem;
		cursor: pointer;
	}
	button:hover:not(:disabled) {
		border-color: var(--accent);
	}
	button:disabled {
		opacity: 0.4;
		cursor: default;
	}
	.danger {
		color: #dc2626;
		margin-left: auto;
	}
	.add {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.9rem;
		color: var(--muted);
	}
	.add input {
		border: none;
		padding: 0;
		background: none;
	}
	.muted {
		color: var(--muted);
		margin: 0;
		font-size: 0.85rem;
	}
	.error {
		color: #dc2626;
		margin: 0;
		font-size: 0.9rem;
	}
</style>
