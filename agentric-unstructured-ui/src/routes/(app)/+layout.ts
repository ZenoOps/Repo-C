import { browser } from '$app/environment';
import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import { validateToken } from '$lib/utils';

export const load: LayoutLoad = () => {
	if (browser) {
		const token = localStorage.getItem('accessToken');

		if (!token || !validateToken(token)) {
			throw redirect(302, '/signin');
		}
	}
};
