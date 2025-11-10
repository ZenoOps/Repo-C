<script lang="ts">
	import ChatBot from '$lib/components/requests/ChatBot.svelte';
	import { page } from '$app/state';
	import Icon from '@iconify/svelte';
	import { goto } from '$app/navigation';
</script>

<div class="flex h-full flex-1 flex-col space-y-2 bg-slate-50 lg:py-3">
	<div class="px-4">
		<button onclick={() => goto('/')}>
			<Icon icon="ic:round-arrow-back-ios" width="14" height="14" />
		</button>
	</div>
	<div class="min-h-0 w-full flex-1 overflow-y-auto lg:px-53">
		<ChatBot worktype="initial" />
	</div>
</div>
