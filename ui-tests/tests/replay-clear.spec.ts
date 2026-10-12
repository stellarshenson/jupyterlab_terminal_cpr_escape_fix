/**
 * Regression tests for the server-side clear before each history replay
 * (clear_before_replay, ACC-CLEAR-58 to ACC-CLEAR-64, ACC-WIDTH-54): the
 * client's terminal is empty when the replay is written.
 *
 * This file belongs to the feature and is deleted with it; see
 * docs/monkeypatches.md. Frames are counted on the page's terminal websockets
 * (TerminalWatch), so the tests need no server watch and run with fish and with
 * TEST_TERMINAL_SHELL='/bin/bash --norc --noprofile'.
 *
 * CPR_FIX_DEFAULTS='{"clear_before_replay": false}' turns the fix off: tests
 * a, b, c and f are then skipped, test d (modes survive) and the test of the
 * first replay frame run and pass. With CPR_FIX_CANARY=1 as well, a, b, c and
 * f run and fail. Test a guards only in fish: in bash it passes without the fix.
 */
import { expect, IJupyterLabPageFixture, test } from '@jupyterlab/galata';
import { mkdirSync, writeFileSync } from 'fs';
import * as path from 'path';
import {
  createTerminal,
  openTerminal,
  reconnectTerminal,
  reloadLab,
  TerminalWatch
} from './helpers/terminalWatch';

// the server switch for this run, as jupyter_server_test_config.py applies it
const CLEAR_ON =
  JSON.parse(process.env.CPR_FIX_DEFAULTS || '{}').clear_before_replay !==
  false;
// CPR_FIX_CANARY=1 runs tests a, b and c with the switch off, to check whether
// upstream no longer needs the patch (docs/monkeypatches.md): they must fail
const SKIP_WHEN_OFF = !CLEAR_ON && !process.env.CPR_FIX_CANARY;
const CLEAR_PREFIX = '\x1b[H\x1b[2J\x1b[3J';

const MARKERS = [1, 2, 3, 4].map(i => `MKR-CLR-R${i}`);
const END = 'CLR-END';
const ALT_UP = 'CLR-ALT-UP';
const ALT_READY = 'CLR-ALT-READY';

/** A 4-row block of 120 characters drawn twice, with a cursor-up between. */
function blockBytes(): string {
  const row = (marker: string) =>
    `${marker} `.padEnd(120, 'abcdefghij'.repeat(12));
  const draw = MARKERS.map(marker => row(marker) + '\x1b[K').join('\r\n');
  return `${draw}\x1b[3A\r${draw}\r\n${END}\r\n`;
}

/** Enters the alternate screen, waits for Enter, leaves it. */
const ALT_PROGRAM = String.raw`import sys
sys.stdout.write('\x1b[?1049h\x1b[2J\x1b[H${ALT_UP}\r\n')
sys.stdout.flush()
sys.stdin.readline()
sys.stdout.write('\x1b[?1049l')
sys.stdout.flush()
`;

/**
 * Enters the alternate screen, sets mouse reporting and bracketed paste, then
 * writes 1600 one-byte chunks, so the replay window of 1000 chunks no longer
 * holds the mode sequences.
 */
const MODE_PROGRAM = String.raw`import os, sys, time
os.write(1, b'\x1b[?1049h\x1b[?1000h\x1b[?2004h${ALT_UP}\r\n')
for _ in range(1600):
    os.write(1, b'.')
    time.sleep(0.005)
os.write(1, b'\r\n${ALT_READY}\r\n')
sys.stdin.readline()
os.write(1, b'\x1b[?1000l\x1b[?2004l\x1b[?1049l')
`;

let BLOCK_FILE = '';
let ALT_FILE = '';
let MODE_FILE = '';

// the block needs a terminal of more than 120 columns
test.use({ autoGoto: false, viewport: { width: 2400, height: 1000 } });

