<script lang="ts">
	import Icon from '@iconify/svelte';

	let {
		currentPage = $bindable(1),
		total,
		limit = 20,
		offset = 0
	}: {
		currentPage: number;
		total: number;
		limit: number;
		offset: number;
	} = $props();

	let totalPageArray = $derived(
		Array.from({ length: Math.ceil(total / limit) }, (_, i: number) => i + 1)
	);
	let firstIndex = $state(0);
	let lastIndex = $state(6);

	$effect(() => {
		if (currentPage > lastIndex) {
			firstIndex += 1;
			lastIndex += 1;
		} else if (currentPage <= firstIndex) {
			firstIndex -= 1;
			lastIndex -= 1;
		} else if (lastIndex === totalPageArray.length - 1) {
			lastIndex = lastIndex;
		}
	});
</script>

<div class="flex w-full items-center rounded-full px-3 lg:justify-between">
	<p class="hidden w-fit text-xs font-bold text-nowrap text-neutral-500 lg:block">
		Showing <span class="text-primary">{offset + limit < total ? offset + limit : total}</span>
		of
		<span class="text-primary">{total}</span> results
	</p>
	<div class="flex w-fit border-collapse items-center space-x-4">
		<button
			onclick={() => {
				currentPage = currentPage - 1;
			}}
			disabled={currentPage === 1}
			class="{currentPage === 1 ? ' text-gray-400' : ' text-black'} text-xs font-bold lg:text-base"
		>
			<Icon icon="ic:round-navigate-before" width="24" height="24" />
		</button>
		<div class="flex items-center">
			{#each totalPageArray.slice(firstIndex, lastIndex) as page}
				<button
					class="{currentPage === page
						? ' bg-primary text-white'
						: 'bg-white'} rounded-lg border border-gray-200 px-2 py-1 text-xs"
					onclick={() => {
						currentPage = page;
					}}
				>
					{page}
				</button>
			{/each}
			{#if totalPageArray.length === 0}
				<span
					class="inline-block w-fit cursor-pointer px-2 py-1 text-xs font-bold drop-shadow-lg lg:px-4 lg:text-base"
					>---</span
				>
			{/if}
		</div>
		<button
			onclick={() => {
				currentPage = currentPage + 1;
			}}
			disabled={currentPage === Math.ceil(total / limit)}
			class="{currentPage === Math.ceil(total / limit)
				? ' text-gray-400'
				: ' text-black '} text-xs font-bold lg:text-base"
		>
			<Icon icon="ic:round-navigate-next" width="24" height="24" />
		</button>
	</div>
</div>
