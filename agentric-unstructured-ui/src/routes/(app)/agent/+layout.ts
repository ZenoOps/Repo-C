import { browser } from '$app/environment';
import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = () => {
	if (browser) {
		// const token = localStorage.getItem('accessToken');
		const user = JSON.parse(localStorage.getItem('user') ?? '');
		if (user && !user.teamName && !user.isSuperuser) throw redirect(302, '/');
	}
};
