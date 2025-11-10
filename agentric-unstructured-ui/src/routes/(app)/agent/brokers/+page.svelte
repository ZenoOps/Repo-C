<script lang="ts">
	import { goto } from '$app/navigation';
	import RequestStatsCard from '$lib/components/UI/RequestStatsCard.svelte';
	import Table from '$lib/components/UI/Table.svelte';
	import Icon from '@iconify/svelte';

	let statsCardsData = $derived([
		{
			title: 'Total Brokers',
			value: '245',
			description: '',
			icon: 'basil:bag-outline'
		},
		{
			title: 'Total Submissions',
			value: '2220',
			icon: 'hugeicons:google-doc'
		},
		{
			title: 'Response Rate',
			value: '78%',
			description: '',
			icon: 'material-symbols-light:check-rounded'
		},
		{
			title: 'Submission Quality ',
			value: '87%',
			description: '',
			icon: 'streamline-block:other-ui-graph-2'
		}
	]);

	let sampleData = [
		{
			name: 'James Smith',
			status: 'Active',
			responseRate: '85%',
			winRatio: '70%',
			avgResponseTime: '6.2 hrs',
			qualityScore: '90%',
			appetiteFit: 'High',
			pendingQuotes: 5
		}
	];
	let selectedBroker = $state('');
</script>

<div class="h-full w-full space-y-8 px-4 py-6">
	<h4 class="text-2xl font-bold">Broker Profiling Dashboard</h4>
	<div class="grid grid-cols-4 space-x-6">
		{#each statsCardsData as ite}
			<RequestStatsCard
				title={ite.title}
				description={ite.description}
				value={ite.value}
				icon={ite.icon}
			/>
		{/each}
	</div>

	<p class="text-xl font-bold">Broker Performance</p>

	<Table
		headColums={[
			'Broker',
			'Status',
			'Response Rate',
			'Win Ratio',
			'Avg Response Time',
			'Quality Score',
			'Appetite Fit',
			'Pending Quotes',
			'Action'
		]}
	>
		{#each sampleData as broker}
			<tr class="border-b border-slate-200 text-slate-800">
				<th class="px-3 py-4 text-start font-semibold">{broker.name}</th>
				<th class="px-3 py-4 text-start font-medium">
					<div
						role="button"
						onkeydown={() => {}}
						tabindex="0"
						class="borde relative flex w-fit items-center rounded-full border-green-600 bg-green-50 px-2 py-1 text-xs font-semibold text-green-600"
					>
						<span>{broker.status}</span>
					</div></th
				>

				<th class="px-3 py-4 text-start font-medium">{broker.responseRate}</th>
				<th class="px-3 py-4 text-start font-medium">{broker.winRatio}</th>

				<th class="px-3 py-4 text-start font-medium">{broker.avgResponseTime}</th>
				<th class="px-3 py-4 text-start font-medium">{broker.qualityScore}</th>
				<th class="px-3 py-4 text-start font-medium">{broker.appetiteFit}</th>
				<th class="px-3 py-4 text-start font-medium">{broker.pendingQuotes}</th>

				<th class="text-primary px-3 py-4 text-start text-sm font-bold">
					<div class="relative">
						<button class="cursor-pointer" onclick={() => (selectedBroker = broker.name)}
							><Icon icon="ph:dots-three-bold" width="24" height="24" /></button
						>
						{#if selectedBroker === broker.name}
							<div
								class="absolute top-10 right-0 z-60 space-y-2 rounded-md border border-slate-200 bg-white p-3 shadow-lg"
							>
								{#each [{ name: 'View Prolfile', icon: 'mdi-light:eye' }, { name: 'Send Mail', icon: 'uiw:mail-o' }] as ite}
									<button
										onclick={() => goto(`/agent/brokers/${broker.name}`)}
										class="hover:bg-secondary hover:text-primary flex w-full cursor-pointer space-x-2 rounded px-3 py-2 text-slate-800"
									>
										<Icon icon={ite.icon} width="20" height="20" class="" />
										<span class=" text-sm text-nowrap hover:font-semibold">{ite.name}</span>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</th>
			</tr>
		{/each}
	</Table>
</div>
