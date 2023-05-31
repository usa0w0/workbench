# Issueの作成を自動化して、毎週のタスクをスケジューリングしよう

## なんで？？
週次のミーティングに向けた準備タスクを、毎週Issueとして作るのはめんどくさい
→自動化しよう！（なんでも自動化するなってこないだ怒られたけど…）

## 方法
GitHub Actionsでワークフローを作成する。

ここでは、[issue の作成をスケジュールする - GitHub Doc](https://docs.github.com/ja/actions/using-workflows/events-that-trigger-workflows#scheduled-events)の内容に、解説やをコメントを追記していく。

# 手順
1. 適用リポジトリに`.github/workflows`ディレクトリを作成する。

2. `.github/workflows`内に、ymlファイルを作成し、ワークフローを記述する。

```imjohnbo/issue-bot Actionsの例
# このワークフローはGitHubによって認定されていないアクションを使用します。
# それらはサードパーティによって提供され、
# 別個の利用規約、プライバシーポリシー、
# ドキュメントを参照してください。

# GitHub では、コミット SHA にアクションをピン留めすることが推奨されます。
# 新しいバージョンを取得するには、SHA を更新する必要があります。
# タグまたはブランチを参照することもできますが、アクションは警告なしに変更される可能性があります。

name: Weekly Team Sync
on:
  schedule:
    - cron: 20 07 * * 1

jobs:
  create_issue:
    name: Create team sync issue
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Create team sync issue
        uses: imjohnbo/issue-bot@3d96848fb5e9a4a473bb81ae62b4b4866a56e93a
        with:
          assignees: "monalisa, doctocat, hubot"
          labels: "weekly sync, docs-team"
          title: "Team sync"
          body: |
            ### Agenda

            - [ ] Start the recording
            - [ ] Check-ins
            - [ ] Discussion points
            - [ ] Post the recording
                    
            ### Discussion Points
            Add things to discuss below

            - [Work this week](https://github.com/orgs/github/projects/3)
          pinned: false
          close-previous: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- `on.schedule`プロパティ：POSIX cron 構文でスケジュールできる。
  - `- cron: <Minute [0,59]> <Hour [0,23]> <Day of the month [1,31]> <Month of the year [1,12]> <Day of the week ([0,6] with 0=Sunday)>`
