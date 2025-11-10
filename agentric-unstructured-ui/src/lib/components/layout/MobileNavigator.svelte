<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Icon from '@iconify/svelte';
	import Button from '../UI/Button.svelte';

	let steps = [
		{ name: 'Chat', path: '/', icon: 'mage:message-dots' },
		{ name: 'Setting', path: '/setting', icon: 'lets-icons:setting-line' },
		{ name: 'Profile', path: '/requests', icon: 'gravity-ui:person' }
	];
	let currentStep = $derived(page.url.pathname);
</script>

<div class="bg-secondary flex justify-around lg:hidden">
	{#each steps as item}
		<Button
			class="hover:bg-secondary/50 py-4"
			onclick={() => {
				if (item.path === '/') {
					goto(item.path);
				}
			}}
		>
			<span class="flex rounded-lg p-2 {currentStep === item.path ? 'bg-primary text-white' : ''}">
				<Icon icon={item.icon} width="16" height="16" /></span
			>
		</Button>
	{/each}
</div>
