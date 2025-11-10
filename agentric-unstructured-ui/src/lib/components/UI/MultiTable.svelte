<script lang="ts">
	let { data } = $props<{
		data: Array<Record<string, string | boolean | number> | string | number | boolean>;
	}>();

	let tableData: Array<Record<string, string | boolean | number> | string | number | boolean> =
		$derived(data ? data : []);

	let headers = $derived(tableData.length ? Object.keys(tableData[0]) : []);
</script>

{#if tableData.length}
	<div class="overflow-auto rounded p-4">
		{#if typeof tableData[0] === 'object'}
			<table class="w-full table-auto border-collapse text-sm">
				<thead class="bg-secondary">
					<tr>
						{#each headers as header}
							<th
								class="border border-gray-300 px-4 py-4 text-left font-medium whitespace-nowrap text-gray-700"
							>
								{header.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each tableData as row}
						{#if typeof row === 'object' && row !== null}
							<tr class="">
								{#each headers as key}
									<td class="border border-gray-200 px-4 py-4">
										{#if typeof row[key] == 'string'}
											{row[key].replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()) ?? '—'}
										{:else if typeof row[key] == 'boolean'}
											<span
												class="font-semibold {(row as Record<string, any>)[key]
													? 'text-red-800'
													: 'text-green-800'}"
											>
												{(row as Record<string, any>)[key] ? 'YES' : 'NO'}
											</span>
										{:else}
											{(row as Record<string, any>)[key] ?? '—'}
										{/if}
									</td>
								{/each}
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		{:else}
			<!-- {#each  as item} -->
			<p class="w-2/3 max-w-[500px] min-w-[300px] text-gray-500">
				{tableData.map((ite) => ite).join(', ')}
			</p>
			<!-- {/each} -->
		{/if}
	</div>
{:else}
	<p class="w-2/3 max-w-[500px] min-w-[300px] p-4 text-gray-500">N/A</p>
{/if}
