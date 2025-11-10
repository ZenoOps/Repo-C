<script lang="ts">
	import Icon from '@iconify/svelte';
	import { slide } from 'svelte/transition';

	let { isOpen, title, children } = $props();
</script>

<div class="w-full rounded-md">
	<button
		class="flex w-full cursor-pointer items-center justify-start {isOpen
			? 'bg-purple-100 rounded-t-md'
			: 'rounded-md bg-gray-50'}  space-x-4 border border-slate-200 px-4 py-2 text-left"
		onclick={() => {
			isOpen = !isOpen;
		}}
	>
		<div class="w-full flex space-x-3 items-center">
			<p transition:slide={{ duration: 300 }}>
				<Icon icon={isOpen ? 'bxs:up-arrow' : 'bxs:right-arrow'} width="14" height="14" />
            </p>
			<span class="font-medium text-slate-800">{title}</span>
		</div>
        <div>
            <!-- <button></button> -->
        </div>
	</button>

	{#if isOpen}
		<div
			transition:slide={{ duration: 300 }}
			class="w-full rounded-b-lg transition-transform duration-300"
		>
			{@render children()}
		</div>
	{/if}
</div>