test.beforeAll(({}, testInfo) => {
  const out = testInfo.project.outputDir;
  mkdirSync(out, { recursive: true });
  BLOCK_FILE = path.join(out, 'replay-clear-block.bin');
  ALT_FILE = path.join(out, 'replay-clear-alt.py');
  MODE_FILE = path.join(out, 'replay-clear-modes.py');
  writeFileSync(BLOCK_FILE, blockBytes(), 'latin1');
  writeFileSync(ALT_FILE, ALT_PROGRAM);
  writeFileSync(MODE_FILE, MODE_PROGRAM);
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
 * The active xterm buffer of terminal `name` as text. A row whose isWrapped
 * flag is set is joined to the row before it, so a marker split by a line wrap
 * is still found.
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

/** Row `index` of the active xterm buffer of terminal `name`. */
async function bufferRow(
  page: IJupyterLabPageFixture,
  name: string,
  index: number
): Promise<string> {
  return page.evaluate(
    ([name, index]) => {
      const widget = Array.from(
        (window as any).jupyterapp.shell.widgets('main')
      ).find((w: any) => w.content?.session?.name === name) as any;
      return (
        widget?.content?._term?.buffer.active
          .getLine(index as number)
          ?.translateToString(true) ?? ''
      );
    },
    [name, index] as [string, number]
  );
}

/** The xterm state that a reconnect must not change. */
async function terminalModes(page: IJupyterLabPageFixture, name: string) {
  return page.evaluate(
    `(t => ({ buffer: t.buffer.active.type, mouse: t.modes.mouseTrackingMode, paste: t.modes.bracketedPasteMode }))((${findWidget(
      name
    )}).content._term)`
  );
}

async function markerCounts(
  page: IJupyterLabPageFixture,
  name: string
): Promise<number[]> {
  const text = await bufferText(page, name);
  return MARKERS.map(marker => text.split(marker).length - 1);
}

async function waitForText(
  page: IJupyterLabPageFixture,
  name: string,
  text: string
): Promise<void> {
  await expect
    .poll(() => bufferText(page, name), { timeout: 30000 })
    .toContain(text);
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

/** Type `command` in terminal `name` and press Enter. */
async function runLine(
  page: IJupyterLabPageFixture,
  name: string,
  command: string
): Promise<void> {
  await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
  await page.keyboard.insertText(command);
  await page.keyboard.press('Enter');
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
  await runLine(page, name, `cat ${BLOCK_FILE}`);
  await waitForText(page, name, END);
  expect(await markerCounts(page, name)).toEqual([1, 1, 1, 1]);
  return name;
}

/** Reload with terminal `name` in a background tab, then show it. */
async function reloadAndShow(
  page: IJupyterLabPageFixture,
  watch: TerminalWatch,
  name: string,
  hiddenText: string
): Promise<void> {
  await openInFront(page, await createTerminal(page));
  await reloadLab(page);
  await waitConnected(page, name);
  await waitForText(page, name, hiddenText);
  expect(await terminalState(page, name)).toEqual({
    visible: false,
    opened: false
  });
  await openTerminal(page, name);
  await expect
    .poll(() => terminalState(page, name))
    .toEqual({ visible: true, opened: true });
  await settle(page, watch, name, 1500);
}

/**
 * The text of the first stdout frame on the socket that terminal `term` opened
 * since `since`. Frames of the old socket that arrive late are not counted.
 */
function firstStdout(
  watch: TerminalWatch,
  term: string,
  since: number
): string | undefined {
  const opened = watch.frames.find(
    f => f.term === term && f.dir === 'open' && f.t >= since
  );
  return watch.frames
    .filter(f => f.ws === opened?.ws && f.dir === 'recv')
    .map(f => JSON.parse(f.payload!))
    .find(msg => msg[0] === 'stdout')?.[1];
}

test.describe('Clear before replay', () => {
  // guards only in fish: in bash this test passes without the fix
  test('a: background-tab redraw starts at the first line of the history', async ({
    page
  }) => {
    test.skip(SKIP_WHEN_OFF, 'server switch clear_before_replay is off');
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await terminalWithBlock(page, watch);
    const rowBefore = await bufferRow(page, name, 0);
    expect(rowBefore).not.toBe('');

    await reloadAndShow(page, watch, name, END);

    expect(await bufferRow(page, name, 0)).toBe(rowBefore);
  });

  test('b: history before a full-screen program has the fitted layout', async ({
    page
  }) => {
    test.skip(SKIP_WHEN_OFF, 'server switch clear_before_replay is off');
    test.setTimeout(180000);
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await terminalWithBlock(page, watch);
    await runLine(page, name, `python3 ${ALT_FILE}`);
    await waitForText(page, name, ALT_UP);

    await reloadAndShow(page, watch, name, ALT_UP);
    expect((await terminalModes(page, name)).buffer).toBe('alternate');
    await waitForText(page, name, ALT_UP);

    await runLine(page, name, '');
    await expect
      .poll(async () => (await terminalModes(page, name)).buffer)
      .toBe('normal');
    await waitForText(page, name, END);
    expect(await markerCounts(page, name)).toEqual([1, 1, 1, 1]);
  });

  test('c: a plain reconnect keeps one copy of the history', async ({
    page
  }) => {
    test.skip(SKIP_WHEN_OFF, 'server switch clear_before_replay is off');
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await terminalWithBlock(page, watch);

    await reconnectTerminal(page, name, 'reconnect');
    await settle(page, watch, name, 1500);

    expect(await markerCounts(page, name)).toEqual([1, 1, 1, 1]);
  });

  /** Create a terminal in front and run the mode program in it up to ALT_READY. */
  async function terminalInModeProgram(
    page: IJupyterLabPageFixture,
    watch: TerminalWatch
  ): Promise<string> {
    const name = await createTerminal(page);
    await openInFront(page, name);
    await settle(page, watch, name);
    await runLine(page, name, `python3 ${MODE_FILE}`);
    await waitForText(page, name, ALT_READY);
    expect(await terminalModes(page, name)).toEqual({
      buffer: 'alternate',
      mouse: 'vt200',
      paste: true
    });
    return name;
  }

  test('d: alternate screen and input modes older than the replay survive a reconnect', async ({
    page
  }) => {
    test.setTimeout(180000);
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await terminalInModeProgram(page, watch);

    const since = Date.now();
    await reconnectTerminal(page, name, 'reconnect');
    await settle(page, watch, name, 1500);

    // the replay must not set the modes again, or the test proves nothing
    const replay = firstStdout(watch, name, since) ?? '';
    expect(replay).not.toBe('');
    expect(replay).not.toContain('\x1b[?1049h');
    expect(replay).not.toContain('\x1b[?1000h');
    expect(replay).not.toContain('\x1b[?2004h');
    expect(await terminalModes(page, name)).toEqual({
      buffer: 'alternate',
      mouse: 'vt200',
      paste: true
    });

    await runLine(page, name, '');
  });

  test('f: after a full-screen program has exited, a reconnect leaves none of its rows on the normal screen', async ({
    page
  }) => {
    test.skip(SKIP_WHEN_OFF, 'server switch clear_before_replay is off');
    test.setTimeout(180000);
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await terminalInModeProgram(page, watch);
    await runLine(page, name, '');
    await expect
      .poll(async () => (await terminalModes(page, name)).buffer)
      .toBe('normal');
    expect(await bufferText(page, name)).not.toContain(ALT_READY);

    // the replay starts inside the alternate screen (its first switch is the
    // leave): the prefix must draw the replayed rows there, not on the normal screen
    await reconnectTerminal(page, name, 'reconnect');
    await settle(page, watch, name, 1500);

    expect((await terminalModes(page, name)).buffer).toBe('normal');
    const text = await bufferText(page, name);
    expect(text).not.toContain(ALT_READY);
    expect(text).not.toContain('.'.repeat(20));
  });

  test('first replay frame starts with the prefix when the switch is on', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await createTerminal(page);
    await openInFront(page, name);
    await settle(page, watch, name);
    await runLine(page, name, 'echo CLR-FRAME-MARK');
    await waitForText(page, name, 'CLR-FRAME-MARK');

    const since = Date.now();
    await reconnectTerminal(page, name, 'reconnect');
    await settle(page, watch, name, 1500);

    const replay = firstStdout(watch, name, since);
    expect(replay).toBeDefined();
    expect(replay!.startsWith(CLEAR_PREFIX)).toBe(CLEAR_ON);
  });
});
