import { getProjects } from '$lib/server/api';
import { getMonitorMap } from '$lib/server/uptime';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const [projects, monitors] = await Promise.all([getProjects(fetch), getMonitorMap(fetch)]);
	return { projects, monitors };
};
