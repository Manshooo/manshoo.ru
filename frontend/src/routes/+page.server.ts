import { getProjects } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	return { projects: await getProjects(fetch) };
};
