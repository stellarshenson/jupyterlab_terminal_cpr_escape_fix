/**
 * Configuration for Playwright using default from @jupyterlab/galata
 *
 * JUPYTER_TEST_PORT threads one port through this config and
 * jupyter_server_test_config.py (default 8899). Test-results and the HTML
 * report are kept per port, so two runs on different ports can run at once.
 */
const path = require('path');
const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

const PORT = process.env.JUPYTER_TEST_PORT || '8899';
if (PORT === '8888') {
  throw new Error('JUPYTER_TEST_PORT=8888 is the developer lab; use 8899-8905');
}
const BASE_URL = `http://localhost:${PORT}`;

// The developer lab's credentials and address must not reach the test server,
// its terminals, or any CLI a test spawns. COLUMNS/LINES go too: the live lab
// has none, and fish takes an inherited COLUMNS as the terminal width.
for (const name of Object.keys(process.env)) {
  if (
    name.startsWith('JUPYTERHUB_') ||
    [
      'JPY_API_TOKEN',
      'JUPYTER_TOKEN',
      'JUPYTERLAB_SERVER_TOKEN',
      'JUPYTER_SERVER_URL',
      'JUPYTER_SERVER_ROOT',
      'JUPYTER_PORT',
      'COLUMNS',
      'LINES'
    ].includes(name)
  ) {
    delete process.env[name];
  }
}
process.env.JUPYTER_TEST_PORT = PORT;
process.env.JUPYTER_RUNTIME_DIR = path.join(__dirname, `.tmp-runtime-${PORT}`);

module.exports = {
  ...baseConfig,
  // experiments keep their specs in ui-tests/experiments (gitignored) and run
  // with PLAYWRIGHT_TEST_DIR=experiments; the suite is tests/
  testDir: path.join(__dirname, process.env.PLAYWRIGHT_TEST_DIR || 'tests'),
  // one server, shared terminals: serialise
  workers: 1,
  fullyParallel: false,
  outputDir: path.join(__dirname, 'test-results', PORT),
  reporter: [
    [process.env.CI ? 'github' : 'list'],
    [
      'html',
      {
        open: 'never',
        outputFolder: path.join(__dirname, 'playwright-report', PORT)
      }
    ]
  ],
  use: { ...baseConfig.use, baseURL: BASE_URL },
  webServer: {
    command: 'jlpm start',
    url: `${BASE_URL}/lab`,
    timeout: 120 * 1000,
    reuseExistingServer: false,
    env: {
      // the server extension under test is the working tree, not site-packages
      PYTHONPATH: [path.resolve(__dirname, '..'), process.env.PYTHONPATH]
        .filter(Boolean)
        .join(path.delimiter),
      // test shells must not write the developer's fish history
      fish_history: ''
    }
  }
};
