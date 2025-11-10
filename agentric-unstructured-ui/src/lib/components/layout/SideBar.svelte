<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Icon from '@iconify/svelte';
	import { slide } from 'svelte/transition';
	import { logOut } from '../helper';
	import { type User } from '$lib/types/user';
	import { isReviewOpen } from '$lib/store/uiStore';
	import Button from '../UI/Button.svelte';

	let user: User = $derived(browser ? JSON.parse(localStorage.getItem('user') ?? '') : null);

	let steps = [
		{ name: 'Dashboard', path: '/agent', icon: 'hugeicons:menu-square' },
		{ name: 'Requests', path: '/agent/requests', icon: 'iconoir:page-edit' },
		{ name: 'Team', path: '/admin/team', icon: 'ri:team-line' },
		{ name: 'User', path: '/admin', icon: 'basil:user-outline' },
		{ name: 'Chat', path: '/', icon: 'mage:message-dots' }
	];
	let openSideBar = $state(false);

	let currentStep = $derived(page.url.pathname);
</script>

<div
	class="bg-secondary hidden {openSideBar
		? 'min-w-[230px]'
		: 'w-fit'} hidden flex-col justify-between px-4 py-3 lg:flex"
>
	<div>
		<div
			class="relative flex items-center space-y-3 py-1 {openSideBar
				? 'space-x-3 '
				: ''} border-b border-dashed border-white"
			transition:slide={{ duration: 300 }}
		>
			<img src="/agentric_logo.png" alt="Agentric Logo" class="h-10 w-10" />
			{#if openSideBar}
				<h4 class="text-primary text-xl font-bold">AgentricAI</h4>
			{/if}

			<Button
				class="absolute top-1 -right-7 cursor-pointer rounded-full border border-gray-200 bg-white p-1.5"
				onclick={() => (openSideBar = !openSideBar)}
			>
				<Icon icon={openSideBar ? 'ep:arrow-left' : 'ep:arrow-right'} width="14" height="14" />
			</Button>
		</div>
		<div class="flex flex-col space-y-3 py-4">
			{#each steps.filter( (ite) => (user.isSuperuser ? ite.path.startsWith('/admin') : user.teamId ? ite.path.startsWith('/agent') : !ite.path.startsWith('/agent') && !ite.path.startsWith('/admin')) ) as step}
				<button
					onclick={() => {
						goto(step.path);
						isReviewOpen.set(true);
					}}
					class="flex space-x-2 rounded-md p-3 font-medium {currentStep === step.path
						? 'bg-primary text-white'
						: 'text-slate-700 hover:bg-slate-100'}"
				>
					<Icon icon={step.icon} width="20" height="20" />
					{#if openSideBar}
						<span>{step.name}</span>
					{/if}
				</button>
			{/each}
			
		</div>
	</div>
	<div
		class="flex {openSideBar
			? 'flex-row items-center justify-between'
			: 'flex-col items-center space-y-6'} border-t border-dashed border-white pt-4"
		transition:slide={{ duration: 300 }}
	>
		{#if user}
			<div class="flex items-center space-x-2">
				<div
					class="bg-primary flex h-10 w-10 items-center justify-center rounded-full pt-0.5 font-bold text-white"
				>
					{user.name ? user.name[0]?.toUpperCase() : user.email[0]?.toUpperCase()}
				</div>
				{#if openSideBar}
					<p class="text-primary font-bold text-nowrap">
						{user.name ? user.name : user.email?.split('@')[0]}
					</p>
				{/if}
			</div>
		{/if}

		<button
			class="cursor-pointer"
			onclick={() => {
				logOut();
			}}
		>
			<Icon icon="material-symbols:logout-rounded" width="24" height="24" />
		</button>
	</div>
</div>
