import { expect, test } from '@jupyterlab/galata';

/**
 * Don't load JupyterLab webpage before running the tests.
 * This is required to ensure we capture all log messages.
 */
test.use({ autoGoto: false });

test('should emit an activation console message', async ({ page }) => {
  const logs: string[] = [];

  page.on('console', message => {
    logs.push(message.text());
  });

  await page.goto();

  expect(
    logs.filter(
      s =>
        s ===
        'JupyterLab extension jupyterlab_terminal_cpr_escape_fix is activated!'
    )
  ).toHaveLength(1);
});

test.describe('Terminal integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto();
    await page.waitForTimeout(2000);
  });

  test('terminal opens successfully', async ({ page }) => {
    await page.menu.clickMenuItem('File>New>Terminal');
    const terminal = page.locator('.jp-Terminal');
    await expect(terminal).toBeVisible({ timeout: 10000 });
  });

  test('terminal accepts keyboard input', async ({ page }) => {
    await page.menu.clickMenuItem('File>New>Terminal');
    const terminal = page.locator('.jp-Terminal');
    await expect(terminal).toBeVisible({ timeout: 10000 });
    await terminal.click();
    await page.waitForTimeout(1000);

    await page.keyboard.type('echo PLAYWRIGHT_TEST');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);

    const xtermScreen = page.locator('.xterm-screen');
    await expect(xtermScreen).toBeVisible();
  });
});
