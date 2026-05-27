// app/javascript/auth/firebase_init.js
//
// Firebase アプリ初期化のシングルトン。client.js から参照される。
// window.FIREBASE_CONFIG はビュー側で注入する（apiKey 等は公開前提のため平文で可）:
//
//   <%# app/views/layouts/application.html.erb 等 %>
//   <script>
//     window.FIREBASE_CONFIG = <%= raw Rails.application.credentials.firebase.to_json %>
//   </script>

import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

export const firebaseApp = initializeApp(window.FIREBASE_CONFIG);
export const auth = getAuth(firebaseApp);
