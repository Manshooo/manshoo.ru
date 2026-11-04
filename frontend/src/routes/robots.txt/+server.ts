import { SITE_URL } from '$lib/seo';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = () => {
	// Отдельных правил для ИИ-краулеров (GPTBot, ClaudeBot, CCBot…) нет намеренно:
	// «*» пускает их везде, кроме админки, а лекции для них и выложены (docs/09-lectures.md).
	const body = [
		'User-agent: *',
		'Disallow: /admin',
		'',
		'# Лекции: свободные лицензии CC, обучение моделей разрешено (условия — на страницах)',
		`# Датасет: ${SITE_URL}/lectures/dataset.jsonl`,
		`Sitemap: ${SITE_URL}/sitemap.xml`,
		''
	].join('\n');
	return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
