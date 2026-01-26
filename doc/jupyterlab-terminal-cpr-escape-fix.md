# JupyterLab Terminal CPR Escape Sequence Fix

When returning to an idle JupyterLab terminal, cursor position report (CPR) escape sequences appear as literal text:
```
[52;1R[13;1R[15;1R[17;1R[19;1R[21;1R[23;1R[25;1R...
```

These are `ESC[row;colR` responses to Device Status Report queries (`ESC[6n`).

## Root Cause

Terminado's reconnection buffer stores raw PTY output without filtering escape sequences. On reconnect, the entire buffer is concatenated and sent as bulk text. xterm.js processes streaming escape sequences correctly but renders bulk concatenated CPR sequences as literal text.

**Data flow on reconnect:**
```
read_buffer.copy() -> concatenate chunks -> send_json_message(["stdout", bulk_data])
    -> JupyterLab _onMessage -> term.write(bulk) -> CPR rendered as text
```

## Key Source Files

| Component | File | Lines |
|-----------|------|-------|
| Buffer storage | `terminado/management.py` | 54, 262-265 |
| Buffer replay | `terminado/websocket.py` | 68-77 |
| Message handler | `jupyterlab/packages/terminal/src/widget.ts` | 436-452 |
| CPR generation | `xterm.js/src/common/InputHandler.ts` | 2748-2752 |

## Backend Fix (Recommended)

Patch Terminado to filter escape sequences during buffer replay. This is the safest approach - fixes the issue at source without JavaScript monkey-patching.

### Option A: Filter on Replay (Preferred)

Patch `terminado/websocket.py` to filter when draining the buffer on reconnect. This preserves CPR sequences for active sessions while filtering them from bulk replay.

**terminado/websocket.py** - modify `open()` method (lines 68-77):
```python
import re

# Add at module level
CPR_PATTERN = re.compile(r'\x1b\[\d+;\d+R')
DA_PATTERN = re.compile(r'\x1b\[\?[\d;]*c')

# In open() method, replace buffer drain logic:
preopen_buffer = self.terminal.read_buffer.copy()
buffered = ""
while preopen_buffer:
    s = preopen_buffer.popleft()
    buffered += s
if buffered:
    # Filter CPR and DA sequences from bulk replay
    buffered = CPR_PATTERN.sub('', buffered)
    buffered = DA_PATTERN.sub('', buffered)
    self.on_pty_read(buffered)
```

### Option B: Filter on Storage

Patch `terminado/management.py` to filter before storing in buffer. More aggressive - CPR sequences never stored.

**terminado/management.py** - modify PTY read loop (line 263):
```python
import re

# Add at module level
CPR_PATTERN = re.compile(rb'\x1b\[\d+;\d+R')
DA_PATTERN = re.compile(rb'\x1b\[\?[\d;]*c')

# In _pty_read() method:
s = ptywclients.ptyproc.read(65536)
s = CPR_PATTERN.sub(b'', s)
s = DA_PATTERN.sub(b'', s)
ptywclients.read_buffer.append(s)
```

### Deployment

For conda environments, patch files directly:
```bash
TERMINADO_PATH=$(python -c "import terminado; print(terminado.__path__[0])")
# Edit $TERMINADO_PATH/websocket.py or management.py
```

For Docker images, create patched version:
```dockerfile
COPY patches/websocket.py /opt/conda/lib/python3.12/site-packages/terminado/websocket.py
```

## Alternative: Frontend Extension

Create a JupyterLab extension that intercepts terminal messages. Less safe due to JavaScript monkey-patching and potential race conditions with message handling.

```bash
copier copy --trust https://github.com/jupyterlab/extension-template jupyterlab_terminal_cpr_filter_extension
```

**src/index.ts:**
```typescript
import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { ITerminalTracker } from '@jupyterlab/terminal';

const CPR_REGEX = /\x1b\[\d+;\d+R/g;
const DA_REGEX = /\x1b\[\?[\d;]*c/g;

function filterEscapeSequences(data: string): string {
  return data.replace(CPR_REGEX, '').replace(DA_REGEX, '');
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab-terminal-cpr-filter:plugin',
  autoStart: true,
  requires: [ITerminalTracker],
  activate: (app: JupyterFrontEnd, tracker: ITerminalTracker) => {
    tracker.widgetAdded.connect((sender, widget) => {
      const session = widget.content.session;
      if (!session) return;

      const originalWrite = widget.content['_term'].write.bind(widget.content['_term']);
      session.messageReceived.connect((sender, msg) => {
        if (msg.type === 'stdout' && msg.content) {
          const filtered = filterEscapeSequences(msg.content[0] as string);
          if (filtered !== msg.content[0]) {
            originalWrite(filtered);
            return;
          }
        }
      });
    });
  }
};

export default plugin;
```

## Verification

1. Open JupyterLab terminal (any shell)
2. Leave idle 5+ minutes
3. Disconnect/reconnect (close laptop lid, network interruption)
4. Return and interact - no `[nn;1R` sequences should appear

## References

- Terminado source: `/opt/conda/lib/python3.12/site-packages/terminado/`
- JupyterLab terminal widget: `jupyterlab/packages/terminal/src/widget.ts`
- xterm.js CPR handling: `xterm.js/src/common/InputHandler.ts`
