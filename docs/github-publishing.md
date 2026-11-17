# 发布到 GitHub：仓库初始化与凭证配置

本文说明如何把本项目推送到 GitHub，以及几种凭证配置方式。
**不要在代码或文档中写入任何真实 token / 密码。**

## 1. 先在 GitHub 创建空仓库

浏览器打开 <https://github.com/new>：

- Repository name：`sqlark-connection-decryptor`
- Description：`Decrypt SQLark (百灵) saved database connection files and recover passwords`
- 可见性：Public（开源）或 Private（先私有验证）
- **不要**勾选 “Add a README / .gitignore / license”（本地已有）

## 2. 本地初始化并推送

```bash
cd sqlark-decryptor
git init
git add .
git commit -m "feat: initial release of SQLark connection decryptor"
git branch -M main
git remote add origin https://github.com/<你的用户名>/sqlark-connection-decryptor.git
git push -u origin main
```

> 推送前先运行：
> `pytest`、`ruff check .`、`python scripts/check_no_secrets.py`

## 3. 凭证配置（四选一）

浏览器里已登录 GitHub **不等于** git 已获得授权：git 需要独立的凭据，浏览器 Cookie
不能被 git 复用，也不应该去导出浏览器会话。

### 方式 A：Git Credential Manager（Windows 推荐，最省事）

Git for Windows 自带 GCM。第一次 `git push` 会弹出窗口：

1. 选择 “Sign in with your browser”；
2. 浏览器会打开 GitHub 授权页（你已登录，直接点 Authorize）；
3. 之后凭据由 Windows 凭据管理器保管，无需重复输入。

确认使用的是 GCM：

```bash
git config --global credential.helper manager
```

### 方式 B：Personal Access Token（PAT，通用）

1. 浏览器打开 <https://github.com/settings/tokens>；
2. 推荐 **Fine-grained token**：
   - Repository access：仅选择目标仓库；
   - Permissions：`Contents: Read and write`、`Metadata: Read`（需要 Actions 时再加 `Workflows`）；
3. 生成后复制一次（页面关闭后不再显示）；
4. 推送时作为密码使用：

```bash
git config --global credential.helper manager   # 由凭据管理器保存
git push -u origin main
# Username: <GitHub 用户名>
# Password: <粘贴 PAT，不是账号密码>
```

不建议把 token 直接写进 remote URL（`https://<token>@github.com/...`），因为它会以明文
保存在 `.git/config` 和 shell 历史里。若确实需要脚本化，使用环境变量：

```bash
export GITHUB_TOKEN=<PAT>     # PowerShell: $env:GITHUB_TOKEN="<PAT>"
```

### 方式 C：SSH Key（免 token，长期使用）

```bash
ssh-keygen -t ed25519 -C "you@example.com"     # 一路回车
# 把 ~/.ssh/id_ed25519.pub 的内容粘贴到
# GitHub → Settings → SSH and GPG keys → New SSH key
ssh -T git@github.com                          # 出现 "Hi <user>!" 即成功
git remote set-url origin git@github.com:<你的用户名>/sqlark-connection-decryptor.git
```

### 方式 D：GitHub CLI（后续管理最方便）

```powershell
winget install --id GitHub.cli
gh auth login          # 选择 GitHub.com → HTTPS → Login with a web browser
gh repo create sqlark-connection-decryptor --public --source . --push
```

## 4. 关于“在自动化工具 / DeepSeek Harness 里使用 GitHub”

DSH 本身不保存 GitHub 凭据，它只执行你机器上的 `git` / `gh` 命令，因此：

- 若你已在**系统层面**配置好 GCM/SSH/`gh auth`，这些命令可直接推送；
- 若希望由自动化代理代推，推荐在启动代理前设置**最小权限、可随时撤销**的 PAT：

  ```powershell
  $env:GITHUB_TOKEN = "<fine-grained PAT>"
  ```

  代理在推送时使用环境变量即可，不要把 token 写进项目文件；
- 用完在 GitHub 上 Revoke 该 token。

## 5. 首次发布后建议的仓库设置

| 项目 | 建议 |
| --- | --- |
| About | 填写描述、主页；Topics：`sqlark` `password-recovery` `aes` `reverse-engineering` `tkinter` `forensics` |
| License | 已包含 MIT，GitHub 会自动识别 |
| Branch protection | `main` 要求 PR + CI 通过（个人项目可选） |
| Actions | 确认 `.github/workflows/ci.yml` 已启用 |
| Secrets | 不要添加任何真实凭据；CI 不需要 token |
| Releases | 打 tag（如 `v0.1.1`）后由 Release 工作流自动构建 6 个平台/架构产物并附 `SHA256SUMS.txt` |
| SECURITY | 已包含 [SECURITY.md](../SECURITY.md)，启用 GitHub 私密漏洞报告 |

## 6. 常见问题

- **403 / Authentication failed**：Windows 凭据管理器里残留了旧的 GitHub 凭据，
  在「控制面板 → 凭据管理器 → Windows 凭据」删除 `git:https://github.com` 后重试。
- **push 被拒绝（non-fast-forward）**：`git pull --rebase origin main` 后再推。
- **文件过大被拒绝**：不要把 exe / zip / 连接文件提交进 Git，二进制放 Releases 附件。
- **不要**把浏览器 Cookie、`Login Data`、会话文件放进仓库或交给任何工具。
