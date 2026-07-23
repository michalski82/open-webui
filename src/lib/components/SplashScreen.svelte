<script>
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let show = true;
	export let onLogin = () => {};
</script>

{#if show}
	<div
		class="fixed inset-0 z-[60] flex flex-col"
		style="background: url('{WEBUI_BASE_URL}/splash-bg.jpg') center center / cover no-repeat #050c1a;"
	>
		<div class="fixed inset-0 bg-black/30"></div>

		<div class="relative z-10 flex justify-end p-6">
			<button
				class="text-sm text-white border border-white/30 rounded-full px-5 py-2.5 hover:bg-white/15 transition backdrop-blur-sm font-medium"
				on:click={onLogin}
			>
				Zaloguj się →
			</button>
		</div>
	</div>
{/if}
