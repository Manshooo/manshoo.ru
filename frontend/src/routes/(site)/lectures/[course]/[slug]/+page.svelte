<script lang="ts">
	import JsonLd from '$lib/components/JsonLd.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { formatDate, kindLabels, qualityLabels } from '$lib/format';
	import { lectureBreadcrumbsJsonLd, lectureJsonLd } from '$lib/jsonld';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const c = $derived(data.course);
	const l = $derived(data.lecture);
	const path = $derived(`/lectures/${c.slug}/${l.slug}`);
</script>

<Seo title={`${l.title} — ${c.title}`} description={l.summary} {path} type="article" />
<JsonLd data={[lectureJsonLd(c, l), lectureBreadcrumbsJsonLd(c, l)]} />

<svelte:head>
	<link rel="alternate" type="text/markdown" href={`${path}.md`} />
	{#if data.preview}<meta name="robots" content="noindex" />{/if}
</svelte:head>

{#if data.preview && !l.is_published}
	<p class="preview-banner">Предпросмотр черновика: страница видна только вам.</p>
{/if}

<nav class="crumbs">
	<a href="/lectures">Лекции</a> / <a href={`/lectures/${c.slug}`}>{c.title}</a>
</nav>

<article>
	<header>
		<p class="kind">{kindLabels[l.kind]}</p>
		<h1>{l.title}</h1>
		<p class="summary">{l.summary}</p>

		<dl class="facts">
			<div>
				<dt>Лектор</dt>
				<dd>{l.lecturer}</dd>
			</div>
			{#if l.kind === 'notes'}
				<div>
					<dt>Конспект составил</dt>
					<dd>{l.author}</dd>
				</div>
			{/if}
			<div>
				<dt>Дата лекции</dt>
				<dd>{formatDate(l.date)}</dd>
			</div>
			{#if l.source}
				<div>
					<dt>Видео</dt>
					<dd>
						<a href={l.source.url} rel="noopener">{l.source.title || 'оригинал'}</a>{l.source
							.duration
							? `, ${l.source.duration}`
							: ''}
					</dd>
				</div>
			{/if}
			<div>
				<dt>Текст</dt>
				<dd>{qualityLabels[l.quality]}</dd>
			</div>
		</dl>

		{#if l.topics.length}
			<ul class="chips" aria-label="Темы">
				{#each l.topics as t (t)}
					<li>{t}</li>
				{/each}
			</ul>
		{/if}

		{#if l.quality === 'asr'}
			<p class="warning">
				Текст получен автоматическим распознаванием речи и ещё не вычитан: возможны ошибки в
				терминах и формулах. Сверяйтесь с видео.
			</p>
		{/if}
	</header>

	{#if data.toc.length > 1}
		<nav class="toc" aria-label="Содержание">
			<p>Содержание</p>
			<ol>
				{#each data.toc as item (item.id)}
					<li><a href={`#${item.id}`}>{item.text}</a></li>
				{/each}
			</ol>
		</nav>
	{/if}

	<!-- eslint-disable-next-line svelte/no-at-html-tags -- контент пишет владелец сайта -->
	<div class="body">{@html data.html}</div>

	<footer class="license">
		<p>
			{#if l.kind === 'transcript'}
				Текст лекции: {l.lecturer}.
			{:else}
				Конспект: {l.author}, по лекции: {l.lecturer}.
			{/if}
			Лицензия <a href={l.license.url} rel="license">{l.license.name}</a>: можно копировать,
			цитировать и использовать для обучения моделей с указанием автора и ссылки на эту страницу.
		</p>
		<p><a href={`${path}.md`}>Исходный Markdown</a> · обновлено {formatDate(l.updated)}</p>
	</footer>
</article>

{#if data.prev || data.next}
	<nav class="pager">
		{#if data.prev}
			<a href={`/lectures/${c.slug}/${data.prev.slug}`} rel="prev">← {data.prev.title}</a>
		{/if}
		{#if data.next}
			<a class="next" href={`/lectures/${c.slug}/${data.next.slug}`} rel="next"
				>{data.next.title} →</a
			>
		{/if}
	</nav>
{/if}

<style>
	.preview-banner {
		background: var(--card);
		border: 1px dashed var(--border);
		border-radius: 8px;
		padding: 0.5rem 0.9rem;
		color: var(--muted);
		font-size: 0.9rem;
	}
	.crumbs {
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
		color: var(--muted);
	}
	.kind {
		margin: 0;
		color: var(--muted);
		font-size: 0.85rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	h1 {
		margin: 0.25rem 0;
		font-size: 1.8rem;
	}
	.summary {
		color: var(--muted);
		font-size: 1.05rem;
		margin-top: 0;
	}

	.facts {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem 2rem;
		margin: 1.25rem 0 0;
		font-size: 0.95rem;
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
		margin: 1rem 0 0;
	}
	.chips li {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 0.1rem 0.65rem;
		font-size: 0.82rem;
	}

	.warning {
		border: 1px dashed var(--border);
		border-radius: 8px;
		padding: 0.5rem 0.9rem;
		font-size: 0.9rem;
		color: var(--muted);
	}

	.toc {
		margin-top: 2rem;
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 0.75rem 1.25rem;
		font-size: 0.95rem;
	}
	.toc p {
		margin: 0 0 0.25rem;
		font-weight: 600;
	}
	.toc ol {
		margin: 0;
		padding-left: 1.25rem;
	}

	.body {
		margin-top: 2rem;
		overflow-wrap: break-word;
	}
	.body :global(p) {
		margin: 0.75rem 0;
	}
	.body :global(h2) {
		margin-top: 2.25rem;
		scroll-margin-top: 1rem;
	}
	.body :global(blockquote) {
		margin: 1.25rem 0;
		padding: 0.5rem 1rem;
		border-left: 3px solid var(--accent);
		background: var(--card);
		border-radius: 0 8px 8px 0;
	}
	.body :global(table) {
		border-collapse: collapse;
		display: block;
		overflow-x: auto;
	}
	.body :global(th),
	.body :global(td) {
		border: 1px solid var(--border);
		padding: 0.2rem 0.6rem;
	}
	.body :global(pre) {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.75rem 1rem;
		overflow-x: auto;
	}
	.body :global(.math) {
		font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
		font-size: 0.92em;
	}
	.body :global(.math-display) {
		display: block;
		overflow-x: auto;
		text-align: center;
		margin: 1rem 0;
	}

	.license {
		margin-top: 3rem;
		border-top: 1px solid var(--border);
		padding-top: 1rem;
		font-size: 0.9rem;
		color: var(--muted);
	}
	.license p {
		margin: 0.4rem 0;
	}

	.pager {
		display: flex;
		gap: 1rem;
		margin-top: 2rem;
		font-size: 0.95rem;
	}
	.pager .next {
		margin-left: auto;
		text-align: right;
	}
</style>
