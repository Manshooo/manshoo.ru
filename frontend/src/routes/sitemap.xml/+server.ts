import { getProjects } from '$lib/server/api';
import { getCatalog } from '$lib/server/lectures';
import { SITE_URL } from '$lib/seo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ fetch }) => {
	// без лекций sitemap всё равно нужен: проекты важнее
	const [projects, catalog] = await Promise.all([
		getProjects(fetch),
		getCatalog(fetch).catch(() => [])
	]);

	const urls = [
		`  <url><loc>${SITE_URL}/</loc></url>`,
		`  <url><loc>${SITE_URL}/status</loc></url>`,
		...projects.map(
			(p) =>
				`  <url><loc>${SITE_URL}/projects/${p.slug}</loc>` +
				`<lastmod>${p.updated_at.slice(0, 10)}</lastmod></url>`
		),
		...(catalog.length ? [`  <url><loc>${SITE_URL}/lectures</loc></url>`] : []),
		...catalog.flatMap((c) => [
			`  <url><loc>${SITE_URL}/lectures/${c.slug}</loc></url>`,
			...c.lectures.map(
				(l) =>
					`  <url><loc>${SITE_URL}/lectures/${c.slug}/${l.slug}</loc><lastmod>${l.updated}</lastmod></url>`
			)
		])
	].join('\n');

	const xml =
		`<?xml version="1.0" encoding="UTF-8"?>\n` +
		`<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;

	return new Response(xml, {
		headers: { 'Content-Type': 'application/xml', 'Cache-Control': 'max-age=3600' }
	});
};
