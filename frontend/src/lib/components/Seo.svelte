<script lang="ts">
	import { SITE_URL } from '$lib/seo';

	let {
		title,
		description,
		path,
		type = 'website'
	}: { title: string; description: string; path: string; type?: 'website' | 'article' } = $props();

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
	<meta name="twitter:card" content="summary" />
</svelte:head>
