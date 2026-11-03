<p align="center">
  <img src="docs/assets/hero.svg" alt="TeslaSkin — 用文字制作 Model Y 车机皮肤" width="100%" />
</p>

<p align="center">
  <strong>用一句主题描述，开始制作你的 Model Y 车机皮肤。</strong><br />
  内置白版 · 文字生图 · 对话修改 · 超限压缩 · 文件校验
</p>

<p align="center">
  <a href="skills/tesla-skin-generator/SKILL.md"><img src="https://img.shields.io/badge/Agent_Skill-tesla--skin--generator-17232d?style=flat-square&amp;labelColor=101820" alt="Agent Skill" /></a>
  <img src="https://img.shields.io/badge/Vehicle-Model_Y-e9b77f?style=flat-square&amp;labelColor=17232d" alt="Model Y" />
  <a href="tests/"><img src="https://img.shields.io/badge/Local_tests-18_passed-7eaa91?style=flat-square&amp;labelColor=17232d" alt="18 local tests passed" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-9daab5?style=flat-square&amp;labelColor=17232d" alt="Apache 2.0" /></a>
</p>

<p align="center">
  <a href="#安装">安装</a> · <a href="#使用">使用</a> · <a href="#生成示例与实测状态">生成示例</a> · <a href="#检查与测试">检查与测试</a> · <a href="skills/tesla-skin-generator/SKILL.md">技能指令</a>
</p>

---

> **推荐基于 ChatGPT 运行本技能，以获得最佳使用体验。** 优先选择同时支持 Skills、内置生图和文件处理的环境，便于在同一对话中完成白版编辑、持续修改、超限压缩与检查。不同入口、套餐和工作区的工具可用性可能不同，请确认当前会话具备相应能力。

## 从想法开始

> 用 `$tesla-skin-generator` 生成一款奶油白底、橘猫主题、简洁可爱的 Model Y 皮肤。

TeslaSkin 是运行在支持 Agent Skills 和内置生图能力环境中的技能。它将主题描述、Model Y 固定贴图模板、分区方向规则和文件检查串成一套制作流程。你只需描述想要的设计，无需每次上传白版或准备风格参考图。

| 描述主题 | 生成与修改 | 检查与交付 |
| :--- | :--- | :--- |
| 说出风格、配色和元素，默认制作一款 | 基于内置白版生图，通过对话继续调整 | 超限时先压缩，再检查尺寸、体积和透明范围，保留原图与提示词 |

> **当前状态：实验性。** 技能、压缩与检查脚本已可使用，18 项本地测试通过。下方保留原始生图实测记录；压缩步骤用于解决文件体积，不修复尺寸、方向或轮廓。当前示例仍是候选图，尚无通过全部检查的上车成品。详见[验收记录](output/validation-summary.md)。

### 为什么推荐 ChatGPT

- **文字和白版一起处理。** 本技能围绕 ChatGPT 的原生生图、图片编辑和对话式修改流程设计，并已在当前环境实测，可直接将内置白版作为结构约束。
- **在同一对话中持续调整。** 从“生成橘猫主题”到“只改引擎盖”，可以接续已有作品与修改要求，减少在多个工具间搬运图片、重复说明设计的操作。
- **将生成与交付衔接起来。** 具备文件处理及 Python 执行能力的环境，可继续运行随包的压缩和校验脚本，保留版本、提示词和处理报告。

