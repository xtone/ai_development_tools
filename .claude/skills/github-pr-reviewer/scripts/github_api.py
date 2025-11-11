#!/usr/bin/env python3
"""
GitHub API操作の共通モジュール

GitHub REST API v3を使用してPR情報の取得、レビューの投稿、Issueの作成などを行います。
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class GitHubAPI:
    """GitHub API操作を行うクラス"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """
        GitHub APIクライアントを初期化

        Args:
            token: GitHub Personal Access Token
                   指定しない場合は環境変数GITHUB_TOKENまたは~/.github_tokenから取得
        """
        self.token = token or self._get_token()
        if not self.token:
            raise ValueError(
                "GitHub token not found. Please set GITHUB_TOKEN environment variable "
                "or create ~/.github_token file."
            )

    def _get_token(self) -> Optional[str]:
        """環境変数またはファイルからGitHub tokenを取得"""
        # 環境変数から取得
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            return token

        # ~/.github_tokenファイルから取得
        token_file = os.path.expanduser("~/.github_token")
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                return f.read().strip()

        return None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Any:
        """
        GitHub APIリクエストを実行

        Args:
            method: HTTPメソッド (GET, POST, PUT, PATCH)
            endpoint: APIエンドポイント (/repos/owner/repo/pulls/123)
            data: リクエストボディ
            headers: 追加のHTTPヘッダー

        Returns:
            APIレスポンスのJSON
        """
        url = f"{self.BASE_URL}{endpoint}"

        req_headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-PR-Reviewer-Skill"
        }
        if headers:
            req_headers.update(headers)

        request_data = None
        if data:
            request_data = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        request = Request(url, data=request_data, headers=req_headers, method=method)

        try:
            with urlopen(request) as response:
                response_data = response.read().decode("utf-8")
                if response_data:
                    return json.loads(response_data)
                return None
        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"GitHub API error ({e.code}): {error_body}")
        except URLError as e:
            raise Exception(f"Network error: {e.reason}")

    @staticmethod
    def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
        """
        PR URLをパースしてowner, repo, pr_numberを取得

        Args:
            pr_url: PR URL (https://github.com/owner/repo/pull/123)

        Returns:
            (owner, repo, pr_number)のタプル
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, pr_url)
        if not match:
            raise ValueError(f"Invalid PR URL: {pr_url}")

        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict:
        """
        PR情報を取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            pr_number: PR番号

        Returns:
            PR情報の辞書
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        return self._make_request("GET", endpoint)

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        PRで変更されたファイル一覧を取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            pr_number: PR番号

        Returns:
            変更されたファイル情報のリスト
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        return self._make_request("GET", endpoint)

    def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        PRのコミット一覧を取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            pr_number: PR番号

        Returns:
            コミット情報のリスト
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        return self._make_request("GET", endpoint)

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        PRのレビュー一覧を取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            pr_number: PR番号

        Returns:
            レビュー情報のリスト
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        return self._make_request("GET", endpoint)

    def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        event: str,
        body: str,
        comments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        PRレビューを作成

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            pr_number: PR番号
            event: レビューイベント (APPROVE, REQUEST_CHANGES, COMMENT)
            body: レビューコメント
            comments: 行別コメントのリスト

        Returns:
            作成されたレビュー情報
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"

        data = {
            "event": event,
            "body": body
        }

        if comments:
            data["comments"] = comments

        return self._make_request("POST", endpoint, data)

    def create_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int
    ) -> Dict:
        """
        PR内の特定行にコメントを追加

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            pr_number: PR番号
            body: コメント本文
            commit_id: コミットSHA
            path: ファイルパス
            line: 行番号

        Returns:
            作成されたコメント情報
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"

        data = {
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line
        }

        return self._make_request("POST", endpoint, data)

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> Dict:
        """
        Issueを作成

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            title: Issueタイトル
            body: Issue本文
            assignees: アサインするユーザー名のリスト
            labels: ラベルのリスト

        Returns:
            作成されたIssue情報
        """
        endpoint = f"/repos/{owner}/{repo}/issues"

        data = {
            "title": title,
            "body": body
        }

        if assignees:
            data["assignees"] = assignees

        if labels:
            data["labels"] = labels

        return self._make_request("POST", endpoint, data)

    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> str:
        """
        リポジトリからファイルの内容を取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            path: ファイルパス
            ref: ブランチ、タグ、またはコミットSHA

        Returns:
            ファイルの内容
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        if ref:
            endpoint += f"?ref={ref}"

        response = self._make_request("GET", endpoint)

        # Base64デコード
        import base64
        content = base64.b64decode(response["content"]).decode("utf-8")
        return content
