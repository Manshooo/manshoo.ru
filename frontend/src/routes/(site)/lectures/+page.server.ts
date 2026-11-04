import { getCatalog } from '$lib/server/lectures';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => ({
	courses: (await getCatalog(fetch)).map((c) => ({
		slug: c.slug,
		title: c.title,
		description: c.description,
		lecturer: c.lecturer,
		institution: c.institution,
		year: c.year,
		count: c.lectures.length
	}))
});
