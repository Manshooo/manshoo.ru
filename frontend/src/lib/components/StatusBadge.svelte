<script lang="ts">
	import type { MonitorStatus } from '$lib/types';

	let { monitor, compact = false }: { monitor: MonitorStatus; compact?: boolean } = $props();

	const label = $derived(
		{ up: 'online', down: 'офлайн', unknown: 'проверяется' }[monitor.status] ?? monitor.status
	);
	const uptime = $derived(
		monitor.uptime_30d === null
			? null
			: `${monitor.uptime_30d.toFixed(monitor.uptime_30d === 100 ? 0 : 1)}%`
	);
	const title = $derived(
		uptime ? `Доступность за 30 дней: ${uptime}` : 'Данных о доступности пока нет'
	);
</script>

<span class="badge" data-status={monitor.status} {title}>
	<span class="dot" aria-hidden="true"></span>
	{label}{#if uptime && !compact}<span class="uptime"> · {uptime} за 30 дн.</span>{/if}
</span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.78rem;
		color: var(--muted);
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 0.05rem 0.6rem;
		white-space: nowrap;
	}
	.dot {
		width: 0.45rem;
		height: 0.45rem;
		border-radius: 50%;
		background: var(--muted);
	}
	.badge[data-status='up'] {
		color: #16a34a;
		border-color: color-mix(in srgb, #16a34a 40%, transparent);
	}
	.badge[data-status='up'] .dot {
		background: #16a34a;
	}
	.badge[data-status='down'] {
		color: #dc2626;
		border-color: color-mix(in srgb, #dc2626 40%, transparent);
	}
	.badge[data-status='down'] .dot {
		background: #dc2626;
	}
	.uptime {
		color: var(--muted);
	}
</style>
