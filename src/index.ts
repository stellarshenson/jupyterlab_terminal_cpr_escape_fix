import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './request';

/**
 * Initialization data for the jupyterlab_terminal_cpr_escape_fix extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_terminal_cpr_escape_fix:plugin',
  description: 'Fix to the jupyterlab terminado issue that when returning to an idle JupyterLab terminal, cursor position report (CPR) escape sequences appear as literal text',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyterlab_terminal_cpr_escape_fix is activated!');

    requestAPI<any>('hello')
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The jupyterlab_terminal_cpr_escape_fix server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
