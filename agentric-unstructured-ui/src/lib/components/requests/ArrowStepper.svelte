<script lang="ts">
	import { APPETITESTATUS } from '$lib/types/request';
	import Icon from '@iconify/svelte';
	import { isReviewOpen } from '$lib/store/uiStore';

	let {
		selectedStep = $bindable('Claim Review'),
		status,
		selectedWork = $bindable('initial')
	}: {
		selectedStep: string;
		status: APPETITESTATUS;
		selectedWork: string;
	} = $props();

	// temporay remove ---> 'Policy Alignment'

	let stepArray = ['Claim Review', 'Claim Payment'];
</script>

<div class="relative flex w-fit items-center justify-center text-sm font-medium">
	<button
		class="text-slate-700 hover:text-primary hover:bg-secondary ms-1 me-2 rounded-sm p-1"
		onclick={() => {
			isReviewOpen.set(true);
			history.back();
		}}
	>
		<Icon icon="stash:arrow-left" width="20" height="20" />
	</button>

	<button
		class="relative block w-fit cursor-pointer"
		onclick={() => {
			selectedStep = 'Claim Review';
			selectedWork = 'initial';
		}}
	>
		<div
			class="clip-arrow-left {stepArray.indexOf(selectedStep) >= 0
				? 'border-primary bg-primary text-primary'
				: 'border-slate-200 bg-slate-50 text-slate-500'} h-full border px-6.5 py-2 font-semibold text-nowrap"
		>
			Claim Review
		</div>
		{#if stepArray.indexOf(selectedStep) >= 0}
			<div
				class="over-clip-arrow-left text-primary bg-secondary absolute inset-y-0.5 left-0.5 w-full py-2 font-semibold text-nowrap"
			>
				Claim Review
			</div>
		{/if}
	</button>

	<button
		class="relative block w-fit {[APPETITESTATUS.DECLINED, APPETITESTATUS.MISSING].includes(status)
			? ''
			: 'cursor-pointer'}"
		disabled={[APPETITESTATUS.DECLINED, APPETITESTATUS.MISSING].includes(status)}
		onclick={() => {
			selectedStep = 'Claim Payment';
		}}
	>
		<div
			class="clip-arrow-right w-full {stepArray.indexOf(selectedStep) >= 1
				? 'border-primary bg-primary text-primary'
				: 'border-slate-200 bg-slate-50 text-slate-500'} h-full -translate-x-4 border px-6.5 py-2 text-nowrap"
		>
			Claim Payment
		</div>
		{#if stepArray.indexOf(selectedStep) >= 1}
			<div
				class="over-clip-arrow-right text-primary bg-secondary absolute inset-y-0.5 left-0.5 w-full -translate-x-4.5 px-6.5 py-2 font-bold text-nowrap text-nowrap"
			>
				Claim Payment
			</div>
		{/if}
	</button>

	<!-- <button
		class="relative block w-fit {[APPETITESTATUS.DECLINED, APPETITESTATUS.MISSING].includes(status)
			? ''
			: 'cursor-pointer'}"
		disabled={[APPETITESTATUS.DECLINED, APPETITESTATUS.MISSING].includes(status)}
		onclick={() => {
			selectedStep = 'Claim Payment';
			selectedWork = 'quoted';
		}}
	>
		<div
			class="clip-arrow-right {stepArray.indexOf(selectedStep) >= 2
				? 'border-primary bg-primary text-primary -translate-x-10'
				: '-translate-x-9 border-slate-200 bg-slate-50 text-slate-500'} h-full border px-6.5 py-3"
		>
			Claim Payment
		</div>
		{#if stepArray.indexOf(selectedStep) >= 2}
			<div
				class="over-clip-arrow-right text-primary bg-secondary absolute inset-y-0.5 left-0.5 w-full -translate-x-9.5 px-4 py-2 font-bold"
			>
				Claim Payment
			</div>
		{/if}
	</button> -->
</div>

<style>
	.clip-arrow-right {
		clip-path: polygon(0 0, calc(100% - 22px) 0, 96% 50%, calc(100% - 22px) 100%, 0 100%, 15px 50%);
	}
	.over-clip-arrow-right {
		clip-path: polygon(0 0, calc(100% - 22px) 0, 95% 50%, calc(100% - 22px) 100%, 0 100%, 15px 50%);
	}

	.clip-arrow-left {
		clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 50%, calc(100% - 15px) 100%, 0 100%);
	}
	.over-clip-arrow-left {
		clip-path: polygon(0 0, calc(100% - 19px) 0, 97% 50%, calc(100% - 19px) 100%, 0 100%);
	}
</style>
