<script lang="ts">
	import { openOverlay } from '$lib/store/openOverlay';
	import { onDestroy, onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	let {
		style = '',
		show = $bindable(true),
		useInBox = false,
		notoutsideclose = true,
		children
	}: {
		style?: string;
		show?: boolean;
		useInBox?: boolean;
		notoutsideclose?: boolean;
		children: any;
	} = $props();

	$effect(() => {
		if ($openOverlay.name !== '') {
			document.body.classList.add('overflow-hidden');
		} else {
			document.body.classList.remove('overflow-hidden');
		}
	});

	onMount(() => {
		document.body.classList.add('overflow-hidden');
	});

	onDestroy(() => {
		document.body.classList.remove('overflow-hidden');
	});
</script>

{#if show && $openOverlay.name}
	<div
		class="fixed inset-0 z-50 grid min-h-screen place-items-center p-4 px-8"
		transition:fade|local={{ duration: 100 }}
	>
		<div
			class="absolute inset-0 cursor-default bg-black/50"
			onclick={() => {
				if (!notoutsideclose) {
					// if (!useInBox) {
					openOverlay.set({ name: '', id: '' });
					// }
				}
			}}
			onkeydown={() => {}}
			role="button"
			tabindex="0"
		></div>
		<div class="z-30 {style} max-h-screen overflow-y-auto rounded-lg bg-white">
			{@render children()}
		</div>
	</div>
{/if}
