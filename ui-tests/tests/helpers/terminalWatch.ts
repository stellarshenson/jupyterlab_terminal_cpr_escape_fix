/**
 * Terminal helpers for experiments and regression tests (test-only).
 *
 * TerminalWatch records every frame on the page's terminal websockets, in both
 * directions, with epoch-millisecond timestamps - the same clock as the
 * server-side watch (TERMINAL_WATCH_FILE, see jupyter_server_test_config.py).
 * Construct it before the page opens a terminal socket: with galata's default
 * autoGoto the lab is already loaded, so use `test.use({ autoGoto: false })`
 * and call `page.goto()` after the watch exists.
 *
 * The other helpers reach the terminal widget through `window.jupyterapp`,
 * which galata's server config exposes.
 */
import {
  expect,
  IJupyterLabPageFixture,
  JupyterLabPage
} from '@jupyterlab/galata';
import { mkdirSync, writeFileSync } from 'fs';
import { dirname } from 'path';

export interface IWatchFrame {
  /** epoch milliseconds */
  t: number;
  /** 1-based index of the socket in this page, so reconnects stay apart */
  ws: number;
  term: string;
  dir: 'open' | 'sent' | 'recv' | 'close' | 'error';
  /** raw frame text: terminado JSON such as ["stdout", "..."] */
  payload?: string;
}

export class TerminalWatch {
  readonly frames: IWatchFrame[] = [];
  private _sockets = 0;

  constructor(page: IJupyterLabPageFixture) {
    page.on('websocket', ws => {
      const match = /\/terminals\/websocket\/([^/?]+)/.exec(ws.url());
      if (!match) {
        return;
      }
      const id = ++this._sockets;
      const term = decodeURIComponent(match[1]);
      const push = (dir: IWatchFrame['dir'], payload?: string) =>
        this.frames.push({
          t: Date.now(),
          ws: id,
          term,
          dir,
          ...(payload === undefined ? {} : { payload })
        });
      push('open');
      ws.on('framesent', f => push('sent', String(f.payload)));
      ws.on('framereceived', f => push('recv', String(f.payload)));
      ws.on('close', () => push('close'));
      ws.on('socketerror', error => push('error', error));
    });
  }

  /** Write the frames recorded so far as JSON lines. */
  dump(file: string): void {
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(
      file,
      this.frames.map(f => JSON.stringify(f) + '\n').join('')
    );
  }
}

/**
 * Create a terminal through the REST API and return its name.
 *
 * The request is made from the page, not from `page.request`: galata answers
 * the page's GET /api/terminals with only the terminals it saw created through
 * the page, so a terminal made elsewhere is missing from the lab's list, and
 * `terminal:open` then starts a second terminal under the same name - terminado
 * replaces the first in its registry and leaves that PTY orphaned.
 */
export async function createTerminal(
  page: IJupyterLabPageFixture,
  name?: string
): Promise<string> {
  return page.evaluate(async (name?: string) => {
    const response = await fetch('/api/terminals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(name ? { name } : {})
    });
    if (!response.ok) {
      throw new Error(`POST /api/terminals answered ${response.status}`);
    }
    return (await response.json()).name;
  }, name);
}

/** Open terminal `name` in the lab and wait until its socket is connected. */
export async function openTerminal(
  page: IJupyterLabPageFixture,
  name: string
): Promise<void> {
  await page.evaluate(async (name: string) => {
    await (window as any).jupyterapp.commands.execute('terminal:open', {
      name
    });
  }, name);
  await page.waitForFunction((name: string) => {
    const widget = Array.from(
      (window as any).jupyterapp.shell.widgets('main')
    ).find((w: any) => w.content?.session?.name === name) as any;
    return widget?.content?.session?.connectionStatus === 'connected';
  }, name);
}

/** The visible screen of terminal `name`, one string per row, read from the xterm buffer. */
export async function readScreen(
  page: IJupyterLabPageFixture,
  name: string
): Promise<string[]> {
  return page.evaluate((name: string) => {
    const widget = Array.from(
      (window as any).jupyterapp.shell.widgets('main')
    ).find((w: any) => w.content?.session?.name === name) as any;
    const term = widget.content._term;
    const buffer = term.buffer.active;
    const rows: string[] = [];
    for (let i = 0; i < term.rows; i++) {
      rows.push(
        buffer.getLine(buffer.viewportY + i)?.translateToString(true) ?? ''
      );
    }
    return rows;
  }, name);
}

/** Wait until `text` is on the visible screen of terminal `name`. */
export async function waitForScreenText(
  page: IJupyterLabPageFixture,
  name: string,
  text: string,
  timeout = 15000
): Promise<void> {
  await expect
    .poll(async () => (await readScreen(page, name)).join('\n'), { timeout })
    .toContain(text);
}

/**
 * Reload the page and wait until the lab has started. Galata's own readiness
 * check waits for an active Launcher tab, which a restored workspace holding
 * only a terminal never shows, so it is skipped.
 */
export async function reloadLab(page: IJupyterLabPageFixture): Promise<void> {
  // the fixture's type exposes Playwright's reload; galata's takes the option
  await (page as unknown as JupyterLabPage).reload({ waitForIsReady: false });
  await page.locator('#jupyterlab-splash').waitFor({ state: 'detached' });
}

/**
 * Replace the websocket of terminal `name` without reloading the page.
 *
 * - `reconnect` - `session.reconnect()`, the path of the lab's terminal:refresh
 * - `drop` - close the socket with code 4000, so the connection takes the
 *   lost-connection path (onclose -> automatic reconnect), as after a network
 *   drop or a sleeping laptop
 *
 * Resolves once a new socket is connected.
 */
export async function reconnectTerminal(
  page: IJupyterLabPageFixture,
  name: string,
  mode: 'reconnect' | 'drop' = 'reconnect'
): Promise<void> {
  await page.evaluate(
    async ([name, mode]) => {
      const widget = Array.from(
        (window as any).jupyterapp.shell.widgets('main')
      ).find((w: any) => w.content?.session?.name === name) as any;
      const session = widget.content.session;
      const old = session._ws;
      if (mode === 'reconnect') {
        await session.reconnect();
        return;
      }
      old.close(4000, 'test drop');
      await new Promise<void>((resolve, reject) => {
        const start = Date.now();
        const tick = () => {
          if (
            session._ws &&
            session._ws !== old &&
            session.connectionStatus === 'connected'
          ) {
            resolve();
          } else if (Date.now() - start > 30000) {
            reject(new Error(`terminal ${name} did not reconnect`));
          } else {
            setTimeout(tick, 50);
          }
        };
        tick();
      });
    },
    [name, mode]
  );
}
