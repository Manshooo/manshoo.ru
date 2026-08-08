// Статусы мониторов от uptime-чекера. Он не опубликован наружу, поэтому
// ходим к нему только с сервера, по внутренней docker-сети.
import { env } from '$env/dynamic/private';
import type { MonitorStatus } from '$lib/types';

const BASE = env.UPTIME_URL ?? 'http://uptime:8080';
const CACHE_TTL_MS = 30_000;

let cache: { at: number; monitors: MonitorStatus[] } | null = null;

/**
 * Статусы всех мониторов. Чекер — необязательная зависимость сайта:
 * если он недоступен, отдаём пустой список, и бейджи просто не рисуются.
 */
export async function getMonitors(fetchFn: typeof fetch): Promise<MonitorStatus[]> {
	if (cache && Date.now() - cache.at < CACHE_TTL_MS) {
		return cache.monitors;
	}
	try {
		const res = await fetchFn(`${BASE}/api/status`, { signal: AbortSignal.timeout(2000) });
		if (!res.ok) throw new Error(`uptime ответил ${res.status}`);
		const monitors: MonitorStatus[] = await res.json();
		cache = { at: Date.now(), monitors };
		return monitors;
	} catch {
		// Не роняем страницу из-за мониторинга: сайт важнее бейджа
		cache = { at: Date.now(), monitors: [] };
		return [];
	}
}

/** Карта slug → статус: удобна для карточек проектов. */
export async function getMonitorMap(fetchFn: typeof fetch): Promise<Record<string, MonitorStatus>> {
	const monitors = await getMonitors(fetchFn);
	return Object.fromEntries(monitors.map((m) => [m.slug, m]));
}
