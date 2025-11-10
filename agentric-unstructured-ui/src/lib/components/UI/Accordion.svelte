<script lang="ts">
	import Icon from '@iconify/svelte';
	import { slide } from 'svelte/transition';

	let { isOpen, title, children, fixedView = false, isStickyHeader = true } = $props();
</script>

<div class="relative w-full rounded-md">
	<button
		class="{isStickyHeader
			? 'sticky top-0 z-50'
			: ''} flex w-full cursor-pointer items-center justify-start {isOpen || fixedView
			? 'bg-secondary rounded-t-md'
			: 'rounded-md bg-white'} {fixedView
			? ''
			: 'space-x-4'} border border-slate-200 px-4 py-4.5 text-left"
		disabled={fixedView}
		onclick={() => {
			isOpen = !isOpen;
		}}
	>
		{#if !fixedView}
			<span transition:slide={{ duration: 300 }}>
				<Icon icon={isOpen ? 'oui:arrow-up' : 'oui:arrow-right'} width="20" height="20" />
			</span>
		{/if}

		<span class="font-semibold">{title}</span>
	</button>

	{#if isOpen || fixedView}
		<div
			transition:slide={{ duration: 300 }}
			class=" flex h-full min-h-0 w-full flex-col rounded-b-lg transition-transform duration-300"
		>
			{@render children()}
		</div>
	{/if}
</div>
