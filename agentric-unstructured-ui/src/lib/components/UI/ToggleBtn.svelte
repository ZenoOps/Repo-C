<script lang="ts">
	let {isOn = false} = $props();

	function toggle() {
		isOn = !isOn;
	}
</script>

<button
	onclick={toggle}
	class="relative inline-flex cursor-pointer {isOn
		? 'bg-primary'
		: 'bg-[#7B7B7B4D]/30'} h-6.5 w-12 items-center rounded-full transition-colors duration-300"
>
	<span
		class="inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-300"
		class:translate-x-6={isOn}
	></span>
</button>
