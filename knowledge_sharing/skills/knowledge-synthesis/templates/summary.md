<!--
「まとめ」ページの形（Notion-flavored Markdown）。synth.py render がこの形で組み立てる。
読み手: Web 制作会社のエンジニアが、開発の進め方を議論するために読む。
Progressive Disclosure: 1 層目（わかったこと）→ 2 層目（決めること）→ 3 層目（テーマの詳細）。
例・根拠・数字はトグル（<details>）にしまい、開いた人だけが読む。
<...> は埋める箇所。投稿者名は書かない。
-->
<callout icon="🧭" color="gray_bg">
	<週タイトル>のまとめ。<n> 人のカード <n> 枚から、わかったことを <n> 点にまとめました。採否は共有会で決めます。
</callout>
## 今週わかったこと
- **<テーマ: 結論の一文>**<br>→ <提案: 何をするかの一文>
## 共有会で決めること
- [ ] <〜しますか？>（テーマ: <mention-page url="<合成テーマの URL>"/>）
## テーマの詳細
### <テーマ: 結論の一文>
**提案**（<両立案 / 条件分け / 仕組み化>）: <提案>
**根拠**: <n> 人・<n> プロジェクト・<n> 枚
<details>
<summary>うまくいった例（<n>）</summary>
	- <カードの claim>（<プロジェクト>）<mention-page url="<カードの URL>"/>
</details>
<details>
<summary>うまくいかなかった例（<n>）</summary>
	- <カードの claim>（<プロジェクト>）<mention-page url="<カードの URL>"/>
</details>
<details>
<summary>分かれ目と限界</summary>
	- 分かれ目（推定）: <分かれ目>（対立が無いテーマは「共通解（正と反の対立は無い）」）
	- 限界: <限界>
</details>
## 次に聞くこと
- <問い ID>「<問いの文>」: <なぜ次に聞くか>
<details>
<summary>今週動いていたプロジェクト（<n> 件）</summary>
	- **<プロジェクト>**: <内容> <mention-page url="<カードの URL>"/>
</details>
<details>
<summary>数字で見る今週</summary>
	- 参加者: <n> 人
	- カード: <n> 枚（<問い別>）
	- テーマ: <n>（うち正と反の対立があるもの <n>）
	- 記録に直接あるカード（observed）: <n> / <n>
</details>
