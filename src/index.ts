import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ITerminalTracker } from '@jupyterlab/terminal';
import { holdUntilOpened } from './unopenedTerminal';

/**
 * Frontend part of the CPR filter extension.
 * The filtering of terminal query responses happens server-side in the Python
 * extension. This plugin handles terminals whose xterm is not opened yet (a
 * background tab after a page load): such a terminal sends no size to the
 * server, and its history is drawn again when it is first shown.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_terminal_cpr_escape_fix:plugin',
  description:
    'Fix CPR escape sequences in idle terminal reconnections and redraw background terminals at their real size when first shown',
  autoStart: true,
  optional: [ITerminalTracker, ISettingRegistry],
  activate: (
    app: JupyterFrontEnd,
    tracker: ITerminalTracker | null,
    settingRegistry: ISettingRegistry | null
  ) => {
    console.log(
      'JupyterLab extension jupyterlab_terminal_cpr_escape_fix is activated!'
    );
    if (!tracker) {
      return;
    }

    let settings: ISettingRegistry.ISettings | null = null;
    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then(loaded => {
          settings = loaded;
        })
        .catch(reason => {
          console.error(
            'Failed to load settings for jupyterlab_terminal_cpr_escape_fix.',
            reason
          );
        });
    }
    const isEnabled = () =>
      settings === null ||
      (settings.get('redrawBackgroundTerminals').composite as boolean);

    tracker.widgetAdded.connect((_, widget) => {
      holdUntilOpened(widget.content, isEnabled);
    });
  }
};

export default plugin;
