<script lang="ts">
	import { slide } from 'svelte/transition';
	import ChatAccordion from './ChatAccordion.svelte';
	let { data = [], title = '' } = $props();
</script>

{#if data.length > 0}
	<ChatAccordion {title} isOpen={false}>
		<div class="border border-slate-200">
			{#each data as classification}
				<div class="divide-y divide-slate-200">
					{#each Object.entries(classification) as ite}
						<div class="flex divide-x divide-slate-200 text-sm">
							<p class="w-96 p-3 break-all whitespace-normal text-gray-500">{ite[0]}</p>
							<p class="w-full p-3 {!ite[1] ? ' font-medium' : ''}">{ite[1] || 'missing'}</p>
						</div>
					{/each}
				</div>
			{/each}
		</div>
	</ChatAccordion>
{:else}
	<p class="text-sm text-gray-500 italic">No data to show.</p>
{/if}
