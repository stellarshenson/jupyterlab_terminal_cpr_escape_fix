/**
 * Regression test for DEF-REPLY-1 (ACC-REPLAY-42..45): terminal queries kept in
 * the terminado replay buffer must not be answered again when a client
 * re-attaches, while a live query still gets exactly one reply.
 *
 * Replies are counted on the page's terminal websockets (TerminalWatch), so the
 * test needs no server watch and runs with the CI runner's bash. The checks of
 * fish's command line run only when the test server's shell is fish.
 *
 * CPR_FIX_DEFAULTS='{"strip_replay_queries": false}' turns the fix off: the
 * re-attach tests then fail and the live test passes.
 */
import { expect, IJupyterLabPageFixture, test } from '@jupyterlab/galata';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'fs';
import * as path from 'path';
import {
  createTerminal,
  openTerminal,
  reconnectTerminal,
  reloadLab,
  TerminalWatch
} from './helpers/terminalWatch';

// the shell jupyter_server_test_config.py starts: fish when installed, else bash
const SHELL =
  process.env.TEST_TERMINAL_SHELL ||
  (existsSync('/usr/bin/fish') ? '/usr/bin/fish' : '/bin/bash');
const FISH = path.basename(SHELL.split(' ')[0]) === 'fish';

/** The queries the probe writes: name -> bytes. xterm.js answers each one live. */
const QUERIES: Record<string, string> = {
  osc11_st: '\x1b]11;?\x1b\\',
  da1_c: '\x1b[c',
  da1_0c: '\x1b[0c',
  da2_gt_c: '\x1b[>c',
  dsr_5n: '\x1b[5n',
  cpr_6n: '\x1b[6n',
  decxcpr_q6n: '\x1b[?6n',
  decrqm_q2004p: '\x1b[?2004$p',
  decrqm_4p: '\x1b[4$p',
  decrqss_qp: '\x1bP$q"p\x1b\\',
  decrqss_m: '\x1bP$qm\x1b\\'
};
const CSI_DCS = Object.keys(QUERIES).filter(q => q !== 'osc11_st');

