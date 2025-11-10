<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getCusList, getReqDetail } from '$lib/query/requests';
	import Icon from '@iconify/svelte';
	import { createQuery } from '@tanstack/svelte-query';
	import StatusPill from '../UI/StatusPill.svelte';
	import { formatDate } from '../helper';
	import { slide } from 'svelte/transition';

	let reqDetail = $derived(
		createQuery({
			queryKey: ['req_detail_header', page.params.req_id],
			queryFn: getReqDetail,
			enabled: page.params.req_id ? true : false
		})
	);
	let userListQuery = $derived(
		createQuery({
			queryKey: ['user_list'],
			queryFn: getCusList
		})
	);

	let userId = $derived(
		$userListQuery.data
			? $userListQuery.data.find((ite) => ite.name === $reqDetail.data?.client_name)?.id
			: null
	);
	let tabsData = $derived([
		{
			name: 'Dashboard',
			path: '/'
		},
		{
			name: 'Requests',
			path: '/requests'
		},
		{
			name: $reqDetail.data?.client_name || '[NAME_REDACTED]',
			path: `/requests/${page.params.req_id}`
		},
		{
			name: 'Clients',
			path: '/customer'
		},
		{
			name: 'Brokers',
			path: '/brokers'
		},
		{
			name: 'Automation Control',
			path: '/setting'
		},
		{
			name: 'James Smith',
			path: `/brokers/${page.params.broker_id}`
		},
		{
			name: `${decodeURIComponent(page.params.client_id)}` || '[CLIENT_REDACTED]',
			path: `/customer/${userId}`
		}
	]);
	let isOpen = $state();

	let info = [
		{
			name: 'Received:',
			value: $reqDetail.data ? formatDate($reqDetail.data?.created_at) : ''
		},
		{
			name: 'Broker:',
			value: $reqDetail.data ? $reqDetail.data.broker_name : 'N/A'
		},
		{
			name: 'End Client:',
			value: $reqDetail.data ? $reqDetail.data.client_name : 'N/A'
		}
	];
</script>