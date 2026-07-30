import { describe, expect, it } from 'vitest';
import { formatPeriod } from './format';

describe('formatPeriod', () => {
	it('открытый период оканчивается на «н. в.»', () => {
		const s = formatPeriod('2026-07-01', null);
		expect(s).toContain('2026');
		expect(s).toContain('н. в.');
	});

	it('закрытый период содержит обе даты', () => {
		const s = formatPeriod('2025-01-01', '2026-02-01');
		expect(s).toContain('2025');
		expect(s).toContain('2026');
	});
});
