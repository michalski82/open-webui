<script>
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let show = true;
	export let onLogin = () => {};

	const features = [
		{
			img: `${WEBUI_BASE_URL}/screenshots/chat.png`,
			name: 'Czat',
			desc: 'Rozmawiaj z modelami AI',
			alt: 'Zrzut ekranu czatu'
		},
		{
			img: `${WEBUI_BASE_URL}/screenshots/images.png`,
			name: 'Grafika',
			desc: 'Generuj obrazy z opisu',
			alt: 'Zrzut ekranu generowania obrazów'
		},
		{
			img: `${WEBUI_BASE_URL}/screenshots/music.png`,
			name: 'Muzyka',
			desc: 'Twórz muzykę z tekstu',
			alt: 'Zrzut ekranu generowania muzyki'
		}
	];
</script>

{#if show}
	<div
		class="fixed inset-0 z-[60] bg-gradient-to-br from-gray-950 to-black text-white flex flex-col overflow-y-auto"
	>
		<!-- Top bar -->
		<div class="fixed top-0 left-0 right-0 flex items-center justify-between px-6 py-4 z-[61]">
			<img
				src="{WEBUI_BASE_URL}/static/favicon.png"
				class="w-8 rounded-full"
				alt="MM-AI"
				crossorigin="anonymous"
			/>
			<button
				class="text-sm text-white border border-white/20 rounded-full px-4 py-2 hover:bg-white/10 transition"
				on:click={onLogin}
			>
				Zaloguj się →
			</button>
		</div>

		<!-- Center content -->
		<div class="flex flex-col items-center justify-center min-h-screen gap-6">
			<div class="text-5xl font-secondary">MM-AI</div>
			<div class="text-base text-white/60">Twój prywatny asystent AI</div>

			<!-- Feature cards -->
			<div class="flex gap-4 mt-6 flex-wrap justify-center">
				{#each features as feature}
					<div class="flex flex-col items-center gap-2 w-64">
						<img
							src={feature.img}
							class="w-full rounded-xl border border-white/10 shadow-lg"
							alt={feature.alt}
						/>
						<span class="text-sm font-semibold text-white">{feature.name}</span>
						<span class="text-xs text-white/50">{feature.desc}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
