<script lang="ts">
	import JsonLd from '$lib/components/JsonLd.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { formatDate, kindLabels } from '$lib/format';
	import { courseJsonLd, lectureBreadcrumbsJsonLd } from '$lib/jsonld';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const c = $derived(data.course);
</script>

<Seo title={`${c.title} — лекции`} description={c.description} path={`/lectures/${c.slug}`} />
<JsonLd data={[courseJsonLd(c), lectureBreadcrumbsJsonLd(c)]} />

<nav class="crumbs"><a href="/lectures">← Все курсы</a></nav>

<header>
	<h1>{c.title}</h1>
	<p class="meta">
		{c.lecturer}{c.institution ? ` · ${c.institution}` : ''}{c.year ? ` · ${c.year}` : ''}
	</p>
</header>

<!-- eslint-disable-next-line svelte/no-at-html-tags -- контент пишет владелец сайта -->
<div class="body">{@html data.bodyHtml}</div>

<p class="license">
	Лицензия курса: <a href={c.license.url} rel="license">{c.license.name}</a>.
</p>

{#if data.lectures.length}
	<ol class="lectures">
		{#each data.lectures as l (l.slug)}
			<li>
				<a href={`/lectures/${c.slug}/${l.slug}`}>{l.title}</a>
				<span class="meta">
					{kindLabels[l.kind]} · {formatDate(l.date)}{l.duration ? ` · ${l.duration}` : ''}
				</span>
				<p>{l.summary}</p>
			</li>
		{/each}
	</ol>
{:else}
	<p class="meta">Материалы курса скоро появятся.</p>
{/if}

<style>
	.crumbs {
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
	}
	h1 {
		margin: 0 0 0.25rem;
		font-size: 1.8rem;
	}
	.meta {
		color: var(--muted);
		font-size: 0.9rem;
	}
	header .meta {
		margin-top: 0;
	}
	.body :global(p) {
		margin: 0.75rem 0;
	}
	.license {
		font-size: 0.9rem;
	}
	.lectures {
		list-style: none;
		padding: 0;
		margin: 2rem 0 0;
		display: grid;
		gap: 1.25rem;
	}
	.lectures a {
		font-weight: 600;
		font-size: 1.05rem;
	}
	.lectures .meta {
		display: block;
	}
	.lectures p {
		margin: 0.25rem 0 0;
	}
</style>
