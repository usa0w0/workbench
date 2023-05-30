# GitHub Projectsを使ってタスク管理をしよう！！

## GitHub Projectsって？
> GitHub 上の issue および pull request と統合できる、適応性のあるスプレッドシート。
> 
> 引用：[Projects について - GitHub Docs](https://docs.github.com/ja/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

要するに、GitHub が提供するプロジェクト運用のためのツール。

## 何ができるの？
- IssueやPRを一覧表示できる。 → それなら各リポジトリのIssues画面でいい
- 複数リポジトリのIssueやPRを連携できる。 → プロジェクトが大きいと便利
- `Status`を設定することで、フィールド分けできたり、カンバン方式で表示できる。 → 便利！（これが理由で調べた）
- `Custom fields`による整理ができる。
<img width="1176" alt="スクリーンショット 2023-05-30 22 59 38" src="https://github.com/usa0w0/workbench/assets/61536640/68192713-3478-41d7-8f13-cd40dd46db32">

## Projectの作り方
> Organizationプロジェクトもしくはユーザプロジェクトを作成できます。 Organizationプロジェクトを作成するには、GitHub Organizationが必要。 組織の作成について詳しくは、「新しい Organization をゼロから作成」をご覧ください。
> 
> 引用：[Projects のクイック スタート](https://docs.github.com/ja/issues/planning-and-tracking-with-projects/learning-about-projects/quickstart-for-projects)

公式にこう書かれている通り、プロジェクトはユーザーまたはOrganizationに紐づく。
リポジトリに紐づかないので、チーム運用する場合には、参加メンバーをコラボレーターに招待するか、Organizationに紐づけて作成する必要がある。

1. [Projects]画面を開く。（Organizationプロジェクトの場合は、OrganizationのProfile画面から）
<img width="1176" alt="スクリーンショット 2023-05-30 20 51 20" src="https://github.com/usa0w0/workbench/assets/61536640/ba13d9af-f57f-46bc-a93b-133426c7da1d">

2. [New projects]をクリックして、新規プロジェクトを作成。

3. 組み込みテンプレートかOrganizationのテンプレートから、テンプレートを選択。
<img width="1176" alt="スクリーンショット 2023-05-30 20 58 24" src="https://github.com/usa0w0/workbench/assets/61536640/482b6473-a220-4fcd-bad3-282900673e58">

4. 必要に応じてプロジェクト名をつける。（いつでもリネーム可）
<img width="1176" alt="スクリーンショット 2023-05-30 21 02 16" src="https://github.com/usa0w0/workbench/assets/61536640/00c77184-0276-40db-bf92-ad58586bff3d">

5. [create]をクリックする。

## リポジトリへのプロジェクトの追加
追加したいリポジトリの[Projects]画面から、[Link a project]をクリックすることで、プロジェクトを紐づけることができます。
また、このときに新しいプロジェクトを作成することもできます。

## ビュー
ビューは、複数タブ設定できる。
レイアウトは、`Table`, `Board`, `Roadmap`の3種類から選択でき、フィルターをはじめとした各種カスタマイズができる。
<img width="1176" alt="スクリーンショット 2023-05-30 22 51 22" src="https://github.com/usa0w0/workbench/assets/61536640/e2e9fce5-ba00-4cc9-b81a-d10b5898ce7f">

## カード（チケット）の作り方
### プロジェクトからIssueを作成（Boardレイアウトを例に）
1. 最下部の[+ Add item]をクリックする。
<img width="1176" alt="スクリーンショット 2023-05-30 21 38 59" src="https://github.com/usa0w0/workbench/assets/61536640/5b30d754-ba47-4ac0-a7eb-3cf4e8dbc25a">

2. プレースホルダーにIssueタイトルを入力し、Enterを押すと、ドラフトIssueが作成される。 
<img width="1176" alt="スクリーンショット 2023-05-30 21 45 18" src="https://github.com/usa0w0/workbench/assets/61536640/9757c3ae-335d-4a61-8e87-d0217235e810">

3. カードとして設置されたIssueのタイトルをクリックすると、内容パネルが表示される。[Edit]をクリックすることで、それぞれ「タイトル」と「本文」を編集できる（リポジトリに紐づけ、ドラフトからIssueに変換した場合、リポジトリ側の内容も変更される）。
<img width="1176" alt="スクリーンショット 2023-05-30 21 46 40" src="https://github.com/usa0w0/workbench/assets/61536640/8e95123a-e611-4311-a1e4-3dde4814fa50">

4. 右側パネルでは、`Assignees`, `Status`, `Custom fields`を設定できます。
<img width="1176" alt="スクリーンショット 2023-05-30 21 53 31" src="https://github.com/usa0w0/workbench/assets/61536640/a0603467-2dd6-4a48-952f-b40ffd2af191">

5. [Convert to Issue]をクリック。
<img width="1176" alt="スクリーンショット 2023-05-30 21 56 36" src="https://github.com/usa0w0/workbench/assets/61536640/471cfa3f-02da-42d7-b0b0-9419100fddee">

6. Issueを紐づけるリポジトリを選択することで、ドラフトからIssueに変換。
<img width="1176" alt="スクリーンショット 2023-05-30 21 58 47" src="https://github.com/usa0w0/workbench/assets/61536640/3dfeaa99-7131-4b0d-8c23-3240a09e760b">

7. 変換後は、`Labels`や`Milestone`を設定できる。

### Issueからプロジェクトカードの作成
1. 任意のリポジトリにIssueを作成。

2. 右側パネルから[Projects]をクリックし、割り当て先を選択（画像では、リポジトリにあらかじめ紐づけていないため、表示されていない）。
<img width="1176" alt="スクリーンショット 2023-05-30 22 02 27" src="https://github.com/usa0w0/workbench/assets/61536640/171bf969-84db-4156-9c40-6135a45f1822">

3. プロジェクト側で、`Status`, `Custom fields`は設定する。

※後述する「組み込みの自動化」を設定することで、プロジェクトへの割り当てと初期`Status`の設定を自動化できる。

※複数Issue・PRの追加なども可能だが、使わない気がするので記述しない
（参考：[project への項目の追加 - GitHub Docs](https://docs.github.com/ja/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project)）

## Settings
[Project settings]では、`Project name`のリネーム, `Short description`, `README`の設定ができる。

[Manage access]では、プロジェクトにメンバーを招待できる。

## `Custom fields`
以下の形式の`Custom fields`を設定できる。
- テキスト（入力）
- 数値（入力）
- 日付（選択）
- 単一選択（選択）
- 繰り返し（選択）：開発スプリントのような期間の繰り返しを設定できる。
- （追跡と追跡対象：公式Docには記述があるが、該当機能見つからず。）

## 自動化
ワークフローを設定することで、Issue・PRの作成やCloseなどに伴って行われる自動処理を設定できる。
<img width="1176" alt="スクリーンショット 2023-05-30 22 15 40" src="https://github.com/usa0w0/workbench/assets/61536640/c866c7dd-3c4e-46a3-8cd4-d9faf97481c8">

以下では、有用だと感じたものを紹介する。
- Item added to project
ワークフローやGitHub Actionsでカードが追加されたとき、任意の`Status`に設定する。
<img width="1176" alt="スクリーンショット 2023-05-30 22 18 57" src="https://github.com/usa0w0/workbench/assets/61536640/b9e279e4-84e4-42f8-bc22-0a268d3d2c8c">

- Item closed
ItemやPRがCloseされたとき、任意の`Status`に設定する。
<img width="1176" alt="スクリーンショット 2023-05-30 22 21 11" src="https://github.com/usa0w0/workbench/assets/61536640/0b7b5b0c-bc97-45cc-a73b-f10d0ca8e558">

- Pull request merged
PRがmergeされたとき、任意の`Status`に設定する。
<img width="1176" alt="スクリーンショット 2023-05-30 22 24 00" src="https://github.com/usa0w0/workbench/assets/61536640/478d6bdb-da0c-4e46-9e8b-dacf1e4af40e">

- Auto-archive items
フィルター条件を満たすカードを自動でアーカイブする。
<img width="1176" alt="スクリーンショット 2023-05-30 22 26 34" src="https://github.com/usa0w0/workbench/assets/61536640/0fa1c20d-7507-4a51-a261-50239335f139">

- Auto-add to project
指定したリポジトリにおいて、フィルター条件を満たすものを、自動でカード追加する。
<img width="1176" alt="スクリーンショット 2023-05-30 22 27 29" src="https://github.com/usa0w0/workbench/assets/61536640/cbe05ee9-2243-4d6f-8185-56b62bab3573">

## 分析
プロジェクトは、カード情報を基にグラフ分析する機能を備えている。
運用方法や`Custom fields`に依るところが多いため、今回は調査せず。
<img width="1176" alt="スクリーンショット 2023-05-30 22 53 33" src="https://github.com/usa0w0/workbench/assets/61536640/5a0fc688-7009-4efc-a933-f1b8a42324cc">
<img width="1176" alt="スクリーンショット 2023-05-30 22 54 08" src="https://github.com/usa0w0/workbench/assets/61536640/43e90fe8-472f-477b-85ad-0e8e76752065">
