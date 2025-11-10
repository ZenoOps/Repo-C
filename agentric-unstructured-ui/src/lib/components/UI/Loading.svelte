<script lang="ts">
	import Icon from '@iconify/svelte';
	let { removeText = false } = $props();
</script>

<div class="flex h-full w-full flex-col items-center justify-center space-y-2 text-slate-700">
	<Icon icon="eos-icons:loading" width="50" height="50" />
	{#if !removeText}
		<span>Loading data...</span>
	{/if}
</div>
