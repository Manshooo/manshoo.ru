import { renderMarkdown } from '$lib/markdown';
import { getCourse } from '$lib/server/lectures';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { body_md, lectures, ...course } = await getCourse(fetch, params.course);
	return {
		course,
		// см. (site)/+page.server.ts: marked не должен попадать в клиентский бандл
		bodyHtml: body_md ? renderMarkdown(body_md) : '',
		lectures
	};
};
