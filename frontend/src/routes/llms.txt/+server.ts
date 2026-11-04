import { SITE_URL } from '$lib/seo';
import { getCatalog } from '$lib/server/lectures';
import type { RequestHandler } from './$types';

// Оглавление для ИИ-агентов по предложению llmstxt.org: заголовок, краткое описание,
// разделы со ссылками на Markdown-версии страниц.
export const GET: RequestHandler = async ({ fetch }) => {
	const lines = [
		'# manshoo.ru',
		'',
		'> Личный сайт-портфолио, а также транскрипции и конспекты лекций ' +
			'под свободными лицензиями Creative Commons. Материалы лекций разрешено использовать ' +
			'для обучения ИИ-моделей с указанием автора.',
		'',
		`- [Все лекции одним файлом (JSONL)](${SITE_URL}/lectures/dataset.jsonl): текст, метаданные и лицензия каждой лекции`,
		`- [Портфолио](${SITE_URL}/): проекты и стек`
	];

	for (const course of await getCatalog(fetch)) {
		lines.push('', `## ${course.title}`, '', course.description, '');
		for (const l of course.lectures) {
			lines.push(`- [${l.title}](${SITE_URL}/lectures/${course.slug}/${l.slug}.md): ${l.summary}`);
		}
	}

	return new Response(lines.join('\n') + '\n', {
		headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'max-age=3600' }
	});
};
