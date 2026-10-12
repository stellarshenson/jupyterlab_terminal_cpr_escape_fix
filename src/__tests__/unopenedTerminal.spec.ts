import { Signal } from '@lumino/signaling';
import { holdUntilOpened } from '../unopenedTerminal';

const UNFITTED_SIZE = { type: 'set_size', content: [24, 80, 903, 1522] };
const FITTED_SIZE = { type: 'set_size', content: [63, 177, 903, 1270] };
const STDIN = { type: 'stdin', content: ['ls\r'] };
const STDOUT = { type: 'stdout', content: ['history'] };

/** The parts of the terminal widget that holdUntilOpened uses, in a hidden tab. */
function fakeTerminal(refresh = jest.fn(() => Promise.resolve())) {
  const send = jest.fn();
  const session: any = { send };
  session.messageReceived = new Signal<any, any>(session);
  const terminal: any = {
    node: document.createElement('div'),
    session,
    refresh,
    isVisible: false
  };
  terminal.disposed = new Signal<any, void>(terminal);
  return { terminal, send, refresh };
}

/** What xterm.js does in Terminal.open(): append its element to the widget node. */
function open(terminal: any): void {
  const element = document.createElement('div');
  element.className = 'terminal xterm';
  terminal.node.appendChild(element);
}

/** Let the MutationObserver callback and the promise handlers run. */
function flush(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0));
}

describe('holdUntilOpened', () => {
  it('refreshes exactly once when stdout arrived before the open', async () => {
    const { terminal, refresh } = fakeTerminal();
    holdUntilOpened(terminal, () => true);

    terminal.session.messageReceived.emit(STDOUT);
    open(terminal);
    await flush();
    terminal.node.appendChild(document.createElement('div'));
    await flush();

    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it('does not refresh when stdout arrived while the terminal was visible', async () => {
    const { terminal, refresh } = fakeTerminal();
    terminal.isVisible = true;
    holdUntilOpened(terminal, () => true);

    terminal.session.messageReceived.emit(STDOUT);
    open(terminal);
    await flush();

    expect(refresh).not.toHaveBeenCalled();
  });

  it('does not refresh when no stdout arrived before the open', async () => {
    const { terminal, refresh } = fakeTerminal();
    holdUntilOpened(terminal, () => true);

    open(terminal);
    await flush();

    expect(refresh).not.toHaveBeenCalled();
  });

  it('holds back a set_size and passes a stdin before the open', () => {
    const { terminal, send } = fakeTerminal();
    holdUntilOpened(terminal, () => true);

    terminal.session.send(UNFITTED_SIZE);
    terminal.session.send(STDIN);

    expect(send.mock.calls).toEqual([[STDIN]]);
    expect(send.mock.contexts[0]).toBe(terminal.session);
  });

  it('passes a set_size sent right after the xterm element is appended', () => {
    const { terminal, send } = fakeTerminal();
    holdUntilOpened(terminal, () => true);

    // no await between the two: the observer callback has not run yet
    open(terminal);
    terminal.session.send(FITTED_SIZE);

    expect(send.mock.calls).toEqual([[FITTED_SIZE]]);
  });

  it('puts the original send back after the open', async () => {
    const { terminal, send } = fakeTerminal();
    holdUntilOpened(terminal, () => true);
    expect(terminal.session.send).not.toBe(send);

    open(terminal);
    await flush();

    expect(terminal.session.send).toBe(send);
  });

  it('holds nothing back and refreshes nothing when isEnabled is false', async () => {
    const { terminal, send, refresh } = fakeTerminal();
    holdUntilOpened(terminal, () => false);

    terminal.session.send(UNFITTED_SIZE);
    terminal.session.messageReceived.emit(STDOUT);
    open(terminal);
    await flush();

    expect(send.mock.calls).toEqual([[UNFITTED_SIZE]]);
    expect(refresh).not.toHaveBeenCalled();
  });

  it('leaves a terminal that is already opened untouched', async () => {
    const { terminal, send, refresh } = fakeTerminal();
    open(terminal);
    holdUntilOpened(terminal, () => true);

    expect(terminal.session.send).toBe(send);
    terminal.session.messageReceived.emit(STDOUT);
    terminal.node.appendChild(document.createElement('div'));
    await flush();

    expect(refresh).not.toHaveBeenCalled();
  });

  // jest fails a test during which a promise rejection stays unhandled
  it('catches a rejected refresh', async () => {
    const warn = jest
      .spyOn(console, 'warn')
      .mockImplementation(() => undefined);
    const reason = new Error('reconnect failed');
    const { terminal } = fakeTerminal(jest.fn(() => Promise.reject(reason)));
    holdUntilOpened(terminal, () => true);

    terminal.session.messageReceived.emit(STDOUT);
    open(terminal);
    await flush();

    expect(warn).toHaveBeenCalledTimes(1);
    expect(warn.mock.calls[0]).toContain(reason);
    warn.mockRestore();
  });

  it('puts send back on disposal before the open and does not refresh at a later open', async () => {
    const { terminal, send, refresh } = fakeTerminal();
    holdUntilOpened(terminal, () => true);

    terminal.session.messageReceived.emit(STDOUT);
    terminal.disposed.emit();
    expect(terminal.session.send).toBe(send);
    open(terminal);
    await flush();

    expect(refresh).not.toHaveBeenCalled();
  });
});
