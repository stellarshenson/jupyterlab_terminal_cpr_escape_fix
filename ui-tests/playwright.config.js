/**
 * Configuration for Playwright using default from @jupyterlab/galata
 */
const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  webServer: {
    command: 'jlpm start',
    url: 'http://localhost:8899/lab',
    timeout: 240 * 1000,
    reuseExistingServer: !process.env.CI
  },
  use: {
    ...baseConfig.use,
    baseURL: 'http://localhost:8899'
  }
};
