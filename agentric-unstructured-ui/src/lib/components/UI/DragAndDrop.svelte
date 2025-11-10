<script lang="ts">
	import { browser } from '$app/environment';
	import { uploadClaimFile } from '$lib/query/chat';
	import { openOverlay } from '$lib/store/openOverlay';
	import Icon from '@iconify/svelte';
	import { onMount, tick } from 'svelte';
	import toast from 'svelte-french-toast';

	let {
		uploadedFiles = $bindable([]),
		isloading = $bindable(false),
		attachmentIds = $bindable([]),
		uploadURL = '',
		uploadeMethod = '',
		onsubmit = () => {}
	}: {
		uploadedFiles: FileList | [];
		isloading?: boolean;
		attachmentIds: string[];
		uploadURL: string;
		uploadeMethod: string;
		onsubmit: () => void;
	} = $props();

	let scrollContainer: HTMLDivElement | null = $state(null);
	let scrollAtStart = $state(true);
	let scrollAtEnd = $state(false);
	let canScroll = $state(false);

	function checkScroll() {
		if (!scrollContainer) return;
		const { scrollWidth, clientWidth } = scrollContainer;
		canScroll = scrollWidth > clientWidth + 1;
		handleScroll();
	}

	function handleScroll() {
		if (scrollContainer) {
			const { scrollLeft, scrollWidth, clientWidth } = scrollContainer;
			scrollAtStart = scrollLeft <= 0;
			scrollAtEnd = scrollLeft + clientWidth >= scrollWidth - 5;
		}
	}

	onMount(() => {
		checkScroll();
		if (scrollContainer && browser) {
			window.addEventListener('resize', checkScroll);
		}
		return () => window.removeEventListener('resize', checkScroll);
	});

	$effect(() => {
		if (scrollContainer && browser) {
			checkScroll();
			window.addEventListener('resize', checkScroll);
		}
	});

	let isUploading = $state(false);
	let isDragging = $state(false);
	let selectedFiles: File[] = $state([]);
	let uploadedIndexs: number[] = $state([]);

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragging = true;
	}

	function handleDragLeave() {
		isDragging = false;
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragging = false;
		const files = event.dataTransfer?.files;
		if (files) {
			uploadedFiles = files;
			handleFileChange(files);
		}
	}
	function handleOnchage(e: Event) {
		const target = e.target as HTMLInputElement;
		const files = target.files;
		if (files) {
			uploadedFiles = files;
			handleFileChange(files);
		}
	}

	async function handleFileChange(files: FileList | []) {
		if (!files.length) return;

		selectedFiles = Array.from(files);
		isUploading = true;
		try {
			let index = 0;

			for (const file of selectedFiles) {
				const formData = new FormData();
				let attachmentId = '';
				formData.append('files', file);
				attachmentId = (
					await uploadClaimFile({
						url: uploadURL,
						data: formData,
						method: uploadeMethod
					})
				).attachment_id;
				attachmentIds = [...attachmentIds, attachmentId];
				uploadedIndexs = [...uploadedIndexs, index];
				index++;
			}
		} catch (e) {
			isUploading = false;
			toast.error('Failed to upload File.');
		} finally {
			isUploading = false;
		}
	}
</script>

<div class="flex flex-col items-center justify-center">
	<div role="button" tabindex="0" class="flex min-w-[600px] flex-col space-y-4 px-8 py-6">
		<div class="flex items-center justify-between text-slate-800">
			<h2 class="text-xl font-bold">Upload Files</h2>
			<button type="button" onclick={() => openOverlay.set({ name: '', id: '' })}>
				<Icon icon="charm:cross" width="16" height="16" />
			</button>
		</div>
		<div
			ondragover={handleDragOver}
			ondragleave={handleDragLeave}
			ondrop={handleDrop}
			class="flex min-h-[170px] w-full flex-col items-center justify-center space-y-3 rounded-md border border-dashed transition-colors duration-150"
			class:border-primary={isDragging}
			class:bg-slate-50={isDragging}
		>
			<input type="file" multiple class="hidden" onchange={handleOnchage} />
			<p class="flex items-center justify-center rounded-full bg-white">
				<Icon icon="tabler:upload" width="24" height="24" />
			</p>
			<button
				class="font-medium"
				onclick={() => (document.querySelector('input[type="file"]') as HTMLElement).click()}
				><span class="text-primary">Click to upload </span>
				<span>or drag & drop file</span></button
			>
		</div>
		{#if selectedFiles.length}
			<div class=" flex h-20 w-full max-w-[600px] items-center space-x-2">
				{#if canScroll && !scrollAtStart}
					<button
						type="button"
						class="z-10 hover:bg-slate-100"
						onclick={() => {
							if (scrollContainer) {
								scrollContainer.scrollBy({ left: -200, behavior: 'smooth' });
							}
						}}
					>
						<Icon icon="mdi:chevron-left" width="20" height="20" />
					</button>
				{/if}

				<div
					bind:this={scrollContainer}
					onscroll={handleScroll}
					class="relative flex h-full w-full flex-1 space-x-2 overflow-x-auto scroll-smooth py-2"
				>
					{#each selectedFiles as file, i}
						<div
							class="bg-secondary relative flex h-full shrink-0 space-x-2 rounded-lg border border-slate-200 px-3 py-2"
						>
							<p class="flex h-full items-center justify-center rounded-md bg-white px-3 py-1">
								{#if isUploading && !uploadedIndexs.includes(i)}
									<Icon icon="line-md:loading-twotone-loop" width="24" height="24" />
								{:else}
									<Icon icon="ph:file-light" width="16" height="16" class="text-primary" />
								{/if}
							</p>
							<div class="flex h-full flex-col items-start space-y-1">
								<p class="h-full max-w-20 truncate text-sm font-medium text-slate-800">
									{file.name}
								</p>
								<p class="h-full max-w-20 truncate text-xs text-slate-500">{file.size}</p>
							</div>
							<button
								class="absolute -top-2 -right-2 cursor-pointer"
								type="button"
								onclick={() => {
									selectedFiles = selectedFiles.filter((ite) => ite !== file);
									tick().then(checkScroll);
								}}
							>
								<Icon icon="mdi:cross-circle" width="24" height="24" class="text-slate-400" />
							</button>
						</div>
					{/each}
				</div>

				{#if canScroll && !scrollAtEnd}
					<button
						type="button"
						class="z-10 p-2 hover:bg-slate-100"
						onclick={() => {
							if (scrollContainer) {
								scrollContainer.scrollBy({ left: 200, behavior: 'smooth' });
							}
						}}
					>
						<Icon icon="mdi:chevron-right" width="20" height="20" />
					</button>
				{/if}
			</div>
		{/if}

		<div class="flex items-center justify-end space-x-1.5">
			<button
				class="border-primary text-primary rounded-md border px-4 py-2"
				onclick={() => openOverlay.set({ name: '', id: '' })}>Cancel</button
			>
			<button
				type="button"
				class="border-primary bg-primary rounded-md border px-4 py-2 text-white"
				onclick={onsubmit}
			>
				{#if isloading}
					<Icon icon="line-md:loading-twotone-loop" width="24" height="24" />
				{:else}
					<span>Upload</span>
				{/if}
			</button>
		</div>
	</div>
</div>
