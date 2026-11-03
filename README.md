<p align="center">
  <img src="docs/assets/hero.svg" alt="TeslaSkin — 用文字制作 Model Y 车机皮肤" width="100%" />
</p>

<p align="center">
  <strong>一句话，让你的 Model Y 换上喜欢的皮肤。</strong><br />
  不用提供参考图，告诉它主题，剩下的设计交给 TeslaSkin。
</p>

<p align="center">
  <a href="https://github.com/isunky/TeslaSkin/releases/latest"><img src="https://img.shields.io/github/v/release/isunky/TeslaSkin?style=flat-square&amp;labelColor=17232d&amp;color=e9b77f" alt="最新版本" /></a>
  <img src="https://img.shields.io/badge/Model_Y-车机皮肤-e9b77f?style=flat-square&amp;labelColor=17232d" alt="Model Y 车机皮肤" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-9daab5?style=flat-square&amp;labelColor=17232d" alt="Apache 2.0" /></a>
</p>

<p align="center">
  <a href="#安装">安装</a> · <a href="#使用">使用</a> · <a href="#作品示例">作品示例</a>
</p>

---

> **推荐在支持 Skill、内置生图和文件处理的 ChatGPT 环境中使用。** 这样可以在同一段对话里生成、调整并交付皮肤。不同客户端的能力可能不同；请以当前环境提供的功能为准。

## 安装

在支持安装 Skill 的助手中（例如 Codex），发送以下提示词：

```text
请从 https://github.com/isunky/TeslaSkin 安装最新版 tesla-skin Skill。
技能位于仓库的 skills/tesla-skin 目录，请安装到当前环境的个人 skills 目录，
检查所需依赖。如果已经安装，请先备份已有的自定义内容，再更新到最新版。
```

安装完成后，开启新对话或按客户端提示刷新，即可使用。如果当前环境不支持通过对话安装，可从 [Releases 下载最新技能包](https://github.com/isunky/TeslaSkin/releases/latest)，并按客户端的 Skill 安装方式导入。

## 使用

描述你想要的主题即可，例如：

```text
用 $tesla-skin 生成一款橘猫主题皮肤。
```

TeslaSkin 会自动补充配色、图案和细节，生成后还可以继续说：

```text
颜色再淡一点，只修改引擎盖。
```

目前适配内置白版对应的旧款 Model Y。生成的图片通过文件检查后，仍需在 App 和车辆上确认展示效果。

## 作品示例

以下提示词保留用户的原始输入；图片均为最终皮肤展开图。文件检查已通过，App 和实车效果待确认。

<table>
  <tr>
    <td width="50%" align="center"><strong>Hello Kitty</strong><br /><code>生成一款helloKetty的皮肤</code></td>
    <td width="50%" align="center"><strong>橘猫</strong><br /><code>生成橘猫主题皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="output/hello-kitty-v02.png"><img src="output/hello-kitty-v02.png" alt="Hello Kitty 主题皮肤成品展开图" width="420" /></a></td>
    <td align="center"><a href="output/orange-cat-v05.png"><img src="output/orange-cat-v05.png" alt="橘猫主题皮肤成品展开图" width="420" /></a></td>
  </tr>
  <tr>
    <td width="50%" align="center"><strong>鹦鹉</strong><br /><code>生成鹦鹉主题皮肤</code></td>
    <td width="50%" align="center"><strong>超级飞侠</strong><br /><code>生成超级飞侠主题皮肤</code></td>
  </tr>
  <tr>
    <td align="center"><a href="output/parrot-v01-lossless.png"><img src="output/parrot-v01-lossless.png" alt="鹦鹉主题皮肤成品展开图" width="420" /></a></td>
    <td align="center"><a href="output/superwings-v01.png"><img src="output/superwings-v01.png" alt="超级飞侠主题皮肤成品展开图" width="420" /></a></td>
  </tr>
</table>

---

项目代码与文档遵循 [Apache License 2.0](LICENSE)。示例中的角色和相关品牌属于各自权利人；本项目为独立社区项目，与 Tesla 无隶属关系。
