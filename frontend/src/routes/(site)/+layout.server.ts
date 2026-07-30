import { getProfile } from '$lib/server/api';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ fetch }) => {
	return { profile: await getProfile(fetch) };
};
