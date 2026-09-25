# Spark 安全部署与验收（第三版）

这是 Skill 的可选模型依赖，不是独立 Agent。当前节点已经迁移到 ~/screen-assistance-security-v3，原权重保留。24个运行文件通过原始内容锁，下载器元数据不进入运行目录。

## 启动与验证

使用有Docker权限的非root账户；固定ARM64镜像及模型锁见 image-lock.json 和 model-lock.json。旧的、不匹配目录不会覆盖。

```sh
export SCREEN_ASSISTANCE_RUNTIME="$HOME/screen-assistance-security-v3"
bash deployment/download-model.sh
bash deployment/start-spark.sh
bash deployment/start-relay.sh
# 等模型加载完成后执行：
bash deployment/check-spark.sh
```

新模型服务使用内部网络，不依赖Docker端口映射生效。start-relay.sh 另建固定目标转发容器，只监听宿主127.0.0.1:18000，将字节转发给当前模型IP:8000；不解析业务、不保存请求内容。模型容器重建导致IP变化时，旧转发会被检查拒绝复用；先核对其项目标签，再明确停止并另名保存旧转发，重新运行 start-relay.sh。不要自动删除不明容器。

模型容器非root、根文件系统只读、CapDrop=ALL、no-new-privileges，模型挂载只读，仅/cache和临时目录可写。USER/LOGNAME与显式Torch缓存目录避免没有passwd条目的非root UID触发初始化异常。当前仍需 trust-remote-code，自定义源码核查范围和限制见《第三版部署与验收报告.md》。离线环境变量保留，但网络隔离以容器实际配置为准。

内部网络阻止访问其他网络，但宿主网关仍可通信；这不是与宿主完全隔离。固定目标转发容器使用host网络，且不加载模型代码。只给可信宿主通过SSH隧道访问模型服务；没有面向公众暴露API或提供多租户安全保证。

本机使用原SSH隧道即可访问127.0.0.1:18000。图片会到远程Spark，仍需用户对数据发送的授权。图片辅助脚本需要Pillow；文字调用无需该依赖。

## 文件准备与供应链边界

prepare_model.py 只从下载缓存复制原锁中列出的文件，复制前后核对哈希。缓存只额外允许 .mv、.msc、figures/.gitkeep 三项已知附带文件，其他额外文件拒绝；运行目录严格匹配全部文件，拒绝符号链接和特殊文件。清单不得为了通过测试而重新生成。缓存加运行目录需要两份权重空间。

ModelScope源仍为master；实际字节不符时失败，不自动更新模型。哈希防漂移，不等于来源签名或依赖漏洞认证。原tokenizer兼容处理保留，BF16、8192上下文、单并发、0.45内存预算和eager配置未变。

## 本轮实测与回退

首次非root启动失败后自动回退成功；修正缓存环境后再次切换成功。旧模型容器 screen-assistance-vlm-before-security-v3 已保留；新模型和固定目标转发健康，重复运行启动检查通过。36项本地回归通过；一次合成图片推理约59秒，正确返回“已受理，待审核”。

需要回退时，先核实新模型、转发、旧备份均属于本项目；停止转发释放18000端口并另名保留，再停止并另名保存新模型，最后将旧备份恢复为 screen-assistance-vlm 并启动、检查健康。不要删除新旧权重或操作其他服务。当前无须回退。