这是基于本技能工作流设计的使用建议，不代表其他平台不能运行，也不保证生图必然满足精确 UV 要求。生成后仍需完整检查。相关能力及使用方式可参考 [ChatGPT 图片生成与编辑](https://learn.chatgpt.com/docs/image-generation)和 [Skills 官方说明](https://learn.chatgpt.com/docs/build-skills)。

## 安装

需要支持 Agent Skills 的运行环境、可用的内置生图工具，以及用于校验的 **Python 3 + Pillow**。技能本身不包含生图模型，也不要求单独配置 API Key；无生图工具时会明确说明，不自动切换到付费 API。

### 1. 获取项目

```powershell
git clone https://github.com/isunky/TeslaSkin.git
cd TeslaSkin
python -m pip install -r requirements.txt
```

### 2. 安装到个人 skills 目录

**Windows / PowerShell**

```powershell
$skillsDir = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $env:USERPROFILE '.codex\skills'
}
New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
Copy-Item -LiteralPath '.\skills\tesla-skin-generator' -Destination $skillsDir -Recurse
```

<details>
<summary>macOS / Linux</summary>

```bash
python3 -m pip install -r requirements.txt
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/tesla-skin-generator "${CODEX_HOME:-$HOME/.codex}/skills/"
```

</details>

也可下载 [技能 ZIP 包](tesla-skin-generator.zip)，将其中的 `tesla-skin-generator` 文件夹放入个人 skills 目录。安装后在支持该技能的聊天中调用；已有同名技能时，请先备份你的自定义内容。

以上目录复制步骤适用于读取本地 skills 目录的环境。ChatGPT 中请使用当前客户端提供的技能入口；网页及手机端需通过包含该技能的插件使用。[官方支持范围](https://learn.chatgpt.com/docs/build-skills)

## 使用

**创建一款皮肤**

```text
用 $tesla-skin-generator 生成一款奶油白底、橘猫主题的 Model Y 皮肤。
简洁可爱，点缀少量猫爪，不要文字。
```

**通过对话继续修改**

```text
底色再淡一点，橘色保持不变。
```

```text
只修改引擎盖，把猫换成睡觉的姿势，其他部位保留。
```

每次制作会保存版本化 PNG、实际提示词和检查结果。示例目录：

```text
output/
├── orange-cat-v01.png
├── orange-cat-v01.prompt.txt
└── orange-cat-v01.validation.json
```

文件超过 1,000,000 字节时先进行压缩，保留原图，并重新检查压缩后的文件。其他检查失败时最多做一次定向生图修正，保留前一版本。仍不合格的图片会明确标注为候选图。

## 生成示例与实测状态

<table>
  <tr>
    <td align="center" width="50%"><strong>内置白版 · 几何基准</strong></td>
    <td align="center" width="50%"><strong>橘猫主题 · 修正后候选图</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="skills/tesla-skin-generator/assets/template.png" alt="1024×1024 Model Y 白版，包含 16 个主要白色分区和透明留空" width="390" /></td>
    <td align="center"><img src="output/orange-cat-v02.png" alt="奶油白与橘猫主题候选图，尚未通过文件及方向检查" width="390" /></td>
  </tr>
  <tr>
    <td align="center">1024 × 1024 · 16 个主要白色分区</td>
    <td align="center">未通过检查 · 仅展示设计方向</td>
  </tr>
</table>

2026-11-03 使用内置生图工具实测：

| 检查项 | 目标 | 修正后结果 |
| :--- | :--- | :--- |
| 格式 | PNG | 通过 |
| 尺寸 | 1024 × 1024 | 1254 × 1254，未通过 |
| 体积 | ≤ 1,000,000 字节 | 1,449,204 字节，未通过 |
| 方向与轮廓 | 对应白版及分区规则 | 门板方向未执行，轮廓与透明留空仍需修正 |
| 实车效果 | 车辆导入确认 | 尚未验证 |

生图提示词中的约束不代表模型一定执行。脚本负责文件与几何检查，图案方向、接缝及最终车机效果仍需分别确认。

## 模板规则

- **白版是几何基准。** 固定部位位置、轮廓、细条和透明留空；中心透明洞不能被当作车顶补图。
- **方向按部位处理。** 展开图左右仅指画布位置，不直接推断驾驶员侧；样例中未验证的实际部位对应已单独标记。
- **参考图只帮助理解结构。** `Sample/` 中部分作品的尺寸、透明区和方向不同，不用于替换白版，也不默认继承其风格或角色。
- **只适配当前白版。** 其他年份或车型需要对应模板，不能通过拉伸套用。

完整坐标、方向证据与限制见 [布局规则](skills/tesla-skin-generator/references/layout.md)。

## 检查与测试

### 超限时自动压缩

Skill 会读取实际文件体积。超过 **1,000,000 字节**时，先无损优化 PNG、去掉非必要元数据；仍超限时依次尝试 256、128、64、32 色的 RGB 量化，选择首个达标结果。像素尺寸和完整透明通道保持不变，原图不覆盖。

也可手动运行：

```powershell
python skills/tesla-skin-generator/scripts/compress_skin.py output/orange-cat-v02.png output/orange-cat-v02-export.png --report output/orange-cat-v02-export.compression.json
python skills/tesla-skin-generator/scripts/validate_skin.py output/orange-cat-v02-export.png --report output/orange-cat-v02-export.validation.json
```

颜色量化可能造成色差或色带，需要查看结果。仍无法达标时明确报告失败，不通过缩图、裁图或移除透明度降低体积。**体积达标不等于皮肤整体合格**，压缩后必须重新校验。

仓库中另附[压缩实测候选图](output/orange-cat-v02-c.png)：从 1,449,204 字节降至 886,615 字节，完整 alpha 保持一致；尺寸仍不合格，不能视为上车成品。具体过程见[压缩报告](output/orange-cat-v02-c.compression.json)。重复运行命令时请使用新的输出名称。

### 文件校验

检查一张生成图：

```powershell
python skills/tesla-skin-generator/scripts/validate_skin.py output/orange-cat-v02.png
```

另存 JSON 检查报告：

```powershell
python skills/tesla-skin-generator/scripts/validate_skin.py output/orange-cat-v02.png --report output/review.json
```

脚本不修改图片，不覆盖已有报告。退出码 `0` 表示文件检查通过，`1` 表示图片或模板不合格，`2` 表示命令、依赖或报告保存错误。

运行回归测试：

```powershell
python -m unittest discover -s tests -v
```

目前包含 18 项测试：11 项文件与几何校验，以及 7 项压缩回归，覆盖无损像素保留、颜色量化、完整 alpha 保留、超限失败、禁止覆盖、非法格式和报告保存。

## 项目结构

```text
TeslaSkin/
├── skills/tesla-skin-generator/
│   ├── SKILL.md                # 制作流程与交付规则
│   ├── agents/openai.yaml      # 技能名称与默认调用提示
│   ├── assets/template.png     # 独立打包的固定白版
│   ├── references/layout.md    # 分区、方向、规格与实测限制
│   └── scripts/
│       ├── compress_skin.py     # 超限压缩，保留尺寸与 alpha
│       └── validate_skin.py     # 文件与透明轮廓检查
├── tests/                      # 文件与几何检查回归测试
├── output/                     # 候选图、提示词和验收记录
├── Sample/                     # 用户提供的第三方结构参考
├── template.png                # 原始白版
├── vehicle_image.png           # 原始车辆图，技能运行不依赖
└── tesla-skin-generator.zip     # 可携带的技能包
```

## 许可与致谢

项目代码与文档遵循 [Apache License 2.0](LICENSE)。`Sample/` 中第三方示例的图案及角色版权属于各自权利人，不因本项目的软件许可证而重新授权。车型模板、Tesla 名称及相关标识归其权利人所有；本项目为独立社区项目，与 Tesla 无隶属关系。

- [Tesla 官方自定义皮肤模板与规格](https://github.com/teslamotors/custom-wraps)
- [OpenAI Agent Skills 文档](https://learn.chatgpt.com/docs/build-skills)
