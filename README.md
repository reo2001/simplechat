# SimpleChat — Authenticated LLM Chat on AWS

## Overview

Amazon Bedrock（Amazon Nova Lite）を利用した、AWS上の認証付きLLMチャットアプリケーションです。React製フロントエンドとPython製AWS Lambdaを、API Gateway、Amazon Cognito、CloudFront、Amazon S3と組み合わせ、AWS CDKで一括構築します。

> AIエンジニアリング講座のベース実装をもとにした演習成果物です。教材提供コードを含み、`reo2001` は `lambda/index.py` に外部FastAPI推論経路を追加しました。通常はAmazon Bedrockを使用し、環境変数を設定した場合だけ外部推論APIへ切り替わる構成です。

![SimpleChat architecture: CloudFront and S3 frontend, Cognito authentication, API Gateway, Lambda, and Amazon Bedrock](./architecture.png)

## Architecture

1. ReactアプリをS3へ配置し、CloudFrontから配信します。
2. ユーザー登録とサインインはAmazon Cognitoが管理します。
3. ReactアプリはCognitoのIDトークンを付けてAPI Gatewayの `/chat` を呼び出します。
4. Cognitoオーソライザーで認証後、API GatewayがPython Lambdaを実行します。
5. LambdaがAmazon Bedrock Runtimeを呼び出し、Amazon Nova Liteの応答を返します。
6. AWS CDKが上記リソースの作成、フロントエンドの配置、実行時設定の生成を行います。

## Features

- メールアドレスを使ったユーザー登録、確認、サインイン
- Cognito認証済みユーザーだけが利用できるチャットAPI
- Amazon Nova Liteとの複数ターン会話
- 送信中表示、エラー表示、会話クリアを備えたReact UI
- CloudFrontと非公開S3バケットによるフロントエンド配信
- CDKによるインフラの構築と削除
- 任意設定による外部FastAPI推論エンドポイントの利用

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React 18, AWS Amplify UI, Axios |
| Authentication | Amazon Cognito |
| API | Amazon API Gateway REST API |
| Backend | AWS Lambda, Python 3.10, Boto3 |
| Generative AI | Amazon Bedrock, Amazon Nova Lite |
| Hosting | Amazon S3, Amazon CloudFront |
| Infrastructure as Code | AWS CDK v2, TypeScript |

## Project Structure

```text
.
├── bin/                         # CDKアプリのエントリーポイントとモデル・リージョン設定
├── frontend/
│   ├── public/                  # ReactのHTMLテンプレート
│   └── src/                     # 認証画面とチャットUI
├── lambda/
│   ├── index.py                 # Bedrockまたは外部推論APIを呼び出すチャット処理
│   └── requirements.txt         # Lambda用Python依存関係
├── lib/
│   └── bedrock-chatbot-stack.ts # Cognito、API、Lambda、S3、CloudFrontのCDK定義
├── architecture.png             # AWS構成図
├── cdk.json                     # CDK Toolkit設定
├── package.json                 # CDKプロジェクトの依存関係とコマンド
└── tsconfig.json                # TypeScriptコンパイラ設定
```

## Setup

### Prerequisites

- Node.js 20以上とnpm
- AWS CLIで認証情報を設定済みであること
- デプロイ先リージョンでAmazon Nova Liteを利用できること
- AWSリソースを作成できる権限があること

### Install and deploy

```bash
git clone https://github.com/reo2001/simplechat.git
cd simplechat
npm install
npx cdk bootstrap
npm run synth
npm run deploy
```

`npm install` の `postinstall` でフロントエンドの依存関係インストールと本番ビルドも実行されます。デプロイ完了後、出力された `CloudFrontURL` を開いてください。

AWSアカウントやリージョンを明示する場合は、AWS CLIのプロファイルや `CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION` を設定してから実行します。未指定時のリージョンは `us-east-1` です。

### Local frontend development

`frontend/.env.example` を `frontend/.env` にコピーし、デプロイ済みスタックの出力値を設定します。

```bash
cd frontend
npm install
npm start
```

`.env` はGit管理対象外です。CognitoのUser Pool IDやClient IDはクライアント設定値であり秘密鍵ではありませんが、環境ごとの値をリポジトリへ固定しない方針にしています。

## Usage

1. CloudFront URLを開き、メールアドレスでアカウントを登録します。
2. メールで届く確認コードを入力し、サインインします。
3. チャット欄へメッセージを入力して送信します。Enterで送信、Shift+Enterで改行できます。
4. 「会話をクリア」で画面上の会話履歴を削除できます。

## Design Notes

- 既定モデルは `bin/bedrock-chatbot.ts` の `us.amazon.nova-lite-v1:0` です。
- LambdaはCDKから渡される `MODEL_ID` を参照するため、コード内に環境固有のモデル設定を埋め込んでいません。
- デプロイ時にカスタムリソースが `config.js` をS3へ生成し、API URLとCognito設定をReactアプリへ渡します。
- 外部FastAPI推論経路は、CDK実行時に `EXTERNAL_MODEL_ENDPOINT` を設定した場合のみ有効です。未設定時はAmazon Bedrockを使用し、一時的なngrok URLはリポジトリに保存しません。
- S3バケットとCloudFrontなどのリソースは、学習環境を片付けやすい削除設定です。本番運用では保持ポリシー、ログ、監視、WAFなどを別途検討する必要があります。

外部推論APIを利用する例:

```bash
EXTERNAL_MODEL_ENDPOINT=https://example.com/predict npm run deploy
```

PowerShellでは次のように設定します。

```powershell
$env:EXTERNAL_MODEL_ENDPOINT = "https://example.com/predict"
npm run deploy
```

## Cleanup

検証後にAWSリソースを削除する場合は、次を実行します。

```bash
npm run destroy
```

CloudWatch Logsなど、スタック外または保持設定のリソースが残っていないかAWSコンソールでも確認してください。
