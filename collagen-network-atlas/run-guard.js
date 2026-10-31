'use strict';
// Original local filesystem guard; no external dependencies or network access.
const fs = require('node:fs'),
  path = require('node:path');
exports.requireRun = function (root, outputs) {
  const canonical = fs.realpathSync(root);
  if (
    process.env.ATLAS_RUN_DIR !== canonical ||
    !fs.existsSync(path.join(root, 'RUN_CONTEXT.json'))
  )
    throw new Error(
      'Use node benchmark.js from the live atlas root; saved exports are protected.',
    );
  for (const name of [
    'FINISHED.json',
    'FAILED.json',
    'PREPARED.json',
    ...outputs,
  ]) {
    if (fs.existsSync(path.join(root, name)))
      throw new Error('Refusing to overwrite ' + name + '. Start a fresh run.');
  }
};
