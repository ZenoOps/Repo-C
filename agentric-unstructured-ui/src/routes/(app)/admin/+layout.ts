import { browser } from '$app/environment';
import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = () => {
	if (browser) {
		const user = JSON.parse(localStorage.getItem('user') ?? '');
		if (user && !user.isSuperuser) {
			const patch = '/agent';
			throw redirect(302, patch);
		}
	}
};
