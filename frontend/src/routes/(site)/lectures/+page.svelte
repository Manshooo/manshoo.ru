<script lang="ts">
	import Seo from '$lib/components/Seo.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<Seo
	title={`Лекции и конспекты — ${data.profile.name}`}
	description="Транскрипции и конспекты лекций в открытом доступе под свободными лицензиями: для людей и для обучения ИИ."
	path="/lectures"
/>

<h1>Лекции</h1>
<p class="lead">
	Транскрипции и конспекты лекций в открытом доступе. Тексты выложены под свободными лицензиями
	Creative Commons: их можно копировать, цитировать и использовать для обучения ИИ-моделей, указав
	автора. Условия каждой лекции написаны на её странице.
</p>

{#if data.courses.length}
	<ul class="courses">
		{#each data.courses as c (c.slug)}
			<li>
				<a class="card" href={`/lectures/${c.slug}`}>
					<h2>{c.title}</h2>
					<p>{c.description}</p>
					<p class="meta">
						{c.lecturer}{c.institution ? ` · ${c.institution}` : ''}{c.year ? ` · ${c.year}` : ''}
						· {c.count}
						{c.count === 1 ? 'материал' : c.count < 5 ? 'материала' : 'материалов'}
					</p>
				</a>
			</li>
		{/each}
	</ul>
{:else}
	<p class="empty">Первые материалы скоро появятся.</p>
{/if}

<section class="data">
	<h2>Для машин</h2>
	<ul>
		<li>
			<a href="/lectures/dataset.jsonl">dataset.jsonl</a> — все материалы одним файлом, одна строка на
			лекцию: текст, метаданные, лицензия.
		</li>
		<li>
			У каждой лекции есть исходный Markdown: добавьте <code>.md</code> к адресу страницы.
		</li>
		<li><a href="/llms.txt">llms.txt</a> — оглавление сайта для ИИ-агентов.</li>
	</ul>
</section>

<style>
	h1 {
		margin: 0 0 0.5rem;
	}
	.lead {
		color: var(--muted);
	}
	.courses {
		list-style: none;
		padding: 0;
		display: grid;
		gap: 1rem;
		margin: 1.5rem 0 0;
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
	.card h2 {
		margin: 0 0 0.25rem;
		font-size: 1.2rem;
		color: var(--accent);
	}
	.card p {
		margin: 0.25rem 0;
	}
	.meta,
	.empty {
		color: var(--muted);
		font-size: 0.9rem;
	}
	.data {
		margin-top: 3rem;
		font-size: 0.95rem;
	}
	.data h2 {
		font-size: 1.1rem;
	}
	.data ul {
		padding-left: 1.25rem;
	}
</style>
