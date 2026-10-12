/**
 * Regression test for DEF-WIDTH-3 and DEF-WIDTH-4: a terminal that a page
 * reload restores in a background tab has an unopened xterm of 80x24 until its
 * tab is shown. Without the fix JupyterLab reports that size to the server and
 * writes the replayed history into it, so history drawn with cursor movement
 * for the real width is laid out wrong, and stays so after the tab is shown.
 *
 * Frames are counted on the page's terminal websockets (TerminalWatch), so the
 * test needs no server watch and runs with fish and with
 * TEST_TERMINAL_SHELL=/bin/bash.
 *
 * The setting redrawBackgroundTerminals = false turns the fix off: the first
 * test then fails and the others pass.
 *
 * The last test can fail only with a shell whose first output arrives before
 * the xterm module has loaded (bash, as in CI); the prompt of fish arrives
 * later.
 */
import {
  expect,
  galata,
  IJupyterLabPageFixture,
  test
} from '@jupyterlab/galata';
import { mkdirSync, writeFileSync } from 'fs';
import * as path from 'path';
import {
  createTerminal,
  openTerminal,
  reloadLab,
  TerminalWatch
} from './helpers/terminalWatch';

const PLUGIN_ID = 'jupyterlab_terminal_cpr_escape_fix:plugin';
const MARKERS = [1, 2, 3, 4].map(i => `MKR-S1-R${i}`);
const END = 'S1-END';

/** A 4-row block of 120 characters drawn twice, with a cursor-up between. */
function blockBytes(): string {
  const row = (marker: string) =>
    `${marker} `.padEnd(120, 'abcdefghij'.repeat(12));
  const draw = MARKERS.map(marker => row(marker) + '\x1b[K').join('\r\n');
  return `${draw}\x1b[3A\r${draw}\r\n${END}\r\n`;
}

let BLOCK_FILE = '';

// the block needs a terminal of more than 120 columns: with galata's default
// settings a 1600 px viewport gave 103 columns on the developer's workstation
test.use({ autoGoto: false, viewport: { width: 2400, height: 1000 } });

test.beforeAll(({}, testInfo) => {
  const out = testInfo.project.outputDir;
  mkdirSync(out, { recursive: true });
  BLOCK_FILE = path.join(out, 'background-block.bin');
  writeFileSync(BLOCK_FILE, blockBytes(), 'latin1');
});

function findWidget(name: string): string {
  return `Array.from(window.jupyterapp.shell.widgets('main')).find(w => w.content?.session?.name === ${JSON.stringify(
    name
  )})`;
}

/** Wait until no frame of `term` has arrived for `quietMs`. */
async function settle(
  page: IJupyterLabPageFixture,
  watch: TerminalWatch,
  term: string,
  quietMs = 1000
): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < 15000) {
    const times = watch.frames.filter(f => f.term === term).map(f => f.t);
    if (Date.now() - Math.max(start, ...times) >= quietMs) {
      return;
    }
    await page.waitForTimeout(100);
  }
}

/** Wait until terminal `name` is connected, without activating its tab. */
async function waitConnected(
  page: IJupyterLabPageFixture,
  name: string
): Promise<void> {
  await page.waitForFunction(
    `(${findWidget(name)})?.content?.session?.connectionStatus === 'connected'`,
    undefined,
    { timeout: 30000 }
  );
}

async function terminalState(page: IJupyterLabPageFixture, name: string) {
  return page.evaluate(
    `(w => ({ visible: !!w?.isVisible, opened: !!w?.content?._termOpened }))(${findWidget(
      name
    )})`
  );
}

/**
 * The xterm buffer of terminal `name` as text. A row whose isWrapped flag is
 * set is joined to the row before it, so a marker split by a line wrap is
 * still found.
 */
async function bufferText(
  page: IJupyterLabPageFixture,
  name: string
): Promise<string> {
  return page.evaluate((name: string) => {
    const widget = Array.from(
      (window as any).jupyterapp.shell.widgets('main')
    ).find((w: any) => w.content?.session?.name === name) as any;
    const buffer = widget?.content?._term?.buffer.active;
    let text = '';
    for (let i = 0; i < (buffer?.length ?? 0); i++) {
      const line = buffer.getLine(i);
      text +=
        (line?.isWrapped ? '' : '\n') + (line?.translateToString(true) ?? '');
    }
    return text;
  }, name);
}

/** How often each marker is in the buffer of terminal `name`. */
async function markerCounts(
  page: IJupyterLabPageFixture,
  name: string
): Promise<number[]> {
  const text = await bufferText(page, name);
  return MARKERS.map(marker => text.split(marker).length - 1);
}

async function waitForBlock(
  page: IJupyterLabPageFixture,
  name: string
): Promise<void> {
  await expect
    .poll(() => bufferText(page, name), { timeout: 20000 })
    .toContain(END);
}

