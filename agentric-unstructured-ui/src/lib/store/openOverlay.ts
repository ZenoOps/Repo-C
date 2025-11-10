import { writable } from 'svelte/store';

export const openOverlay = writable({ name: '', id: '' });
