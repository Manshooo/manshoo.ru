import { env } from '$env/dynamic/public';
import { getProject } from '$lib/server/api';
import { getMonitorMap } from '$lib/server/uptime';
import type { PageServerLoad } from './$types';

// og:image открывают чужие серверы (Telegram, соцсети), поэтому ссылка
// должна вести на публичный адрес api, а не на внутренний docker-хост.
const PUBLIC_API = env.PUBLIC_API_URL ?? 'https://api.manshoo.ru';

export const load: PageServerLoad = async ({ fetch, params, url, request }) => {
	const preview = url.searchParams.get('preview') === '1';
	const project = await getProject(fetch, params.slug, {
		preview,
		cookie: preview ? (request.headers.get('cookie') ?? undefined) : undefined
	});

	const monitors = project.uptime_monitor_slug ? await getMonitorMap(fetch) : {};
	return {
		preview,
		project,
		monitor: monitors[project.uptime_monitor_slug] ?? null,
		// у черновика публичной картинки ещё нет
		ogImage: project.is_published
			? `${PUBLIC_API}/api/projects/${encodeURIComponent(project.slug)}/og.png`
			: null
	};
};
