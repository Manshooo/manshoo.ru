import { SITE_URL } from '$lib/seo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = () => {
	const body = ['User-agent: *', 'Disallow: /admin', `Sitemap: ${SITE_URL}/sitemap.xml`, ''].join(
		'\n'
	);
	return new Response(body, { headers: { 'Content-Type': 'text/plain' } });
};
