import { getProject } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, params }) => {
	return { project: await getProject(fetch, params.slug) };
};
