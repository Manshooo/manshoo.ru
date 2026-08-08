import { getMonitors } from '$lib/server/uptime';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, setHeaders }) => {
	// Данные меняются раз в минуту — незачем дёргать чекер на каждый заход
	setHeaders({ 'cache-control': 'public, max-age=30' });
	return { monitors: await getMonitors(fetch) };
};
