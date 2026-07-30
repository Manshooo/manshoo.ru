<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, ApiError } from '$lib/admin/client';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let busy = $state(false);

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		busy = true;
		error = '';
		try {
			await api.login(username, password);
			goto('/admin');
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'Не удалось войти';
		} finally {
			busy = false;
		}
	}
</script>

<h1>Вход в админку</h1>

<form onsubmit={submit}>
	<label>
		Логин
		<input bind:value={username} autocomplete="username" required />
	</label>
	<label>
		Пароль
		<input type="password" bind:value={password} autocomplete="current-password" required />
	</label>
	{#if error}
		<p class="error">{error}</p>
	{/if}
	<button type="submit" disabled={busy}>{busy ? 'Входим…' : 'Войти'}</button>
</form>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		max-width: 20rem;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	input {
		font: inherit;
		padding: 0.4rem 0.6rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: inherit;
	}
	button {
		font: inherit;
		padding: 0.45rem 1rem;
		border: 1px solid var(--accent);
		border-radius: 6px;
		background: var(--accent);
		color: #fff;
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.error {
		color: #dc2626;
		margin: 0;
	}
</style>
