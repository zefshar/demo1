<script lang="ts">
	import Layout from "./Layout.svelte";
</script>

<Layout header hideHeader headerHeight={56} let:scroller>
	<div slot="header">
		<div class="header" class:shadow={!!scroller.scroll}>Page title</div>
	</div>

	<div>
		{#each Array(100) as _, i}
			<div class="item">Row {i}</div>
		{/each}
	</div>

	<div slot="footer">
		<div class="footer" class:shadow={!!scroller.scroll}>Search pannel</div>
	</div>
</Layout>

<style>
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}

	h1 {
		color: #ff3e00;
		text-transform: uppercase;
		font-size: 4em;
		font-weight: 100;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}

	.header {
		background-color: #ff0000;
		height: 56px;
		line-height: 56px;
		color: #ffffff;
		padding-left: 16px;
	}

	.shadow {
		box-shadow: 0px 2px 8px #00000088;
	}
</style>
