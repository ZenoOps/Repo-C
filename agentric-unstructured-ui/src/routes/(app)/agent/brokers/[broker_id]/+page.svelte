<script lang="ts">
	import { page } from '$app/state';
	import BehaviorChart from '$lib/components/broker/BehaviorChart.svelte';
	import SubmitDestributeChart from '$lib/components/broker/SubmitDestributeChart.svelte';
	import SubmitQualityChart from '$lib/components/broker/SubmitQualityChart.svelte';
	import { formatDate } from '$lib/components/helper';
	import Empty from '$lib/components/UI/Empty.svelte';
	import Error from '$lib/components/UI/Error.svelte';
	import FilterButton from '$lib/components/UI/FilterButton.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import RequestStatsCard from '$lib/components/UI/RequestStatsCard.svelte';
	import StatusPill from '$lib/components/UI/StatusPill.svelte';
	import Table from '$lib/components/UI/Table.svelte';
	import { getCusDetail, getReqList } from '$lib/query/requests';
	import { APPETITESTATUS, RequestSubmissionStatus } from '$lib/types/request';
	import Icon from '@iconify/svelte';
	import { createQuery } from '@tanstack/svelte-query';

	let filterstatus: APPETITESTATUS[] = $state([]);
	let reqListQuery = createQuery({
		queryKey: ['list_req_home'],
		queryFn: getReqList
	});
	let tabs = $derived([
		{
			title: 'All',
			count: 0,
			value: []
		},
		{
			title: 'New Requests',
			count: 0,
			value: []
		},
		{
			title: 'Open Requests',
			count: 0,
			value: []
		},
		{
			title: 'In Progress',
			count: 0,
			value: []
		},
		{
			title: 'Closed Requests',
			count: 0,
			value: []
		}
	]);
	let openedTab = $state('All');
	let statsCardsData = $derived([
		{
			title: 'Response Rate',
			value: '20',
			description: '',
			icon: 'material-symbols-light:check-rounded'
		},
		{
			title: 'Avg Response Time',
			value: '4.5 hrs',
			description: '',
			icon: 'weui:time-outlined'
		},
		{
			title: 'Submission Quality ',
			value: '67%',
			description: '',
			icon: 'streamline-block:other-ui-graph-2'
		},
		{
			title: 'Win Ratio',
			value: '85%',
			description: '',
			icon: 'system-uicons:graph-increase'
		}
	]);
	let userInfo = $derived([
		{
			name: 'Email',
			icon: 'uiw:mail-o',
			value: 'example@gmail.com'
		},
		{
			name: 'Phone',
			icon: 'mdi-light:phone',
			value: '11223344'
		},
		{
			name: 'Location',
			icon: 'qlementine-icons:location-16',
			value: 'Miami, FL'
		},
		{
			name: 'Partner Since',
			icon: 'pajamas:calendar',
			value: 'August 3, 2024'
		}
	]);
	let showIndex = $state(2);
</script>

