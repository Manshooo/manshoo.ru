<script lang="ts">
	let { data }: { data: Record<string, unknown> | Record<string, unknown>[] } = $props();

	// Экранируем "<", чтобы содержимое не могло закрыть тег script
	const json = $derived(JSON.stringify(data).replace(/</g, '\\u003c'));
</script>

<svelte:head>
	<!-- eslint-disable-next-line svelte/no-at-html-tags -- JSON.stringify + экранирование "<" выше: содержимое не может выйти из тега -->
	{@html `<script type="application/ld+json">${json}</` + `script>`}
</svelte:head>
