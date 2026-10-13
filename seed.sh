#!/usr/bin/env bash
# Apply websites/acs/content/ to the local WordPress. Safe to run repeatedly.
set -euo pipefail
cd "$(dirname "$0")"
npx @wordpress/env run cli wp eval-file /var/www/html/wp-content/acs-content/seed.php
# Template-preview samples (2 Oct 2026): one SAMPLE article, one SAMPLE vacancy.
npx @wordpress/env run cli wp eval-file /var/www/html/wp-content/acs-content/seed-samples.php
# The permalink change above only takes effect once the rules are rebuilt from the CLI.
npx @wordpress/env run cli wp rewrite flush
