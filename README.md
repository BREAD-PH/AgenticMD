# AgenticMD

A minimal SvelteKit project with TypeScript, created using [`bunx sv create`](https://github.com/sveltejs/kit).

## Project Setup Details

This project was initialized with the following configuration choices in `bunx sv create`:

1. **Project Location**:
   - Selected: `./` (current directory)
   - Confirmed: "Yes" to continue with non-empty directory

2. **Template Selection**:
   - Selected: "SvelteKit minimal"

3. **Type Checking**:
   - Selected: "Yes, using TypeScript syntax"

4. **Additional Tools** (selected using space bar):
   - prettier
   - eslint
   - vitest
   - playwright
   - tailwindcss
   - mdsvex

5. **TailwindCSS Configuration**:
   - Plugins: "none"

6. **Package Manager**:
   - Selected: "bun"

## Development

Once you've cloned the project, install dependencies with:

```bash
bun install
```

Start the development server:

```bash
bun run dev

# or start the server and open the app in a new browser tab
bun run dev -- --open
```

## Building

To create a production version of your app:

```bash
bun run build
```

You can preview the production build with `bun run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.

## Testing

Run unit tests:
```bash
bun run test
```

Run end-to-end tests:
```bash
bun run test:e2e
