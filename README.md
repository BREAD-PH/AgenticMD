# AgenticMD

A minimal SvelteKit project with TypeScript, created using [`bunx sv create`](https://github.com/sveltejs/kit).


# SvelteKit Configuration
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

# Shadcn-svelte Configuration
## Path Aliases Setup

To configure path aliases in your project, update your `svelte.config.js`:

```javascript
const config = {
  kit: {
    alias: {
      "@/*": "./path/to/lib/*"
    }
  }
};
```

## UI Components Setup

This project uses shadcn-svelte for UI components. The initialization was done with:

```bash
bun x shadcn-svelte@next init
```

Configuration choices made:
- Style: Default
- Base color: Slate
- Global CSS file: src/app.css
- Tailwind config: tailwind.config.ts
- Import aliases:
  - Components: $lib/components
  - Utils: $lib/utils
  - Hooks: $lib/hooks
  - UI Components: $lib/components/ui

# Development

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
```

# Deploying a Repository Inside a GitHub Organization to Vercel Using GitHub Actions

## Prerequisites
- personal GitHub account
- repository within a GitHub Organization (source repository)
- separate repository in your personal account to host the copied files (destination repository)

## Step 1: Generate SSH Keys
You'll need to generate an SSH Deploy Key to securely push your content from the organization's repository to the external repository. Although you can also use a Personal Access Token, an SSH deploy key is recommended as it minimizes the impact of potential security breaches.

```sh
ssh-keygen -t ed25519 -C "$(git config user.email)" -N "" -f github-<desitination-repo-name>
```

Replace the <desitination-repo-name> with the name of your destination repository and run the command. Afterwards, you should now have both public and private key files:
- ```github-<desitination-repo-name>.pub``` (public)
- ```github-<desitination-repo-name>``` (private)

## Step 2: Add the private key to the Source Repository
Visit the source repository's GitHub page.
Click on "Settings" in the repository (not account settings).
In the left-hand pane, click "Secrets", then "Actions".
Click on "New repository secret".
Name it SSH_DEPLOY_KEY and paste the contents of the private key file.
Click "Save".

## Step 3: Add the public key to the Destination Repository
Visit the destination repository's GitHub page.
Click on "Settings" in the repository (not account settings).
In the left-hand side pane, click on "Deploy keys."
Click on "Add deploy key".
Paste the contents of the public key file.
Enable "Allow write access".
Click "Save".
## Step 4: Disable GitHub Actions on the Destination Repository
Visit the destination repository's GitHub page.
Click on "Settings" in the repository (not account settings).
Click on "Actions" and then "General".
Select "Disable actions".
Click "Save".

## Step 5: Create a GitHub Action Workflow
Create a new GitHub Action workflow in your source repository by adding a YAML file in the .github/workflows directory. Name the file push-to-external-repo.yml and paste the following content:

.github/workflows/push-to-external-repo.yml
```
name: (main) push to external repo
on:
  push:
    branches:
      - main
jobs:
  push-to-external-repo:
    runs-on: ubuntu-latest
    steps:
      - name: checkout repository
        uses: actions/checkout@v3
      - name: push to external repository
        uses: peaceiris/actions-gh-pages@v3
        with:
          deploy_key: ${{ secrets.SSH_DEPLOY_KEY }}
          publish_dir: .
          external_repository: <your-username>/<destination-repo-name>
          publish_branch: main
          allow_empty_commit: true
```
Replace ```<your-username>``` with your GitHub username and ```<destination-repo-name>``` with the name of the external repository in your personal account. This action will copy everything from your organization's repository to your personal repository, including your GitHub Action workflows, so follow Step 4 to disable GitHub Actions on the destination repository.

## Step 6: Run your workflow
Push something to your main branch and see it be pushed to your ```<your-username>/<destination-repo-name>``` repository.

## Step 7: Set up a project on Vercel
On Vercel's "New Project" page, choose the account linked to the project under the "Import Git Repository" section.
Find your personal repository in the list and select "Import".
Vercel will automatically detect the framework and any necessary build settings. You can configure project settings, including build and development settings and environment variables, at this stage or later.
Click the "Deploy" button. Vercel will create the project and deploy it based on the chosen configurations.