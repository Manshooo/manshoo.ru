import { getProject } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, params, url, request }) => {
	const preview = url.searchParams.get('preview') === '1';
	return {
		preview,
		project: await getProject(fetch, params.slug, {
			preview,
			cookie: preview ? (request.headers.get('cookie') ?? undefined) : undefined
		})
	};
};
