# ACS website

The All Commercial Services website build: a WordPress block theme, versioned page content, and local build and preview tools. This private repository contains website code only. It is a mirror of the website files in the private `marx-media` workspace; make changes there and sync them from that repository.

## Run locally

Install Docker Desktop and Node.js, start Docker, then run from this repository's root:

```bash
npx @wordpress/env start
bash seed.sh
bash check-site.sh
```

Open <http://localhost:8888>. The theme is in `acs/`, and the page content restored by `seed.sh` is in `content/`. On Windows, run the shell scripts from Git Bash. See `acs/README.md` for theme details. The preview and accessibility tools are in `preview/` and `a11y/`.

This is a working build, not an authorized public launch. Live hosting and service credentials are separate from this repository. Do not commit secrets or client review material here.

## Static portfolio preview

The `showcase/site/` directory contains a static snapshot for Vercel. It has a visible John Jopson attribution banner, blocks indexing, and disables form submissions. `vercel.json` serves this directory without running WordPress. To refresh it, start the local WordPress site, run `bash seed.sh`, then run `bash showcase/build.sh` and commit the new snapshot. The static build is a demonstration and does not include WordPress editing or live intake.
