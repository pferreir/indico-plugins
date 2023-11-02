import React from 'react';
import ReactDOM from 'react-dom';
import {Button, Dropdown, Icon, Label} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import './ZoomConnectButton.module.scss';

const options = [
  { key: 'make_owner', icon: 'start', text: 'Make me owner', value: 'make_owner' },
];

function ZoomConnectButton() {
  return <Button.Group size="tiny" styleName="button-group">
    <Button as="div" labelPosition="left">
      <Label basic color='green' pointing='right'>
        <Icon name="video camera" />
        12
      </Label>
      <Button color='green'><Translate>Join</Translate></Button>
      <Dropdown className='button icon' floating options={options} trigger={<></>} />
    </Button>
  </Button.Group>
}

window.setupZoomConnectButton = elementId => {
  ReactDOM.render(
    <ZoomConnectButton />, document.getElementById(elementId));
}
