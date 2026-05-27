// app/javascript/controllers/application.js
//
// Stimulus アプリケーションのシングルトン。controllers/index.js から参照される。

import { Application } from "@hotwired/stimulus";

const application = Application.start();
application.debug = false;
window.Stimulus = application;

export { application };
