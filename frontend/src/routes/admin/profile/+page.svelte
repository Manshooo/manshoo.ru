<script lang="ts">
	import ListInput from '$lib/admin/ListInput.svelte';
	import { api, ApiError } from '$lib/admin/client';
	import { renderMarkdown } from '$lib/markdown';

	const SOCIAL_KEYS = ['github', 'telegram', 'email', 'linkedin'] as const;

	let name = $state('');
	let headline = $state('');
	let bioMd = $state('');
	let location = $state('');
	let metaDescription = $state('');
	let skills = $state<string[]>([]);
	let socials = $state<Record<string, string>>({});

	let loaded = $state(false);
	let saved = $state(false);
	let error = $state('');
	let saving = $state(false);
	let showPreview = $state(false);

	$effect(() => {
		api
			.getProfile()
			.then((p) => {
				name = p.name;
				headline = p.headline;
				bioMd = p.bio_md;
				location = p.location;
				metaDescription = p.meta_description;
				skills = p.skills;
				socials = { ...p.socials };
				loaded = true;
			})
			.catch((e) => (error = e instanceof ApiError ? e.message : 'Не удалось загрузить'));
	});

	async function save(event: SubmitEvent) {
		event.preventDefault();
		saving = true;
		error = '';
		saved = false;
		try {
			const cleaned = Object.fromEntries(Object.entries(socials).filter(([, v]) => v.trim()));
			await api.updateProfile({
				name,
				headline,
				bio_md: bioMd,
				location,
				meta_description: metaDescription,
				skills,
				socials: cleaned
			});
			saved = true;
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'Не удалось сохранить';
		} finally {
			saving = false;
		}
	}
</script>

<h1>Профиль</h1>

{#if !loaded && !error}
	<p class="muted">Загружаем…</p>
{:else}
	<form onsubmit={save}>
		<label>
			Имя
			<input bind:value={name} required />
		</label>
		<label>
			Кто я одной строкой
			<input bind:value={headline} required />
		</label>
		<label>
			<span class="label-row">
				О себе (Markdown)
				<button type="button" class="link" onclick={() => (showPreview = !showPreview)}>
					{showPreview ? 'скрыть превью' : 'показать превью'}
				</button>
			</span>
			<textarea bind:value={bioMd} rows="6"></textarea>
		</label>
		{#if showPreview}
			<!-- eslint-disable-next-line svelte/no-at-html-tags -- превью своего же текста -->
			<div class="preview">{@html renderMarkdown(bioMd)}</div>
		{/if}
		<label>
			Город / часовой пояс
			<input bind:value={location} />
		</label>
		<label>
			SEO-описание главной (до 160 символов)
			<input bind:value={metaDescription} maxlength="160" />
		</label>

		<ListInput bind:items={skills} label="Навыки" placeholder="Python, Go…" />

		<fieldset>
			<legend>Контакты</legend>
			{#each SOCIAL_KEYS as key (key)}
				<label>
					{key}
					<input
						value={socials[key] ?? ''}
						oninput={(e) => (socials = { ...socials, [key]: e.currentTarget.value })}
						placeholder={key === 'email' ? 'you@example.com' : 'https://…'}
					/>
				</label>
			{/each}
		</fieldset>

		{#if error}<p class="error">{error}</p>{/if}
		{#if saved}<p class="ok">Сохранено</p>{/if}

		<div class="actions">
			<button type="submit" class="primary" disabled={saving}>
				{saving ? 'Сохраняем…' : 'Сохранить'}
			</button>
			<a class="secondary" href="/" target="_blank" rel="noopener">Открыть главную ↗</a>
		</div>
	</form>
{/if}

<style>
	h1 {
		font-size: 1.5rem;
		margin: 0 0 1.5rem;
	}
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
	.label-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}
	input,
	textarea {
		font: inherit;
		color: inherit;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 0.4rem 0.6rem;
		resize: vertical;
	}
	fieldset {
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.75rem 1rem 1rem;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	legend {
		padding: 0 0.35rem;
		color: var(--muted);
		font-size: 0.9rem;
	}
	.preview {
		border: 1px dashed var(--border);
		border-radius: 8px;
		padding: 0.5rem 1rem;
		background: var(--card);
	}
	.actions {
		display: flex;
		gap: 0.75rem;
		align-items: center;
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
	.link {
		border: none;
		background: none;
		color: var(--accent);
		padding: 0;
		font-size: 0.85rem;
	}
	.muted {
		color: var(--muted);
	}
	.error {
		color: #dc2626;
	}
	.ok {
		color: #16a34a;
	}
</style>
