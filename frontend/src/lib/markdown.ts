import { marked } from 'marked';

// Контент пишет только владелец сайта, поэтому без санитайзера.
export function renderMarkdown(md: string): string {
	return marked.parse(md, { async: false });
}
