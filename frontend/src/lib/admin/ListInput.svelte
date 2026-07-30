<script lang="ts">
	// Список строк: стек (теги через Enter) и «ключевые фишки» (буллеты).
	let {
		items = $bindable<string[]>(),
		label,
		placeholder = '',
		multiline = false
	}: {
		items: string[];
		label: string;
		placeholder?: string;
		multiline?: boolean;
	} = $props();

	let draft = $state('');

	function add() {
		const value = draft.trim();
		if (!value) return;
		items = [...items, value];
		draft = '';
	}

	function remove(index: number) {
		items = items.filter((_, i) => i !== index);
	}

	function move(index: number, delta: number) {
		const target = index + delta;
		if (target < 0 || target >= items.length) return;
		const next = [...items];
		[next[index], next[target]] = [next[target], next[index]];
		items = next;
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			add();
		}
	}
</script>

<fieldset>
	<legend>{label}</legend>

	{#if items.length}
		<ul class:chips={!multiline}>
			{#each items as item, i (i)}
				<li>
					<span>{item}</span>
					<span class="controls">
						{#if multiline}
							<button type="button" onclick={() => move(i, -1)} aria-label="Выше">↑</button>
							<button type="button" onclick={() => move(i, 1)} aria-label="Ниже">↓</button>
						{/if}
						<button type="button" onclick={() => remove(i)} aria-label="Удалить">×</button>
					</span>
				</li>
			{/each}
		</ul>
	{/if}

	<div class="add">
		{#if multiline}
			<textarea bind:value={draft} {placeholder} rows="2" onkeydown={onKeydown}></textarea>
		{:else}
			<input bind:value={draft} {placeholder} onkeydown={onKeydown} />
		{/if}
		<button type="button" onclick={add}>Добавить</button>
	</div>
</fieldset>

<style>
	fieldset {
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.75rem 1rem 1rem;
		margin: 0;
	}
	legend {
		padding: 0 0.35rem;
		color: var(--muted);
		font-size: 0.9rem;
	}
	ul {
		list-style: none;
		padding: 0;
		margin: 0 0 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	ul.chips {
		flex-direction: row;
		flex-wrap: wrap;
	}
	li {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.2rem 0.5rem 0.2rem 0.7rem;
	}
	ul.chips li {
		border-radius: 999px;
		font-size: 0.9rem;
	}
	.controls {
		display: flex;
		gap: 0.15rem;
		margin-left: auto;
	}
	.add {
		display: flex;
		gap: 0.5rem;
		align-items: flex-start;
	}
	input,
	textarea {
		font: inherit;
		flex: 1;
		padding: 0.35rem 0.6rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: inherit;
		resize: vertical;
	}
	button {
		font: inherit;
		border: 1px solid var(--border);
		background: var(--bg);
		color: inherit;
		border-radius: 6px;
		padding: 0.2rem 0.6rem;
		cursor: pointer;
		line-height: 1.4;
	}
	button:hover {
		border-color: var(--accent);
	}
</style>
