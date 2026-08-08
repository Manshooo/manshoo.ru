<script lang="ts">
	import { SITE_URL } from '$lib/seo';

	let {
		title,
		description,
		path,
		type = 'website',
		image = null
	}: {
		title: string;
		description: string;
		path: string;
		type?: 'website' | 'article';
		image?: string | null;
	} = $props();

	const url = $derived(`${SITE_URL}${path}`);
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<link rel="canonical" href={url} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:url" content={url} />
	<meta property="og:type" content={type} />
	<meta property="og:locale" content="ru_RU" />
	{#if image}
		<meta property="og:image" content={image} />
		<meta property="og:image:width" content="1200" />
		<meta property="og:image:height" content="630" />
		<meta name="twitter:card" content="summary_large_image" />
	{:else}
		<meta name="twitter:card" content="summary" />
	{/if}
</svelte:head>
