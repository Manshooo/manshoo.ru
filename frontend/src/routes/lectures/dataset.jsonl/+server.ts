import { SITE_URL } from '$lib/seo';
import { getLectureDataset } from '$lib/server/api';
import type { RequestHandler } from './$types';

// Все материалы одним файлом, одна лекция — одна JSON-строка: так их удобно
// забрать в датасет (Hugging Face и т. п.). Абсолютный url добавляем здесь.
export const GET: RequestHandler = async ({ fetch }) => {
	const records = await getLectureDataset(fetch);
	const body = records
		.map(
			(r) =>
				// assign, а не spread: id и url остаются первыми ключами строки
				JSON.stringify(Object.assign({ id: r.id, url: `${SITE_URL}/lectures/${r.id}` }, r)) + '\n'
		)
		.join('');
	return new Response(body, {
		headers: {
			'Content-Type': 'application/x-ndjson; charset=utf-8',
			'Content-Disposition': 'inline; filename="manshoo-lectures.jsonl"',
			'Cache-Control': 'max-age=3600'
		}
	});
};
