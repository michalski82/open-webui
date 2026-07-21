<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, onDestroy } from 'svelte';

	import { imageGenerations, imageEdits } from '$lib/apis/images';
	import { getGeminiAccess } from '$lib/apis/users';
	import { notifyAdmin } from '$lib/apis/bot';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { user } from '$lib/stores';

	// Stałe do banera płatności
	const BLIK_PHONE = '501 145 899';
	const TELEGRAM_BOT_URL = 'https://t.me/majkel_servbot';

	// Dostęp Gemini
	let geminiAccess: { active: boolean; until: string | null } = { active: false, until: null };
	let geminiAccessLoaded = false;

	// Polling po notify-admin
	let notifyAdminSent = false;
	let notifyAdminTimedOut = false;
	let pollingIntervalId: ReturnType<typeof setInterval> | null = null;
	let pollingTimeoutId: ReturnType<typeof setTimeout> | null = null;

	const POLL_INTERVAL_MS = 15_000;  // 15 sekund
	const POLL_MAX_MS = 5 * 60_000;   // 5 minut

	const MODELS = [
		{ value: 'flux-realism', label: 'Flux Realism (fotorealizm) — darmowy', editSupport: false, requiresAccess: false },
		{ value: 'flux', label: 'Flux Schnell (szybki) — darmowy', editSupport: false, requiresAccess: false },
		{ value: 'flux-anime', label: 'Flux Anime — darmowy', editSupport: false, requiresAccess: false },
		{ value: 'flux-3d', label: 'Flux 3D — darmowy', editSupport: false, requiresAccess: false },
		{ value: 'turbo', label: 'SDXL Turbo — darmowy', editSupport: false, requiresAccess: false },
		{ value: 'gemini-3.1-flash-lite-image', label: 'Gemini Flash Lite — platny', editSupport: true, requiresAccess: true }
	];

	let loading = false;
	let prompt = '';
	let negativePrompt = '';
	let selectedModel = 'flux-realism';
	let generatedImages: { url: string }[] = [];
	let uploadedImage: string | null = null;
	let isDraggingOver = false;
	let fileInputElement: HTMLInputElement;

	$: isHfModel = selectedModel.startsWith('hf-');
	$: isEditMode = !!uploadedImage;
	$: visibleModels = isEditMode ? MODELS.filter(m => m.editSupport) : MODELS;
	$: if (isEditMode && !MODELS.find(m => m.value === selectedModel)?.editSupport) {
		selectedModel = 'gemini-3.1-flash-lite-image';
	}
	$: geminiModel = MODELS.find(m => m.value === selectedModel);
	$: isGeminiBlocked = geminiAccessLoaded && !geminiAccess.active && geminiModel?.requiresAccess;

	let promptTextareaElement: HTMLTextAreaElement;

	onMount(async () => {
		try {
			geminiAccess = await getGeminiAccess(localStorage.token);
		} catch (e) {
			console.error('Failed to fetch Gemini access:', e);
		} finally {
			geminiAccessLoaded = true;
		}
	});

	onDestroy(() => {
		stopPolling();
	});

	const resizeTextarea = () => {
		if (promptTextareaElement) {
			promptTextareaElement.style.height = '';
			promptTextareaElement.style.height =
				Math.min(promptTextareaElement.scrollHeight, 200) + 'px';
		}
	};

	const submitHandler = async () => {
		if (!prompt.trim()) {
			toast.error(isEditMode ? 'Wpisz opis zmian.' : 'Wpisz opis obrazu.');
			return;
		}
		if (isGeminiBlocked) {
			toast.error('Aktywuj dostep do Gemini — wyslij 9 zl BLIKiem.');
			return;
		}

		loading = true;
		try {
			let result;
			if (isEditMode && uploadedImage) {
				result = await imageEdits(localStorage.token, uploadedImage, prompt, selectedModel);
			} else {
				result = await imageGenerations(
					localStorage.token, prompt, selectedModel,
					isHfModel ? negativePrompt : undefined
				);
			}
			if (result && result.length > 0) {
				generatedImages = [...result, ...generatedImages];
			} else if (result && result.length === 0) {
				toast.error('Operacja nie zwróciła obrazu. Sprawdź ustawienia lub spróbuj ponownie.');
			}
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};

	const openExternal = async (url: string) => {
		try {
			await navigator.clipboard.writeText(prompt);
			toast.success('Prompt skopiowany do schowka');
		} catch {
			toast.error('Nie udalo sie skopiowac promptu');
		}
		window.open(url, '_blank', 'noopener,noreferrer');
	};

	const downloadImage = async (url: string, index: number) => {
		try {
			const response = await fetch(url);
			const blob = await response.blob();
			const blobUrl = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = blobUrl;
			a.download = `obraz-${Date.now()}-${index}.png`;
			a.click();
			URL.revokeObjectURL(blobUrl);
		} catch {
			toast.error('Nie udalo sie pobrac obrazu.');
		}
	};

	const handleFileSelect = (file: File) => {
		if (!file.type.startsWith('image/')) {
			toast.error('Wybierz plik graficzny.');
			return;
		}
		const reader = new FileReader();
		reader.onload = (e) => {
			uploadedImage = e.target?.result as string;
		};
		reader.readAsDataURL(file);
	};

	const onFileInputChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		if (target.files?.[0]) handleFileSelect(target.files[0]);
	};

	const onDrop = (e: DragEvent) => {
		e.preventDefault();
		isDraggingOver = false;
		const file = e.dataTransfer?.files[0];
		if (file) handleFileSelect(file);
	};

	const clearUploadedImage = () => {
		uploadedImage = null;
		if (fileInputElement) fileInputElement.value = '';
	};

	const stopPolling = () => {
		if (pollingIntervalId !== null) {
			clearInterval(pollingIntervalId);
			pollingIntervalId = null;
		}
		if (pollingTimeoutId !== null) {
			clearTimeout(pollingTimeoutId);
			pollingTimeoutId = null;
		}
	};

	const startPolling = () => {
		stopPolling();
		pollingIntervalId = setInterval(async () => {
			try {
				geminiAccess = await getGeminiAccess(localStorage.token);
				if (geminiAccess.active) {
					stopPolling();
				}
			} catch (e) {
				console.error('Polling gemini access failed:', e);
			}
		}, POLL_INTERVAL_MS);

		pollingTimeoutId = setTimeout(() => {
			stopPolling();
			notifyAdminTimedOut = true;
		}, POLL_MAX_MS);
	};

	const notifyAdminHandler = async () => {
		try {
			await notifyAdmin(localStorage.token);
			notifyAdminSent = true;
			notifyAdminTimedOut = false;
			startPolling();
		} catch (e) {
			toast.error('Nie udalo sie wyslac powiadomienia. Sprobuj ponownie.');
		}
	};

	const refreshGeminiAccess = async () => {
		try {
			geminiAccess = await getGeminiAccess(localStorage.token);
		} catch (e) {
			toast.error('Nie udalo sie odswiezac statusu.');
		}
	};
