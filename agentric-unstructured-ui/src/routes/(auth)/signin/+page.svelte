<script lang="ts">
	import { goto } from '$app/navigation';
	import { UserRole } from '$lib/types/user';
	import { getUser, login } from '$lib/query/auth';
	import { userStore } from '$lib/store/userStore';
	import Icon from '@iconify/svelte';
	import { browser } from '$app/environment';
	import toast from 'svelte-french-toast';
	import Button from '$lib/components/UI/Button.svelte';
	import Input from '$lib/components/UI/Input.svelte';
	import Checkbox from '$lib/components/UI/Checkbox.svelte';
	import DropDown from '$lib/components/UI/DropDown.svelte';

	let username = $state('');
	let password = $state('');
	let selectedCity = $state('');

	const handleLogin = async () => {
		try {
			let response = await login(username, password);

			let data = response.data;
			localStorage.setItem('accessToken', data.access_token);
			let token = browser ? localStorage.getItem('accessToken') : null;
			if (token) {
				let me = await getUser();

				let user = {
					id: me.id,
					name: me.name,
					email: me.email,
					token: data.access_token,
					role: me.role,
					teamName: me.teamName,
					teamId: me.teamId,
					isSuperuser: me.isSuperuser
				};

				userStore.updateInfo(user);

				localStorage.setItem('user', JSON.stringify(user));
				toast.success('Successfully Signed In');

				if (user.isSuperuser) {
					goto('/admin');
				} else if (
					(user.teamName === UserRole.COVER_MORE_ROLE ||
						user.teamName === UserRole.TRAVEL_GUARD_ROLE) &&
					!user.isSuperuser
				) {
					goto('/agent');
				} else {
					goto('/');
				}
			}
		} catch (e: any) {
			toast.error(e.message);
		}
	};

	let steps = ['/plane-icon.png', '/dashboard-icon.png', '/notification-lines.png'];
</script>

<div class="flex flex-col lg:flex-row">
	<div class="text-primary w-full lg:h-screen lg:w-1/2">
		<div class="bg-secondary flex flex-col space-y-6 rounded-lg p-6 lg:h-full lg:space-y-12 lg:p-8">
			<div class="flex items-end justify-between">
				<img src="/LogoCover.png" alt="LogoCover" class="w-36 shrink-0 object-contain" />
				<img src="/plane-sign.png" alt="Plane Sign" class=" w-18 shrink-0 object-contain" />
			</div>
			<div class="space-y-4">
				<h2 class="text-lg font-semibold lg:text-3xl">Smart Claims By AgentricAI</h2>

				<p class="text-sm lg:text-xl">
					Easily submit and track your travel insurance claims. Upload your documents, get real-time
					updates, and let our AI guide you step by step - simple, fast, and stress-free.
				</p>
			</div>
			<div>
				<div class=" flex w-full">
					<div class="flex-[1]"></div>
					{#each steps as img, i}
						<div class="flex-[1]">
							<div
								class="flex h-15 w-15 items-center justify-center rounded-full bg-white md:h-23 md:w-23"
							>
								<img src={img} alt="plane-icon" />
							</div>
						</div>

						{#if i < 2}
							<div class="flex flex-[2] items-center">
								<div class="w-full border border-dashed border-gray-400"></div>
							</div>
						{/if}
					{/each}
					<div class="flex-[1]"></div>
				</div>
				<div class="mt-2 flex w-full text-[9px] md:text-[12px]">
					<div class="flex-[2]"></div>
					<div class="flex-[4] items-center">Start Your Claim</div>
					<div class="flex-[2]"></div>
					<div class="flex-[5] items-center">Submit Your Documents</div>
					<div class="flex-[2]"></div>
					<div class="flex-[5]">Track Your Claims & Updates</div>
				</div>
			</div>
			<div class="flex h-full items-center">
				<div class="mb-5 w-full flex-1">
					<img src="/dotted-map.png" alt="dotted-map" class="w-96 object-cover md:w-full" />
				</div>
			</div>
		</div>
	</div>
	<form
		class="flex flex-col items-start justify-center space-y-8 p-6 lg:w-1/2 lg:p-40"
		onsubmit={handleLogin}
	>
		<p class="text-xl font-semibold lg:text-2xl">Sign In</p>
		<div class="w-full space-y-6">
			<div class="space-y-3">
				<div class="flex items-center space-x-3">
					<Icon icon="uiw:mail-o" class="h-4 w-4 text-slate-500 lg:h-6 lg:w-6" />
					<p>Email Address</p>
				</div>
				<Input type="text" bind:value={username} placeholder="Enter Email Address" />
			</div>
			<div class="space-y-3">
				<div class="flex items-center space-x-3">
					<Icon icon="quill:lock" class="h-4 w-4 text-slate-500 lg:h-6 lg:w-6" />
					<p>Password</p>
				</div>
				<Input bind:value={password} type="password" />
			</div>
			<div class="text-primary flex justify-between">
				<div>
					<Checkbox /> Remember Me
				</div>
				<p>Forgot Password?</p>
			</div>
		</div>
		<Button type="submit">
			<p>Sign In</p>
		</Button>
	</form>
</div>
