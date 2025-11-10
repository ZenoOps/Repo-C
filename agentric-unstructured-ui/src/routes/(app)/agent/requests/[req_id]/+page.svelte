<script lang="ts">
	import { page } from '$app/state';
	import ArrowStepper from '$lib/components/requests/ArrowStepper.svelte';
	import DocsEmail from '$lib/components/requests/DocsEmail.svelte';
	import RequestDetailHeader from '$lib/components/requests/RequestDetailHeader.svelte';
	import ExtractingData from '$lib/components/requests/riskAnalysis/ExtractingData.svelte';

	import Error from '$lib/components/UI/Error.svelte';
	import Loading from '$lib/components/UI/Loading.svelte';
	import { getReqDetail } from '$lib/query/requests';
	import Icon from '@iconify/svelte';
	import { createMutation, createQuery } from '@tanstack/svelte-query';
	import { mandatories } from './mandatoryField';
	import { APPETITESTATUS } from '$lib/types/request';
	import { slide } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';

	import ClaimPayment from '$lib/components/requests/ClaimPayment/ClaimPayment.svelte';
	import ChatBot from '$lib/components/requests/ChatBot.svelte';
	import { deleteChatHistory } from '$lib/query/chat';
	import Modal from '$lib/components/UI/Modal.svelte';
	import MailTemplateForm from '$lib/components/form/MailTemplateForm.svelte';
	import { openOverlay } from '$lib/store/openOverlay';
	import { isReviewOpen } from '$lib/store/uiStore';

	let reqDetailQuery = $derived(
		createQuery({
			queryKey: ['req_detail', page.params.req_id],
			queryFn: getReqDetail
		})
	);

	let docmentTabs = [
		{
			name:
				$reqDetailQuery.data?.status === APPETITESTATUS.DECLINED
					? 'Declined Reasons'
					: 'Classification',
			value: 1,
			icon: ''
		},
		{
			name: 'Attachment',
			value: 2,
			icon: ''
		}
	];

	let selectedStep = $state('Claim Review');
	let selectedWork = $state('initial');
	let selectedTab = $state(1);
	let isloading = $state(false);

	let conversations = $state([]);

	const deletChatHistoryMutation = createMutation({
		mutationFn: deleteChatHistory,
		onSuccess: () => {
			conversations = [];
		},
		onError: (e) => {
			console.log(e);
		}
	});
</script>

<div class="flex h-full min-h-0 w-full flex-col space-y-4 overflow-hidden px-4 py-4">
	{#if $reqDetailQuery.isLoading}
		<Loading />
	{:else if $reqDetailQuery.isError}
		<Error />
	{:else if $reqDetailQuery.data}
		<div class="flex items-center justify-between">
			<div class="flex w-1/2 items-end justify-between">
				<ArrowStepper bind:selectedStep status={$reqDetailQuery.data.status} bind:selectedWork />
			</div>
			<RequestDetailHeader request={$reqDetailQuery.data} />
		</div>
		<div
			class=" flex h-full w-full flex-1 {$isReviewOpen
				? 'space-x-3'
				: 'space-x-0'} overflow-x-hidden overflow-y-auto"
		>
			<div
				class={`overflow-x-hidden overflow-y-auto transition-all duration-300 ${$isReviewOpen ? 'w-3/5' : 'w-0'}`}
			>
				{#if selectedStep === 'Claim Review'}
					<div class="relative h-full overflow-y-auto">
						<div class="sticky top-0 z-10">
							{#if $isReviewOpen}
								<div
									class="bg-secondary flex w-full cursor-pointer items-center justify-start space-x-4
										rounded-t-md border border-slate-200 px-4 py-3 text-left"
									
								>
									<span class="font-semibold">Review Data</span>
								</div>
								<div in:slide={{ duration: 400, easing: cubicOut }}>
									<div
										class="border-gray flex w-full items-center justify-between border-x border-b border-slate-200 bg-white pr-4"
									>
										<div class="flex space-x-3">
											{#each docmentTabs as ite}
												<button
													class=" flex cursor-pointer items-center space-x-2 p-3 {selectedTab ===
													ite.value
														? 'text-primary border-primary border-b text-sm font-bold'
														: 'text-sm text-slate-400'}"
													onclick={() => (selectedTab = ite.value)}
												>
													<Icon icon="bi:file-text" width="14" height="14" />
													<span class="">{ite.name}</span>
												</button>
											{/each}
										</div>
									</div>
								</div>
							{/if}
						</div>
						{#if $isReviewOpen}
							<div class=" h-auto w-full flex-1 bg-slate-50 px-6 py-4">
								{#if selectedTab === 1}
									<ExtractingData mandatoriesField={mandatories} />
								{:else if selectedTab === 2}
									<DocsEmail />
								{/if}
							</div>
						{/if}
					</div>
				{:else if selectedStep === 'Claim Payment'}
					{#if $isReviewOpen}
						<ClaimPayment
							data={$reqDetailQuery.data}
							isError={$reqDetailQuery.isError}
							bind:isloading
						/>
					{/if}
				{/if}
			</div>

			<div
				class={`flex min-h-0 w-full flex-col rounded-lg border border-slate-200
					transition-all duration-300
					${!$isReviewOpen ? '' : ''}`}
				transition:slide={{ duration: 500, axis: 'x' }}
			>
				<div class="bg-secondary flex justify-between rounded-t-lg px-4 py-3">
					<div class="flex gap-3 justify-center items-center">
					{#if $isReviewOpen}
						<button
							class=""
							onclick={() => isReviewOpen.set(false)}
						>
								<span>
									<Icon
										icon="tabler:arrow-bar-left"
										width="16"
										height="16"
										class="hover:text-primary text-slate-700"
									/>
								</span>
						</button>
					{:else if !$isReviewOpen}
						<button
							class={`flex space-x-2 rounded-md  font-medium  transition-all duration-300
								${$isReviewOpen ? ' ' : 'hover:text-primary text-slate-700 '}
							`}
							onclick={() => isReviewOpen.set(true)}
							title={$isReviewOpen ? "Collapse Review Data" : "Expand Review Data"}
						>
							<Icon icon="streamline-plump:table" width="16" height="16" />
						</button>
					{/if}
						<p class="font-semibold text-nowrap">Claims AI Digital Colleague</p>
					</div>
					<div class="space-x-2">
						<button
							class="hover:text-primary cursor-pointer"
							onclick={() => {
								$deletChatHistoryMutation.mutate(page.params.req_id);
							}}><Icon icon="nrk:reload" width="16" height="16" /></button
						>
					</div>
				</div>
				<ChatBot {conversations} />
			</div>
		</div>
	{/if}
</div>

{#if $openOverlay.name === 'email_preview'}
	<Modal>
		<MailTemplateForm />
	</Modal>
{/if}
