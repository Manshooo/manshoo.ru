// Серверный клиент api: SSR-фетчи идут по внутренней docker-сети.
import { env } from '$env/dynamic/private';
import { error } from '@sveltejs/kit';
import type { Profile, ProjectCard, ProjectDetail } from '$lib/types';

const BASE = env.API_URL ?? 'http://api:8000';

async function getJSON<T>(fetchFn: typeof fetch, path: string, cookie?: string): Promise<T> {
	const res = await fetchFn(`${BASE}${path}`, cookie ? { headers: { cookie } } : undefined);
	if (!res.ok) {
		error(res.status === 404 ? 404 : 502, res.status === 404 ? 'Не найдено' : 'API недоступен');
	}
	return res.json();
}

export const getProfile = (fetchFn: typeof fetch) => getJSON<Profile>(fetchFn, '/api/profile');

export const getProjects = (fetchFn: typeof fetch) =>
	getJSON<ProjectCard[]>(fetchFn, '/api/projects');

/**
 * preview + cookie владельца отдают черновик: сессионная кука общая для
 * manshoo.ru и api.manshoo.ru (SESSION_COOKIE_DOMAIN), поэтому её можно
 * передать дальше — проверку прав делает api.
 */
export const getProject = (
	fetchFn: typeof fetch,
	slug: string,
	options: { preview?: boolean; cookie?: string } = {}
) => {
	const path = `/api/projects/${encodeURIComponent(slug)}${options.preview ? '?preview=1' : ''}`;
	return getJSON<ProjectDetail>(fetchFn, path, options.cookie);
};