</script>

<div class="flex flex-col justify-between w-full overflow-y-auto h-full">
	<div class="mx-auto w-full md:px-0 h-full">
		<div class="flex flex-col h-full px-4">

			<!-- Generated images grid -->
			<div class="pt-0.5 pb-2.5 flex flex-col justify-between w-full flex-auto overflow-auto h-0">
				<div class="h-full w-full flex flex-col">
					<div class="flex-1 p-1">
						{#if generatedImages.length > 0}
							<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
								{#each generatedImages as image, index}
									<button
										class="relative group cursor-pointer"
										on:click={() => downloadImage(image.url, index)}
									>
										<img
											src={image.url}
											alt=""
											class="w-full aspect-square object-cover rounded-lg border border-gray-100/30 dark:border-gray-850/30"
										/>
										<div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition rounded-lg flex items-center justify-center">
											<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
												<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
												<polyline points="7,10 12,15 17,10" />
												<line x1="12" y1="15" x2="12" y2="3" />
											</svg>
										</div>
									</button>
								{/each}
							</div>
						{:else}
							<div class="h-full flex items-center justify-center text-gray-400 dark:text-gray-600 text-sm">
								Wygenerowane obrazy pojawia sie tutaj
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Upload zone (zawsze widoczna) -->
			<div class="pb-2">
				{#if uploadedImage}
					<!-- Podgląd wgranego obrazu + przycisk czyszczenia -->
					<div class="relative inline-block">
						<img
							src={uploadedImage}
							alt="Wgrany obraz"
							class="max-h-40 rounded-lg border border-gray-200/50 dark:border-gray-700/50 object-contain"
						/>
						<button
							type="button"
							class="absolute top-1 right-1 bg-black/60 hover:bg-black/80 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
							on:click={clearUploadedImage}
							title="Usuń obraz"
						>
							✕
						</button>
					</div>
					<p class="text-xs text-blue-500 dark:text-blue-400 mt-1 px-1">
						Tryb edycji — opisz co zmienić
					</p>
				{:else}
					<!-- Strefa drag-and-drop -->
					<div
						role="button"
						tabindex="0"
						class="border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition
							   {isDraggingOver
								   ? 'border-blue-400 bg-blue-50/10'
								   : 'border-gray-200/40 dark:border-gray-700/40 hover:border-gray-300/60 dark:hover:border-gray-600/60'}"
						on:click={() => fileInputElement?.click()}
						on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputElement?.click(); }}
						on:dragover|preventDefault={() => { isDraggingOver = true; }}
						on:dragleave={() => { isDraggingOver = false; }}
						on:drop={onDrop}
					>
						<p class="text-xs text-gray-400 dark:text-gray-600">
							Wgraj obraz do edycji — kliknij lub przeciągnij tutaj
						</p>
					</div>
					<input
						bind:this={fileInputElement}
						type="file"
						accept="image/*"
						class="hidden"
						on:change={onFileInputChange}
					/>
				{/if}
			</div>

			<!-- Baner Gemini — dostęp / aktywacja -->
			{#if geminiAccessLoaded}
				{#if geminiAccess.active && geminiAccess.until}
					<div class="mb-2 px-3 py-2 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-xs">
						Dostep Gemini aktywny do: {new Date(geminiAccess.until).toLocaleString('pl-PL')}
					</div>
				{:else}
					<div class="mb-2 px-3 py-2.5 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200/50 dark:border-amber-700/50 text-xs space-y-1">
						<p class="font-semibold text-amber-800 dark:text-amber-300">Gemini wymaga aktywacji</p>
						<p class="text-amber-700 dark:text-amber-400">Wyslij <strong>9 zl BLIKiem</strong> na numer: <strong>{BLIK_PHONE}</strong></p>
						<p class="text-amber-700 dark:text-amber-400">Tytul przelewu: <code class="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">{$user?.email ?? 'twoj@email.pl'}</code></p>
						<p class="text-amber-700 dark:text-amber-400">
							Po przelewie napisz na
							<a href={TELEGRAM_BOT_URL} target="_blank" rel="noopener noreferrer" class="underline">Telegram</a>
							lub kliknij nizej:
						</p>
						<div class="flex gap-2 pt-1 flex-wrap">
							{#if !notifyAdminSent}
								<button
									type="button"
									class="px-3 py-1.5 text-xs font-medium bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition"
									on:click={notifyAdminHandler}
								>
									Powiadom administratora
								</button>
							{:else if geminiAccess.active}
								<!-- baner przejdzie do gałęzi active, ten blok nie wystąpi, ale dla bezpieczeństwa: -->
								<span class="text-green-600 dark:text-green-400 font-medium">Aktywowano!</span>
							{:else if notifyAdminTimedOut}
								<span class="text-amber-700 dark:text-amber-400 italic">Nie aktywowano w ciagu 5 minut — sprobuj ponownie.</span>
								<button
									type="button"
									class="px-3 py-1.5 text-xs font-medium bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition"
									on:click={notifyAdminHandler}
								>
									Wyslij ponownie
								</button>
							{:else}
								<button
									type="button"
									disabled
									class="px-3 py-1.5 text-xs font-medium bg-amber-400 text-white rounded-lg cursor-not-allowed opacity-70"
								>
									Wyslano — czekam...
								</button>
							{/if}
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition"
								on:click={refreshGeminiAccess}
							>
								Odswiez
							</button>
						</div>
					</div>
				{/if}
			{/if}

			<!-- Input area -->
			<div class="pb-3">
				<p class="text-xs text-gray-400 dark:text-gray-600 mb-1.5 px-1">
					Wskazowka: popros AI w czacie o napisanie szczegolowego promptu, a nastepnie wklej go tutaj.
				</p>

				<div class="border border-gray-100/30 dark:border-gray-850/30 w-full px-3 py-2.5 rounded-xl">
					<!-- Textarea -->
					<div class="py-0.5">
						<textarea
							bind:this={promptTextareaElement}
							bind:value={prompt}
							class="w-full h-full bg-transparent resize-none outline-hidden text-sm"
							placeholder={isEditMode
								? 'Opisz co chcesz zmienić w obrazie...'
								: 'Opisz obraz, który chcesz wygenerować...'}
							on:input={resizeTextarea}
							on:focus={resizeTextarea}
							on:keydown={(e) => {
								if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !loading) {
									e.preventDefault();
									submitHandler();
								}
							}}
							rows="3"
						/>
					</div>

					{#if isHfModel && !isEditMode}
					<!-- Negative prompt (only for HF models) -->
					<div class="mt-2 border-t border-gray-100/20 pt-2">
						<textarea
							bind:value={negativePrompt}
							class="w-full bg-transparent resize-none outline-hidden text-xs text-gray-400 dark:text-gray-500"
							placeholder="Negative prompt (opcjonalnie): czego nie chcesz na obrazie..."
							rows="2"
						/>
					</div>
					{/if}

					<!-- Model selector + actions row -->
					<div class="flex justify-between items-center gap-2 mt-2 flex-wrap">
						<!-- Left: model selector + external buttons -->
						<div class="flex gap-2 items-center shrink-0 flex-wrap">
							<select
								bind:value={selectedModel}
								class="text-xs bg-gray-50 dark:bg-gray-850 border border-gray-200/50 dark:border-gray-700/50 text-gray-700 dark:text-gray-300 rounded-lg px-2 py-1.5 outline-none cursor-pointer"
							>
								{#each visibleModels as m}
									<option
										value={m.value}
										disabled={m.requiresAccess && geminiAccessLoaded && !geminiAccess.active}
									>{m.label}{m.requiresAccess && geminiAccessLoaded && !geminiAccess.active ? ' 🔒' : ''}</option>
								{/each}
							</select>

							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://gemini.google.com/app')}
							>
								Gemini ↗
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://www.bing.com/images/create')}
							>
								Bing ↗
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://ideogram.ai/t/generate')}
							>
								Ideogram ↗
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-lg"
								on:click={() => openExternal('https://firefly.adobe.com/generate/images')}
							>
								Firefly ↗
							</button>
						</div>

						<!-- Right: generate button -->
						<div class="shrink-0">
							{#if !loading}
								<button
									disabled={prompt.trim() === ''}
									class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
									on:click={submitHandler}
								>
									{isEditMode ? 'Edytuj' : 'Generuj'}
								</button>
							{:else}
								<button
									class="px-3.5 py-1.5 text-sm font-medium bg-gray-300 text-black transition rounded-lg flex items-center gap-2"
									disabled
								>
									<Spinner className="size-4" />
									{isEditMode ? 'Edytowanie...' : 'Generowanie...'}
								</button>
							{/if}
						</div>
					</div>
				</div>
			</div>

		</div>
	</div>
</div>
