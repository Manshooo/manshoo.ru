import { SITE_URL } from '$lib/seo';
import { getLectureRaw } from '$lib/server/api';
import type { RequestHandler } from './$types';

// Исходник лекции как загрузили, вместе с YAML-шапкой: метаданные и лицензия
// едут вместе с текстом, если файл скачают отдельно от сайта.
export const GET: RequestHandler = async ({ fetch, params, url, request }) => {
	const preview = url.searchParams.get('preview') === '1';
	const raw = await getLectureRaw(fetch, params.course, params.slug, {
		preview,
		cookie: preview ? (request.headers.get('cookie') ?? undefined) : undefined
	});
	return new Response(raw, {
		headers: {
			'Content-Type': 'text/markdown; charset=utf-8',
			// тот же текст, что и на HTML-странице: в поиске должна быть она
			Link: `<${SITE_URL}/lectures/${params.course}/${params.slug}>; rel="canonical"`,
			'Cache-Control': preview ? 'no-store' : 'max-age=3600'
		}
	});
};
