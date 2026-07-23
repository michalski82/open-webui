<script>
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let show = true;
	export let onLogin = () => {};
</script>

{#if show}
	<div class="fixed inset-0 z-[60] flex flex-col bg-[#050c1a]">
		<div class="flex justify-end p-4 flex-shrink-0">
			<button
				class="text-sm text-white border border-white/30 rounded-full px-5 py-2.5 hover:bg-white/15 transition backdrop-blur-sm font-medium"
				on:click={onLogin}
			>
				Zaloguj się →
			</button>
		</div>

		<img
			src="{WEBUI_BASE_URL}/splash-bg.jpg"
			alt="MM-AI"
			class="flex-1 w-full min-h-0 object-contain"
		/>

		<div class="flex justify-center py-6 flex-shrink-0">
			<button
				class="text-white font-semibold text-base px-8 py-3 rounded-full border border-white/40 hover:bg-white/15 transition backdrop-blur-sm tracking-wide"
				style="background: linear-gradient(135deg, rgba(100,60,200,0.5), rgba(20,100,200,0.5));"
				on:click={onLogin}
			>
				Wejdź do świata AI
			</button>
		</div>
	</div>
{/if}
