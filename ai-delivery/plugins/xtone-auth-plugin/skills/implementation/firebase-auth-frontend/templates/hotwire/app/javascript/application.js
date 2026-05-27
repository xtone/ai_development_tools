// app/javascript/application.js
//
// Propshaft + importmap-rails 前提。すべての import は bare specifier。
// 相対パス（"./controllers" 等）にすると Propshaft がフィンガープリント無しパスを
// 解決できず 503 を返し、Stimulus が起動しない。
//
// 対応する pin は config/importmap.rb の pin_all_from（"controllers" / "auth"）。

import "@hotwired/turbo-rails";
import "controllers";
