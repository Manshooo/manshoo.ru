// Клиент админки: браузер ходит на api.manshoo.ru напрямую (cross-origin,
// но same-site), поэтому нужны credentials и X-CSRFToken.
import { env } from '$env/dynamic/public';
import type { Profile, ProjectDetail } from '$lib/types';

const BASE = env.PUBLIC_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
	}
}

// Куку csrf выставляет api.manshoo.ru, и с manshoo.ru её не прочитать —
// поэтому токен берём эндпоинтом и держим в памяти вкладки.
let csrfToken: string | null = null;

async function getCsrfToken(force = false): Promise<string> {
	if (!csrfToken || force) {
		const res = await fetch(`${BASE}/api/auth/csrf`, { credentials: 'include' });
		csrfToken = (await res.json()).csrf_token;
	}
	return csrfToken!;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
	const method = init.method ?? 'GET';
	const headers = new Headers(init.headers);
	if (method !== 'GET') {
		headers.set('X-CSRFToken', await getCsrfToken());
	}

	const res = await fetch(`${BASE}${path}`, { ...init, headers, credentials: 'include' });
	if (!res.ok) {
		let detail = `Ошибка ${res.status}`;
		try {
			detail = (await res.json()).detail ?? detail;
		} catch {
			// тело без JSON — оставляем общий текст
		}
		throw new ApiError(res.status, detail);
	}
	return res.status === 204 ? (null as T) : res.json();
}

const json = (method: string, body: unknown): RequestInit => ({
	method,
	body: JSON.stringify(body),
	headers: { 'Content-Type': 'application/json' }
});

export const api = {
	async login(username: string, password: string) {
		await getCsrfToken(true);
		const me = await request<{ username: string }>(
			'/api/auth/login',
			json('POST', { username, password })
		);
		// Django ротирует csrf-токен при входе — старый уже недействителен
		await getCsrfToken(true);
		return me;
	},
	logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
	me: () => request<{ username: string }>('/api/auth/me'),

	listProjects: () => request<ProjectDetail[]>('/api/admin/projects'),
	getProject: (id: number) => request<ProjectDetail>(`/api/admin/projects/${id}`),
	createProject: (data: unknown) =>
		request<ProjectDetail>('/api/admin/projects', json('POST', data)),
	updateProject: (id: number, data: unknown) =>
		request<ProjectDetail>(`/api/admin/projects/${id}`, json('PUT', data)),
	deleteProject: (id: number) => request<null>(`/api/admin/projects/${id}`, { method: 'DELETE' }),

	async uploadCover(id: number, file: File) {
		const form = new FormData();
		form.append('file', file);
		return request<ProjectDetail>(`/api/admin/projects/${id}/cover`, {
			method: 'POST',
			body: form
		});
	},
	deleteCover: (id: number) =>
		request<ProjectDetail>(`/api/admin/projects/${id}/cover`, { method: 'DELETE' }),

	getProfile: () => request<Profile>('/api/profile'),
	updateProfile: (data: unknown) => request<Profile>('/api/admin/profile', json('PUT', data))
};
