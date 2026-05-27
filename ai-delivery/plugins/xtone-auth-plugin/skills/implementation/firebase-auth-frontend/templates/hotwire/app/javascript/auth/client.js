// app/javascript/auth/client.js
//
// AuthClient（SKILL.md の言語非依存契約）を Firebase JS SDK v9+ modular で実装。
// import パスはすべて bare specifier（config/importmap.rb の pin と対応）。

import { auth } from "auth/firebase_init";
import {
	setPersistence,
	inMemoryPersistence,
	signInWithEmailAndPassword,
	sendSignInLinkToEmail,
	isSignInWithEmailLink,
	signInWithEmailLink,
	GoogleAuthProvider,
	OAuthProvider,
	signInWithPopup,
	linkWithPopup,
	sendPasswordResetEmail,
	updatePassword,
	updateEmail,
	signOut,
	onAuthStateChanged,
} from "firebase/auth";

// XSS 配慮: トークンをメモリのみに保持（Firebase 既定の localStorage/indexedDB を使わない）。
// リロードでセッションが切れるため、戦略B（クッキーセッション）と併用するか SSR で
// ログイン状態を保持する（references/hotwire.md「セッション戦略」参照）。
setPersistence(auth, inMemoryPersistence);

const providerOf = (id) =>
	id === "apple" ? new OAuthProvider("apple.com") : new GoogleAuthProvider();

export const AuthClient = {
	signInWithPassword: (email, pw) =>
		signInWithEmailAndPassword(auth, email, pw),

	signInWithEmailLink: (email) => {
		window.localStorage.setItem("emailForSignIn", email); // completeEmailLink で参照
		return sendSignInLinkToEmail(auth, email, {
			url: window.location.origin + "/auth/email-link", // ActionCodeSettings（要件に合わせ調整）
			handleCodeInApp: true,
		});
	},

	completeEmailLink: () => {
		if (!isSignInWithEmailLink(auth, window.location.href)) {
			return Promise.reject(new Error("invalid link"));
		}
		const email = window.localStorage.getItem("emailForSignIn");
		return signInWithEmailLink(auth, email, window.location.href);
	},

	signInWithOIDC: (id) => signInWithPopup(auth, providerOf(id)),
	linkProvider: (id) => linkWithPopup(auth.currentUser, providerOf(id)),

	sendPasswordReset: (email) => sendPasswordResetEmail(auth, email), // Firebase 完結（iaas）
	updatePassword: (pw) => updatePassword(auth.currentUser, pw),
	updateEmail: (email) => updateEmail(auth.currentUser, email),

	signOut: () => signOut(auth),

	// 期限切れは Firebase が自動リフレッシュ
	getIdToken: (force = false) =>
		auth.currentUser
			? auth.currentUser.getIdToken(force)
			: Promise.resolve(null),

	onAuthStateChanged: (cb) => onAuthStateChanged(auth, cb),

	// 退会（responsibility=shared）: サーバが論理削除 + Admin SDK で IaaS 削除
	withdraw: async () => {
		const idToken = auth.currentUser
			? await auth.currentUser.getIdToken(true)
			: null;
		await fetch("/account", {
			method: "DELETE",
			headers: { Authorization: `Bearer ${idToken}` },
		});
		return signOut(auth);
	},
};
