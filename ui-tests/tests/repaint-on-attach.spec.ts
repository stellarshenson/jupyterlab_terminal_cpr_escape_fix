/**
 * Tests of the repaint on attach (repaint_on_attach, MP-5 in
 * docs/monkeypatches.md): after a reconnect the server sets the PTY one column
 * narrower and back, so a full-screen program repaints the rows that are older
 * than the replay window of 1000 chunks.
 *
 * Test 1 is the canary. CPR_FIX_DEFAULTS='{"repaint_on_attach": false}' turns
 * the patch off: the test is then skipped. With CPR_FIX_CANARY=1 as well it
 * runs and fails.
 *
 * Test 2 is a regression test for the step itself (DEF-BOUNCE-14): a row step
 * made a program that addresses rows absolutely write one row below the
 * browser's last row, so the line it committed during the step was lost. The
 * test must pass with the switch on and with it off, so it has no skip rule.
 *
 * Test 3 is a regression test for the guard of the step: a width step makes the
 * line editor of bash erase the output line above a typed line that fills the
 * width, so the server makes no step while the foreground process group of the
 * terminal is one shell alone. It has no skip rule either.
 */
import { expect, IJupyterLabPageFixture, test } from '@jupyterlab/galata';
import { execFileSync } from 'child_process';
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
const REPAINT_ON =
  JSON.parse(process.env.CPR_FIX_DEFAULTS || '{}').repaint_on_attach !== false;
const SKIP_WHEN_OFF = !REPAINT_ON && !process.env.CPR_FIX_CANARY;

const HEADER = 'PRB-HEADER';
const FOOTER = 'PRB-FOOTER';
const READY = 'PRB-READY';

/**
 * A full-screen program: static header and footer drawn once and again on
 * SIGWINCH, then 1600 one-byte updates of one field, so the static rows are
 * older than the replay window.
 */
const STATIC_PROGRAM = String.raw`import os, signal, sys, time
def paint(*_):
    os.write(1, b'\x1b[1;1H${HEADER}\x1b[20;1H${FOOTER}')
os.write(1, b'\x1b[?1049h\x1b[2J')
paint()
signal.signal(signal.SIGWINCH, paint)
for i in range(1600):
    os.write(1, b'\x1b[10;1H%04d' % i)
    time.sleep(0.005)
os.write(1, b'\x1b[12;1H${READY}')
sys.stdin.readline()
os.write(1, b'\x1b[?1049l')
`;

/**
 * A program that addresses rows absolutely on the normal buffer (the abs mode
 * of ui-tests/experiments/e3_standin.py at 20 frames a second): 4 live rows at
 * the bottom of the PTY, redrawn every frame and on SIGWINCH, and every second
 * frame a committed line 'LOG<n> W<cols>x<rows>' scrolled in above them. The
 * lines are short and not padded: a terminal present at page load and one
 * opened later are fitted to different column counts in the test browser, and
 * a padded line would wrap when the replay lands in the narrower one.
 */
const ABS_PROGRAM = String.raw`import os, signal, time
K = 4
FRAME_S = 0.05
COMMIT_EVERY = 2
frame = 0
committed = 0

def size():
    s = os.get_terminal_size(1)
    return s.columns, s.lines

def draw(commit):
    cols, rows = size()
    top = rows - K + 1
    out = []
    if commit:
        out.append('\x1b[%d;1H\n' % rows)
        out.append('\x1b[%d;1HLOG%d W%dx%d\x1b[K' % (rows - K, committed, cols, rows))
    for i in range(K):
        out.append('\x1b[%d;1HLIVE r%d f%05d W%dx%d\x1b[K' % (top + i, i, frame, cols, rows))
    os.write(1, ''.join(out).encode())

signal.signal(signal.SIGWINCH, lambda *_: draw(False))
try:
    while True:
        frame += 1
        commit = frame % COMMIT_EVERY == 0
        if commit:
            committed += 1
        draw(commit)
        time.sleep(FRAME_S)
except KeyboardInterrupt:
    os.write(1, b'\r\n')
`;

let PROGRAM_FILE = '';
let ABS_FILE = '';

test.use({ autoGoto: false });

