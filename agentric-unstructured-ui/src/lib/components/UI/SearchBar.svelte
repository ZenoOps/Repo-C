<script lang="ts">
	import Icon from '@iconify/svelte';

	let { value = $bindable<string | null>(null)} = $props();
</script>

<div class="relative m-3 h-9">
	<input
		bind:value={value}
		type="text"
		placeholder="Search"
		class="focus:border-primary-600 w-full rounded-lg bg-gray-50 py-2 pr-3 pl-8 text-sm placeholder-slate-600 focus:outline-none"
	/>
	<Icon
		icon="mdi:magnify"
		class="absolute top-1/2 left-2 -translate-y-1/2 text-gray-400"
		width="18"
		height="18"
	/>
</div>
