<script lang="ts">
	import Icon from '@iconify/svelte';

	let { title, value, description, icon = 'hugeicons:google-doc' } = $props();
</script>

<div class="border-secondary space-y-4 border border-t-5 p-4 w-full">
	<div class="flex justify-between">
		<p class="text-sm font-medium">{title}</p>
		<p class="bg-secondary w-fit rounded-full lg:p-2 p-1 flex justify-center items-center">
			<Icon {icon} width="16" height="16" class="text-primary" />
		</p>
	</div>
	<p class="text-2xl font-bold">{value}</p>
	<span class="text-sm text-slate-500">{description}</span>
</div>
