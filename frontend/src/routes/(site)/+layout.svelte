<script lang="ts">
	import '../../app.css';
	import type { Snippet } from 'svelte';
	import type { LayoutServerData } from './$types';

	let { data, children }: { data: LayoutServerData; children: Snippet } = $props();

	const socialLabels: Record<string, string> = {
		github: 'GitHub',
		telegram: 'Telegram',
		email: 'Почта',
		linkedin: 'LinkedIn'
	};
</script>

<div class="page">
	<header class="container">
		<nav>
			<a href="/" class="brand">{data.profile.name}</a>
			<a href="/#projects">Проекты</a>
		</nav>
	</header>

	<main class="container">
		{@render children()}
	</main>

	<footer class="container">
		<div class="socials">
			{#each Object.entries(data.profile.socials) as [key, url] (key)}
				<a href={key === 'email' ? `mailto:${url}` : url} rel="me noopener">
					{socialLabels[key] ?? key}
				</a>
			{/each}
		</div>
		<p class="colophon">
			Сайт — тоже проект: <a href="https://github.com/Manshooo/manshoo.ru">исходники на GitHub</a>
		</p>
	</footer>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		min-height: 100dvh;
	}
	.container {
		width: 100%;
		max-width: 46rem;
		margin: 0 auto;
		padding: 0 1.25rem;
		box-sizing: border-box;
	}
	header {
		padding-top: 1.5rem;
	}
	nav {
		display: flex;
		align-items: baseline;
		gap: 1.25rem;
	}
	.brand {
		font-weight: 700;
		color: var(--fg);
		margin-right: auto;
	}
	main {
		flex: 1;
		padding: 2.5rem 1.25rem 4rem;
	}
	footer {
		border-top: 1px solid var(--border);
		padding-top: 1.5rem;
		padding-bottom: 2.5rem;
		font-size: 0.9rem;
		color: var(--muted);
	}
	.socials {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	.colophon {
		margin-bottom: 0;
	}
</style>