test.beforeAll(({}, testInfo) => {
  const out = testInfo.project.outputDir;
  mkdirSync(out, { recursive: true });
  PROGRAM_FILE = path.join(out, 'repaint-static.py');
  ABS_FILE = path.join(out, 'repaint-abs.py');
  writeFileSync(PROGRAM_FILE, STATIC_PROGRAM);
  writeFileSync(ABS_FILE, ABS_PROGRAM);
});

function findWidget(name: string): string {
  return `Array.from(window.jupyterapp.shell.widgets('main')).find(w => w.content?.session?.name === ${JSON.stringify(
    name
  )})`;
}

/** The active xterm buffer of terminal `name` as text. */
async function bufferText(
  page: IJupyterLabPageFixture,
  name: string
): Promise<string> {
  return page.evaluate((name: string) => {
    const widget = Array.from(
      (window as any).jupyterapp.shell.widgets('main')
    ).find((w: any) => w.content?.session?.name === name) as any;
    const buffer = widget?.content?._term?.buffer.active;
    const lines: string[] = [];
    for (let i = 0; i < (buffer?.length ?? 0); i++) {
      lines.push(buffer.getLine(i)?.translateToString(true) ?? '');
    }
    return lines.join('\n');
  }, name);
}

function count(text: string, marker: string): number {
  return text.split(marker).length - 1;
}

/** The width of terminal `name` and the cursor position in its buffer. */
async function cursorState(
  page: IJupyterLabPageFixture,
  name: string
): Promise<{ cols: number; x: number; row: number }> {
  return page.evaluate((name: string) => {
    const widget = Array.from(
      (window as any).jupyterapp.shell.widgets('main')
    ).find((w: any) => w.content?.session?.name === name) as any;
    const term = widget.content._term;
    const buffer = term.buffer.active;
    return {
      cols: term.cols,
      x: buffer.cursorX,
      row: buffer.baseY + buffer.cursorY
    };
  }, name);
}

async function runLine(
  page: IJupyterLabPageFixture,
  name: string,
  command: string
): Promise<void> {
  await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
  await page.keyboard.insertText(command);
  await page.keyboard.press('Enter');
}

/**
 * Open terminal `name` in front and wait until the workspace that the next
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

/** Wait until the restored terminal `name` is connected again. */
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

/** Ctrl-C through the terminal; kill what still runs the program file. */
async function stopProgram(
  page: IJupyterLabPageFixture,
  name: string,
  file: string
): Promise<void> {
  await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
  await page.keyboard.press('Control+c');
  await page.waitForTimeout(500);
  try {
    execFileSync('pgrep', ['-f', file], { stdio: 'ignore' });
  } catch {
    return; // exit 1: no process left
  }
  execFileSync('pkill', ['-f', file], { stdio: 'ignore' });
}

