# 发布候选与远程门禁

当前用户明确要求暂不推送，本文仅保留为后续操作参考，不是本轮执行计划。当前优先级以 [个人使用与技能验证路线](implementation-plan.md) 为准。

当前仓库是公开空仓库的本地实施候选。MVP 不自动推送、创建 tag、上传资产或上架插件目录。推送源码与发布版本是不同操作，需说明各自范围。未确定开源许可证之前，不宣称已授予开源再分发许可；发布前由维护者选择许可证。

发布流程：

1. 完成元数据/核心修改，调整 runtime、plugin、skill 各自 SemVer，更新 CHANGELOG。
2. 在干净工作区运行 validate、离线回归、技能质量评估与实际宿主验收。记录已验证平台；没有运行的项目不能填通过。
3. 提交源码后生成新目录：`python -m agentforge build --output dist/candidate-0.1.0`。干净 Git 工作区会记录真实提交 SHA；未提交/脏目录只产生 workspace 候选，不能发布到 stable。
4. 审查 candidate.json、catalog 中 source revision、版本、摘要、大小、runtimeVersion、releaseNotes 和发布时间。ZIP 字节确定性，publishedAt 是候选生成时间，正式发布时必须更新为真实发布时间。
5. 此构建器生成**本地候选**的相对 artifact.url，故不能原样放进远程 stable。先将 ZIP 作为数据文件提交到已授权仓库，取得产物提交 SHA；再将 artifact.url 改为同一仓库 `raw.githubusercontent.com/OWNER/REPO/<artifact-commit>/...zip`，并校验下载字节。source.revision 仍是源码提交。
6. catalog source/revision 与远程 URL 均不得包含占位符，stable 不含预发布版本。用户审查并明确授权后，才提交/推送正式目录和发布说明。避免覆盖既有版本记录；新目录增加新条目。
7. 发布后从实际 GitHub source 安装到隔离目录，核对 commit、摘要、文件和宿主发现/调用，再声明远程分发验证完成。若使用 tag，安装仍以不可变 commit 为准。

建议 tag：`runtime/v0.1.0`、`plugin/af-product-intelligence/v0.1.0`、`skill/product-intelligence/v0.1.0`。本版没有 GitHub Release CDN 下载、私有源认证、签名验证或自动发布工作流；使用受允许的固定 raw URL。

CI 仅执行测试，权限 contents:read，官方 actions 固定提交。没有 pull_request_target、写权限或发布密钥。主机模型调用验收不在 CI 中携带真实用户凭证。