/** A reply xterm.js sends for a query: OSC color, DA, DA2, DSR, CPR, DECRPM, DECRQSS. */
const REPLY =
  /\x1b(?:\](?:4;\d+|10|11|12);rgb:|\[[?>][\d;]*c|\[\??\d+(?:;\d+)?[nR]|\[\??\d+;\d+\$y|P[01]\$r)/;

/**
 * Writes each query with the tty in raw mode, counts the replies that arrive
 * within 1 s (stops after 0.3 s of quiet), restores the tty and prints
 * `LIVE <count>,<count>,...`.
 */
const PROBE_SOURCE = String.raw`import json, os, re, select, sys, termios, time, tty

QUERIES = {k: v.encode('latin-1') for k, v in json.loads(${JSON.stringify(
  JSON.stringify(QUERIES)
)}).items()}
REPLY = re.compile(rb'\x1b(?:\[[0-?]*[ -/]*[@-~]|[\]P][^\x07\x1b]*(?:\x07|\x1b\\))')

fd = sys.stdin.fileno()
saved = termios.tcgetattr(fd)
tty.setraw(fd)
counts = []
try:
    for name in sys.argv[1].split(','):
        os.write(sys.stdout.fileno(), QUERIES[name])
        buf = b''
        deadline = time.monotonic() + 1.0
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                break
            ready, _, _ = select.select([fd], [], [], min(left, 0.3) if buf else left)
            if not ready:
                if buf:
                    break
                continue
            buf += os.read(fd, 4096)
        counts.append(len(REPLY.findall(buf)))
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, saved)
print('LIVE', ','.join(map(str, counts)))
`;

let OUT = '';

test.use({ autoGoto: false });

test.beforeAll(({}, testInfo) => {
  OUT = testInfo.project.outputDir;
  mkdirSync(OUT, { recursive: true });
  writeFileSync(path.join(OUT, 'query_probe.py'), PROBE_SOURCE);
});

/** Control bytes spelled out, for readable failure messages. */
function vis(s: string): string {
  return s.replace(/\x1b/g, 'ESC').replace(/\x07/g, 'BEL');
}

function payloads(
  watch: TerminalWatch,
  term: string,
  dir: 'sent' | 'recv',
  kind: string,
  since: number
): string[] {
  return watch.frames
    .filter(f => f.term === term && f.dir === dir && f.t >= since)
    .map(f => JSON.parse(f.payload!))
    .filter(msg => msg[0] === kind)
    .map(msg => msg[1] as string);
}

/** The reply-shaped stdin frames the page sent to terminal `term` since `since`. */
function replies(watch: TerminalWatch, term: string, since: number): string[] {
  return payloads(watch, term, 'sent', 'stdin', since)
    .filter(data => REPLY.test(data))
    .map(vis);
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

function findWidget(name: string): string {
  return `Array.from(window.jupyterapp.shell.widgets('main')).find(w => w.content?.session?.name === ${JSON.stringify(
    name
  )})`;
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

async function focusTerminal(
  page: IJupyterLabPageFixture,
  name: string
): Promise<void> {
  await openTerminal(page, name);
  await page.evaluate(`(${findWidget(name)}).content._term.focus()`);
}

/** Type `text` as one stdin frame, then Enter. */
async function runLine(
  page: IJupyterLabPageFixture,
  name: string,
  text: string
): Promise<void> {
  await focusTerminal(page, name);
  await page.keyboard.insertText(text);
  await page.keyboard.press('Enter');
}

/** Create and open a terminal; under fish, bind F12 to dump the command line. */
async function setupTerminal(
  page: IJupyterLabPageFixture,
  watch: TerminalWatch
): Promise<string> {
  const name = await createTerminal(page);
  await openTerminal(page, name);
  await settle(page, watch, name);
  if (FISH) {
    const file = path.join(OUT, `cl-${name}.txt`);
    await runLine(page, name, `bind \\e\\[24~ 'commandline > ${file}'`);
    await settle(page, watch, name, 800);
  }
  return name;
}

/** fish's command line, read through the F12 binding without running it. */
async function commandLine(
  page: IJupyterLabPageFixture,
  name: string
): Promise<string> {
  const file = path.join(OUT, `cl-${name}.txt`);
  rmSync(file, { force: true });
  await focusTerminal(page, name);
  await page.keyboard.press('F12');
  // `commandline` ends its output with a newline, so a complete dump ends in one
  await expect
    .poll(() => (existsSync(file) ? readFileSync(file, 'utf-8') : ''))
    .toMatch(/\n$/);
  return readFileSync(file, 'utf-8').replace(/\n$/, '');
}

/** Run the probe with `queries` and return the reply count of each. */
async function probe(
  page: IJupyterLabPageFixture,
  watch: TerminalWatch,
  name: string,
  queries: string[]
): Promise<number[]> {
  const since = Date.now();
  const script = path.join(OUT, 'query_probe.py');
  await runLine(page, name, `python3 ${script} ${queries.join(',')}`);
  let counts: number[] = [];
  await expect
    .poll(
      () => {
        const out = payloads(watch, name, 'recv', 'stdout', since).join('');
        const match = /LIVE ([\d,]+)\r?\n/.exec(out);
        counts = match ? match[1].split(',').map(Number) : [];
        return counts.length;
      },
      { timeout: 15000 + queries.length * 1500 }
    )
    .toBe(queries.length);
  await settle(page, watch, name, 800);
  return counts;
}

test.describe('Replayed terminal queries', () => {
  test('live query reaches the client unchanged and gets one reply', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await setupTerminal(page, watch);

    const since = Date.now();
    const counts = await probe(page, watch, name, ['osc11_st']);

    expect(payloads(watch, name, 'recv', 'stdout', since).join('')).toContain(
      QUERIES.osc11_st
    );
    expect(counts).toEqual([1]);
    expect(replies(watch, name, since)).toHaveLength(1);
    if (FISH) {
      expect(await commandLine(page, name)).toBe('');
    }
  });

  test('3 drops, 1 reconnect and 3 reloads send no replies', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await setupTerminal(page, watch);
    await probe(page, watch, name, ['osc11_st']);

    const since = Date.now();
    for (const mode of ['drop', 'drop', 'drop', 'reconnect'] as const) {
      await reconnectTerminal(page, name, mode);
      await settle(page, watch, name, 1500);
    }
    for (let i = 0; i < 3; i++) {
      await reloadLab(page);
      await waitConnected(page, name);
      await settle(page, watch, name, 1500);
    }

    expect(replies(watch, name, since)).toEqual([]);
    if (FISH) {
      expect(await commandLine(page, name)).toBe('');
    }
  });

  test('hidden terminal opened earlier sends no replies on re-attach', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await setupTerminal(page, watch);
    await probe(page, watch, name, ['osc11_st', 'osc11_st', 'osc11_st']);
    // a second terminal takes the tab: the first stays opened but hidden
    await setupTerminal(page, watch);
    expect(await terminalState(page, name)).toEqual({
      visible: false,
      opened: true
    });

    const since = Date.now();
    await reconnectTerminal(page, name, 'drop');
    await settle(page, watch, name, 1500);

    expect(replies(watch, name, since)).toEqual([]);
    if (FISH) {
      expect(await commandLine(page, name)).toBe('');
    }
  });

  test('restored terminal never opened sends no CSI or DCS replies after reload', async ({
    page
  }) => {
    const watch = new TerminalWatch(page);
    await page.goto();
    const name = await setupTerminal(page, watch);
    expect(await probe(page, watch, name, CSI_DCS)).toEqual(
      CSI_DCS.map(() => 1)
    );
    // a second terminal takes the tab, so the reload restores the first hidden
    await setupTerminal(page, watch);

    const since = Date.now();
    await reloadLab(page);
    await waitConnected(page, name);
    await settle(page, watch, name, 1500);
    expect(await terminalState(page, name)).toEqual({
      visible: false,
      opened: false
    });

    expect(replies(watch, name, since)).toEqual([]);
    // reading the command line activates the tab; the replies were counted before
    if (FISH) {
      expect(await commandLine(page, name)).toBe('');
    }
  });
});
