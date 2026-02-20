# 月間戦果最適化計算機 v0.31

使用する出撃，遠征，課金アイテムを変数として扱い，戦果を最大化するような組み合わせを求めます

この最適化は線形計画問題に帰着されるため，ソルバーとしてPuLP/CBCを使います

ダウンロード（アプリ）：https://drive.google.com/file/d/1JAL_6djwIMaGUGtPkMb5nDNMjIURGmU5/

ダウンロード（出撃データテンプレ）：https://docs.google.com/spreadsheets/d/1rOqHXiJcmuV5CXCUL1KUckUWW7uGotGa/

## 紹介画像
<img width="702" height="832" alt="image" src="https://github.com/user-attachments/assets/ddd66a47-5a2d-4e4e-9d23-8a7e7bee913e" />
<img width="664" height="279" alt="image" src="https://github.com/user-attachments/assets/9f6cb1e0-7ef2-4113-ad2b-dabb2a523fe8" />
<img width="702" height="832" alt="image" src="https://github.com/user-attachments/assets/c48e232a-b4c0-4fbf-9088-95d5a6442c80" />
<img width="1002" height="632" alt="image" src="https://github.com/user-attachments/assets/d981d75a-4cf4-4dbf-baac-0a11de9b6fe6" />

## 操作手順
1. アプリと出撃データテンプレをダウンロードします
2. 出撃データは自分のデータで埋めてください（出撃シミュの数値を推奨します）
3. アプリから最適化パラメータを入力します
4. 出撃データのエクセルを読み込みます
5. 最適化を実行します
6. 結果が別画面にて出力されます

## 備考
- 出撃データエクセルは自由に編集してください
  - テンプレ通りに作成するなら出撃の種類や個数に制限は課されません
  - cond値とは，遠征に使えるcond値を意味します．キラ付け出撃は適当な数字（マイナスで入れてください），他の出撃は0と設定してください
  - 最大割合とは，全体の出撃に対しその出撃の最大の割合を指定します．例えば戦果ローテで３－２艦隊が不足している場合などに使えます．0~1の値で設定してください
  - 轟沈周回を行う場合はテンプレに書いてある数字の使用を推奨します．60秒換算の燃弾収入74/116に，ドロップを拾うために必要な10秒（概算）を足した出撃として扱っています
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

アプリ v0.3：https://drive.google.com/file/d/1vaGriPGRYMml-tBNjG2Ky1H82kg2A5xT/
