<script lang="ts">
	import ChatSideBar from '$lib/components/layout/ChatSideBar.svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import Icon from '@iconify/svelte';
	import NavigationBar from '$lib/components/layout/NavigationBar.svelte';
	import MobileNavigator from '$lib/components/layout/MobileNavigator.svelte';
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import { type User } from '$lib/types/user';
	import { userStore } from '$lib/store/userStore';
	import SideBar from '../../lib/components/layout/SideBar.svelte';
	import Button from '$lib/components/UI/Button.svelte';
	let { children } = $props();

	let token: string | null = $state(null);
	let authenticated = $state(false);
	if (browser) {
		token = localStorage.getItem('accessToken');
	}
	let user = $derived(
		browser ? JSON.parse(localStorage.getItem('user') || 'null') : (null as User | null)
	);
	onMount(() => {
		if (browser) {
			if (!token) {
				userStore.updateToken(null);
			}
			userStore.subscribe((value) => {
				if (value === null) {
					authenticated = false;
				} else {
					authenticated = true;
				}
			});
		}
	});
</script>

<div class="flex h-screen flex-col">
	<div class="flex h-full w-full flex-col-reverse lg:flex-row">
		{#if authenticated || token}
			<SideBar />
			{#if page.url.pathname === '/'}
				<MobileNavigator />
			{/if}
		{/if}
		<div class="flex min-h-0 w-full flex-1 flex-col">
			<div class="flex flex-1 flex-col overflow-y-auto lg:flex-row">
				<ChatSideBar />

				<div class="flex h-screen w-full flex-col lg:min-h-0">
					{#if !user.teamId && !user.isSuperuser}
						<div
							class=" top-0 z-30 hidden w-full items-center justify-between bg-white py-4 pr-4 lg:flex"
						>
							<div class="flex w-full items-end justify-end space-x-4">
								<Icon icon="mingcute:search-3-line" width="16" height="16" />
							</div>
						</div>
					{/if}
					<div
						class="h-full flex-1 rounded-t-xl {!user.teamId && !user.isSuperuser
							? 'lg:bg-slate-100'
							: 'lg:bg-white'}"
					>
						{@render children()}
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
