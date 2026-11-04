import { getProfile } from '$lib/server/api';
import { getCatalog } from '$lib/server/lectures';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ fetch }) => {
	// Пункт меню — не повод ронять весь сайт: если api лекций недоступен
	// (или фронтенд задеплоился раньше api), просто прячем ссылку.
	const [profile, catalog] = await Promise.all([
		getProfile(fetch),
		getCatalog(fetch).catch(() => [])
	]);
	// опубликованный, но пустой курс — ещё не повод показывать раздел
	return { profile, hasLectures: catalog.some((c) => c.lectures.length > 0) };
};