test.describe('Repaint on attach', () => {
  test('static rows older than the replay are drawn again after a reconnect', async ({
    page
  }) => {
    test.skip(SKIP_WHEN_OFF, 'server switch repaint_on_attach is off');
    test.setTimeout(180000);
    new TerminalWatch(page);
    await page.goto();
    const name = await createTerminal(page);
    await openTerminal(page, name);
    await page.waitForTimeout(2000);
    await runLine(page, name, `python3 ${PROGRAM_FILE}`);
    await expect
      .poll(() => bufferText(page, name), { timeout: 40000 })
      .toContain(READY);
    const before = await bufferText(page, name);
    expect(count(before, HEADER)).toBe(1);
    expect(count(before, FOOTER)).toBe(1);

    await reconnectTerminal(page, name, 'reconnect');
    await page.waitForTimeout(3000);

    const after = await bufferText(page, name);
    expect(count(after, HEADER)).toBe(1);
    expect(count(after, FOOTER)).toBe(1);
    await runLine(page, name, '');
  });

  test('a program that addresses rows absolutely keeps every committed line across a page reload', async ({
    page
  }) => {
    test.setTimeout(240000);
    new TerminalWatch(page);
    await page.goto();
    for (const trial of [1, 2, 3]) {
      const name = await createTerminal(page);
      await openInFront(page, name);
      await page.waitForTimeout(2000);
      await runLine(page, name, `python3 ${ABS_FILE}`);
      await page.waitForTimeout(3000);

      await reloadLab(page);
      await waitConnected(page, name);
      await page.waitForTimeout(3000);
      const lines = (await bufferText(page, name)).split('\n');
      await stopProgram(page, name, ABS_FILE);

      const ids = lines
        .map(line => /^LOG(\d+) W/.exec(line))
        .filter(m => m)
        .map(m => Number(m![1]));
      // soft: a damaged trial is reported and the next trial still runs
      const top = Math.max(0, ...ids);
      expect.soft(top, `trial ${trial}: no LOG line`).toBeGreaterThan(0);
      for (let n = 1; n <= top; n++) {
        expect
          .soft(
            lines.filter(line => line.startsWith(`LOG${n} `)).length,
            `trial ${trial}: LOG${n}`
          )
          .toBe(1);
      }
      expect
        .soft(
          lines.filter(line => line.startsWith('LIVE r')).length,
          `trial ${trial}: live rows`
        )
        .toBe(4);
    }
  });

  test('a shell prompt with a typed line that fills the width keeps the output above it across a reconnect', async ({
    page
  }) => {
    test.setTimeout(180000);
    const watch = new TerminalWatch(page);
    await page.goto();
    for (const trial of ['own shell', 'nested bash']) {
      const name = await createTerminal(page);
      await openTerminal(page, name);
      await page.waitForTimeout(2000);
      if (trial === 'nested bash') {
        const start = (await cursorState(page, name)).row;
        await runLine(page, name, 'bash --norc --noprofile');
        await expect
          .poll(
            async () => {
              const { row } = await cursorState(page, name);
              const line = (await bufferText(page, name)).split('\n')[row];
              return row > start && /^bash-[\d.]+\$ $/.test(line);
            },
            { timeout: 20000 }
          )
          .toBe(true);
      }
      // the command line holds the marker in two quoted parts, so only the
      // output line is equal to the marker
      const id = trial === 'own shell' ? 1 : 2;
      const markers = ['A', 'B', 'C'].map(part => `PRL-${id}-${part}`);
      for (const marker of markers) {
        await runLine(
          page,
          name,
          `echo "${marker.slice(0, 5)}""${marker.slice(5)}"`
        );
        await expect
          .poll(
            async () =>
              (await bufferText(page, name))
                .split('\n')
                .filter(line => line === marker).length,
            { timeout: 20000 }
          )
          .toBe(1);
      }
      await page.waitForTimeout(1500);
      // the cursor column at the empty prompt is the width of the prompt
      const prompt = await cursorState(page, name);
      const typed = 'abcdefghijklmnopqrstuvwxyz'
        .repeat(20)
        .slice(0, prompt.cols - 1 - prompt.x);
      expect(
        typed.length,
        `${trial}: columns left of the width`
      ).toBeGreaterThan(0);
      await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
      await page.keyboard.insertText(typed);
      await page.waitForTimeout(1000);
      const before = (await bufferText(page, name)).split('\n');

      // the repaint is debounced 5 s per terminal: reconnect later than that
      // after the last socket open of this terminal
      const opened = Math.max(
        ...watch.frames
          .filter(frame => frame.term === name && frame.dir === 'open')
          .map(frame => frame.t)
      );
      await page.waitForTimeout(Math.max(0, opened + 6000 - Date.now()));
      await reconnectTerminal(page, name, 'reconnect');
      await page.waitForTimeout(3000);
      const after = (await bufferText(page, name)).split('\n');

      // soft: a damaged trial is reported and the next trial still runs
      for (const marker of markers) {
        expect
          .soft(
            before.filter(line => line === marker).length,
            `${trial}: ${marker} before the reconnect`
          )
          .toBe(1);
        expect
          .soft(
            after.filter(line => line === marker).length,
            `${trial}: ${marker} after the reconnect`
          )
          .toBe(1);
      }
      const row = before.findIndex(line => line.includes(typed));
      expect
        .soft(row, `${trial}: typed text before the reconnect`)
        .toBeGreaterThanOrEqual(0);
      expect
        .soft(
          after.findIndex(line => line.includes(typed)),
          `${trial}: row of the typed text after the reconnect`
        )
        .toBe(row);

      await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
      await page.keyboard.press('Control+u');
      if (trial === 'nested bash') {
        await runLine(page, name, 'exit');
      }
    }
  });
});
