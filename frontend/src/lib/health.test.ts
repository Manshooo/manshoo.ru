import { describe, expect, it } from 'vitest';
import { health } from './health';

describe('health', () => {
	it('возвращает ok', () => {
		expect(health()).toEqual({ status: 'ok' });
	});
});
