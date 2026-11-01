'use strict';
// Every invocation reserves a fresh directory, including failures and retries.
const { spawnSync } = require('node:child_process'),
  path = require('node:path');
const result = spawnSync(
  'python3',
  ['-I', path.join(__dirname, 'run-atlas.py'), ...process.argv.slice(2)],
  { stdio: 'inherit' },
);
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status === null ? 1 : result.status);
