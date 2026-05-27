// app/javascript/controllers/index.js
//
// controllers/ 配下の *_controller.js を Stimulus に自動登録する。
// pin_all_from "app/javascript/controllers", under: "controllers" によって
// bare specifier "controllers/xxx_controller" が解決される。

import { application } from "controllers/application";
import { eagerLoadControllersFrom } from "@hotwired/stimulus-loading";

eagerLoadControllersFrom("controllers", application);
