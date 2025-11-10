<script lang="ts">
	let { headColums, children } = $props();
</script>

<table class="table-auto min-w-full ">
	<thead>
		<tr class="rounded-md bg-slate-100">
			{#each headColums as col, i}
				<th
					class="py-3 px-2 text-start font-medium text-slate-600 {i === 0
						? 'rounded-l-md'
						: headColums.length - 1 === i
							? 'rounded-r-md'
							: ''}">{col}</th
				>
			{/each}
		</tr>
	</thead>
	<tbody>
		{@render children()}
	</tbody>
</table>
