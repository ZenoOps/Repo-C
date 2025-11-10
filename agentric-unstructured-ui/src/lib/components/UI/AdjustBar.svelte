<script lang="ts">
	let { value = 50 } = $props();

	function handleVolumeChange(event: Event) {
		const target = event.target as HTMLInputElement;
		value = +target.value;
	}
</script>

<div class=" w-full">
	<input
		id="volume"
		type="range"
		min="0"
		max="100"
		step="1"
		bind:value
		oninput={handleVolumeChange}
		class="relative h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-300"
		style="background: linear-gradient(to right, #3A7E92 0%, #3A7E92 {value}%, #d1d5db {value}%, #d1d5db 100%)"
	/>

	<style>
		input[type='range']::-webkit-slider-thumb {
			-webkit-appearance: none;
			height: 16px;
			width: 16px;
			border-radius: 50%;
			background: #ffffff;
			cursor: pointer;
			border: 2px solid #3a7e92;
		}
		input[type='range']::-moz-range-thumb {
			height: 16px;
			width: 16px;
			border-radius: 50%;
			background: #3a7e92;
			cursor: pointer;
			border: 2px solid #3a7e92;
		}
	</style>
</div>
