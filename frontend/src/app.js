import React from 'react';

import '@patternfly/react-core/dist/styles/base.css';
import {
  AboutModal,
  Alert,
  AlertActionLink,
  AlertGroup,
  AlertVariant,
  Brand,
  Button,
  Flex,
  FlexItem,
  Nav,
  NavList,
  Page,
  PageHeader,
  PageSidebar,
  Select,
  SelectOption,
  SelectVariant,
  TextContent,
  TextList,
  TextListItem,
  PageHeaderTools,
  PageHeaderToolsGroup,
  PageHeaderToolsItem
} from '@patternfly/react-core';
import EventEmitter from 'wolfy87-eventemitter';

import { UploadIcon, ServerIcon, QuestionCircleIcon } from '@patternfly/react-icons';
import { BrowserRouter as Router, NavLink, Route, Switch, withRouter } from 'react-router-dom';
import accessibleStyles from '@patternfly/patternfly/utilities/Accessibility/accessibility.css';
import { css } from '@patternfly/react-styles';

import { Dashboard } from './dashboard';
import { ReportBuilder } from './report-builder';
import { RunList } from './run-list';
import { Run } from './run';
import { ResultList } from './result-list';
import { Result } from './result';
import { Settings } from './settings';
import { FileUpload, View } from './components';
import { ALERT_TIMEOUT, MONITOR_UPLOAD_TIMEOUT, VERSION_CHECK_TIMEOUT } from './constants';
import { buildUrl, getActiveProject } from './utilities';
import { version } from '../package.json'
import './app.css';


function getDateString() {
  return String((new Date()).getTime());
}

function projectToSelect(project) {
  return {
    project: project,
    toString: function() {
      return this.project.title;
    },
    compareTo: function (value) {
      return this.project.title.toLowerCase().includes(value.toLowerCase());
    }
  };
}


class App extends React.Component {
  constructor(props) {
    super(props);
    let project = getActiveProject();
    this.eventEmitter = new EventEmitter();
    this.version = version;
    this.versionCheckId = '';
    this.state = {
      uploadFileName: '',
      importId: '',
      notifications: [],
      monitorUploadId: null,
      isAboutOpen: false,
      isProjectSelectorOpen: false,
      selectedProject: project,
      selectedProjectTitle: project ? project.title : '',
      searchValue: '',
      projects: [],
      views: []
    };
    this.eventEmitter.on('projectChange', () => {
      this.getViews();
    });
  }

  getViews() {
    let params = {'filter': ['type=view', 'navigable=true']};
    let project = getActiveProject();
    if (project) {
      params['filter'].push('project=' + project.id);
    }
    fetch(buildUrl(Settings.serverUrl + '/widget-config', params))
      .then(response => response.json())
      .then(data => {
        data.widgets.forEach(widget => {
          if (project) {
            widget.params['project'] = project.id;
          }
          else {
            delete widget.params['project'];
          }
        });
        this.setState({views: data.widgets});
      });
  }

  showNotification(type, title, message, action?, timeout?, key?) {
    let notifications = this.state.notifications;
    let alertKey = key || getDateString();
    timeout = timeout !== undefined ? timeout : true
    if (notifications.find(element => element.key === alertKey) !== undefined) {
      return;
    }
    let notification = {
      'key': alertKey,
      'type': AlertVariant[type],
      'title': title,
      'message': message,
      'action': action
    };
    notifications.push(notification);
    this.setState({notifications}, () => {
      if (timeout === true) {
        setTimeout(() => {
          let notifications = this.state.notifications.filter((n) => {
            if (n.type === type && n.title === title && n.message === message) {
              return false;
            }
            return true;
          });
          this.setState({notifications});
        }, ALERT_TIMEOUT);
      }
    });
  }

  onBeforeUpload = (files) => {
    for (var i = 0; i < files.length; i++) {
      this.showNotification('info', 'File Uploaded', files[i].name + ' has been uploaded, importing will start momentarily.');
    }
  }

