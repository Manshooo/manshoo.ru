<script lang="ts">
	import Seo from '$lib/components/Seo.svelte';
	import { formatPeriod, statusLabels, typeLabels } from '$lib/format';
	import { renderMarkdown } from '$lib/markdown';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const profile = $derived(data.profile);
	const projects = $derived(data.projects);
</script>

<Seo
	title={`${profile.name} — проекты и портфолио`}
	description={profile.meta_description || profile.headline}
	path="/"
/>

<section class="hero">
	<h1>{profile.name}</h1>
	<p class="headline">{profile.headline}</p>
	<!-- eslint-disable-next-line svelte/no-at-html-tags -- контент пишет владелец сайта -->
	<div class="bio">{@html renderMarkdown(profile.bio_md)}</div>
	{#if profile.skills.length}
		<ul class="chips" aria-label="Навыки">
			{#each profile.skills as skill (skill)}
				<li>{skill}</li>
			{/each}
		</ul>
	{/if}
</section>

<section id="projects">
	<h2>Проекты</h2>
	<p class="note">Вместо раздела «опыт работы»: что делал, какую роль играл и что получилось.</p>
	{#if projects.length}
		<div class="grid">
			{#each projects as p (p.slug)}
				<a class="card" href={`/projects/${p.slug}`}>
					<div class="card-head">
						<h3>{p.title}</h3>
						<span class="badge" data-status={p.status}>{statusLabels[p.status]}</span>
					</div>
					<p class="tagline">{p.tagline}</p>
					<p class="meta">
						{typeLabels[p.project_type]} · {formatPeriod(p.period_start, p.period_end)}
					</p>
					{#if p.stack.length}
						<ul class="chips small">
							{#each p.stack.slice(0, 6) as tech (tech)}
								<li>{tech}</li>
							{/each}
						</ul>
					{/if}
				</a>
			{/each}
		</div>
	{:else}
		<p>Проекты скоро появятся.</p>
	{/if}
</section>

<style>
	.hero h1 {
		font-size: 2rem;
		margin: 0 0 0.25rem;
	}
	.headline {
		font-size: 1.15rem;
		color: var(--muted);
		margin-top: 0;
	}
	.bio :global(p) {
		margin: 0.75rem 0;
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
		padding: 0.15rem 0.7rem;
		font-size: 0.85rem;
	}
	.chips.small li {
		font-size: 0.78rem;
		padding: 0.05rem 0.55rem;
	}

	#projects {
		margin-top: 3rem;
	}
	#projects .note {
		color: var(--muted);
		margin-top: -0.5rem;
	}
	.grid {
		display: grid;
		gap: 1rem;
		margin-top: 1.25rem;
	}
	.card {
		display: block;
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 1rem 1.25rem;
		color: inherit;
	}
	.card:hover {
		text-decoration: none;
		border-color: var(--accent);
	}
	.card-head {
		display: flex;
		align-items: baseline;
		gap: 0.75rem;
	}
	.card h3 {
		margin: 0;
		color: var(--accent);
	}
	.badge {
		font-size: 0.75rem;
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 0.05rem 0.6rem;
		color: var(--muted);
		white-space: nowrap;
	}
	.badge[data-status='active'] {
		color: #16a34a;
		border-color: color-mix(in srgb, #16a34a 40%, transparent);
	}
	.tagline {
		margin: 0.5rem 0 0.25rem;
	}
	.meta {
		margin: 0;
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