<div class="h-full w-full space-y-8 px-4 py-6">
	<div class="space-y-6 rounded-lg border border-slate-200 p-6 shadow">
		<div class="flex items-center justify-between">
			<div class="bg-green flex items-center space-x-3">
				<span class="bg-secondary text-primary w-fit rounded-full px-3.5 py-3 text-sm font-semibold"
					>{decodeURIComponent(page.params.broker_id).split(' ')[0][0]}{decodeURIComponent(
						page.params.broker_id
					).split(' ')[1][0]}</span
				>
				<div>
					<p class="font-bold">{decodeURIComponent(page.params.broker_id)}</p>
					<p>Meridian Brokers</p>
				</div>
			</div>
			<button class="bg-primary flex space-x-2.5 rounded-md px-6 py-3 text-white"
				><Icon icon="uiw:mail-o" width="24" height="24" />
				<span class="font-semibold">Send Email</span></button
			>
		</div>
		<div class="grid grid-cols-4 gap-x-8">
			{#each userInfo as info}
				<div class="flex items-start space-x-2">
					<Icon icon={info.icon} width="20" height="20" class="text-gray-500" />
					<div class="flex flex-col space-y-2 text-sm">
						<span class="text-slate-600">{info.name}</span><span class="font-medium"
							>{info.value}</span
						>
					</div>
				</div>
			{/each}
		</div>
		<hr class="border-dashed border-slate-200" />
		<div class="space-y-2 text-sm">
			<p class="text-slate-600">Notes</p>
			<p class="font-medium">
				Top-performing broker. Always provides complete information and responds quickly to
				inquiries.
			</p>
		</div>
	</div>
	<div class="grid grid-cols-4 gap-x-6">
		{#each statsCardsData as ite}
			<RequestStatsCard
				title={ite.title}
				description={ite.description}
				value={ite.value}
				icon={ite.icon}
			/>
		{/each}
	</div>
	<div class="flex items-center justify-between">button
		<div class="flex space-x-4">
			{#each tabs as ite}
				<button
					class="flex cursor-pointer space-x-2 rounded-md px-3 py-2 {openedTab === ite.title
						? 'text-secondary bg-primary '
						: 'hover:bg-gray-200'}"
					onclick={() => (openedTab = ite.title)}
				>
					<span class="">{ite.title} </span>
					<span
						class="bg-secondary text-primary block h-6 w-6 rounded-full border p-1 text-xs font-medium"
						>{ite.count}</span
					>
				</button>
			{/each}
		</div>
		<FilterButton bind:selected={filterstatus} />
	</div>
	<h4 class="text-2xl font-bold">Recent Requests</h4>

	{#if $reqListQuery.isLoading}
		<Loading />
	{:else if $reqListQuery.isError}
		<Error />
	{:else if $reqListQuery.data}
		{#if $reqListQuery.data.length}
			<Table
				headColums={[
					'Req Number',
					'Client',
					'Broker',
					'Line of Business',
					'Price',
					'Appetite',
					'Status',
					'Date',
					'Action'
				]}
			>
				{#each $reqListQuery.data.slice(0, showIndex) as req}
					<tr class="border-b border-slate-200 text-slate-800">
						<th class="px-3 py-4 text-start font-semibold">{req.request_number || 'N/A'}</th>
						<th class="px-3 py-4 text-start font-medium">
							{req.client_name}
						</th>
						<th class="px-3 py-4 text-start font-medium">{req.broker_name || 'N/A'}</th>
						<th class="px-3 py-4 text-start font-normal">{'N/A'}</th>
						<th class="px-3 py-4 text-start font-medium">
							{req.premium_amount ? '$' + req.premium_amount : 'N/A'}
						</th>

						<th class="px-3 py-4 text-start font-normal">
							<StatusPill status={req.status} req_id={req.id} />
						</th>
						<th class="px-3 py-4 text-start font-normal">
							<StatusPill status={req.submission_status} />
						</th>

						<th class="px-3 py-4 text-start font-normal text-nowrap"
							>{formatDate(req.created_at)}</th
						>
						<th class="text-primary px-3 py-4 text-start text-sm font-bold">
							<div class="flex h-full items-center justify-center space-x-2">
								{#if APPETITESTATUS.PENDING !== req.status && RequestSubmissionStatus.ERROR !== req.submission_status}
									<a href="/requests/{req.id}" class="underline">Review</a>
								{/if}
							</div>
						</th>
					</tr>
				{/each}
			</Table>
		{:else}
			<Empty />
		{/if}
	{/if}
	<div class="flex items-center justify-center">
		{#if showIndex > 2}
			<button
				onclick={() => (showIndex = $reqListQuery.data ? $reqListQuery.data?.length - 1 : 2)}
				class="text-primary cursor-pointer font-bold underline">View All Requests</button
			>
		{/if}
	</div>
	<h4 class="text-2xl font-bold">Broker Behavior Analytics</h4>
	<div class="grid grid-cols-3 space-x-8">
		<div class="space-y-4 rounded-lg border border-slate-200 p-6">
			<h6 class=" text-sm font-bold">Submission Trend</h6>
			<BehaviorChart />
			<p class=" flex items-center justify-center">
				<Icon icon="icon-park-outline:dot" width="20" height="20" class="text-primary inline" />
				<span>2025</span>
			</p>
		</div>
		<div class="space-y-4 rounded-lg border border-slate-200 p-6">
			<h6 class=" text-sm font-bold">Submission Quality</h6>
			<SubmitQualityChart />
			<ul class="space-y-3 text-sm text-black/70">
				<li class="flex items-center justify-between">
					<span
						><Icon
							icon="icon-park-outline:dot"
							width="20"
							height="20"
							class="text-primary inline"
						/> Complete</span
					>
					<span class="font-medium">88%</span>
				</li>
				<li class="flex items-center justify-between">
					<span
						><Icon
							icon="icon-park-outline:dot"
							width="20"
							height="20"
							class="inline text-slate-200"
						/> Incomplete</span
					>
					<span class="font-medium">12%</span>
				</li>
			</ul>
		</div>
		<div class="space-y-4 rounded-lg border border-slate-200 p-6">
			<h6 class=" text-sm font-bold">Submission Types Distribution</h6>
			<SubmitDestributeChart />
			<ul class="space-y-3 text-sm text-black/70">
				<li class="flex items-center justify-between">
					<span
						><Icon
							icon="icon-park-outline:dot"
							width="20"
							height="20"
							class="inline text-[#8979FF]"
						/> Commercial Property</span
					>
					<span class="font-medium">40%</span>
				</li>
				<li class="flex items-center justify-between">
					<span
						><Icon
							icon="icon-park-outline:dot"
							width="20"
							height="20"
							class="text-primary inline"
						/> General Liability
					</span>
					<span class="font-medium">30%</span>
				</li>
				<li class="flex items-center justify-between">
					<span
						><Icon
							icon="icon-park-outline:dot"
							width="20"
							height="20"
							class="inline text-[#FFAE4C]"
						/> Workers Comp
					</span>
					<span class="font-medium">20%</span>
				</li>
				<li class="flex items-center justify-between">
					<span
						><Icon
							icon="icon-park-outline:dot"
							width="20"
							height="20"
							class="inline text-blue-600"
						/> Auto</span
					>
					<span class="font-medium">10%</span>
				</li>
			</ul>
		</div>
	</div>
	<h4 class="text-2xl font-bold">Communication History</h4>
	<div class="space-y-4">
		{#each [1, 2] as item}
			<div class="space-y-4 rounded-md bg-slate-50 px-3 py-4">
				<div class="flex items-center justify-between">
					<div class="flex space-x-3">
						<span class="text-slate-600">Req Number: <span class="text-primary">REQ-101</span></span
						>
						<span class="flex items-center space-x-3 text-sm"
							><Icon
								icon="icon-park-outline:dot"
								width="20"
								height="20"
								class="inline text-slate-300"
							/> 2025-01-15, 8:45:00 PM</span
						>
						<button class="text-primary text-sm font-semibold underline">View Mail</button>
					</div>
				</div>
				<p class="font-semibold">
					Request for Additional Information – Qatar Plaster Factory LLC (2024/25 Property
					Programme)
				</p>
				<p class="text-sm text-neutral-500">
					Dear James Smith,<br />Thank you for your submission regarding the 2024/25 property
					programme for Qatar Plaster Factory LLC. We have reviewed the documents provided. ...
				</p>
			</div>
		{/each}
	</div>
	<div class="flex items-center justify-center pb-6">
		<button class="text-primary cursor-pointer font-bold underline">View All Communication</button>
	</div>
</div>
