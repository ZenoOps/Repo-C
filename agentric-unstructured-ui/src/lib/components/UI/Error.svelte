<script lang="ts">
	import Icon from '@iconify/svelte';

	let { errMessage = 'Server Error Failed to fetch.' } = $props();
</script>

<div class="flex h-full w-full flex-col items-center justify-center space-y-2 text-slate-700">
	<Icon icon="ic:twotone-error" width="50" height="50" />
	<span>{errMessage}</span>
</div>
