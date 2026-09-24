<script lang="ts">
	// Сетка превью и просмотр кадра по клику. Без JS превью — обычные ссылки
	// на полный кадр, так что галерея работает и до гидратации.
	import type { ProjectImage } from '$lib/types';

	let { images, title }: { images: ProjectImage[]; title: string } = $props();

	let dialog: HTMLDialogElement;
	let current = $state(0);
	let touchX: number | null = null;

	const image = $derived(images[current]);
	const altText = (img: ProjectImage, index: number) =>
		img.caption || `${title}: кадр ${index + 1}`;

	function open(event: MouseEvent, index: number) {
		// ctrl/cmd-клик и средняя кнопка — пусть браузер откроет файл сам
		if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey) return;
		event.preventDefault();
		current = index;
		dialog.showModal();
	}

	function step(delta: number) {
		current = (current + delta + images.length) % images.length;
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'ArrowLeft') step(-1);
		if (event.key === 'ArrowRight') step(1);
	}

	// Клик мимо кадра (по затемнению) закрывает просмотр
	function onClick(event: MouseEvent) {
		if (event.target === dialog) dialog.close();
	}

	// Свайп на телефоне листает кадры
	function onTouchStart(event: TouchEvent) {
		touchX = event.touches[0].clientX;
	}
	function onTouchEnd(event: TouchEvent) {
		if (touchX === null) return;
		const dx = event.changedTouches[0].clientX - touchX;
		touchX = null;
		if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
	}
</script>

<ul class="grid">
	{#each images as img, i (img.id)}
		<li>
			<a href={img.url} onclick={(e) => open(e, i)}>
				<img src={img.thumb_url} alt={altText(img, i)} loading="lazy" decoding="async" />
			</a>
			{#if img.caption}<p class="caption">{img.caption}</p>{/if}
		</li>
	{/each}
</ul>

<!-- Стрелки листают кадры, Esc закрывает <dialog> сам -->
<dialog
	bind:this={dialog}
	aria-label="Просмотр галереи"
	onkeydown={onKeydown}
	onclick={onClick}
	ontouchstart={onTouchStart}
	ontouchend={onTouchEnd}
>
	<!-- первой в DOM: showModal() отдаёт фокус ей, а не стрелке -->
	<button class="close" onclick={() => dialog.close()} aria-label="Закрыть">×</button>
	{#if image}
		<figure>
			<img
				src={image.url}
				alt={altText(image, current)}
				width={image.width}
				height={image.height}
			/>
			<figcaption>
				{#if images.length > 1}<span class="counter">{current + 1} / {images.length}</span>{/if}
				{image.caption}
			</figcaption>
		</figure>
	{/if}
	{#if images.length > 1}
		<button class="nav prev" onclick={() => step(-1)} aria-label="Предыдущий кадр">‹</button>
		<button class="nav next" onclick={() => step(1)} aria-label="Следующий кадр">›</button>
	{/if}
</dialog>

<style>
	.grid {
		list-style: none;
		padding: 0;
		margin: 1rem 0 0;
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}
	@media (min-width: 40rem) {
		.grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}
	.grid a {
		display: block;
		border-radius: 8px;
		overflow: hidden;
		border: 1px solid var(--border);
	}
	.grid a:hover {
		border-color: var(--accent);
	}
	.grid img {
		display: block;
		width: 100%;
		height: auto;
		aspect-ratio: 4 / 3;
		object-fit: cover;
		background: var(--card);
	}
	.caption {
		margin: 0.3rem 0 0;
		font-size: 0.85rem;
		color: var(--muted);
		line-height: 1.4;
	}

	dialog {
		width: 100vw;
		height: 100dvh;
		max-width: none;
		max-height: none;
		margin: 0;
		padding: 0;
		border: none;
		background: transparent;
		color: #fff;
	}
	dialog[open] {
		display: flex;
		align-items: center;
		justify-content: center;
	}
	dialog::backdrop {
		background: rgb(0 0 0 / 0.88);
	}
	/* страница под открытым просмотром не прокручивается */
	:global(html:has(dialog[open])) {
		overflow: hidden;
	}
	figure {
		margin: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.6rem;
		max-width: calc(100vw - 2rem);
	}
	figure img {
		display: block;
		max-width: 100%;
		max-height: calc(100dvh - 7rem);
		width: auto;
		height: auto;
		object-fit: contain;
		border-radius: 4px;
	}
	figcaption {
		font-size: 0.9rem;
		text-align: center;
		color: rgb(255 255 255 / 0.85);
		min-height: 1.4em;
	}
	.counter {
		color: rgb(255 255 255 / 0.55);
		margin-right: 0.5rem;
	}
	dialog button {
		position: fixed;
		font: inherit;
		color: #fff;
		background: rgb(255 255 255 / 0.12);
		border: none;
		border-radius: 999px;
		width: 2.75rem;
		height: 2.75rem;
		font-size: 1.6rem;
		line-height: 1;
		cursor: pointer;
	}
	dialog button:hover,
	dialog button:focus-visible {
		background: rgb(255 255 255 / 0.25);
	}
	.nav {
		top: 50%;
		transform: translateY(-50%);
	}
	.prev {
		left: 0.75rem;
	}
	.next {
		right: 0.75rem;
	}
	.close {
		top: 0.75rem;
		right: 0.75rem;
	}
</style>
