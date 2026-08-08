<script lang="ts">
	import Seo from '$lib/components/Seo.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import { formatSince, formatUptime } from '$lib/format';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<Seo
	title="Статус проектов — {data.profile.name}"
	description="Живой мониторинг моих проектов: доступность, задержка ответа, срок сертификатов."
	path="/status"
/>

<h1>Статус проектов</h1>
<p class="lead">
	Проверки делает <a href="https://github.com/Manshooo/manshoo.ru/tree/main/uptime">мой чекер</a> на Go:
	HTTP-запрос раз в минуту, история в SQLite, алерты в Telegram.
</p>

{#if data.monitors.length === 0}
	<p class="muted">Чекер сейчас недоступен — данные появятся, когда он ответит.</p>
{:else}
	<div class="grid">
		{#each data.monitors as m (m.slug)}
			<article>
				<header>
					<h2><a href={m.url} rel="noopener">{m.name}</a></h2>
					<StatusBadge monitor={m} compact />
				</header>

				<dl>
					<div>
						<dt>С</dt>
						<dd>{formatSince(m.since)}</dd>
					</div>
					<div>
						<dt>24 часа</dt>
						<dd>{formatUptime(m.uptime_24h)}</dd>
					</div>
					<div>
						<dt>7 дней</dt>
						<dd>{formatUptime(m.uptime_7d)}</dd>
					</div>
					<div>
						<dt>30 дней</dt>
						<dd>{formatUptime(m.uptime_30d)}</dd>
					</div>
					{#if m.median_latency_ms_24h !== null}
						<div>
							<dt>Ответ</dt>
							<dd>{m.median_latency_ms_24h} мс (медиана за сутки)</dd>
						</div>
					{/if}
					{#if m.tls_days_left !== null}
						<div>
							<dt>Сертификат</dt>
							<dd class:warn={m.tls_days_left <= 14}>ещё {m.tls_days_left} дн.</dd>
						</div>
					{/if}
				</dl>

				{#if m.last_check && !m.last_check.ok && m.last_check.error}
					<p class="error">Последняя проверка: {m.last_check.error}</p>
				{/if}
			</article>
		{/each}
	</div>
{/if}

<style>
	h1 {
		margin-bottom: 0.25rem;
	}
	.lead {
		color: var(--muted);
		margin-top: 0;
	}
	.grid {
		display: grid;
		gap: 1rem;
		margin-top: 2rem;
	}
	article {
		border: 1px solid var(--border);
		background: var(--card);
		border-radius: 12px;
		padding: 1rem 1.25rem;
	}
	header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	h2 {
		margin: 0;
		font-size: 1.1rem;
	}
	dl {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem 1.75rem;
		margin: 0.75rem 0 0;
		font-size: 0.9rem;
	}
	dl div {
		display: flex;
		gap: 0.4rem;
	}
	dt {
		color: var(--muted);
	}
	dt::after {
		content: ':';
	}
	dd {
		margin: 0;
	}
	dd.warn {
		color: #d97706;
	}
	.error {
		margin: 0.75rem 0 0;
		font-size: 0.9rem;
		color: #dc2626;
	}
	.muted {
		color: var(--muted);
	}
</style>