  onAfterUpload = (response) => {
    if (response.status >= 200 && response.status < 400) {
      response.json().then((importObject) => {
        this.showNotification('info', 'Import Starting', importObject.filename + ' is being imported...');
        this.setState({importId: importObject['id']}, () => {
          let monitorUploadId = setInterval(this.monitorUpload, MONITOR_UPLOAD_TIMEOUT);
          this.setState({monitorUploadId});
        });
      });
    }
    else {
      this.showNotification('danger', 'Import Error', 'There was a problem importing your file');
    }
  }

  monitorUpload = () => {
    fetch(Settings.serverUrl + '/import/' + this.state.importId)
      .then(response => response.json())
      .then(data => {
        if (data['status'] === 'done') {
          clearInterval(this.state.monitorUploadId);
          this.setState({monitorUploadId: null});
          let action = null;
          if (data.run_id) {
            const RunButton = withRouter(({history}) => (
              <AlertActionLink onClick={() => {history.push('/runs/' + data.run_id)}}>
                Go to Run
              </AlertActionLink>
            ));
            action = <RunButton />;
          }
          this.showNotification('success', 'Import Complete', `${data.filename} has been successfully imported as run ${data.run_id}`, action);
        }
      });
  }

  checkVersion() {
    const frontendUrl = window.location.origin;
    fetch(frontendUrl + '/version.json?v=' + getDateString())
      .then(response => response.json())
      .then((data) => {
        if (data && data.version && (data.version !== this.version)) {
          const action = <AlertActionLink onClick={() => { window.location.reload(); }}>Reload</AlertActionLink>;
          this.showNotification('info', 'Ibutsu has been updated', 'A newer version of Ibutsu is available, click reload to get it.', action, true, 'check-version');
        }
      });
  }

  getProjects() {
    fetch(Settings.serverUrl + '/project')
      .then(response => response.json())
      .then(data => this.setState({projects: data['projects']}));
  }

  toggleAbout = () => {
    this.setState({isAboutOpen: !this.state.isAboutOpen});
  };

  onProjectToggle = (isOpen) => {
    this.setState({isProjectSelectorOpen: isOpen});
  };

  onProjectSelect = (event, value, isPlaceholder) => {
    if (isPlaceholder) {
      this.onProjectClear();
      return;
    }
    const project = JSON.stringify(value.project);
    localStorage.setItem('project', project);
    this.setState({
      selectedProject: value.project,
      selectedProjectTitle: value.toString(),
      isProjectSelectorOpen: false
    });
    this.eventEmitter.emit('projectChange');
  };

  onProjectClear = () => {
    localStorage.removeItem('project');
    this.setState({
      selectedProject: null,
      selectedProjectTitle: '',
      isProjectSelectorOpen: false
    });
    this.eventEmitter.emit('projectChange');
  }

  componentWillUnmount() {
    if (this.state.monitorUploadId) {
      clearInterval(this.state.monitorUploadId);
    }
    if (this.versionCheckId) {
      clearInterval(this.versionCheckId);
    }
  }

  componentDidMount() {
    this.getProjects();
    this.getViews();
    this.checkVersion();
    this.versionCheckId = setInterval(() => this.checkVersion(), VERSION_CHECK_TIMEOUT);
  }

