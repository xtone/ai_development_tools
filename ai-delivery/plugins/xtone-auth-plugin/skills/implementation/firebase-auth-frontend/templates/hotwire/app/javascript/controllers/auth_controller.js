// app/javascript/controllers/auth_controller.js
//
// Firebase JS SDK でサインインし、ID トークンを取り出して /auth/session に POST する。
// 戦略B（クッキーセッション）想定。戦略A（Bearer 都度付与）の場合は establishSession を
// 個別の API 呼び出し時に getIdToken して Authorization ヘッダに乗せる形に置き換える。
//
// alert() / confirm() は使わない（claude-in-chrome / playwright / E2E でモーダルが
// 後続イベントをブロックして固まるため）。エラーは flashTarget に DOM 出力し、
// console.error にも残す。

import { Controller } from "@hotwired/stimulus";
import { AuthClient } from "auth/client";

export default class extends Controller {
	static targets = ["email", "password", "flash"];

	async signIn(e) {
		e.preventDefault();
		try {
			await AuthClient.signInWithPassword(
				this.emailTarget.value,
				this.passwordTarget.value,
			);
			await this.establishSession();
		} catch (err) {
			this.notify(
				"ログインに失敗しました。メールアドレスとパスワードを確認してください。",
				err,
			);
		}
	}

	async establishSession() {
		const idToken = await AuthClient.getIdToken(true);
		const res = await fetch("/auth/session", {
			method: "POST",
			headers: {
				Authorization: `Bearer ${idToken}`,
				"X-CSRF-Token": this.csrf(),
			},
		});
		if (!res.ok) throw new Error(`/auth/session failed: ${res.status}`);
		Turbo.visit("/");
	}

	csrf() {
		return document.querySelector("meta[name='csrf-token']")?.content;
	}

	notify(message, err = null) {
		if (this.hasFlashTarget) {
			this.flashTarget.textContent = message;
			this.flashTarget.hidden = false;
		}
		if (err) console.error("[auth]", err);
	}
}
