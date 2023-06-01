# GitHubでMDに数式を入れる方法

## 答え
GitHubのmdは、latexに対応している。
→Qiitaとかにそのまま移植すると動かないかもなので注意

## 使い方
- インラインで数式を入れる場合`$`で囲む。
（例）`$F = ma$` → $F = ma$

- ブロックで数式を入れる場合`$$`で囲む。
（例）`$$V(s_t) = \sum \pi(s_t) Q(s_t, a_\pi)$$`
→ $$V(s_t) = \sum \pi(s_t) Q(s_t, a_\pi)$$
（自動でセンタリングしてくれるんだね）

- ` ```math`でもブロック化してくれるらしいけど、ここでは動かなかったので割愛

- 数式内で$を使いたい場合には、`\`でエスケープ。
（例）`$\sqrt{\$4}$` → $\sqrt{\$4}$

## 参考資料
- [数式の記述 GitHub Docs](https://docs.github.com/ja/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions)
：ここに全部書いてあった