/**
 * Put terminal `name` in front and wait until the workspace that the next
 * reload restores has it as the current tab.
 */
async function openInFront(
  page: IJupyterLabPageFixture,
  name: string
): Promise<void> {
  const saved = page.waitForRequest(request => {
    if (
      request.method() !== 'PUT' ||
      !/\/api\/workspaces\//.test(request.url())
    ) {
      return false;
    }
    const layout = request.postDataJSON()?.data?.['layout-restorer:data'];
    return layout?.main?.current === `terminal:${name}`;
  });
  await openTerminal(page, name);
  await saved;
}

/** Create a terminal in front and print the block in it at its fitted size. */
async function terminalWithBlock(
  page: IJupyterLabPageFixture,
  watch: TerminalWatch
): Promise<string> {
  const name = await createTerminal(page);
  await openInFront(page, name);
  await settle(page, watch, name);
  expect(
    await page.evaluate(`(${findWidget(name)}).content._term.cols`)
  ).toBeGreaterThan(120);
  await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
  await page.keyboard.insertText(`cat ${BLOCK_FILE}`);
  await page.keyboard.press('Enter');
  await waitForBlock(page, name);
  expect(await markerCounts(page, name)).toEqual([1, 1, 1, 1]);
  return name;
}

function framesSince(
  watch: TerminalWatch,
  term: string,
  dir: 'open' | 'sent',
  since: number
) {
  return watch.frames.filter(
    f => f.term === term && f.dir === dir && f.t >= since
  );
}

/** The [rows, cols] of each set_size frame the page sent to `term` since `since`. */
function sizesSent(
  watch: TerminalWatch,
  term: string,
  since: number
): number[][] {
  return framesSince(watch, term, 'sent', since)
    .map(f => JSON.parse(f.payload!))
    .filter(msg => msg[0] === 'set_size')
    .map(msg => [msg[1], msg[2]]);
}

/**
 * Print the block in terminal A, put terminal B in front, reload, wait until
 * the unopened A has parsed its replayed history, then show A.
 */
async function showAfterBackgroundRestore(
  page: IJupyterLabPageFixture,
  watch: TerminalWatch
): Promise<{ name: string; since: number }> {
  await page.goto();
  const name = await terminalWithBlock(page, watch);
  await openInFront(page, await createTerminal(page));

  const since = Date.now();
  await reloadLab(page);
  await waitConnected(page, name);
  await waitForBlock(page, name);
  expect(await terminalState(page, name)).toEqual({
    visible: false,
    opened: false
  });

  await openTerminal(page, name);
  await expect
    .poll(() => terminalState(page, name))
    .toEqual({ visible: true, opened: true });
  await settle(page, watch, name, 1500);
  return { name, since };
}

test.describe('Background terminal redraw', () => {
  test('a terminal restored in a background tab is drawn once at its real size', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    const { name, since } = await showAfterBackgroundRestore(page, watch);

    expect.soft(await markerCounts(page, name)).toEqual([1, 1, 1, 1]);
    const sizes = sizesSent(watch, name, since);
    expect.soft(sizes.length).toBeGreaterThanOrEqual(1);
    expect.soft(sizes).not.toContainEqual([24, 80]);
    expect.soft(framesSince(watch, name, 'open', since)).toHaveLength(2);
  });

  test.describe('setting off', () => {
    test.use({
      mockSettings: {
        ...galata.DEFAULT_SETTINGS,
        [PLUGIN_ID]: { redrawBackgroundTerminals: false }
      }
    });

    test('with the setting off a background terminal is left to JupyterLab', async ({
      page
    }) => {
      const watch = new TerminalWatch(page);
      const { name, since } = await showAfterBackgroundRestore(page, watch);

      expect(framesSince(watch, name, 'open', since)).toHaveLength(1);
    });
  });

  test('a terminal visible during the reload keeps one copy of its history', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await terminalWithBlock(page, watch);

    const since = Date.now();
    await reloadLab(page);
    await waitConnected(page, name);
    await waitForBlock(page, name);
    await settle(page, watch, name, 1500);

    expect(await markerCounts(page, name)).toEqual([1, 1, 1, 1]);
    expect(framesSince(watch, name, 'open', since).length).toBeLessThanOrEqual(
      2
    );
  });

  test('a terminal the user creates is not reconnected', async ({ page }) => {
    const watch = new TerminalWatch(page);
    await page.goto();

    const since = Date.now();
    const name: string = await page.evaluate(async () => {
      const widget = await (window as any).jupyterapp.commands.execute(
        'terminal:create-new'
      );
      return widget.content.session.name;
    });
    await waitConnected(page, name);
    await expect
      .poll(() => terminalState(page, name))
      .toEqual({ visible: true, opened: true });
    await settle(page, watch, name, 1500);

    expect(framesSince(watch, name, 'open', since)).toHaveLength(1);
  });
});
