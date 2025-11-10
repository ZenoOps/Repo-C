<script lang="ts">
	let { children, class: dynamicClass = '', ...restProps } = $props();
</script>

<button
	{...restProps}
	class={`${
		dynamicClass
			? dynamicClass
			: 'bg-primary-600 bg-primary hover:bg-primary-700 flex w-full items-center justify-center space-x-2 rounded-lg px-3 py-2 text-sm font-semibold text-nowrap text-white md:text-lg'
	}`}
>
	{@render children()}
</button>
