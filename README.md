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
