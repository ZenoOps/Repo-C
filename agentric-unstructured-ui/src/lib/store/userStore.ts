import { type User } from '$lib/types/user';
import { writable, get } from 'svelte/store';

function createStore() {
	const { set, subscribe } = writable<User>({
		name: '',
		email: '',
		token: '',
		role: '',
		isSuperuser: false,
		id: '',
		teamId: '',
		teamName: ''
	});

	return {
		subscribe,
		updateInfo: (info: User) => set(info),
		updateToken: (token: string | null) => set({ ...get(userStore), token })
	};
}

export const userStore = createStore();
