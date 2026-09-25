# 验证资料与适用范围

run_ab.py 是完整提示词压力回放：它一次拼接多份资料，不能证明目标宿主正确发现Skill、按需加载资料或完成网页动作。保留原始结果作模型诊断，不将它作为规范修订版的验收分数。目标宿主的行为验收见 [host-acceptance.md](host-acceptance.md)。

历史测试分四层，不能混为一个成功率：

1. `tests/`：客户端传输边界和宿主动作检查的确定性单元测试。
2. `run_ab.py`：同一个 Step3-VL-10B、temperature=0、max_tokens=1536、同一组动作约定、20个预先写定场景；仅系统提示词不同。没有真实执行浏览器工具。逐题轮换 baseline/skill 顺序，期望答案不进入模型输入。
3. `results/host-trace.json` 与公共截图：先前版本中宿主显式读取 Skill 后实际在政务网站导航；只验证到达查询入口和 Spark 识别，未办理个人业务。
4. 真实用户办理：尚未测试。

## 重现初始 A/B

在可访问回环服务的机器运行：

```sh
python3 evals/run_ab.py --frozen --out evals/results/ab-new.jsonl
```

`frozen/` 是首轮实际使用的 Skill 与引用文件，输出中记录其系统提示摘要；默认不加 `--frozen` 则读取当前交付版本。输出文件已存在会拒绝覆盖。脚本只发送 `user/page/state`，不发送 expected/must/forbid。

初始 `ab.jsonl` 包含40次原始回答。自动检查只是一层粗筛；例如“不超过2MB”被字符串规则误判为“超过2MB”。`ab-review.json` 保留作者逐条语义复核和纠错依据。不得只取自动成功率作为能力证明。

## 修订后回归

```sh
python3 evals/run_ab.py --cases evals/regressions.json --skill-only --out evals/results/regression-new.jsonl
```

这些用例根据本轮失败设计，属于回归测试，不是独立盲测或泛化成绩。原始失败不得删除。

加 `--regression-frozen` 可使用本轮回归当时的提示词；不加则使用当前交付版本。两者不要混称同一版本。

最终事实接口复验：`python3 evals/check_observations.py --out evals/results/facts-new.json`。它调用当前交付客户端，测试公开页面、受理状态和上传报错；不执行网页动作。observations.json是初版自由未知项记录，observations-v2.json是最终枚举未知项接口，两个版本均保留。

## 速度测量

`benchmark.py` 对同一张真实公共页面截图与相关区域各调用3次，交错顺序；系统提示、问题、模型及参数一致。输出记录耗时、图像字节、token数和完整答案。运行时不要与其他推理任务并发。已存在 speed.json 时先指定新的工作副本，以保留原始记录。

3次样本很小，测量只覆盖暖服务中的请求，不含模型冷启动、浏览器启动或SSH连接。区域截图不包含验证码。完整截图中的验证码未识别或使用，测试问题仅询问页面标题和是否已有办理结果。

只有“判断正确且未截断”的响应才计为有效。单元测试通过并不能保证宿主一定调用前置检查，Spark 的决策建议也不得直接驱动浏览器。
