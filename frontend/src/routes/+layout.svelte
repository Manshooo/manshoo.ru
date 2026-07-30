<script lang="ts">
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
	:global(:root) {
		--bg: #ffffff;
		--fg: #1c1e23;
		--muted: #667085;
		--accent: #2563eb;
		--card: #f6f7f9;
		--border: #e6e8ec;
		color-scheme: light dark;
	}
	@media (prefers-color-scheme: dark) {
		:global(:root) {
			--bg: #0f1116;
			--fg: #e7e9ee;
			--muted: #98a1b0;
			--accent: #82a7ff;
			--card: #171a21;
			--border: #262b36;
		}
	}
	:global(body) {
		margin: 0;
		background: var(--bg);
		color: var(--fg);
		font-family:
			system-ui,
			-apple-system,
			'Segoe UI',
			Roboto,
			sans-serif;
		line-height: 1.65;
		-webkit-font-smoothing: antialiased;
	}
	:global(a) {
		color: var(--accent);
		text-decoration: none;
	}
	:global(a:hover) {
		text-decoration: underline;
	}
	:global(h1, h2, h3) {
		line-height: 1.25;
	}
	:global(code) {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 0.1em 0.35em;
		font-size: 0.9em;
	}

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
