<script lang="ts">
	import { page } from '$app/state';
</script>

<svelte:head>
	<title>{page.status === 404 ? 'Страница не найдена' : 'Ошибка'} — manshoo.ru</title>
</svelte:head>

<section>
	<h1>{page.status}</h1>
	{#if page.status === 404}
		<p>Такой страницы нет. Возможно, она ещё не написана.</p>
	{:else}
		<p>{page.error?.message ?? 'Что-то сломалось.'}</p>
	{/if}
	<p><a href="/">На главную</a></p>
</section>

<style>
	h1 {
		font-size: 3rem;
		margin-bottom: 0;
	}
</style>
