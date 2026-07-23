<script>
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { onMount } from 'svelte';

	export let show = true;
	export let onLogin = () => {};

	let canvas;

	onMount(() => {
		if (!canvas) return;

		const ctx = canvas.getContext('2d');
		let animId;

		const resize = () => {
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
		};
		resize();
		window.addEventListener('resize', resize);

		const COLORS = ['#a855f7', '#06b6d4', '#3b82f6', '#8b5cf6', '#22d3ee'];
		const particles = Array.from({ length: 55 }, () => ({
			x: Math.random() * window.innerWidth,
			y: Math.random() * window.innerHeight,
			vx: (Math.random() - 0.5) * 0.7,
			vy: (Math.random() - 0.5) * 0.7,
			r: Math.random() * 1.8 + 0.8,
			color: COLORS[Math.floor(Math.random() * COLORS.length)],
			alpha: Math.random() * 0.35 + 0.1
		}));

		const animate = () => {
			ctx.clearRect(0, 0, canvas.width, canvas.height);

			for (let i = 0; i < particles.length; i++) {
				const p = particles[i];
				p.x += p.vx;
				p.y += p.vy;
				if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
				if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

				ctx.beginPath();
				ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
				ctx.fillStyle = p.color;
				ctx.globalAlpha = p.alpha;
				ctx.fill();
				ctx.globalAlpha = 1;

				for (let j = i + 1; j < particles.length; j++) {
					const q = particles[j];
					const dist = Math.hypot(p.x - q.x, p.y - q.y);
					if (dist < 140) {
						ctx.beginPath();
						ctx.moveTo(p.x, p.y);
						ctx.lineTo(q.x, q.y);
						ctx.strokeStyle = `rgba(140, 80, 220, ${0.18 * (1 - dist / 140)})`;
						ctx.lineWidth = 0.6;
						ctx.stroke();
					}
				}
			}

			animId = requestAnimationFrame(animate);
		};

		animate();

		return () => {
			window.removeEventListener('resize', resize);
			cancelAnimationFrame(animId);
		};
	});
</script>

{#if show}
	<div class="fixed inset-0 z-[60] flex flex-col bg-[#050c1a]">
		<canvas bind:this={canvas} class="absolute inset-0 w-full h-full" />

		<div class="relative z-10 flex justify-end p-4 flex-shrink-0">
			<button
				class="text-sm text-white border border-white/30 rounded-full px-5 py-2.5 hover:bg-white/15 transition backdrop-blur-sm font-medium"
				on:click={onLogin}
			>
				Zaloguj się →
			</button>
		</div>

		<div class="relative z-10 flex-1 min-h-0 overflow-hidden sm:flex sm:items-center sm:justify-center sm:px-4">
			<img
				src="{WEBUI_BASE_URL}/splash-bg.jpg"
				alt="MM-AI — AI solutions"
				class="w-full h-full object-cover object-center drop-shadow-2xl sm:w-auto sm:h-auto sm:max-w-full sm:max-h-[70vh] sm:object-contain"
			/>
		</div>

		<div class="relative z-10 flex justify-center py-6 flex-shrink-0">
			<button
				class="text-white font-semibold text-base px-8 py-3 rounded-full border border-purple-500/50 hover:bg-purple-500/20 transition backdrop-blur-sm tracking-wide"
				style="background: linear-gradient(135deg, rgba(100,40,180,0.55), rgba(20,100,200,0.55));"
				on:click={onLogin}
			>
				Wejdź do świata AI
			</button>
		</div>
	</div>
{/if}