  render() {
    document.title = 'Ibutsu';
    const apiUiUrl = Settings.serverUrl + '/ui/';
    const { views } = this.state;
    const navigation = (
      <Nav onSelect={this.onNavSelect} theme="dark" aria-label="Nav">
        <NavList>
          <li className="pf-c-nav__item">
            <NavLink to="/" className="pf-c-nav__link" activeClassName="pf-m-active" exact>Dashboard</NavLink>
          </li>
          <li className="pf-c-nav__item">
            <NavLink to="/runs" className="pf-c-nav__link" activeClassName="pf-m-active">Runs</NavLink>
          </li>
          <li className="pf-c-nav__item">
            <NavLink to="/results" className="pf-c-nav__link" activeClassName="pf-m-active">Test Results</NavLink>
          </li>
          <li className="pf-c-nav__item">
            <NavLink to="/reports" className="pf-c-nav__link" activeClassName="pf-m-active">Report Builder</NavLink>
          </li>
          {views && views.map(view => (
            <li className="pf-c-nav__item" key={view.id}>
              <NavLink to={`/view/${view.id}`} className="pf-c-nav__link" activeClassName="pf-m-active">{view.title}</NavLink>
            </li>
          ))}
        </NavList>
      </Nav>
    );
    const topNav = (
      <Flex>
        <FlexItem id="project-selector">
          <Select
            ariaLabelTypeAhead="Select a project"
            placeholderText="No active project"
            variant={SelectVariant.typeahead}
            isOpen={this.state.isProjectSelectorOpen}
            selections={this.state.selectedProjectTitle}
            onToggle={this.onProjectToggle}
            onSelect={this.onProjectSelect}
            onClear={this.onProjectClear}
          >
            {this.state.projects.map(project => (
              <SelectOption key={project.id} value={projectToSelect(project)} />
            ))}
          </Select>
        </FlexItem>
      </Flex>
    );
    const headerTools = (
      <PageHeaderTools>
        <PageHeaderToolsGroup className={css(accessibleStyles.srOnly, accessibleStyles.visibleOnLg)}>
          <PageHeaderToolsItem>
            <Button variant="plain" onClick={this.toggleAbout}><QuestionCircleIcon /></Button>
          </PageHeaderToolsItem>
          <PageHeaderToolsItem>
            <FileUpload component="button" className="pf-c-button pf-m-plain" isUnstyled name="importFile" url={`${Settings.serverUrl}/import`} multiple={false} beforeUpload={this.onBeforeUpload} afterUpload={this.onAfterUpload} title="Upload JUnit XML"><UploadIcon /> Import</FileUpload>
          </PageHeaderToolsItem>
          <PageHeaderToolsItem>
            <a href={apiUiUrl} className="pf-c-button pf-m-plain" target="_blank" rel="noopener noreferrer"><ServerIcon/> API</a>
          </PageHeaderToolsItem>
        </PageHeaderToolsGroup>
      </PageHeaderTools>
    );
    const header = (
      <PageHeader
        logo={<Brand src="/images/ibutsu-wordart-164.png" alt="Ibutsu"/>}
        headerTools={headerTools}
        showNavToggle={true}
        topNav={topNav}
      />
    );
    const sidebar = <PageSidebar nav={navigation} theme="dark" />;

    return (
      <Router>
        <React.Fragment>
          <AboutModal
            isOpen={this.state.isAboutOpen}
            onClose={this.toggleAbout}
            brandImageSrc="/images/ibutsu.svg"
            brandImageAlt="Ibutsu"
            productName="Ibutsu"
            backgroundImageSrc="/images/about-bg.jpg"
          >
            <TextContent>
              <TextList component="dl">
                <TextListItem component="dt">Version</TextListItem>
                <TextListItem component="dd">{this.version}</TextListItem>
                <TextListItem component="dt">Source code</TextListItem>
                <TextListItem component="dd"><a href="https://github.com/ibutsu/ibutsu-server">github.com/ibutsu/ibutsu-server</a></TextListItem>
              </TextList>
            </TextContent>
          </AboutModal>
          <AlertGroup isToast>
            {this.state.notifications.map((notification) => (
              <Alert key={notification.key} variant={notification.type} title={notification.title} action={notification.action} isLiveRegion>
                {notification.message}
              </Alert>
            ))}
          </AlertGroup>
          <Page header={header} sidebar={sidebar} isManagedSidebar={true} style={{position: "relative"}}>
            <Switch>
              <Route
                path="/"
                exact
                render={routerProps => (
                  <Dashboard eventEmitter={this.eventEmitter} {...routerProps} />
                )}
              />
              <Route
                path="/runs"
                exact
                render={routerProps => (
                  <RunList eventEmitter={this.eventEmitter} {...routerProps} />
                )}
              />
              <Route
                path="/results"
                exact
                render={routerProps => (
                  <ResultList eventEmitter={this.eventEmitter} {...routerProps} />
                )}
              />
              <Route
                path="/reports"
                exact
                render={routerProps => (
                  <ReportBuilder eventEmitter={this.eventEmitter} {...routerProps} />
                )}
              />
              <Route path="/runs/:id" component={Run} />
              <Route path="/results/:id" component={Result} />
              <Route path="/view/:id" component={View} />
            </Switch>
          </Page>
        </React.Fragment>
      </Router>
    );
  }
}

export default App;
