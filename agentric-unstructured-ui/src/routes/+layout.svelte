<script lang="ts">
	import { QueryClientProvider } from '@tanstack/svelte-query';
	import toast, { Toaster } from 'svelte-french-toast';

	import '../app.css';
	import markerSDK from '@marker.io/browser';
	import { onMount } from 'svelte';
	import { env } from '$env/dynamic/public';

	let { children } = $props();
	// let widget: any; 

	// onMount(async () => {
	// 	try {

	// 		widget = await markerSDK.loadWidget({
	// 			project: `${env.PUBLIC_MARKER_PROJECT_ID}`, 
	// 		});

	// 	} catch (e:any) {
	// 		toast.error(e)
	// 	}
	// });
</script>

<svelte:head>
	<title>Agentric</title>
	<link rel="icon" type="image/png" href="/agentric_logo.png" />
	<link rel="shortcut icon" href="/agentric_logo.png" />
</svelte:head>

<QueryClientProvider>
	<!-- <SvelteToast options={{ duration: 3000, intro: { y: -100 } }} /> -->
	<Toaster />

	{@render children()}
</QueryClientProvider>