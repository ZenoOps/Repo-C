<script lang="ts">
	import { APPETITESTATUS } from '$lib/types/request';
	import Icon from '@iconify/svelte';

	let { selected = $bindable([]) }: { selected: string[] } = $props();
	let isOpen = $state(false);
	let openfilters = $state(true);

	let options = [
		{ name: 'Partial payment', value: APPETITESTATUS.PARTIAL_PAYMENT },
		{ name: 'Inappetite', value: APPETITESTATUS.APPROVED },
		{ name: 'Pending', value: APPETITESTATUS.PENDING },
		{ name: 'Declined', value: APPETITESTATUS.DECLINED },
		{ name: 'Duplicate', value: APPETITESTATUS.DUPLICATE },
		{ name: 'Missing', value: APPETITESTATUS.MISSING }
	];

	function toggleSelection(value: string) {
		if (selected.includes(value)) {
			selected = selected.filter((v) => v !== value);
		} else {
			selected = [...selected, value];
		}
	}
</script>

<div class="relative">
	<button
		onclick={() => (isOpen = !isOpen)}
		class="border-primary text-primary flex cursor-pointer items-center space-x-1 rounded-md border px-6 py-1.5 font-semibold hover:bg-blue-50"
	>
		<Icon icon="lsicon:filter-outline" width="16" height="16" />
		<span> Filter </span>
	</button>
	{#if isOpen}
		<div
			class="absolute top-10 right-0 z-60 min-w-[310px] rounded-md border border-slate-200 bg-white shadow-lg"
		>
			<div class="flex items-center justify-between border-b border-gray-200 px-6 py-4">
				<h5 class="text-xl font-semibold text-slate-800">Filter</h5>
				<button class="text-primary text-sm font-bold cursor-pointer" onclick={() => (selected = [])}
					>Clear filter</button
				>
			</div>
			<div class="w-full space-y-2.5 p-4 text-slate-800">
				<button
					class="flex w-full cursor-pointer items-center justify-between px-2"
					onclick={() => (openfilters = !openfilters)}
				>
					<span class="font-medium">Appetite</span>
					<svg
						width="16"
						height="17"
						viewBox="0 0 16 17"
						fill="none"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							fill-rule="evenodd"
							clip-rule="evenodd"
							d="M14.354 5.14604C14.4005 5.19248 14.4375 5.24766 14.4627 5.30841C14.4879 5.36915 14.5009 5.43427 14.5009 5.50004C14.5009 5.56581 14.4879 5.63093 14.4627 5.69167C14.4375 5.75242 14.4005 5.80759 14.354 5.85404L8.35396 11.854C8.30752 11.9006 8.25234 11.9375 8.19159 11.9628C8.13085 11.988 8.06573 12.0009 7.99996 12.0009C7.93419 12.0009 7.86907 11.988 7.80833 11.9628C7.74758 11.9375 7.69241 11.9006 7.64596 11.854L1.64596 5.85404C1.55207 5.76015 1.49933 5.63281 1.49933 5.50004C1.49933 5.36726 1.55207 5.23993 1.64596 5.14604C1.73985 5.05215 1.86719 4.99941 1.99996 4.99941C2.13274 4.99941 2.26007 5.05215 2.35396 5.14604L7.99996 10.793L13.646 5.14604C13.6924 5.09948 13.7476 5.06253 13.8083 5.03733C13.8691 5.01212 13.9342 4.99915 14 4.99915C14.0657 4.99915 14.1308 5.01212 14.1916 5.03733C14.2523 5.06253 14.3075 5.09948 14.354 5.14604Z"
							fill="black"
						/>
					</svg>
				</button>
				{#if openfilters}
					<div class="">
						{#each options as ite}
							<label class="flex cursor-pointer items-center space-x-2 p-2">
								<input
									type="checkbox"
									class="peer hidden"
									checked={selected.includes(ite.value)}
									onchange={() => toggleSelection(ite.value)}
								/>

								<!-- Icon (change appearance based on checkbox state) -->
								<div
									class="flex h-5 w-5 items-center justify-center rounded-md border border-gray-300 bg-gray-300 p-1 peer-checked:bg-blue-500 peer-checked:text-white"
								>
									<Icon
										icon="streamline-ultimate:check-bold"
										width="14"
										height="14"
										color="white"
									/>
								</div>

								<span class="text-slate-600">{ite.name}</span>
							</label>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
