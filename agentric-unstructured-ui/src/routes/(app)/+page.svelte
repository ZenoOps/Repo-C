<script lang="ts">
	import { goto } from '$app/navigation';
	import Icon from '@iconify/svelte';
	import { browser } from '$app/environment';
	import { v4 as uuidv4 } from 'uuid';
	import Button from '$lib/components/UI/Button.svelte';

	const uuid = uuidv4();

	const startNewChat = async () => {
		const randomUUID = uuid;
		location.replace('/chat/' + randomUUID);
	};

	let isChatHad = $derived(browser ? localStorage.getItem('isChatHad') === 'true' : false);
</script>

<div class="flex h-full w-full flex-col space-y-3 px-4 {isChatHad ? 'hidden lg:flex' : ''}">
	<div class="flex h-full w-full flex-1 flex-col items-center justify-center space-y-6">
		<svg width="64" height="65" viewBox="0 0 64 65" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path
				opacity="0.4"
				d="M53.6011 19.0067C53.6011 20.4467 52.8278 21.7532 51.6011 22.4199L46.9611 24.9266L43.0144 27.0333L34.8278 31.46C33.9478 31.94 32.9878 32.18 32.0011 32.18C31.0144 32.18 30.0544 31.94 29.1744 31.46L12.4011 22.4199C11.1744 21.7532 10.4011 20.4467 10.4011 19.0067C10.4011 17.5667 11.1744 16.2599 12.4011 15.5932L17.6544 12.7666L21.8411 10.5L29.1744 6.55337C30.9344 5.59337 33.0678 5.59337 34.8278 6.55337L51.6011 15.5932C52.8278 16.2599 53.6011 17.5667 53.6011 19.0067Z"
				fill="#3A7E92"
			/>
			<path
				opacity="0.4"
				d="M26.4019 34.6064L10.8018 26.793C9.60183 26.1797 8.21519 26.2597 7.06852 26.953C5.92185 27.6464 5.25519 28.8731 5.25519 30.2064V44.9531C5.25519 47.5131 6.66849 49.8064 8.96183 50.9531L24.5618 58.7397C25.0952 59.0064 25.6819 59.1397 26.2685 59.1397C26.9619 59.1397 27.6552 58.9531 28.2685 58.5531C29.4152 57.8597 30.0819 56.6331 30.0819 55.2997V40.5531C30.1085 38.0464 28.6952 35.7531 26.4019 34.6064Z"
				fill="#3A7E92"
			/>
			<path
				opacity="0.4"
				d="M58.7491 30.2338V44.9802C58.7491 47.5136 57.336 49.8069 55.0427 50.9536L39.4427 58.7669C38.9094 59.0336 38.3224 59.1669 37.7358 59.1669C37.0424 59.1669 36.3494 58.9805 35.7094 58.5805C34.5894 57.8872 33.8958 56.6602 33.8958 55.3269V40.6069C33.8958 38.0469 35.3094 35.7536 37.6027 34.6069L43.3358 31.7536L47.3358 29.7536L53.2027 26.8203C54.4027 26.207 55.7894 26.2603 56.936 26.9803C58.056 27.6736 58.7491 28.9005 58.7491 30.2338Z"
				fill="#3A7E92"
			/>
			<path
				d="M60.2669 58.2067L58.2403 56.18C59.3069 54.58 59.9203 52.66 59.9203 50.6067C59.9203 44.98 55.3603 40.42 49.7336 40.42C44.1069 40.42 39.5469 44.98 39.5469 50.6067C39.5469 56.2334 44.1069 60.7934 49.7336 60.7934C51.7869 60.7934 53.7069 60.18 55.3069 59.1134L57.3336 61.14C57.7336 61.54 58.2669 61.7534 58.8003 61.7534C59.3336 61.7534 59.8669 61.54 60.2669 61.14C61.0669 60.3134 61.0669 59.0067 60.2669 58.2067Z"
				fill="#3A7E92"
			/>
		</svg>

		<p class="font-medium">No Chats Yet</p>
		<span class="text-sm text-slate-500">Start by filling a claim or getting assistance</span>
		<div>
			<Button
			onclick={startNewChat}
		>
			<Icon icon="bitcoin-icons:plus-filled" width="20" height="20" />
			<span>Start a claim</span>
		</Button>
		</div>
	</div>
</div>
