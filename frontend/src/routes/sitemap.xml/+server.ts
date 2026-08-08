import { getProjects } from '$lib/server/api';
import { SITE_URL } from '$lib/seo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ fetch }) => {
	const projects = await getProjects(fetch);

	const urls = [
		`  <url><loc>${SITE_URL}/</loc></url>`,
		`  <url><loc>${SITE_URL}/status</loc></url>`,
		...projects.map(
			(p) =>
				`  <url><loc>${SITE_URL}/projects/${p.slug}</loc>` +
				`<lastmod>${p.updated_at.slice(0, 10)}</lastmod></url>`
		)
	].join('\n');

	const xml =
		`<?xml version="1.0" encoding="UTF-8"?>\n` +
		`<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;

	return new Response(xml, {
		headers: { 'Content-Type': 'application/xml', 'Cache-Control': 'max-age=3600' }
	});
};
