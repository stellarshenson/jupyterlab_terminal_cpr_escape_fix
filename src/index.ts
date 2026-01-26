import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Plugin that confirms the CPR filter extension is active.
 * The actual filtering happens server-side in the Python extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_terminal_cpr_escape_fix:plugin',
  description: 'Fix CPR escape sequences in idle terminal reconnections',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyterlab_terminal_cpr_escape_fix is activated!');
  }
};

export default plugin;
