<script lang="ts">
	import '../../app.css';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api } from '$lib/admin/client';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	let checking = $state(true);
	let username = $state<string | null>(null);

	const isLoginPage = $derived(page.url.pathname === '/admin/login');

	$effect(() => {
		// Проверяем сессию при входе в раздел; на странице логина не нужно
		if (isLoginPage) {
			checking = false;
			return;
		}
		api
			.me()
			.then((me) => (username = me.username))
			.catch(() => goto('/admin/login'))
			.finally(() => (checking = false));
	});

	async function logout() {
		await api.logout().catch(() => {});
		username = null;
		goto('/admin/login');
	}
</script>

<svelte:head>
	<meta name="robots" content="noindex, nofollow" />
	<title>Админка — manshoo.ru</title>
</svelte:head>

<div class="admin">
	{#if !isLoginPage}
		<nav>
			<a href="/admin">Проекты</a>
			<a href="/admin/profile">Профиль</a>
			<a href="/" class="site">Открыть сайт ↗</a>
			{#if username}
				<span class="user">{username}</span>
				<button type="button" onclick={logout}>Выйти</button>
			{/if}
		</nav>
	{/if}

	{#if checking && !isLoginPage}
		<p class="muted">Проверяем сессию…</p>
	{:else}
		{@render children()}
	{/if}
</div>

<style>
	.admin {
		max-width: 52rem;
		margin: 0 auto;
		padding: 1.5rem 1.25rem 4rem;
	}
	nav {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding-bottom: 1rem;
		margin-bottom: 1.5rem;
		border-bottom: 1px solid var(--border);
		font-size: 0.95rem;
	}
	nav .site {
		margin-left: auto;
	}
	.user {
		color: var(--muted);
	}
	button {
		font: inherit;
		border: 1px solid var(--border);
		background: var(--card);
		color: inherit;
		border-radius: 6px;
		padding: 0.2rem 0.7rem;
		cursor: pointer;
	}
	button:hover {
		border-color: var(--accent);
	}
	.muted {
		color: var(--muted);
	}
</style>
