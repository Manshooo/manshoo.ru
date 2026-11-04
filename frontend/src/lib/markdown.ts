import { Marked, marked, type TokenizerAndRendererExtension, type Tokens } from 'marked';

// Контент пишет только владелец сайта, поэтому без санитайзера.
export function renderMarkdown(md: string): string {
	return marked.parse(md, { async: false });
}

const escapeHtml = (s: string) =>
	s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/**
 * Формулы $…$ и $$…$$ отдаём как есть, в исходном LaTeX: его одинаково читают
 * люди и модели. Без этого marked ломает их, превращая a_1 … b_1 в курсив.
 * Открывающий $ не перед пробелом, закрывающий — не после, поэтому «$5 и $10» не формула.
 */
const math: TokenizerAndRendererExtension = {
	name: 'math',
	level: 'inline',
	start: (src) => src.indexOf('$'),
	tokenizer(src) {
		const m = /^\$\$([\s\S]+?)\$\$|^\$([^\s$](?:[^$\n]*?[^\s$])?)\$/.exec(src);
		if (m) return { type: 'math', raw: m[0], display: m[1] !== undefined };
	},
	renderer(token) {
		const cls = token.display ? 'math math-display' : 'math';
		return `<span class="${cls}">${escapeHtml(token.raw)}</span>`;
	}
};

export interface TocItem {
	id: string;
	text: string;
}

/** Таймкод «[00:12:30]» в конце заголовка в якорь не идёт. */
const TIMECODE = /\s*\[(?:\d+:)?\d{1,2}:\d{2}\]\s*$/;

export function headingId(text: string): string {
	return (
		text
			.replace(TIMECODE, '')
			.toLowerCase()
			.replace(/ё/g, 'е')
			.replace(/[^\p{L}\p{N}\s-]/gu, '')
			.trim()
			.replace(/[\s-]+/g, '-') || 'section'
	);
}

/** Markdown лекции: формулы как LaTeX, якоря у заголовков, оглавление по h2. */
export function renderLectureMarkdown(md: string): { html: string; toc: TocItem[] } {
	const toc: TocItem[] = [];
	const used = new Map<string, number>();

	const renderer = new Marked({ extensions: [math] });
	renderer.use({
		renderer: {
			heading({ tokens, depth, text }: Tokens.Heading) {
				let id = headingId(text);
				const seen = used.get(id) ?? 0;
				used.set(id, seen + 1);
				if (seen) id = `${id}-${seen + 1}`;
				if (depth === 2) toc.push({ id, text: text.replace(TIMECODE, '') });
				return `<h${depth} id="${id}">${this.parser.parseInline(tokens)}</h${depth}>\n`;
			}
		}
	});

	const html = renderer.parse(md, { async: false });
	return { html, toc };
}
