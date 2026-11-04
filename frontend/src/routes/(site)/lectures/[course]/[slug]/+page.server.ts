import { renderLectureMarkdown } from '$lib/markdown';
import { getLecture } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, params, url, request }) => {
	const preview = url.searchParams.get('preview') === '1';
	const { body_md, course, prev, next, ...lecture } = await getLecture(
		fetch,
		params.course,
		params.slug,
		{ preview, cookie: preview ? (request.headers.get('cookie') ?? undefined) : undefined }
	);
	// Markdown разворачиваем на сервере, исходник в клиент не отправляем: HTML уже на странице
	const { html, toc } = renderLectureMarkdown(body_md);
	return { preview, course, lecture, html, toc, prev, next };
};
