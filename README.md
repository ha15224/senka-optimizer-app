# 月間戦果最適化計算機 v0.91

使用する出撃，遠征，課金アイテムを変数として扱い，戦果を最大化するような組み合わせを求めます

この最適化は線形計画問題に帰着されるため，ソルバーとしてPuLP/CBCを使います

ダウンロード（アプリ）：https://drive.google.com/file/d/1fV14onuOceWrzfcg3Kmhpzia2EMpI5tZ

ダウンロード（出撃データテンプレ）：https://docs.google.com/spreadsheets/d/1eBN6qbRLIPYyuEY1H3xTFn0sNhZYGGZn/

ダウンロード（ドロップデータ）：https://docs.google.com/spreadsheets/d/107yJmRhAyjkye3ZP8doCkqTm0RmpeolM/

**『『『 このREADMEの一番下にある備考を必ず読んでから使用してください 』』』**

## 紹介画像
<img width="702" height="832" alt="image" src="https://github.com/user-attachments/assets/af559520-6816-4f45-a561-d65f02b68226" />
<img width="641" height="277" alt="image" src="https://github.com/user-attachments/assets/5ad7a906-ba8b-469d-92ed-b1ef7f1e9e3d" />
<img width="893" height="477" alt="image" src="https://github.com/user-attachments/assets/6195f79d-938c-43fa-b87f-b5d360907630" />
<img width="702" height="832" alt="image" src="https://github.com/user-attachments/assets/8b86f7a1-191a-466d-a479-82321793a3f0" />
<img width="1402" height="832" alt="image" src="https://github.com/user-attachments/assets/3ec9114d-c5bd-46d5-bff9-6fdb5a09915c" />

## 操作手順
1. アプリと出撃データテンプレ・ドロップデータをダウンロードします
2. 出撃データは自分のデータで埋めてください（出撃シミュの数値を推奨します）
3. アプリから最適化パラメータを入力します
4. 出撃データのエクセルを読み込みます
5. ドロップデータは修正せずダウンロードしたものをそのまま読み込んでください
6. 最適化を実行します
7. 結果が別画面にて出力されます

## 備考
- 出撃データエクセルは自由に編集してください
  - テンプレ通りに作成するなら出撃の種類や個数に制限はありません
  - cond値とは，遠征に使えるcond値を意味します．キラ付け出撃は適当な数字（マイナスで入れてください），他の出撃は0と設定してください
  - 最大割合とは，全体の出撃に対しその出撃の最大の割合を指定します．例えば戦果ローテで３－２艦隊が不足している場合などに使えます．0~1の値で設定してください
  - 轟沈周回は出撃のテンプレに入れず，「轟沈回収を許容」オプションを使ってください．
  - 秒数はすべてドロップカットした周回時間で設定してください．最適解としてドロップが必要な場合は別途時間ペナルティが課されます（各艦+7.5秒）．
- 日数を1に，特別戦果を0に設定するとデイ戦果の最適化ソルバーとして使えます
- パラメータ設定のオフセットには，初期資源，任務，プレ箱，勲章割りからの収入を入れてください．遠征・課金からの収入は自動的に最適化されて加算されます
  - 出撃の組み合わせは，遠征からの収入，課金からの収入，そしてこれらのオフセットを足した全予算に収まるように計算されます
- 遠征用cond値とは，予めキラ付けしておいた遠征艦のキラ合計です．例えば，cond80の遠征艦が100隻いたら遠征用cond値は(80-50)*100=3000です
  - 課金アイテムには間宮が含まれており，遠征のキラ付けに間宮が用いられることがあります
  - 野崎によるキラ付けはモデリングしていません
- 結果画面に表示される「出撃数」とは，エクセルに設定した各出撃の実行数です
- 結果画面に表示される「稼働する遠征の時間数」は各遠征の稼働時間数です．例えば長距離が300と出力された場合，300時間分の長距離の稼働（600回）を意味します
- 結果画面に表示される「休息時間の遠征選択」には0.00か1.00しか出力されません．1.00が出力された遠征を休息中に稼働してください

## 旧バージョン
アプリ v0.1：https://drive.google.com/file/d/1hwLqBoDngyR6y98UbXFTuZhRBsSE5jE1/

アプリ v0.2：https://drive.google.com/file/d/1VLpqsWsZS0iUbLgf_R6uEJ15fZuOMTfO/

アプリ v0.32：https://drive.google.com/file/d/1cF1oJ-qfD63CSK4LfvHJYdrpZYTSBYPK/
