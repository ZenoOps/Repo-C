<script lang="ts">
	import Icon from '@iconify/svelte';

	let { title = 'No Data Found.' } = $props();
</script>

<div class="flex h-full w-full flex-col items-center justify-center space-y-2 text-slate-700">
	<Icon icon="mingcute:empty-box-line" width="50" height="50" />
	<span>{title}</span>
</div>
