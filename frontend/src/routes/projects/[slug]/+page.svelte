<script lang="ts">
	import Seo from '$lib/components/Seo.svelte';
	import { formatPeriod, statusLabels, typeLabels } from '$lib/format';
	import { renderMarkdown } from '$lib/markdown';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const p = $derived(data.project);

	const linkLabels: Record<string, string> = {
		live: 'Открыть проект',
		repo: 'Исходный код',
		case: 'Кейс/статья'
	};
</script>

<Seo
	title={`${p.title} — ${data.profile.name}`}
	description={p.tagline}
	path={`/projects/${p.slug}`}
	type="article"
/>

<nav class="crumbs"><a href="/#projects">← Все проекты</a></nav>

<article>
	<header>
		<h1>{p.title}</h1>
		<p class="tagline">{p.tagline}</p>

		<dl class="facts">
			{#if p.role}
				<div>
					<dt>Роль</dt>
					<dd>{p.role}</dd>
				</div>
			{/if}
			{#if p.org}
				<div>
					<dt>Контекст</dt>
					<dd>{p.org}</dd>
				</div>
			{/if}
			<div>
				<dt>Период</dt>
				<dd>{formatPeriod(p.period_start, p.period_end)}</dd>
			</div>
			<div>
				<dt>Тип</dt>
				<dd>{typeLabels[p.project_type]}</dd>
			</div>
			<div>
				<dt>Статус</dt>
				<dd>{statusLabels[p.status]}</dd>
			</div>
		</dl>

		{#if p.stack.length}
			<ul class="chips" aria-label="Стек">
				{#each p.stack as tech (tech)}
					<li>{tech}</li>
				{/each}
			</ul>
		{/if}
	</header>

	{#if p.description_md}
		<!-- eslint-disable-next-line svelte/no-at-html-tags -- контент пишет владелец сайта -->
		<div class="body">{@html renderMarkdown(p.description_md)}</div>
	{/if}

	{#if p.highlights.length}
		<h2>Ключевые фишки</h2>
		<ul class="highlights">
			{#each p.highlights as h (h)}
				<li>{h}</li>
			{/each}
		</ul>
	{/if}

	{#if Object.keys(p.links).length}
		<div class="links">
			{#each Object.entries(p.links) as [key, url] (key)}
				<a class="button" href={url} rel="noopener">{linkLabels[key] ?? key}</a>
			{/each}
		</div>
	{/if}
</article>

<style>
	.crumbs {
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}
	h1 {
		margin: 0 0 0.25rem;
		font-size: 1.8rem;
	}
	.tagline {
		color: var(--muted);
		font-size: 1.1rem;
		margin-top: 0;
	}

	.facts {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem 2rem;
		margin: 1.25rem 0 0;
	}
	.facts div {
		display: flex;
		gap: 0.5rem;
	}
	.facts dt {
		color: var(--muted);
	}
	.facts dt::after {
		content: ':';
	}
	.facts dd {
		margin: 0;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		list-style: none;
		padding: 0;
		margin: 1.25rem 0 0;
	}
	.chips li {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 0.15rem 0.7rem;
		font-size: 0.85rem;
	}

	.body {
		margin-top: 1.5rem;
	}
	.body :global(p) {
		margin: 0.75rem 0;
	}

	h2 {
		margin-top: 2rem;
	}
	.highlights {
		padding-left: 1.25rem;
	}
	.highlights li {
		margin: 0.4rem 0;
	}

	.links {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin-top: 2rem;
	}
	.button {
		border: 1px solid var(--accent);
		border-radius: 8px;
		padding: 0.4rem 1rem;
	}
	.button:hover {
		background: var(--accent);
		color: var(--bg);
		text-decoration: none;
	}
</style>
